#!/usr/bin/env python3
import re
import uuid
import time
import shutil
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Optional

import cv2
import numpy as np
import pypdfium2 as pdfium
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# — Logging —
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("madein")

app = FastAPI(title="MADEIN Full Extraction", version="3.4.2")

# Carpeta de salida para imágenes
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
app.mount("/files", StaticFiles(directory=str(OUTPUT_DIR)), name="files")

# — Lazy init de EasyOCR Reader —
_OCR_READER = None
def get_ocr_reader():
    global _OCR_READER
    if _OCR_READER is None:
        import easyocr  # se importa solo al primer uso
        logger.info("Inicializando EasyOCR...")
        _OCR_READER = easyocr.Reader(["es", "en"], gpu=False, verbose=False)
    return _OCR_READER

# — UTILITIES OCR & MONEY —

def ocr_text(img: np.ndarray) -> str:
    reader = get_ocr_reader()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binar = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return " ".join(reader.readtext(binar, detail=0, paragraph=False))

def normalize_money(raw: str) -> str:
    s = raw.strip()
    s = re.sub(r"\s+", "", s)
    if "," in s and s.count(",") == 1 and s.count(".") > 1:
        s = s.replace(".", "").replace(",", ".")
    elif "." in s and s.count(".") == 1 and "," in s:
        s = s.replace(",", "")
    s = re.sub(r"[^\d\.]", "", s)
    if "." not in s:
        s += ".00"
    intp, decp = s.split(".")
    decp = (decp + "00")[:2]
    return f"{intp}.{decp}"

def find_any(patterns: List[str], text: str) -> Optional[str]:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None

# — PATTERNS COMPROBANTES —

COMPRO_PATTERNS = {
    "documento": [
        r"Documento[:\s]*(\d{6,})",
        r"Doc(?:umento)?[:\s]*(\d{6,})",
        r"(\d{6,})"
    ],
    "valor": [
        r"Valor[:\s\$]*([\d\.,\s]+)",
        r"([\d]{1,3}(?:\.\d{3})+,\d{2})"
    ]
}

def detect_comprobantes(
    img: np.ndarray,
    page_text: Optional[str],
    min_area: int = 50_000
) -> List[Dict]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 51, 9
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25,25))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    comps = []
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        if w*h < min_area:
            continue

        crop = img[y:y+h, x:x+w]
        texto = ocr_text(crop)

        raw_doc = find_any(COMPRO_PATTERNS["documento"], texto)
        doc = (raw_doc.lstrip("0") or "0") if raw_doc else uuid.uuid4().hex[:8]

        raw_val = find_any(COMPRO_PATTERNS["valor"], texto)
        if not raw_val and page_text:
            raw_val = find_any(COMPRO_PATTERNS["valor"], page_text)
        valor = normalize_money(raw_val) if raw_val else None

        comps.append({
            "bbox": [int(x), int(y), int(w), int(h)],
            "documento": doc,
            "valor": valor,
            "imagen": crop
        })

    comps.sort(key=lambda c: (c["bbox"][1], c["bbox"][0]))
    return comps

# — ENDPOINT: EXTRAER IMÁGENES —

@app.post("/extract-imagenes")
async def extract_imagenes(
    file: UploadFile = File(..., description="PDF con varios comprobantes")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo PDF permitido")

    tmpdir = Path(tempfile.mkdtemp(prefix="imgs_"))
    pdf_path = tmpdir / file.filename
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    session = f"imgs_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    out_dir = OUTPUT_DIR / session
    out_dir.mkdir(parents=True)

    resultados = []
    doc = pdfium.PdfDocument(str(pdf_path))

    for page_idx, page in enumerate(doc, start=1):
        try:
            bmp = page.render(scale=300/72)
            img = cv2.cvtColor(np.array(bmp.to_pil()), cv2.COLOR_RGB2BGR)
            page_text = ocr_text(img)

            comps = detect_comprobantes(img, page_text=page_text)
            for comp in comps:
                fn = f"{comp['documento']}.png"
                save_path = out_dir / fn
                cv2.imwrite(str(save_path), comp["imagen"])
                resultados.append({
                    "page": page_idx,
                    "documento": comp["documento"],
                    "valor": comp["valor"],
                    "imagen_url": f"/files/{session}/{fn}"
                })
        except Exception as e:
            logger.exception(f"Error en página {page_idx}: {e}")

    try:
        doc.close()
    except:
        pass

    try:
        shutil.rmtree(tmpdir)
    except PermissionError as e:
        logger.warning(f"No se pudo eliminar {tmpdir}: {e}")

    return JSONResponse({
        "success": True,
        "session": session,
        "total_comprobantes": len(resultados),
        "results": resultados
    })

# — ENDPOINT: EXTRAER VALORES FISCALES —

@app.post("/extract-valor-neto")
async def extract_valor_neto(
    files: List[UploadFile] = File(..., description="Uno o varios PDFs")
):
    patterns = {
        "subtotal":  [r"SUBTOTAL[:\s\$]*([\d\.,\s]+)"],
        "iva":       [r"I\.?V\.?A[:\s\$]*([\d\.,\s]+)", r"IVA[:\s\$]*([\d\.,\s]+)"],
        "ret":       [r"RET[:\s\$]*([\d\.,\s]+)"],
        "reten_iva": [r"RETEN\.?IVA[:\s\$]*([\d\.,\s]+)"],
        "neto":      [r"NETO[:\s\$]*([\d\.,\s]+)"]
    }

    results = []
    for upload in files:
        if not upload.filename.lower().endswith(".pdf"):
            continue

        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.write(await upload.read())
        tmp.flush()

        full_text = ""
        doc2 = pdfium.PdfDocument(tmp.name)
        for page in doc2:
            bmp = page.render(scale=300/72)
            img = cv2.cvtColor(np.array(bmp.to_pil()), cv2.COLOR_RGB2BGR)
            full_text += "\n" + ocr_text(img)
        try:
            doc2.close()
        except:
            pass

        extracted: Dict[str, str] = {}
        for field, pats in patterns.items():
            raw = find_any(pats, full_text)
            if raw:
                extracted[field] = normalize_money(raw)

        if "neto" not in extracted:
            raise HTTPException(422, f"NETO no encontrado en {upload.filename}")

        results.append({"filename": upload.filename, **extracted})
        try:
            tmp.close()
        except:
            pass

    return JSONResponse({"success": True, "files": results})

if __name__ == "__main__":
    import uvicorn
    # reload=False para evitar recarga continua
    uvicorn.run("main:app", host="localhost", port=8000, reload=False)
