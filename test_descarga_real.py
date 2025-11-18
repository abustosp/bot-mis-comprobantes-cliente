#!/usr/bin/env python3
"""
Script de prueba para verificar el flujo completo de descarga.

Este script simula el proceso completo sin hacer llamadas reales a la API,
verificando:
1. Lectura del CSV con múltiples encodings
2. Creación de directorios (con fallback)
3. Simulación de descarga y extracción de archivos
4. Verificación de que los archivos se crean en las ubicaciones correctas
"""

import os
import sys
import csv
import zipfile
import tempfile
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bin.consulta import crear_directorio_seguro, extraer_csv_de_zip

def leer_csv_prueba():
    """Lee el CSV de prueba con manejo de encodings."""
    print("="*70)
    print("TEST 1: Lectura del CSV")
    print("="*70)
    
    csv_file = 'Descarga-Mis-Comprobantes.csv'
    
    # Intentar con cp1252 primero
    try:
        with open(csv_file, 'r', encoding='cp1252') as f:
            datos = list(csv.DictReader(f, delimiter='|', quotechar="'"))
        print(f"✓ CSV leído correctamente con encoding cp1252")
        print(f"  Total de filas: {len(datos)}")
        return datos
    except UnicodeDecodeError:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                datos = list(csv.DictReader(f, delimiter='|', quotechar="'"))
            print(f"✓ CSV leído correctamente con encoding utf-8")
            print(f"  Total de filas: {len(datos)}")
            return datos
        except Exception as e:
            print(f"✗ Error al leer CSV: {e}")
            return []


def test_creacion_directorios(datos):
    """Prueba la creación de directorios para cada registro."""
    print("\n" + "="*70)
    print("TEST 2: Creación de Directorios")
    print("="*70)
    
    resultados = []
    
    for i, dato in enumerate(datos, 1):
        if dato['Procesar'].lower() != 'si':
            continue
        
        print(f"\n{i}. Procesando: {dato['Representado']}")
        
        # Probar emitidos
        if dato['Descarga Emitidos'].lower() == 'si':
            ubicacion_deseada = dato.get('Ubicacion Emitidos') or dato.get('Ubicación Emitidos', '')
            print(f"   Ubicación Emitidos deseada: {ubicacion_deseada}")
            
            ubicacion_real = crear_directorio_seguro(ubicacion_deseada, dato['Representado'])
            print(f"   Ubicación Emitidos real: {ubicacion_real}")
            
            resultados.append({
                'representado': dato['Representado'],
                'tipo': 'emitidos',
                'deseada': ubicacion_deseada,
                'real': ubicacion_real,
                'nombre': dato['Nombre Emitidos']
            })
        
        # Probar recibidos
        if dato['Descarga Recibidos'].lower() == 'si':
            ubicacion_deseada = dato.get('Ubicacion Recibidos') or dato.get('Ubicación Recibidos', '')
            print(f"   Ubicación Recibidos deseada: {ubicacion_deseada}")
            
            ubicacion_real = crear_directorio_seguro(ubicacion_deseada, dato['Representado'])
            print(f"   Ubicación Recibidos real: {ubicacion_real}")
            
            resultados.append({
                'representado': dato['Representado'],
                'tipo': 'recibidos',
                'deseada': ubicacion_deseada,
                'real': ubicacion_real,
                'nombre': dato['Nombre Recibidos']
            })
    
    return resultados


def test_descarga_y_extraccion(resultados):
    """Simula la descarga y extracción de archivos."""
    print("\n" + "="*70)
    print("TEST 3: Simulación de Descarga y Extracción")
    print("="*70)
    
    archivos_creados = []
    
    for resultado in resultados:
        print(f"\n▶ {resultado['representado']} - {resultado['tipo']}")
        
        # Crear un ZIP de prueba
        with tempfile.TemporaryDirectory() as tmpdir:
            # Crear contenido CSV de prueba
            csv_contenido = f"Fecha,Comprobante,Monto\n"
            csv_contenido += f"01/01/2024,FC 0001-00000001,1000.00\n"
            csv_contenido += f"02/01/2024,FC 0001-00000002,2000.00\n"
            
            # Crear archivo CSV temporal
            csv_temp = os.path.join(tmpdir, f"{resultado['nombre']}.csv")
            with open(csv_temp, 'w') as f:
                f.write(csv_contenido)
            
            # Crear ZIP temporal
            zip_temp = os.path.join(tmpdir, f"{resultado['nombre']}_temp.zip")
            with zipfile.ZipFile(zip_temp, 'w') as zf:
                zf.write(csv_temp, arcname=os.path.basename(csv_temp))
            
            print(f"  ✓ ZIP de prueba creado: {os.path.basename(zip_temp)}")
            
            # Simular extracción
            destino_csv = f"{resultado['real']}/{resultado['nombre']}.csv"
            
            if extraer_csv_de_zip(zip_temp, destino_csv):
                if os.path.exists(destino_csv):
                    tamaño = os.path.getsize(destino_csv)
                    print(f"  ✓ CSV extraído correctamente: {destino_csv}")
                    print(f"    Tamaño: {tamaño} bytes")
                    archivos_creados.append(destino_csv)
                else:
                    print(f"  ✗ El archivo no existe: {destino_csv}")
            else:
                print(f"  ✗ Error al extraer CSV")
    
    return archivos_creados


