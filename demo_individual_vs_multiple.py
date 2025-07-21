#!/usr/bin/env python3
"""
Demo: Diferencia entre procesamiento INDIVIDUAL vs MÚLTIPLE de comprobantes
"""
import requests
import json

def demo_individual_vs_multiple():
    """Demostrar la diferencia entre los dos enfoques"""
    
    print("🔄 DEMO: INDIVIDUAL vs MÚLTIPLE")
    print("=" * 50)
    
    # Crear imagen de prueba
    create_response = requests.get("http://localhost:8000/test")
    if create_response.status_code != 200:
        print("❌ API no disponible. Ejecuta: python main.py")
        return
    
    print("✅ API funcionando")
    
    # Simular que tenemos un archivo con 3 comprobantes
    print("\n📄 Simulando archivo con 3 comprobantes Bancolombia:")
    print("   • Comprobante 1: 000000801363627")
    print("   • Comprobante 2: 000000801363627") 
    print("   • Comprobante 3: 000000898059575")
    
    print("\n" + "="*60)
    print("🔸 MÉTODO ANTERIOR (MÚLTIPLE):")
    print("="*60)
    print("Endpoint: POST /run-image-extractor")
    print("Parámetro: individual_comprobantes=false")
    print("\n📊 Resultado esperado:")
    multiple_result = {
        "success": True,
        "session_id": "session_abc123",
        "total_comprobantes": 3,
        "comprobantes": [
            {"id": 1, "documento_id": "000000801363627", "filename": "000000801363627.png"},
            {"id": 2, "documento_id": "000000801363627", "filename": "000000801363627.png"},
            {"id": 3, "documento_id": "000000898059575", "filename": "000000898059575.png"}
        ],
        "message": "Procesado exitosamente: 3 comprobantes extraídos"
    }
    print(json.dumps(multiple_result, indent=2, ensure_ascii=False))
    
    print("\n❌ Problema: Te da MÚLTIPLES comprobantes en 1 respuesta")
    print("   • total_comprobantes: 3")
    print("   • Tienes que manejar array de comprobantes")
    print("   • No es 1 comprobante por imagen")
    
    print("\n" + "="*60)
    print("🎯 MÉTODO NUEVO (INDIVIDUAL):")
    print("="*60)
    print("Endpoint: POST /extract-individual-comprobantes")
    print("Parámetro: individual_comprobantes=true (automático)")
    print("\n📊 Resultado esperado:")
    individual_result = {
        "individual_results": [
            {
                "success": True,
                "session_id": "session_abc123_comp_1", 
                "total_comprobantes": 1,
                "comprobantes": [
                    {"id": 1, "documento_id": "000000801363627", "filename": "000000801363627.png"}
                ],
                "message": "Comprobante individual 1: 000000801363627"
            },
            {
                "success": True,
                "session_id": "session_abc123_comp_2",
                "total_comprobantes": 1, 
                "comprobantes": [
                    {"id": 1, "documento_id": "000000801363627", "filename": "000000801363627.png"}
                ],
                "message": "Comprobante individual 2: 000000801363627"
            },
            {
                "success": True,
                "session_id": "session_abc123_comp_3",
                "total_comprobantes": 1,
                "comprobantes": [
                    {"id": 1, "documento_id": "000000898059575", "filename": "000000898059575.png"}
                ],
                "message": "Comprobante individual 3: 000000898059575"
            }
        ]
    }
    print(json.dumps(individual_result, indent=2, ensure_ascii=False))
    
    print("\n✅ Ventajas del método INDIVIDUAL:")
    print("   • Cada comprobante se trata como imagen separada")
    print("   • total_comprobantes: 1 para cada uno")
    print("   • Perfecto para tu caso: '1 solo comprobante por imagen'")
    print("   • Más fácil de procesar en el frontend")
    
    print("\n🎯 ENDPOINTS DISPONIBLES:")
    print("   • /extract-individual-comprobantes   ← USA ESTE para tu caso")
    print("   • /process-bancolombia               ← Usa individual automáticamente")
    print("   • /run-image-extractor               ← Método anterior (múltiple)")
    
    print("\n🧪 PARA PROBAR:")
    print("   1. python test_real_bancolombia.py tu_archivo.pdf")
    print("   2. http://localhost:8000/docs → POST /extract-individual-comprobantes")
    print("   3. Sube tu imagen con 3 comprobantes → Obtienes 3 resultados individuales")

if __name__ == "__main__":
    demo_individual_vs_multiple() 