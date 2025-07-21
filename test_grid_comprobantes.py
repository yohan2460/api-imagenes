#!/usr/bin/env python3
"""
Test específico para CUADRÍCULAS de comprobantes pequeños

Para el caso del usuario: imagen con 11+ comprobantes organizados en cuadrícula
"""
import sys
import requests
from pathlib import Path
import json

def test_grid_detection(file_path: Path):
    """Probar detección de cuadrícula de comprobantes"""
    
    print("🎯 TEST: DETECCIÓN DE CUADRÍCULA DE COMPROBANTES")
    print("=" * 60)
    print(f"📁 Archivo: {file_path}")
    print(f"📊 Tamaño: {file_path.stat().st_size / 1024:.1f} KB")
    
    # Determinar tipo de contenido
    if file_path.suffix.lower() == '.pdf':
        content_type = 'application/pdf'
    elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
        content_type = f'image/{file_path.suffix[1:].lower()}'
        if content_type == 'image/jpg':
            content_type = 'image/jpeg'
    else:
        content_type = 'application/octet-stream'
    
    # Probar diferentes endpoints para comparar
    endpoints_to_test = [
        {
            "name": "🎯 CUADRÍCULA (RECOMENDADO)",
            "url": "http://localhost:8000/extract-grid-comprobantes",
            "description": "Ultra-sensible para cuadrículas (min_area: 3000)"
        },
        {
            "name": "📋 INDIVIDUAL", 
            "url": "http://localhost:8000/extract-individual-comprobantes",
            "description": "Sensible para comprobantes pequeños (min_area: 5000)"
        },
        {
            "name": "⚙️ GENÉRICO",
            "url": "http://localhost:8000/run-image-extractor", 
            "description": "Estándar (min_area: 50000) - para comparar"
        }
    ]
    
    results = {}
    
    for endpoint_info in endpoints_to_test:
        print(f"\n" + "="*50)
        print(f"{endpoint_info['name']}")
        print(f"🔗 {endpoint_info['url']}")
        print(f"📝 {endpoint_info['description']}")
        print("="*50)
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, content_type)}
                
                # Configurar parámetros según endpoint
                if "grid" in endpoint_info['url']:
                    data = {'debug': True}  # Ya tiene min_area: 3000
                elif "individual" in endpoint_info['url']:
                    data = {'debug': True}  # Ya tiene min_area: 5000
                else:
                    data = {
                        'debug': True,
                        'min_area': 3000,  # Forzar área pequeña para comparar
                        'individual_comprobantes': True
                    }
                
                print(f"🔄 Enviando request...")
                response = requests.post(endpoint_info['url'], files=files, data=data, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    results[endpoint_info['name']] = result
                    
                    # Contar comprobantes detectados
                    if "individual_results" in result:
                        count = len(result["individual_results"])
                        print(f"✅ ¡Éxito! Detectados: {count} comprobantes individuales")
                        
                        # Mostrar primeros 3 para verificar
                        for i, individual_result in enumerate(result["individual_results"][:3], 1):
                            comp = individual_result["comprobantes"][0]
                            print(f"   📄 {i}. {comp['documento_id']} ({comp['area']:,} px²)")
                        
                        if count > 3:
                            print(f"   📄 ... y {count - 3} más")
                            
                    elif result.get("total_comprobantes", 0) > 0:
                        count = result["total_comprobantes"]
                        print(f"✅ ¡Éxito! Detectados: {count} comprobantes (múltiples)")
                        for i, comp in enumerate(result["comprobantes"][:3], 1):
                            print(f"   📄 {i}. {comp['documento_id']} ({comp['area']:,} px²)")
                    else:
                        print(f"❌ No se detectaron comprobantes")
                        
                else:
                    print(f"❌ Error HTTP {response.status_code}: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Resumen de resultados
    print(f"\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS:")
    print("="*60)
    
    best_count = 0
    best_endpoint = None
    
    for endpoint_name, result in results.items():
        if "individual_results" in result:
            count = len(result["individual_results"])
            result_type = "individual"
        elif result.get("total_comprobantes", 0) > 0:
            count = result["total_comprobantes"] 
            result_type = "múltiple"
        else:
            count = 0
            result_type = "sin detectar"
            
        status = "🏆" if count > best_count else "📊"
        if count > best_count:
            best_count = count
            best_endpoint = endpoint_name
            
        print(f"{status} {endpoint_name}: {count} comprobantes ({result_type})")
    
    print(f"\n🏆 MEJOR RESULTADO: {best_endpoint}")
    print(f"🎯 Comprobantes detectados: {best_count}")
    
    if best_count >= 10:
        print(f"✅ ¡Excelente! Detectó {best_count} comprobantes (esperados ~11)")
    elif best_count >= 5:
        print(f"⚠️ Parcial: Detectó {best_count} comprobantes (esperados ~11)")
        print(f"💡 Intenta usar el endpoint de CUADRÍCULA con debug=True")
    else:
        print(f"❌ Pocos detectados: {best_count} comprobantes")
        print(f"💡 Sugerencias:")
        print(f"   • Verificar calidad de imagen (mínimo 150 DPI)")
        print(f"   • Probar con min_area más pequeño (1000-2000)")
        print(f"   • Usar el endpoint /extract-grid-comprobantes")
    
    print(f"\n🧪 Para usar el mejor endpoint:")
    if best_endpoint and "CUADRÍCULA" in best_endpoint:
        print(f"   python test_real_bancolombia.py {file_path}")
        print(f"   curl -X POST 'http://localhost:8000/extract-grid-comprobantes' -F 'file=@{file_path}' -F 'debug=true'")
    
    return results

def main():
    if len(sys.argv) < 2:
        print("📋 Uso:")
        print(f"   python {sys.argv[0]} <tu_archivo_con_cuadricula>")
        print("\n🎯 Este script es específico para CUADRÍCULAS de comprobantes:")
        print("   • Imágenes con 10+ comprobantes pequeños organizados")
        print("   • Prueba 3 endpoints diferentes para comparar")
        print("   • Te dice cuál funciona mejor para tu imagen")
        print("\n📁 Ejemplos:")
        print(f"   python {sys.argv[0]} cuadricula_comprobantes.png")
        print(f"   python {sys.argv[0]} documento_con_11_facturas.pdf")
        return
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ Archivo no encontrado: {file_path}")
        return
    
    # Verificar que la API está corriendo
    try:
        response = requests.get("http://localhost:8000/test", timeout=5)
        if response.status_code != 200:
            print("❌ API no responde correctamente. Ejecuta: python main.py")
            return
    except:
        print("❌ API no disponible. Ejecuta primero: python main.py")
        return
    
    print("✅ API disponible")
    
    # Ejecutar test
    test_grid_detection(file_path)

if __name__ == "__main__":
    main() 