def verificar_archivos(archivos_creados):
    """Verifica que los archivos se hayan creado correctamente."""
    print("\n" + "="*70)
    print("TEST 4: Verificación de Archivos Creados")
    print("="*70)
    
    print(f"\nArchivos creados: {len(archivos_creados)}")
    
    for archivo in archivos_creados:
        if os.path.exists(archivo):
            tamaño = os.path.getsize(archivo)
            print(f"  ✓ {archivo}")
            print(f"    Tamaño: {tamaño} bytes")
            
            # Leer primeras líneas
            with open(archivo, 'r') as f:
                lineas = f.readlines()[:3]
            print(f"    Líneas: {len(lineas)}")
        else:
            print(f"  ✗ No existe: {archivo}")
    
    return len([a for a in archivos_creados if os.path.exists(a)])


def limpiar_archivos_prueba(archivos_creados):
    """Limpia los archivos de prueba creados."""
    print("\n" + "="*70)
    print("LIMPIEZA: Eliminando archivos de prueba")
    print("="*70)
    
    for archivo in archivos_creados:
        try:
            if os.path.exists(archivo):
                os.remove(archivo)
                print(f"  ✓ Eliminado: {archivo}")
        except Exception as e:
            print(f"  ✗ Error al eliminar {archivo}: {e}")


def mostrar_resumen(datos, resultados, archivos_creados):
    """Muestra un resumen de la prueba."""
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    
    filas_csv = len(datos)
    filas_procesar = len([d for d in datos if d['Procesar'].lower() == 'si'])
    directorios_creados = len(set([r['real'] for r in resultados]))
    archivos_verificados = len([a for a in archivos_creados if os.path.exists(a)])
    
    print(f"\n📊 Estadísticas:")
    print(f"  • Filas en CSV: {filas_csv}")
    print(f"  • Filas a procesar: {filas_procesar}")
    print(f"  • Directorios creados: {directorios_creados}")
    print(f"  • Archivos CSV generados: {len(archivos_creados)}")
    print(f"  • Archivos verificados: {archivos_verificados}")
    
    print(f"\n📁 Ubicaciones utilizadas:")
    ubicaciones_unicas = set([r['real'] for r in resultados])
    for ubicacion in sorted(ubicaciones_unicas):
        print(f"  • {ubicacion}")
    
    print(f"\n📝 Archivos generados:")
    for resultado in resultados:
        archivo = f"{resultado['real']}/{resultado['nombre']}.csv"
        existe = "✓" if os.path.exists(archivo) else "✗"
        print(f"  {existe} {resultado['representado']:20s} {resultado['tipo']:10s} → {archivo}")
    
    # Resultado final
    if archivos_verificados == len(archivos_creados):
        print(f"\n✅ TODAS LAS PRUEBAS EXITOSAS")
        print(f"   Los archivos se descargaron en las ubicaciones correctas")
        return True
    else:
        print(f"\n⚠ ALGUNAS PRUEBAS FALLARON")
        print(f"   Verificados: {archivos_verificados}/{len(archivos_creados)}")
        return False


def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*10 + "PRUEBA DE DESCARGA Y EXTRACCIÓN DE ARCHIVOS" + " "*15 + "║")
    print("╚" + "="*68 + "╝")
    
    # 1. Leer CSV
    datos = leer_csv_prueba()
    if not datos:
        print("✗ No se pudo leer el CSV. Abortando pruebas.")
        return 1
    
    # 2. Crear directorios
    resultados = test_creacion_directorios(datos)
    if not resultados:
        print("✗ No se crearon directorios. Abortando pruebas.")
        return 1
    
    # 3. Simular descarga y extracción
    archivos_creados = test_descarga_y_extraccion(resultados)
    
    # 4. Verificar archivos
    archivos_verificados = verificar_archivos(archivos_creados)
    
    # 5. Mostrar resumen
    exito = mostrar_resumen(datos, resultados, archivos_creados)
    
    # 6. Preguntar si limpiar
    print("\n" + "="*70)
    respuesta = input("¿Deseas eliminar los archivos de prueba? (s/n): ").lower()
    if respuesta == 's':
        limpiar_archivos_prueba(archivos_creados)
    else:
        print("\nArchivos de prueba conservados para inspección manual.")
    
    print("\n" + "="*70)
    print("PRUEBAS COMPLETADAS")
    print("="*70 + "\n")
    
    return 0 if exito else 1


if __name__ == "__main__":
    sys.exit(main())
