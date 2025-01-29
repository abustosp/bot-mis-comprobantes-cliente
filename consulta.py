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
        if dato['Descarga Emitidos'].lower() == 'si':
            descarga_emitidos = True
        else:
            descarga_emitidos = False
        if dato['Descarga Recibidos'].lower() == 'si':
            descarga_recibidos = True
        else:
            descarga_recibidos = False
        
        print(consulta_mc(desde, 
                          hasta, 
                          cuit_inicio_sesion, 
                          representado_nombre, 
                          representado_cuit, 
                          contrasena, 
                          descarga_emitidos, 
                          descarga_recibidos))
        
        print("Consulta realizada con éxito")
        

        
if __name__ == '__main__':
    consulta_mc_csv()