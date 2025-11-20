#!/usr/bin/env python3
"""
Script de prueba completo para verificar todas las funcionalidades.
"""

import os
import sys
import csv
from dotenv import load_dotenv

print("="*70)
print("TEST COMPLETO - Bot Mis Comprobantes Cliente")
print("="*70)

# Test 1: Verificar archivos de configuración
print("\n[TEST 1] Verificando archivos de configuración...")
print("-"*70)

# Verificar .env
if os.path.exists('.env'):
    print("✓ Archivo .env existe")
    load_dotenv()
    
    url = os.getenv('URL')
    mail = os.getenv('MAIL')
    api_key = os.getenv('API_KEY')
    
    if url:
        print(f"  ✓ URL configurada: {url}")
    else:
        print("  ✗ URL no configurada")
    
    if mail:
        print(f"  ✓ MAIL configurado: {mail}")
    else:
        print("  ✗ MAIL no configurado")
    
    if api_key:
        print(f"  ✓ API_KEY configurada: {api_key[:10]}...")
    else:
        print("  ✗ API_KEY no configurada")
else:
    print("✗ Archivo .env no existe")
    print("  Por favor, crea el archivo .env basándote en .env.example")

# Verificar CSV
print("\n[TEST 2] Verificando archivo CSV...")
print("-"*70)

if os.path.exists('Descarga-Mis-Comprobantes.csv'):
    print("✓ Archivo CSV existe")
    
    try:
        # Intentar leer con cp1252
        try:
            with open('Descarga-Mis-Comprobantes.csv', 'r', encoding='cp1252') as f:
                datos = list(csv.DictReader(f, delimiter='|'))
            encoding_usado = 'cp1252'
        except UnicodeDecodeError:
            with open('Descarga-Mis-Comprobantes.csv', 'r', encoding='utf-8') as f:
                datos = list(csv.DictReader(f, delimiter='|'))
            encoding_usado = 'utf-8'
        
        print(f"  ✓ CSV leído correctamente con encoding {encoding_usado}")
        print(f"  ✓ Total de filas: {len(datos)}")
        
        # Verificar columnas
        if datos:
            columnas_esperadas = [
                'Procesar', 'Desde', 'Hasta', 'CUIT Inicio', 'Clave',
                'CUIT Representado', 'Representado', 'Descarga Emitidos',
                'Descarga Recibidos', 'Ubicacion Emitidos', 'Nombre Emitidos',
                'Ubicacion Recibidos', 'Nombre Recibidos'
            ]
            
            columnas_csv = list(datos[0].keys())
            print(f"\n  Columnas en CSV: {len(columnas_csv)}")
            
            columnas_faltantes = set(columnas_esperadas) - set(columnas_csv)
            if columnas_faltantes:
                print(f"  ⚠ Columnas faltantes: {columnas_faltantes}")
            else:
                print("  ✓ Todas las columnas esperadas están presentes")
            
            # Mostrar datos de cada fila
            print(f"\n  Filas a procesar:")
            for i, dato in enumerate(datos, 1):
                procesar = dato.get('Procesar', '').upper()
                representado = dato.get('Representado', '')
                cuit = dato.get('CUIT Representado', '')
                desde = dato.get('Desde', '')
                hasta = dato.get('Hasta', '')
                
                simbolo = "✓" if procesar == "SI" else "○"
                print(f"  {simbolo} Fila {i}: {representado} ({cuit}) - {desde} a {hasta} - Procesar: {procesar}")
        
    except Exception as e:
        print(f"  ✗ Error al leer CSV: {e}")
        import traceback
        traceback.print_exc()
else:
    print("✗ Archivo CSV no existe")

# Test 3: Verificar módulos importados
print("\n[TEST 3] Verificando módulos...")
print("-"*70)

try:
    from bin.consulta import (
        consulta_mc,
        consulta_requests_restantes,
        descargar_archivos_minio_concurrente,
        consulta_mc_csv,
        crear_directorio_seguro,
        extraer_csv_de_zip
    )
    print("✓ Todos los módulos importados correctamente")
except ImportError as e:
    print(f"✗ Error al importar módulos: {e}")

# Test 4: Verificar conexión a API (solo si hay credenciales)
print("\n[TEST 4] Verificando conexión a API...")
print("-"*70)

if os.getenv('MAIL') and os.getenv('API_KEY'):
    try:
        from bin.consulta import consulta_requests_restantes
        
        print(f"  Consultando requests restantes para {os.getenv('MAIL')}...")
        response = consulta_requests_restantes(os.getenv('MAIL'))
        
        if 'consultas_disponibles' in response:
            print(f"  ✓ Conexión exitosa con la API")
            print(f"    • Consultas disponibles: {response.get('consultas_disponibles')}")
            print(f"    • Máximas consultas mensuales: {response.get('maximas_consultas_mensuales')}")
            print(f"    • Consultas realizadas este mes: {response.get('consultas_realizadas_mes_actual')}")
        else:
            print(f"  ⚠ Respuesta inesperada de la API:")
            print(f"    {response}")
    except Exception as e:
        print(f"  ✗ Error al consultar API: {e}")
else:
    print("  ○ Saltando (credenciales no configuradas)")

# Test 5: Verificar estructura de directorios
print("\n[TEST 5] Verificando estructura de directorios...")
print("-"*70)

directorios = ['Descargas', 'bin', 'Ejecutable']
for directorio in directorios:
    if os.path.exists(directorio):
        print(f"  ✓ {directorio}/ existe")
    else:
        print(f"  ○ {directorio}/ no existe (se creará cuando sea necesario)")

# Resumen
print("\n" + "="*70)
print("RESUMEN DE TESTS")
print("="*70)

tests_ok = []
tests_warning = []
tests_error = []

# Evaluar resultados
if os.path.exists('.env') and os.getenv('URL') and os.getenv('MAIL') and os.getenv('API_KEY'):
    tests_ok.append("✓ Configuración .env completa")
else:
    tests_error.append("✗ Configuración .env incompleta")

if os.path.exists('Descarga-Mis-Comprobantes.csv'):
    tests_ok.append("✓ Archivo CSV presente")
else:
    tests_error.append("✗ Archivo CSV faltante")

try:
    from bin.consulta import consulta_mc
    tests_ok.append("✓ Módulos importados correctamente")
except:
    tests_error.append("✗ Error en importación de módulos")

print("\n📊 Resultados:")
for msg in tests_ok:
    print(f"  {msg}")
for msg in tests_warning:
    print(f"  {msg}")
for msg in tests_error:
    print(f"  {msg}")

if tests_error:
    print("\n⚠ HAY ERRORES QUE REQUIEREN ATENCIÓN")
    print("  Por favor, revisa los errores arriba y corrígelos antes de continuar.")
    sys.exit(1)
elif tests_warning:
    print("\n✓ CONFIGURACIÓN BÁSICA CORRECTA (con advertencias)")
    print("  Puedes continuar pero revisa las advertencias.")
    sys.exit(0)
else:
    print("\n✅ TODOS LOS TESTS EXITOSOS")
    print("  El sistema está listo para descargar comprobantes.")
    sys.exit(0)
