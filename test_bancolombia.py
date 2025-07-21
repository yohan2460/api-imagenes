#!/usr/bin/env python3
"""
Script de prueba para la API MADEIN con documentos bancarios tipo Bancolombia
"""
import requests
import json
from PIL import Image, ImageDraw, ImageFont
import os

def create_bancolombia_test():
    """Crear imagen simulando comprobantes de Bancolombia"""
    # Crear imagen de 800x1400 (tamaño ajustado para 3 comprobantes)
    img = Image.new('RGB', (800, 1400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Colores Bancolombia
    blue_color = '#003366'
    yellow_color = '#FFD700'
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 16)
        font_normal = ImageFont.truetype("arial.ttf", 12)
        font_small = ImageFont.truetype("arial.ttf", 10)
    except:
        font_title = ImageFont.load_default()
        font_normal = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Simular 3 comprobantes de Bancolombia con datos de la imagen real
    comprobantes_data = [
        {
            "y_pos": 50,
            "cuenta_num": "245-000003-15",
            "doc_num": "000000801363627",
            "nit": "890531228",
            "valor": "4.688.072,50",
            "beneficiario": "MADERAS INDUSTRIALES"
        },
        {
            "y_pos": 400,
            "cuenta_num": "245-000003-15", 
            "doc_num": "000000801363627",
            "nit": "890531228", 
            "valor": "2.564.846,00",
            "beneficiario": "MADERAS INDUSTRIALES"
        },
        {
            "y_pos": 750,
            "cuenta_num": "091-600075-09",
            "doc_num": "000000898059575",
            "nit": "890531228",
            "valor": "536.800,00", 
            "beneficiario": "MADERAS INDUSTRIALES"
        }
    ]
    
    for i, comp in enumerate(comprobantes_data):
        y = comp["y_pos"]
        
        # Marco del comprobante (aumentado para incluir más contenido)
        draw.rectangle([20, y, 780, y+280], outline='black', width=2)
        draw.rectangle([20, y, 780, y+35], fill=blue_color, outline='black', width=2)
        
        # Header con logo simulado
        draw.text((30, y+8), "🏦 Bancolombia", fill='white', font=font_title)
        draw.text((650, y+8), "Recibo individual de pagos", fill='white', font=font_small)
        
        # Información principal
        draw.text((30, y+50), "Compañía:", fill='black', font=font_normal)
        draw.text((120, y+50), comp["beneficiario"], fill='black', font=font_normal)
        
        draw.text((30, y+75), "NIT Compañía:", fill='black', font=font_normal)
        draw.text((130, y+75), comp["nit"], fill='black', font=font_normal)
        
        draw.text((30, y+100), "Fecha Actual:", fill='black', font=font_normal)
        draw.text((130, y+100), "Martes, 24 de junio de 2025 - 10:42 AM", fill='black', font=font_normal)
        
        # NÚMERO DE CUENTA Y DOCUMENTO - Región superior derecha que busca la API
        draw.text((450, y+50), "Número de cuenta:", fill='black', font=font_normal)
        draw.text((580, y+50), comp["cuenta_num"], fill='black', font=font_normal)
        
        draw.text((450, y+75), "Tipo de cuenta:", fill='black', font=font_normal)
        draw.text((560, y+75), "Corriente", fill='black', font=font_normal)
        
        draw.text((450, y+100), "Entidad:", fill='black', font=font_normal)
        draw.text((510, y+100), "BANCOLOMBIA", fill='black', font=font_normal)
        
        draw.text((450, y+125), "Documento:", fill=blue_color, font=font_title)
        draw.text((540, y+125), comp["doc_num"], fill=blue_color, font=font_title)
        
        # Agregar referencias adicionales que puede captar el OCR
        draw.text((450, y+150), "Referencia:", fill='black', font=font_small)
        draw.text((520, y+150), comp["doc_num"], fill='black', font=font_small)
        
        # Valor y conceptos
        draw.text((30, y+175), "Valor:", fill='black', font=font_normal)
        draw.text((80, y+175), f"${comp['valor']}", fill='black', font=font_normal)
        
        draw.text((30, y+200), "Concepto:", fill='black', font=font_normal)
        draw.text((100, y+200), "ABONADO EN BANCOLOMBIA. PROVENIENTE DE CLIENTE", fill='black', font=font_normal)
        
        draw.text((30, y+225), "Fecha de aplicación:", fill='black', font=font_normal)
        draw.text((170, y+225), "20 de Junio de 2025", fill='black', font=font_normal)
        
        # Línea separadora
        if i < len(comprobantes_data) - 1:
            draw.line([50, y+290, 750, y+290], fill='gray', width=1)
    
    # Guardar
    filename = "test_bancolombia.png"
    img.save(filename)
    print(f"✅ Imagen de prueba creada: {filename}")
    return filename

def test_api_with_bancolombia():
    """Probar la API con el documento de Bancolombia simulado"""
    
    # 1. Crear imagen de prueba
    test_file = create_bancolombia_test()
    
    # 2. Verificar que la API esté funcionando
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code != 200:
            print("❌ API no está disponible en http://localhost:8000")
            return
        
        health = response.json()
        print(f"✅ API funcionando - OCR: {health.get('ocr_engine', 'none')}")
        
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API. ¿Está ejecutándose?")
        print("   Ejecuta: python main.py")
        return
    
    # 3. Procesar con la API
    print("\n🔄 Procesando documento con API MADEIN...")
    
    with open(test_file, 'rb') as f:
        files = {'file': f}
        data = {
            'min_area': 50000,  # Área del Api.py original
            'debug': True       # Activar debug para ver detalles
        }
        
        try:
            response = requests.post(
                "http://localhost:8000/run-image-extractor",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Procesamiento exitoso!")
                print(f"📊 Total comprobantes: {result['total_comprobantes']}")
                print(f"🆔 Sesión: {result['session_id']}")
                
                print(f"\n📋 Comprobantes detectados:")
                for comp in result['comprobantes']:
                    print(f"  • {comp['documento_id']} -> {comp['filename']}")
                    print(f"    Posición: ({comp['coordinates']['x']}, {comp['coordinates']['y']})")
                    print(f"    Tamaño: {comp['coordinates']['width']}x{comp['coordinates']['height']}")
                    
                    # URL de descarga
                    download_url = f"http://localhost:8000/files/{result['session_id']}/{comp['filename']}"
                    print(f"    Descargar: {download_url}")
                    print()
                
                # Mostrar cómo limpiar
                print(f"🧹 Para limpiar sesión: DELETE http://localhost:8000/cleanup/{result['session_id']}")
                
            else:
                print(f"❌ Error en API: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error en request: {e}")
    
    # 4. Limpiar archivo de prueba
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\n🗑️ Archivo de prueba eliminado: {test_file}")

if __name__ == "__main__":
    print("🧪 PRUEBA DE API MADEIN - DOCUMENTOS BANCOLOMBIA")
    print("=" * 50)
    test_api_with_bancolombia() 