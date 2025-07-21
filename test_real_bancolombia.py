#!/usr/bin/env python3
"""
Script para probar la API MADEIN con documentos REALES de Bancolombia
Puedes usar este script para subir tu propia imagen/PDF de Bancolombia
"""
import requests
import json
import sys
import os
from pathlib import Path

def test_real_bancolombia_file(file_path: str, use_optimized_endpoint: bool = True):
    """
    Probar la API con un archivo real de Bancolombia
    
    Args:
        file_path: Ruta al archivo PDF o imagen
        use_optimized_endpoint: Si usar /process-bancolombia (True) o /run-image-extractor (False)
    """
    
    if not os.path.exists(file_path):
        print(f"❌ Archivo no encontrado: {file_path}")
        return
    
    file_path = Path(file_path)
    print(f"📁 Procesando archivo: {file_path.name}")
    print(f"📏 Tamaño: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Verificar que la API esté funcionando
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code != 200:
            print("❌ API no está disponible en http://localhost:8000")
            print("   Asegúrate de ejecutar: python main.py")
            return
        
        health = response.json()
        print(f"✅ API funcionando")
        print(f"   OCR Engine: {health.get('ocr_engine', 'none')}")
        print(f"   OpenCV: {health.get('opencv', 'unknown')}")
        print(f"   Dependencias: {'✅' if health.get('dependencies_loaded', False) else '❌'}")
        
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API. ¿Está ejecutándose?")
        print("   Ejecuta: python main.py")
        return
    
    # Detectar tipo de archivo
    file_extension = file_path.suffix.lower()
    if file_extension == '.pdf':
        content_type = 'application/pdf'
    elif file_extension in ['.png', '.jpg', '.jpeg']:
        content_type = f'image/{file_extension[1:]}'
    else:
        print(f"⚠️ Tipo de archivo no reconocido: {file_extension}")
        print("   Soportados: .pdf, .png, .jpg, .jpeg")
        content_type = 'application/octet-stream'
    
    # Elegir endpoint basado en el tipo de imagen
    if use_optimized_endpoint:
        # Detectar si es una cuadrícula analizando el nombre del archivo
        is_grid = any(word in file_path.name.lower() for word in ['grid', 'cuadricula', 'multiple', 'varios', 'many'])
        
        if is_grid or file_path.stat().st_size > 500000:  # Archivos grandes probablemente tienen muchos comprobantes
            endpoint = "http://localhost:8000/extract-grid-comprobantes"
            print(f"\n🎯 Usando endpoint para CUADRÍCULAS (ultra-sensible)")
            print(f"   • min_area: 3000 (vs 50000 normal)")
            print(f"   • Optimizado para 10+ comprobantes pequeños")
        else:
            endpoint = "http://localhost:8000/extract-individual-comprobantes" 
            print(f"\n🎯 Usando endpoint para comprobantes individuales")
            print(f"   • min_area: 5000 (vs 50000 normal)")
    else:
        endpoint = "http://localhost:8000/run-image-extractor"
        print(f"\n⚙️ Usando endpoint genérico (múltiples comprobantes)")
    
    print(f"🔄 Procesando con {endpoint}...")
    
    # Preparar datos
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, content_type)}
        
        if use_optimized_endpoint:
            # Los endpoints optimizados ya tienen parámetros preconfigurados
            data = {'debug': True}
        else:
            # Endpoint genérico con parámetros manuales
            data = {
                'min_area': 3000,  # Área más pequeña para cuadrículas
                'debug': True,
                'individual_comprobantes': True  # Forzar tratamiento individual
            }
        
        try:
            response = requests.post(endpoint, files=files, data=data, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                print_results(result, file_path.name)
                
            elif response.status_code == 503:
                print("❌ Dependencias no disponibles")
                print("   Ejecuta: pip install -r requirements.txt")
                
            else:
                print(f"❌ Error en API: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Detalle: {error_detail.get('detail', 'Sin detalles')}")
                except:
                    print(f"   Respuesta: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print("⏱️ Timeout - El archivo es muy grande o complejo")
            print("   Intenta con una imagen más pequeña o menos comprobantes")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en request: {e}")

def print_results(result: dict, filename: str):
    """Imprimir resultados de forma legible"""
    
    print(f"\n✅ ¡Procesamiento exitoso!")
    print(f"📊 Archivo: {filename}")
    
    # Verificar si es respuesta individual o múltiple
    if "individual_results" in result:
        # Respuesta con comprobantes individuales
        individual_results = result["individual_results"]
        print(f"🎯 Comprobantes procesados individualmente: {len(individual_results)}")
        
        for i, individual_result in enumerate(individual_results, 1):
            comp = individual_result["comprobantes"][0]  # Solo hay 1 comprobante por resultado
            
            print(f"\n📄 ═══ COMPROBANTE {i} (INDIVIDUAL) ═══")
            print(f"     🆔 Documento: {comp['documento_id']}")
            print(f"     📁 Archivo: {comp['filename']}")
            print(f"     📐 Posición: ({comp['coordinates']['x']}, {comp['coordinates']['y']})")
            print(f"     📏 Tamaño: {comp['coordinates']['width']} × {comp['coordinates']['height']} px")
            print(f"     📦 Área: {comp['area']:,} px²")
            print(f"     🆔 Sesión individual: {individual_result['session_id']}")
            
            if 'page' in comp:
                print(f"     📄 Página: {comp['page']}")
            
            # URL de descarga (usa session_id principal sin sufijo)
            base_session = individual_result['session_id'].split('_comp_')[0]
            download_url = f"http://localhost:8000/files/{base_session}/{comp['filename']}"
            print(f"     🔗 Descargar: {download_url}")
            
            # Si es optimizado, mostrar características
            if "optimization" in individual_result:
                print(f"     🏦 Optimización: {individual_result['optimization']}")
        
        print(f"\n🌐 URLs útiles:")
        if individual_results:
            base_session = individual_results[0]['session_id'].split('_comp_')[0]
            print(f"   📊 Ver sesiones: http://localhost:8000/sessions")
            print(f"   🧹 Limpiar sesión: DELETE http://localhost:8000/cleanup/{base_session}")
        print(f"   📖 Documentación: http://localhost:8000/docs")
        
    else:
        # Respuesta múltiple tradicional
        print(f"🎯 Total comprobantes: {result['total_comprobantes']}")
        print(f"🆔 Sesión: {result['session_id']}")
        
        # Si es endpoint optimizado, mostrar características usadas
        if "optimization" in result:
            print(f"🏦 Optimización: {result['optimization']}")
            print(f"🔧 Características usadas:")
            for feature in result.get('features_used', []):
                print(f"   • {feature}")
        
        if result['total_comprobantes'] > 0:
            print(f"\n📋 Comprobantes detectados:")
            for i, comp in enumerate(result['comprobantes'], 1):
                print(f"\n  📄 Comprobante {i}:")
                print(f"     🆔 Documento: {comp['documento_id']}")
                print(f"     📁 Archivo: {comp['filename']}")
                print(f"     📐 Posición: ({comp['coordinates']['x']}, {comp['coordinates']['y']})")
                print(f"     📏 Tamaño: {comp['coordinates']['width']} × {comp['coordinates']['height']} px")
                print(f"     📦 Área: {comp['area']:,} px²")
                
                if 'page' in comp:
                    print(f"     📄 Página: {comp['page']}")
                
                # URL de descarga
                download_url = f"http://localhost:8000/files/{result['session_id']}/{comp['filename']}"
                print(f"     🔗 Descargar: {download_url}")
            
            print(f"\n🌐 URLs útiles:")
            print(f"   📊 Ver sesiones: http://localhost:8000/sessions")
            print(f"   🧹 Limpiar sesión: DELETE http://localhost:8000/cleanup/{result['session_id']}")
            print(f"   📖 Documentación: http://localhost:8000/docs")
        else:
            print(f"\n⚠️ No se detectaron comprobantes")
            print(f"💡 Sugerencias:")
            print(f"   • Verificar que el archivo contenga comprobantes Bancolombia")
            print(f"   • Asegurar buena calidad de imagen (mínimo 150 DPI)")
            print(f"   • Verificar que los comprobantes tengan suficiente contraste")
            print(f"   • Probar con min_area más pequeño (40000-45000)")

def main():
    """Función principal"""
    print("🧪 PRUEBA DE API MADEIN - DOCUMENTOS REALES BANCOLOMBIA")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("📋 Uso:")
        print(f"   python {sys.argv[0]} <archivo_pdf_o_imagen>")
        print(f"   python {sys.argv[0]} <archivo> --generic   # Usar endpoint genérico")
        print("\n🎯 Por defecto usa COMPROBANTES INDIVIDUALES:")
        print("   • Tu imagen con 3 comprobantes → 3 resultados separados")
        print("   • Cada resultado tiene total_comprobantes: 1")
        print("   • Perfecto para cuando quieres 1 comprobante por imagen")
        print("\n📁 Ejemplos:")
        print(f"   python {sys.argv[0]} mi_documento.pdf        # 3 comprobantes → 3 resultados individuales")
        print(f"   python {sys.argv[0]} comprobantes.png        # Comprobantes individuales") 
        print(f"   python {sys.argv[0]} documento.pdf --generic # Múltiples comprobantes en 1 respuesta")
        return
    
    file_path = sys.argv[1]
    use_optimized = "--generic" not in sys.argv
    
    test_real_bancolombia_file(file_path, use_optimized)

if __name__ == "__main__":
    main() 