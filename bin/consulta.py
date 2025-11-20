import requests
import csv
from dotenv import load_dotenv
import os
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import pandas as pd


load_dotenv(".env", override=True)

root_url = os.getenv("URL", "https://api-bots.mrbot.com.ar")
mail = os.getenv("MAIL")
api_key = os.getenv("API_KEY")

# Configuración para descargas concurrentes
MAX_WORKERS = 10


def consulta_mc(desde, 
                hasta, 
                cuit_inicio_sesion, 
                representado_nombre, 
                representado_cuit, 
                contrasena, 
                descarga_emitidos: bool, 
                descarga_recibidos: bool,
                carga_minio: bool = True,
                carga_json: bool = True,
                b64: bool = False,
                carga_s3: bool = False,
                proxy_request: Optional[bool] = None):
    """
    Consulta de Mis Comprobantes usando la API v1.
    
    Args:
        desde: Fecha inicio en formato DD/MM/YYYY
        hasta: Fecha fin en formato DD/MM/YYYY
        cuit_inicio_sesion: CUIT del representante
        representado_nombre: Nombre del representado
        representado_cuit: CUIT del representado
        contrasena: Contraseña fiscal
        descarga_emitidos: True para descargar emitidos
        descarga_recibidos: True para descargar recibidos
        carga_minio: True para subir archivos a MinIO y obtener URLs
        carga_json: True para recibir datos en JSON
        b64: True para recibir archivos en base64
        carga_s3: True para subir archivos a S3
        proxy_request: True/False/None para usar proxy
    
    Returns:
        Dict con la respuesta de la API
    """
    url = root_url.rstrip('/') + "/api/v1/mis_comprobantes/consulta"
    
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'email': mail
    }
    
    payload = {
        'desde': desde,
        'hasta': hasta,
        'cuit_inicio_sesion': cuit_inicio_sesion,
        'representado_nombre': representado_nombre,
        'representado_cuit': representado_cuit,
        'contrasena': contrasena,
        'descarga_emitidos': descarga_emitidos,
        'descarga_recibidos': descarga_recibidos,
        'carga_minio': carga_minio,  # IMPORTANTE: True para obtener URLs de descarga desde MinIO
        'carga_json': carga_json,
        'b64': b64,
        'carga_s3': carga_s3
    }
    
    if proxy_request is not None:
        payload['proxy_request'] = proxy_request
    
    # Debug: Mostrar configuración de carga (sin mostrar la contraseña)
    debug_payload = {k: v for k, v in payload.items() if k != 'contrasena'}
    print(f"📤 Request payload: carga_minio={payload['carga_minio']}, carga_json={payload['carga_json']}")
    
    response = requests.post(url, headers=headers, json=payload)
    
    try:
        return response.json()
    except ValueError:
        # Respuesta no es JSON; devolver detalle para registrar el error
        return {
            'success': False,
            'error': f'Respuesta no JSON (HTTP {response.status_code})',
            'http_status': response.status_code,
            'content': response.text[:500]
        }


def consulta_requests_restantes(mail: str) -> Dict[str, Any]:
    """
    Consulta las requests restantes del usuario usando la API v1.
    
    Args:
        mail: Email del usuario
    
    Returns:
        Dict con información de consultas disponibles
    """
    url = root_url.rstrip('/') + f"/api/v1/user/consultas/{mail}"
    
    headers = {
        'x-api-key': api_key
    }
    
    response = requests.get(url, headers=headers)
    
    try:
        return response.json()
    except ValueError:
        return {
            'success': False,
            'error': f'Respuesta no JSON (HTTP {response.status_code})',
            'http_status': response.status_code,
            'content': response.text[:500]
        }


