#!/usr/bin/env python3
"""
Crear imagen de prueba para probar la API MADEIN
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    # Crear imagen blanca de 800x600
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Intentar usar fuente del sistema, si no usar default
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
        font_small = font
    
    # Simular 3 comprobantes como rectángulos
    comprobantes = [
        {"x": 50, "y": 50, "w": 300, "h": 150, "doc": "123456789"},
        {"x": 400, "y": 80, "w": 320, "h": 180, "doc": "987654321"},
        {"x": 100, "y": 350, "w": 280, "h": 140, "doc": "555666777"}
    ]
    
    for i, comp in enumerate(comprobantes):
        x, y, w, h = comp["x"], comp["y"], comp["w"], comp["h"]
        doc_id = comp["doc"]
        
        # Dibujar rectángulo del comprobante
        draw.rectangle([x, y, x+w, y+h], outline='black', width=2)
        
        # Título del comprobante
        draw.text((x+10, y+10), f"COMPROBANTE DE PAGO #{i+1}", fill='black', font=font)
        
        # Número de documento
        draw.text((x+10, y+40), f"Documento: {doc_id}", fill='blue', font=font)
        
        # Información adicional
        draw.text((x+10, y+70), "Fecha: 2025-01-20", fill='black', font=font_small)
        draw.text((x+10, y+90), f"Monto: ${(i+1)*1500:.2f}", fill='black', font=font_small)
        draw.text((x+10, y+110), "Estado: AUTORIZADO", fill='green', font=font_small)
        
        # Líneas decorativas
        draw.line([x+10, y+h-20, x+w-10, y+h-20], fill='gray', width=1)
    
    # Título principal
    draw.text((250, 10), "FACTURAS TRUPER - PRUEBA", fill='red', font=font)
    
    # Guardar imagen
    output_path = "test_comprobantes.png"
    img.save(output_path)
    print(f"✅ Imagen de prueba creada: {output_path}")
    print(f"📊 Contiene 3 comprobantes simulados")
    print(f"📁 Úsala en http://localhost:8000/docs para probar")
    
    return output_path

if __name__ == "__main__":
    create_test_image() 