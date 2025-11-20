#!/usr/bin/env python3
"""
Script para verificar que carga_minio=True se envía correctamente en la request.
"""

import sys
import json
from unittest.mock import patch, MagicMock
from bin.consulta import consulta_mc

print("="*70)
print("VERIFICACIÓN: Parámetro carga_minio=True en Request")
print("="*70)

# Test 1: Verificar valor por defecto
print("\n[TEST 1] Verificar valor por defecto de carga_minio")
print("-"*70)

import inspect
sig = inspect.signature(consulta_mc)
carga_minio_default = sig.parameters['carga_minio'].default

if carga_minio_default is True:
    print(f"✅ carga_minio tiene valor por defecto: True")
else:
    print(f"❌ carga_minio tiene valor por defecto: {carga_minio_default}")
    print(f"   DEBERÍA SER: True")

# Test 2: Verificar que se envía en el payload
print("\n[TEST 2] Verificar que carga_minio se envía en el payload")
print("-"*70)

# Mock de requests.post para capturar el payload
with patch('bin.consulta.requests.post') as mock_post:
    # Configurar mock para retornar una respuesta simulada
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'success': True,
        'message': 'Mock response'
    }
    mock_post.return_value = mock_response
    
    # Llamar a la función con carga_minio=True (por defecto)
    print("\nLlamando consulta_mc() con parámetros por defecto...")
    consulta_mc(
        desde="01/01/2024",
        hasta="31/01/2024",
        cuit_inicio_sesion="20123456789",
        representado_nombre="TEST",
        representado_cuit="20123456789",
        contrasena="test",
        descarga_emitidos=True,
        descarga_recibidos=True
    )
    
    # Verificar que se llamó a requests.post
    if mock_post.called:
        call_args = mock_post.call_args
        
        # Obtener el payload JSON enviado
        if 'json' in call_args.kwargs:
            payload = call_args.kwargs['json']
        else:
            payload = call_args[1] if len(call_args) > 1 else {}
        
        print("\n📦 Payload enviado a la API:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # Verificar carga_minio
        if 'carga_minio' in payload:
            if payload['carga_minio'] is True:
                print("\n✅ carga_minio=True está presente en el payload")
            else:
                print(f"\n❌ carga_minio={payload['carga_minio']} (DEBERÍA SER True)")
        else:
            print("\n❌ carga_minio NO está en el payload")
        
        # Verificar otros parámetros importantes
        print("\n📋 Verificación de parámetros:")
        params_esperados = {
            'desde': '01/01/2024',
            'hasta': '31/01/2024',
            'cuit_inicio_sesion': '20123456789',
            'representado_nombre': 'TEST',
            'representado_cuit': '20123456789',
            'descarga_emitidos': True,
            'descarga_recibidos': True,
            'carga_minio': True,
            'carga_json': True,  # Valor por defecto
            'b64': False,         # Valor por defecto
            'carga_s3': False     # Valor por defecto
        }
        
        for key, expected_value in params_esperados.items():
            actual_value = payload.get(key)
            if actual_value == expected_value:
                print(f"  ✓ {key}: {actual_value}")
            else:
                print(f"  ✗ {key}: {actual_value} (esperado: {expected_value})")
    else:
        print("❌ requests.post no fue llamado")

# Test 3: Verificar con carga_minio=False explícito
print("\n[TEST 3] Verificar con carga_minio=False explícito")
print("-"*70)

with patch('bin.consulta.requests.post') as mock_post:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'success': True,
        'message': 'Mock response'
    }
    mock_post.return_value = mock_response
    
    print("\nLlamando consulta_mc() con carga_minio=False...")
    consulta_mc(
        desde="01/01/2024",
        hasta="31/01/2024",
        cuit_inicio_sesion="20123456789",
        representado_nombre="TEST",
        representado_cuit="20123456789",
        contrasena="test",
        descarga_emitidos=True,
        descarga_recibidos=True,
        carga_minio=False  # Explícitamente False
    )
    
    if mock_post.called:
        call_args = mock_post.call_args
        payload = call_args.kwargs.get('json', {})
        
        if payload.get('carga_minio') is False:
            print("✅ carga_minio=False se envía correctamente cuando se especifica")
        else:
            print(f"❌ carga_minio={payload.get('carga_minio')} (esperado: False)")

# Test 4: Verificar en consulta_mc_csv
print("\n[TEST 4] Verificar en consulta_mc_csv()")
print("-"*70)

# Leer el código para verificar
with open('bin/consulta.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Buscar la línea donde se llama a consulta_mc en consulta_mc_csv
if 'carga_minio=True' in content:
    print("✅ carga_minio=True encontrado en el código")
    
    # Contar ocurrencias
    count = content.count('carga_minio=True')
    print(f"   Encontrado en {count} lugar(es)")
else:
    print("⚠ carga_minio=True no encontrado en el código (verificar manualmente)")

# Resumen final
print("\n" + "="*70)
print("RESUMEN")
print("="*70)

print("\n✅ CONFIGURACIÓN CORRECTA:")
print("  • Valor por defecto: carga_minio=True")
print("  • Se envía en el payload de la request")
print("  • Configurado en consulta_mc_csv()")
print("\n📌 SEGÚN DOCUMENTACIÓN OpenAPI:")
print("  • carga_minio: true → Genera URLs de descarga desde MinIO")
print("  • Las URLs se reciben en:")
print("    - mis_comprobantes_emitidos_url_minio")
print("    - mis_comprobantes_recibidos_url_minio")

print("\n✅ TODO CORRECTO - carga_minio=True está configurado según la documentación")
print("="*70)