def descargar_archivo_minio(url: str, destino: str) -> Dict[str, Any]:
    """
    Descarga un archivo desde MinIO.
    
    Args:
        url: URL del archivo en MinIO
        destino: Ruta local donde guardar el archivo
    
    Returns:
        Dict con información del resultado de la descarga
    """
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        
        with open(destino, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return {
            'success': True,
            'url': url,
            'destino': destino,
            'size': os.path.getsize(destino)
        }
    except Exception as e:
        return {
            'success': False,
            'url': url,
            'destino': destino,
            'error': str(e)
        }


def descargar_archivos_minio_concurrente(urls: List[Dict[str, str]], max_workers: int = MAX_WORKERS) -> List[Dict[str, Any]]:
    """
    Descarga múltiples archivos desde MinIO de forma concurrente.
    
    Args:
        urls: Lista de dicts con 'url' y 'destino'
        max_workers: Número de workers concurrentes (default: 10)
    
    Returns:
        Lista de resultados de las descargas
    """
    resultados = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(descargar_archivo_minio, item['url'], item['destino']): item 
            for item in urls
        }
        
        for future in as_completed(futures):
            resultado = future.result()
            resultados.append(resultado)
            
            if resultado['success']:
                print(f"✓ Descargado: {os.path.basename(resultado['destino'])}")
            else:
                print(f"✗ Error descargando: {resultado['destino']} - {resultado['error']}")
    
    return resultados


def save_to_csv(data, filename):
    """Guarda datos en formato CSV."""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        if data:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(data)


def leer_csv_con_encoding(archivo):
    """
    Intenta leer un archivo CSV con diferentes encodings.
    Primero intenta cp1252, luego utf-8.
    """
    encodings = ['cp1252', 'utf-8']
    
    for encoding in encodings:
        try:
            with open(archivo, 'r', encoding=encoding) as f:
                return csv.DictReader(f, delimiter='|')
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"⚠ Error al leer archivo con encoding {encoding}: {e}")
            continue
    
    # Si ninguno funciona, lanzar error
    raise ValueError(f"No se pudo leer el archivo {archivo} con los encodings disponibles (cp1252, utf-8)")


