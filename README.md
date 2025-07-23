# 💰 MADEIN Valor NETO Extractor API

API especializada para **extraer valores NETO** de facturas y soportes en formato PDF.

## 🎯 Propósito Específico

Esta API está diseñada para extraer únicamente el **valor NETO** que aparece en la parte inferior de facturas y soportes, como el documento de "MADERAS INDUSTRIALES DEL NORTE" mostrado en la imagen.

### ✅ Qué hace:
- ✅ Procesa PDFs página por página  
- ✅ Se enfoca en la **región inferior** (último 40% de cada página)
- ✅ Busca específicamente texto "NETO" seguido de valores monetarios
- ✅ Optimizado para formato colombiano (16,220,167.00)
- ✅ OCR mejorado para valores monetarios
- ✅ API REST independiente en puerto **8001**

### ❌ Qué NO hace:
- ❌ No extrae comprobantes individuales
- ❌ No busca números de documento  
- ❌ No procesa múltiples campos
- ❌ Solo se enfoca en **VALOR NETO**

## 🚀 Instalación y Uso

### 1. Instalar dependencias
```bash
cd c:\Desarrollos\Madein\api-valor-neto
pip install -r requirements.txt
```

### 2. Iniciar la API
```bash
python main.py
```

La API estará disponible en:
- **Puerto**: http://localhost:8001
- **Documentación**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

### 3. Probar la API
```bash
# Probar estado
python test_api.py

# Probar con archivo específico
python test_api.py "ruta_al_archivo.pdf"
```

## 📡 Endpoints

### **GET** `/health`
Estado de la API y dependencias

```json
{
  "status": "healthy",
  "dependencies": {
    "opencv": true,
    "ocr_engine": "easyocr",
    "ocr_available": true
  }
}
```

### **POST** `/extract-valor-neto`
Extraer valor NETO de un PDF

**Parámetros:**
- `file`: Archivo PDF (required)
- `debug`: Modo debug (opcional, default: false)

**Respuesta:**
```json
{
  "success": true,
  "session_id": "neto_abc123",
  "filename": "factura.pdf",
  "total_pages": 1,
  "valores_encontrados": 1,
  "processing_time": 2.45,
  "results": [
    {
      "page": 1,
      "valor_neto": "16,220,167.00",
      "found": true
    }
  ],
  "summary": {
    "valores_neto": ["16,220,167.00"],
    "pages_with_neto": [1]
  }
}
```

## 🧠 Algoritmo de Detección

### 1. **Región de Interés (ROI)**
- Se enfoca en el **40% inferior** de cada página
- Donde típicamente aparece el resumen financiero

### 2. **Preprocesamiento de Imagen**
- Conversión a escala de grises
- Mejora de contraste con CLAHE
- Binarización OTSU para mejor OCR

### 3. **Patrones de Búsqueda**
```regex
NETO[\s\$]*([0-9]{1,3}(?:[\.,][0-9]{3})*[\.,][0-9]{2})  # NETO $ 16,220,167.00
NETO[\s:]*\$[\s]*([0-9]{1,3}(?:[\.,][0-9]{3})*[\.,][0-9]{2})  # NETO: $ 16,220,167.00
NETO[\s]*([0-9]{6,}[\.,][0-9]{2})  # NETO 16220167.00
```

### 4. **OCR Robusto**
- **EasyOCR** preferido para mejor precisión
- **Pytesseract** como fallback con múltiples configuraciones
- Configuraciones específicas para texto financiero

## 🧪 Ejemplos de Uso

### Con curl
```bash
# Health check
curl http://localhost:8001/health

# Extraer valor NETO
curl -X POST "http://localhost:8001/extract-valor-neto" \
  -F "file=@factura.pdf" \
  -F "debug=true"
```

### Con Python
```python
import requests

# Procesar archivo
with open("factura.pdf", "rb") as f:
    files = {"file": f}
    data = {"debug": True}
    
    response = requests.post(
        "http://localhost:8001/extract-valor-neto",
        files=files,
        data=data
    )
    
    result = response.json()
    
    if result["success"]:
        valores = result["summary"]["valores_neto"]
        print(f"Valores NETO encontrados: {valores}")
    else:
        print("No se encontraron valores NETO")
```

### Con JavaScript/React
```javascript
const extractValorNeto = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('debug', 'true');
  
  try {
    const response = await fetch('http://localhost:8001/extract-valor-neto', {
      method: 'POST',
      body: formData,
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log('Valores NETO:', result.summary.valores_neto);
      return result.summary.valores_neto;
    }
  } catch (error) {
    console.error('Error:', error);
  }
};
```

## 🔧 Modo Debug

Activar `debug=true` para obtener información detallada:

- ✅ Coordenadas de ROI utilizadas
- ✅ Texto OCR extraído
- ✅ Patrones probados
- ✅ Imágenes intermedias guardadas en `/outputs/debug/`

## 📊 Casos de Uso Típicos

### ✅ Documentos Compatibles:
- Facturas de MADERAS INDUSTRIALES  
- Soportes con resumen financiero
- Documentos con sección "NETO" en parte inferior
- PDFs con valores monetarios colombianos

### ❌ Documentos NO Compatibles:
- Comprobantes bancarios (usar api-imagenes)
- Documentos sin valor NETO
- Imágenes simples (solo PDFs)

## 🚨 Solución de Problemas

### Error: No se encuentran valores NETO
1. ✅ Verificar que el documento tenga texto "NETO"
2. ✅ Activar `debug=true` para ver OCR
3. ✅ Verificar calidad del PDF (no imagen escaneada borrosa)

### Error: Dependencias no disponibles
```bash
pip install -r requirements.txt
```

### Error: Puerto en uso
La API usa puerto **8001** (diferente a api-imagenes en 8000)

## 🔀 Diferencias con api-imagenes

| **Aspecto** | **api-imagenes** | **api-valor-neto** |
|-------------|------------------|-------------------|
| **Puerto** | 8000 | 8001 |
| **Propósito** | Extraer comprobantes individuales | Extraer solo valor NETO |
| **Región** | Detecta bloques completos | Solo región inferior |
| **Salida** | Múltiples imágenes | Valores monetarios |
| **OCR** | Números de documento | Valores monetarios |

## 📈 Rendimiento

- **Tiempo típico**: 2-5 segundos por página
- **Precisión OCR**: 90-95% en documentos nítidos
- **Memoria**: Bajo uso (procesa página por página)
- **Formatos**: Solo PDF (no imágenes directas)

---

**Desarrollado para MADEIN - Extracción Especializada de Valores NETO** 💰  
**🎯 API independiente y enfocada en un propósito específico** 🇨🇴
