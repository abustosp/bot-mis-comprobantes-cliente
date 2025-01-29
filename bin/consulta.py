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
    
    url = root_url + "/api/v1/comprobantes/consulta"
    
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
        'descarga_recibidos': descarga_recibidos
}
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
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
        
        try:
            response = consulta_mc(desde, 
                                    hasta, 
                                    cuit_inicio_sesion, 
                                    representado_nombre, 
                                    representado_cuit, 
                                    contrasena, 
                                    descarga_emitidos, 
                                    descarga_recibidos)
            
            def guardar_data(ubicacion, nombre, seccion_response):
                if not os.path.exists(ubicacion):
                    os.makedirs(ubicacion)
                filename = nombre
                json.dump(response[seccion_response], open(f'{ubicacion}/{filename}.json', 'w'))
                save_to_csv(response[seccion_response], f'{ubicacion}/{filename}.csv')

            if descarga_emitidos:
                guardar_data(dato['Ubicación Emitidos'], 
                            dato['Nombre Emitidos'], 
                            'mis_comprobantes_emitidos')

            if descarga_recibidos:
                guardar_data(dato['Ubicación Recibidos'], 
                            dato['Nombre Recibidos'], 
                            'mis_comprobantes_recibidos')
                
        except Exception as e:
            errores.append(f"Error en {representado_nombre} - {representado_cuit}: {str(e)}")
            
    if errores:
        open('errores.txt', 'w').write('\n'.join(errores))
        
if __name__ == '__main__':
    consulta_mc_csv()