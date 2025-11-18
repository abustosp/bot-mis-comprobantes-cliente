import requests
import csv
from dotenv import load_dotenv
import os
import json


load_dotenv(".env", override=True)

root_url = os.getenv("URL")
mail = os.getenv("MAIL")
api_key = os.getenv("API_KEY")


def consulta_mc(desde, 
                hasta, 
                cuit_inicio_sesion, 
                representado_nombre, 
                representado_cuit, 
                contrasena, 
                descarga_emitidos: bool, 
                descarga_recibidos: bool):
    
    url = root_url + "/mis-comprobantes"
    
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key
    }
    
    payload = {
        'email': mail,
        'fecha_desde': desde,
        'fecha_hasta': hasta,
        'cuit_contribuyente': cuit_inicio_sesion,
        'cuit_representada': representado_cuit,
        'password': contrasena,
        'descargar_recibidas': descarga_recibidos,
        'descargar_emitidas': descarga_emitidos,
        'carga_json': True
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    return response.json()


def consulta_requests_restantes(mail):
    
    url = root_url + "/consultas-disponibles"
    
    headers = {
        'x-api-key': api_key
    }
    
    params = {
        'email': mail
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    return response.json()


def save_to_csv(data, filename):
    with open(filename, 'w', newline='') as csvfile:
        if data:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(data)


def consulta_mc_csv():
    
    datos = csv.DictReader(open('Descarga-Mis-Comprobantes.csv'), delimiter='|', quotechar="'")
    
    for dato in datos:
        if dato['Procesar'].lower() != 'si':
            continue
        desde = dato['Desde']
        hasta = dato['Hasta']
        cuit_inicio_sesion = dato['CUIT Inicio']
        representado_nombre = dato['Representado']
        representado_cuit = dato['CUIT Representado']
        contrasena = dato['Clave']
        
        descarga_emitidos = dato['Descarga Emitidos'].lower() == 'si'
        descarga_recibidos = dato['Descarga Recibidos'].lower() == 'si'
        
        errores = []
        errores2 = []
        
        try:
            response = consulta_mc(desde, 
                                    hasta, 
                                    cuit_inicio_sesion, 
                                    representado_nombre, 
                                    representado_cuit, 
                                    contrasena, 
                                    descarga_emitidos, 
                                    descarga_recibidos)
            
            if 'error' in response or 'detail' in response:
                error_msg = response.get('error', response.get('detail', 'Error desconocido'))
                errores2.append({
                    'request': {
                        'desde': desde,
                        'hasta': hasta,
                        'cuit_inicio_sesion': cuit_inicio_sesion,
                        'representado_nombre': representado_nombre,
                        'representado_cuit': representado_cuit,
                        'contrasena': contrasena,
                        'descarga_emitidos': descarga_emitidos,
                        'descarga_recibidos': descarga_recibidos
                    },
                    'error': str(error_msg)
                })
            
            def guardar_data(ubicacion, nombre, seccion_response):
                if not os.path.exists(ubicacion):
                    os.makedirs(ubicacion)
                filename = nombre
                json.dump(response[seccion_response], open(f'{ubicacion}/{filename}.json', 'w'))
                save_to_csv(response[seccion_response], f'{ubicacion}/{filename}.csv')

            if descarga_emitidos and 'emitidas' in response:
                guardar_data(dato['Ubicación Emitidos'], 
                            dato['Nombre Emitidos'], 
                            'emitidas')

            if descarga_recibidos and 'recibidas' in response:
                guardar_data(dato['Ubicación Recibidos'], 
                            dato['Nombre Recibidos'], 
                            'recibidas')
                
        except Exception as e:
            errores.append(f"Error en {representado_nombre} - {representado_cuit}: {str(e)}")
            
    if errores:
        open('errores.txt', 'w').write('\n'.join(errores))
        
    if errores2:
        json.dump(errores2, open('errores.json', 'w'))

        
#if __name__ == '__main__':
    #consulta_mc_csv()
    #consulta_requests_restantes(mail)