#!/usr/bin/env python3
"""
Script para verificar y crear el archivo .env si no existe.
"""

import os
import shutil

print("="*70)
print("VERIFICACIÓN DE CONFIGURACIÓN")
print("="*70)

# Verificar si existe .env
if os.path.exists('.env'):
    print("\n✓ El archivo .env ya existe")
    
    # Mostrar contenido (sin valores sensibles)
    print("\nContenido actual de .env:")
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if value and key.strip() in ['API_KEY', 'MAIL']:
                        # Ocultar valor sensible
                        print(f"  {key}=***")
                    else:
                        print(f"  {line}")
                else:
                    print(f"  {line}")
    
    print("\n✅ Configuración presente")
    
else:
    print("\n⚠ El archivo .env NO existe")
    
    if os.path.exists('.env.example'):
        print("\nSe encontró .env.example")
        respuesta = input("\n¿Deseas crear .env basándote en .env.example? (s/n): ")
        
        if respuesta.lower() == 's':
            shutil.copy('.env.example', '.env')
            print("\n✓ Archivo .env creado")
            print("\n⚠ IMPORTANTE: Debes editar el archivo .env y completar:")
            print("  1. MAIL: Tu email registrado en api-bots.mrbot.com.ar")
            print("  2. API_KEY: Tu clave API (solicítala en el sitio)")
            print("\nPuedes editar .env con cualquier editor de texto.")
        else:
            print("\n❌ No se creó el archivo .env")
            print("Debes crear manualmente el archivo .env con el siguiente contenido:")
            print("\n" + "-"*70)
            if os.path.exists('.env.example'):
                with open('.env.example', 'r') as f:
                    print(f.read())
            else:
                print("""URL=https://api-bots.mrbot.com.ar
MAIL=tu_email@ejemplo.com
API_KEY=tu_api_key_aqui""")
            print("-"*70)
    else:
        print("\nEl archivo .env.example tampoco existe")
        print("Crea manualmente el archivo .env con:")
        print("\n" + "-"*70)
        print("""URL=https://api-bots.mrbot.com.ar
MAIL=tu_email@ejemplo.com
API_KEY=tu_api_key_aqui""")
        print("-"*70)

print("\n" + "="*70)
