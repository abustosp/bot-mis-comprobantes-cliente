#!/usr/bin/env python3
"""
Script para probar la respuesta de la API y verificar los campos de MinIO.
"""

import json
from bin.consulta import consulta_mc
from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("TEST: Verificación de Respuesta de la API")
print("="*70)

# Datos de prueba (usa los primeros del CSV)
desde = "01/01/2024"
hasta = "31/12/2024"
cuit_inicio = "20374730429"
representado = "Agustin Bustos"
cuit_representado = "20374730429"
password = "Agustin2025"

print(f"\n📋 Parámetros de la consulta:")
print(f"   Desde: {desde}")
print(f"   Hasta: {hasta}")
print(f"   CUIT: {cuit_representado}")
print(f"   Representado: {representado}")

print(f"\n⚙️  Enviando request a la API...")
print(f"   carga_minio=True")
print(f"   carga_json=False")

try:
    response = consulta_mc(
        desde=desde,
        hasta=hasta,
        cuit_inicio_sesion=cuit_inicio,
        representado_nombre=representado,
        representado_cuit=cuit_representado,
        contrasena=password,
        descarga_emitidos=True,
        descarga_recibidos=True,
        carga_minio=True,
        carga_json=False
    )
    
    print(f"\n✅ Response recibida")
    print(f"\n📦 Claves en response:")
    for key in response.keys():
        print(f"   • {key}")
    
    print(f"\n🔍 Campos importantes:")
    
    # Verificar campo success
    if 'success' in response:
        print(f"   success: {response['success']}")
    
    # Verificar campos de MinIO
    campos_minio = [
        'mis_comprobantes_emitidos_url_minio',
        'mis_comprobantes_recibidos_url_minio'
    ]
    
    for campo in campos_minio:
        if campo in response:
            valor = response[campo]
            if valor:
                print(f"   ✓ {campo}:")
                print(f"     {valor[:100]}...")
            else:
                print(f"   ✗ {campo}: None o vacío")
        else:
            print(f"   ✗ {campo}: NO EXISTE en response")
    
    # Verificar si hay errores
    if 'error' in response:
        print(f"\n⚠️  Error en response: {response['error']}")
    
    if 'detail' in response:
        print(f"\n⚠️  Detail en response: {response['detail']}")
    
    # Mostrar response completa (sin datos sensibles)
    print(f"\n📄 Response completa (primeros 500 caracteres):")
    response_str = json.dumps(response, indent=2, ensure_ascii=False)
    print(response_str[:500])
    if len(response_str) > 500:
        print("...")
    
    print(f"\n{'='*70}")
    
    # Verificar si hay URLs de MinIO
    tiene_minio_emitidos = 'mis_comprobantes_emitidos_url_minio' in response and response['mis_comprobantes_emitidos_url_minio']
    tiene_minio_recibidos = 'mis_comprobantes_recibidos_url_minio' in response and response['mis_comprobantes_recibidos_url_minio']
    
    if tiene_minio_emitidos or tiene_minio_recibidos:
        print("✅ LA API ESTÁ DEVOLVIENDO URLs DE MinIO")
        if tiene_minio_emitidos:
            print("   ✓ Emitidos: URL disponible")
        if tiene_minio_recibidos:
            print("   ✓ Recibidos: URL disponible")
    else:
        print("❌ LA API NO ESTÁ DEVOLVIENDO URLs DE MinIO")
        print("\nPosibles causas:")
        print("   1. carga_minio no se está enviando correctamente")
        print("   2. La API no tiene configurado MinIO")
        print("   3. No hay comprobantes en el período")
        print("   4. Error en el procesamiento de la API")
    
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Error al consultar API: {e}")
    import traceback
    traceback.print_exc()
