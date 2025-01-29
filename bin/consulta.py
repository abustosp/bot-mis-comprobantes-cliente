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
        
        response = consulta_mc(desde, 
                                hasta, 
                                cuit_inicio_sesion, 
                                representado_nombre, 
                                representado_cuit, 
                                contrasena, 
                                descarga_emitidos, 
                                descarga_recibidos)

        if descarga_emitidos:
            ruta_emitidos = dato['Ubicación Emitidos']
            if not os.path.exists(ruta_emitidos):
                os.makedirs(ruta_emitidos)
            filename = dato['Nombre Emitidos'] 
            json.dump(response['mis_comprobantes_emitidos'], open(f'{ruta_emitidos}/{filename}.json', 'w'))
            save_to_csv(response['mis_comprobantes_emitidos'], f'{ruta_emitidos}/{filename}.csv')

        if descarga_recibidos:
            ruta_recibidos = dato['Ubicación Recibidos']
            if not os.path.exists(ruta_recibidos):
                os.makedirs(ruta_recibidos)
            filename = dato['Nombre Recibidos']
            json.dump(response['mis_comprobantes_recibidos'], open(f'{ruta_recibidos}/{filename}.json', 'w'))
            save_to_csv(response['mis_comprobantes_recibidos'], f'{ruta_recibidos}/{filename}.csv')

        
if __name__ == '__main__':
    consulta_mc_csv()