def extraer_csv_de_zip(zip_path, destino_csv):
    """
    Extrae el único archivo CSV de un ZIP y lo guarda con el nombre especificado.
    
    Args:
        zip_path: Ruta al archivo ZIP descargado
        destino_csv: Ruta completa donde guardar el CSV extraído
    
    Returns:
        bool: True si se extrajo exitosamente, False en caso contrario
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Obtener lista de archivos en el ZIP
            archivos_en_zip = zip_ref.namelist()
            
            if not archivos_en_zip:
                print(f"⚠ El ZIP {zip_path} está vacío")
                return False
            
            # Buscar el primer archivo CSV en el ZIP
            archivo_csv = None
            for archivo in archivos_en_zip:
                if archivo.lower().endswith('.csv'):
                    archivo_csv = archivo
                    break
            
            if not archivo_csv:
                # Si no hay CSV, tomar el primer archivo
                archivo_csv = archivos_en_zip[0]
            
            # Extraer el archivo
            contenido = zip_ref.read(archivo_csv)
            
            # Guardar con el nombre especificado
            os.makedirs(os.path.dirname(destino_csv), exist_ok=True)
            with open(destino_csv, 'wb') as f:
                f.write(contenido)
            
            print(f"✓ Extraído: {os.path.basename(destino_csv)}")
            return True
            
    except zipfile.BadZipFile:
        print(f"✗ Error: {zip_path} no es un archivo ZIP válido")
        return False
    except Exception as e:
        print(f"✗ Error al extraer ZIP: {e}")
        return False


def crear_directorio_seguro(ruta, nombre_representado, representado_cuit: Optional[str] = None, nombre_archivo: Optional[str] = None):
    """
    Intenta crear un directorio. Si falla, retorna una ruta alternativa.
    
    Args:
        ruta: Ruta deseada para el directorio
        nombre_representado: Nombre del representado para usar en fallback
        representado_cuit: CUIT del representado para construir fallback específico
        nombre_archivo: Nombre base para carpeta de fallback
    
    Returns:
        str: Ruta del directorio (original o fallback)
    """
    try:
        # Intentar crear el directorio original
        os.makedirs(ruta, exist_ok=True)
        # Verificar que se puede escribir
        test_file = os.path.join(ruta, '.test_write')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"✓ Directorio verificado: {ruta}")
            return ruta
        except:
            raise PermissionError(f"No se puede escribir en {ruta}")
    except Exception as e:
        # Si falla, usar directorio fallback
        # Limpiar nombre del representado para usarlo como nombre de carpeta
        nombre_limpio = "".join(c for c in nombre_representado if c.isalnum() or c in (' ', '-', '_')).strip()
        nombre_limpio = nombre_limpio.replace(' ', '_')
        cuit_limpio = str(representado_cuit).strip() if representado_cuit else ""
        nombre_dir_final = nombre_archivo or nombre_limpio or "descarga"
        if cuit_limpio:
            fallback_dir = os.path.join(cuit_limpio, nombre_dir_final)
        else:
            fallback_dir = os.path.join('Descargas', nombre_dir_final)
        try:
            os.makedirs(fallback_dir, exist_ok=True)
            print(f"⚠ No se pudo usar {ruta}: {e}")
            print(f"✓ Usando directorio alternativo: {fallback_dir}")
            return fallback_dir
        except Exception as e2:
            print(f"✗ Error creando directorio fallback: {e2}")
            # Último recurso: directorio Descargas
            os.makedirs('Descargas', exist_ok=True)
            print(f"✓ Usando directorio por defecto: ./Descargas")
            return 'Descargas'


def consulta_mc_csv():
    """
    Procesa el archivo Excel (o CSV legacy) de consultas masivas de Mis Comprobantes.
    
    Lee el archivo 'Descarga-Mis-Comprobantes.xlsx' (o el CSV legado si existiera) y procesa cada fila que tenga
    'Procesar' = 'si'. Para cada consulta:
    - Realiza la consulta a la API
    - Descarga archivos ZIP desde MinIO
    - Extrae los CSV de los ZIPs descargados
    
    El archivo Excel se lee con pandas. Si no existe, se intenta usar el CSV con cp1252 y luego utf-8.
    """
    datos = []
    excel_path = 'Descarga-Mis-Comprobantes.xlsx'
    csv_path = 'Descarga-Mis-Comprobantes.csv'
    def _to_str(value: Any) -> str:
        return '' if value is None else str(value).strip()
    def _format_date(value: Any) -> str:
        if isinstance(value, (pd.Timestamp, datetime, date)):
            return value.strftime("%d/%m/%Y")
        text = _to_str(value)
        if not text:
            return text
        parsed = pd.to_datetime(text, dayfirst=True, errors='coerce')
        if pd.notna(parsed):
            return parsed.strftime("%d/%m/%Y")
        return text

    # Intentar leer Excel
    try:
        df = pd.read_excel(excel_path, dtype=str).fillna('')
        datos = df.to_dict(orient='records')
        print("✓ Excel leído correctamente")
    except FileNotFoundError:
        print(f"⚠ No se encontró el archivo '{excel_path}', intentando leer CSV legado...")
    except Exception as e:
        print(f"✗ Error al leer Excel: {e}")
        return

    # Fallback al CSV legacy
    if not datos:
        try:
            with open(csv_path, 'r', encoding='cp1252') as f:
                datos = list(csv.DictReader(f, delimiter='|'))
            print("✓ CSV leído con encoding cp1252 (modo compatibilidad)")
        except UnicodeDecodeError:
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    datos = list(csv.DictReader(f, delimiter='|'))
                print("✓ CSV leído con encoding utf-8 (modo compatibilidad)")
            except Exception as e:
                print(f"✗ Error al leer CSV: {e}")
                return
        except FileNotFoundError:
            print(f"✗ Error: No se encontró el archivo '{excel_path}' ni el CSV de respaldo '{csv_path}'")
            return
        except Exception as e:
            print(f"✗ Error al leer CSV: {e}")
            return

    if not datos:
        print("⚠ El archivo de configuración no contiene filas para procesar")
        return
    
    errores = []
    errores2 = []
    
    for dato in datos:
        if _to_str(dato.get('Procesar', '')).lower() != 'si':
            continue
            
        desde = _format_date(dato.get('Desde', ''))
        hasta = _format_date(dato.get('Hasta', ''))
        cuit_inicio_sesion = _to_str(dato.get('CUIT Inicio', ''))
        representado_nombre = _to_str(dato.get('Representado', ''))
        representado_cuit = _to_str(dato.get('CUIT Representado', ''))
        contrasena = _to_str(dato.get('Clave', ''))
        
        descarga_emitidos = _to_str(dato.get('Descarga Emitidos', '')).lower() == 'si'
        descarga_recibidos = _to_str(dato.get('Descarga Recibidos', '')).lower() == 'si'
        
        print(f"\n{'='*60}")
        print(f"Procesando: {representado_nombre} ({representado_cuit})")
        print(f"Período: {desde} - {hasta}")
        print(f"{'='*60}")
        
        try:
            response = consulta_mc(
                desde, 
                hasta, 
                cuit_inicio_sesion, 
                representado_nombre, 
                representado_cuit, 
                contrasena, 
                descarga_emitidos, 
                descarga_recibidos,
                carga_minio=True,  # Usar MinIO para obtener URLs de descarga
                carga_json=False   # No necesitamos JSON, usaremos los archivos de MinIO
            )
            
            # Verificar si hubo un error FATAL (success = false)
            # Nota: el campo 'error' puede contener advertencias incluso cuando success=true
            if not response.get('success', False):
                error_msg = response.get('error', response.get('detail', response.get('message', 'Error desconocido')))
                errores2.append({
                    'request': {
                        'desde': desde,
                        'hasta': hasta,
                        'cuit_inicio_sesion': cuit_inicio_sesion,
                        'representado_nombre': representado_nombre,
                        'representado_cuit': representado_cuit,
                        'descarga_emitidos': descarga_emitidos,
                        'descarga_recibidos': descarga_recibidos
                    },
                    'error': str(error_msg)
                })
                print(f"✗ Error FATAL en la consulta: {error_msg}")
                continue
            
            # Mostrar advertencias si las hay (pero continuar con el procesamiento)
            if 'error' in response and response['error']:
                error_list = response['error']
                if isinstance(error_list, list) and error_list:
                    print(f"⚠ Advertencia(s): {', '.join(error_list)}")
                elif error_list:
                    print(f"⚠ Advertencia: {error_list}")
            
            # Debug: Mostrar claves de la respuesta
            print(f"\n📋 Claves en response: {list(response.keys())}")
            
            # Preparar lista de archivos a descargar desde MinIO
            archivos_a_descargar = []
            archivos_info = []  # Info para extraer después
            
            # Procesar emitidos
            if descarga_emitidos:
                # Usar "Ubicacion" sin tilde para mayor compatibilidad
                ubicacion_deseada = _to_str(dato.get('Ubicacion Emitidos') or dato.get('Ubicación Emitidos', ''))
                nombre_emitidos = _to_str(dato.get('Nombre Emitidos', ''))
                
                # Intentar crear directorio, con fallback si falla
                ubicacion_emitidos = crear_directorio_seguro(
                    ubicacion_deseada,
                    representado_nombre,
                    representado_cuit=representado_cuit,
                    nombre_archivo=nombre_emitidos
                )
                
                # Debug: Verificar si existe el campo de MinIO
                print(f"\n🔍 Emitidos - Verificando campo MinIO...")
                print(f"   Campo 'mis_comprobantes_emitidos_url_minio' existe: {'mis_comprobantes_emitidos_url_minio' in response}")
                if 'mis_comprobantes_emitidos_url_minio' in response:
                    print(f"   URL: {response['mis_comprobantes_emitidos_url_minio'][:100] if response['mis_comprobantes_emitidos_url_minio'] else 'None'}...")
                
                # Agregar URL de MinIO a la lista de descargas
                if 'mis_comprobantes_emitidos_url_minio' in response and response['mis_comprobantes_emitidos_url_minio']:
                    zip_path = f'{ubicacion_emitidos}/{nombre_emitidos}_temp.zip'
                    csv_path = f'{ubicacion_emitidos}/{nombre_emitidos}.csv'
                    
                    archivos_a_descargar.append({
                        'url': response['mis_comprobantes_emitidos_url_minio'],
                        'destino': zip_path
                    })
                    
                    archivos_info.append({
                        'zip': zip_path,
                        'csv': csv_path,
                        'tipo': 'emitidos'
                    })
                    print(f"   ✓ Agregado a lista de descarga")
                else:
                    print(f"   ✗ No hay URL de MinIO para emitidos")
            
            # Procesar recibidos
            if descarga_recibidos:
                # Usar "Ubicacion" sin tilde para mayor compatibilidad
                ubicacion_deseada = _to_str(dato.get('Ubicacion Recibidos') or dato.get('Ubicación Recibidos', ''))
                nombre_recibidos = _to_str(dato.get('Nombre Recibidos', ''))
                
                # Intentar crear directorio, con fallback si falla
                ubicacion_recibidos = crear_directorio_seguro(
                    ubicacion_deseada,
                    representado_nombre,
                    representado_cuit=representado_cuit,
                    nombre_archivo=nombre_recibidos
                )
                
                # Debug: Verificar si existe el campo de MinIO
                print(f"\n🔍 Recibidos - Verificando campo MinIO...")
                print(f"   Campo 'mis_comprobantes_recibidos_url_minio' existe: {'mis_comprobantes_recibidos_url_minio' in response}")
                if 'mis_comprobantes_recibidos_url_minio' in response:
                    print(f"   URL: {response['mis_comprobantes_recibidos_url_minio'][:100] if response['mis_comprobantes_recibidos_url_minio'] else 'None'}...")
                
                # Agregar URL de MinIO a la lista de descargas
                if 'mis_comprobantes_recibidos_url_minio' in response and response['mis_comprobantes_recibidos_url_minio']:
                    zip_path = f'{ubicacion_recibidos}/{nombre_recibidos}_temp.zip'
                    csv_path = f'{ubicacion_recibidos}/{nombre_recibidos}.csv'
                    
                    archivos_a_descargar.append({
                        'url': response['mis_comprobantes_recibidos_url_minio'],
                        'destino': zip_path
                    })
                    
                    archivos_info.append({
                        'zip': zip_path,
                        'csv': csv_path,
                        'tipo': 'recibidos'
                    })
                    print(f"   ✓ Agregado a lista de descarga")
                else:
                    print(f"   ✗ No hay URL de MinIO para recibidos")
            
            # Descargar archivos desde MinIO de forma concurrente
            if archivos_a_descargar:
                print(f"\nDescargando {len(archivos_a_descargar)} archivo(s) desde MinIO...")
                resultados_descarga = descargar_archivos_minio_concurrente(archivos_a_descargar)
                
                # Extraer CSVs de los ZIPs descargados
                print(f"Extrayendo archivos CSV de los ZIPs...")
                for info in archivos_info:
                    if os.path.exists(info['zip']):
                        if extraer_csv_de_zip(info['zip'], info['csv']):
                            # Eliminar el ZIP temporal después de extraer
                            try:
                                os.remove(info['zip'])
                            except:
                                pass
                        else:
                            print(f"✗ No se pudo extraer {info['tipo']}")
                    else:
                        print(f"✗ No se descargó el ZIP para {info['tipo']}")
                
                # Contar éxitos y errores
                exitosos = sum(1 for r in resultados_descarga if r['success'])
                fallidos = len(resultados_descarga) - exitosos
                print(f"Descargas completadas: {exitosos} exitosas, {fallidos} fallidas")
            else:
                print("⚠ No hay archivos de MinIO para descargar")
            
            print(f"✓ Procesamiento completado para {representado_nombre}")
                
        except Exception as e:
            error_msg = f"Error en {representado_nombre} - {representado_cuit}: {str(e)}"
            errores.append(error_msg)
            print(f"✗ {error_msg}")
    
    # Guardar errores si los hay
    if errores:
        with open('errores.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(errores))
        print(f"\n⚠ Se registraron {len(errores)} errores en errores.txt")
        
    if errores2:
        with open('errores.json', 'w', encoding='utf-8') as f:
            json.dump(errores2, f, ensure_ascii=False, indent=2)
        print(f"⚠ Se registraron {len(errores2)} errores de API en errores.json")
    
    print(f"\n{'='*60}")
    print("Procesamiento masivo finalizado")
    print(f"{'='*60}")
    
    # Mostrar diálogo de finalización
    try:
        from tkinter import messagebox
        
        # Preparar mensaje de resumen
        total_procesados = len([d for d in datos if d['Procesar'].lower() == 'si'])
        exitosos = total_procesados - len(errores) - len(errores2)
        
        mensaje = f"Procesamiento completado\n\n"
        mensaje += f"Total procesados: {total_procesados}\n"
        mensaje += f"Exitosos: {exitosos}\n"
        
        if errores:
            mensaje += f"Errores de ejecución: {len(errores)}\n"
        if errores2:
            mensaje += f"Errores de API: {len(errores2)}\n"
            
        if errores or errores2:
            mensaje += f"\nRevisa los archivos de errores para más detalles."
            messagebox.showwarning("Procesamiento Finalizado", mensaje)
        else:
            mensaje += f"\n¡Todos los archivos se descargaron correctamente!"
            messagebox.showinfo("Procesamiento Exitoso", mensaje)
    except ImportError:
        # Si no está disponible tkinter, solo imprimir en consola
        pass


if __name__ == '__main__':
    # Ejemplo de uso
    # consulta_mc_csv()
    # print(consulta_requests_restantes(mail))
    pass
