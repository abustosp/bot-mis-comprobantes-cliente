# 🚀 Guía Rápida - API v1 Mis Comprobantes

## Instalación Rápida

```bash
git clone https://github.com/abustosp/bot-mis-comprobantes-cliente.git
cd bot-mis-comprobantes-cliente
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus credenciales
```

## Uso Rápido

### GUI (Interfaz Gráfica)
```bash
python consulta-mc-gui.py
```

### Consulta Simple
```python
from bin.consulta import consulta_mc

response = consulta_mc(
    desde="01/01/2024",
    hasta="31/01/2024",
    cuit_inicio_sesion="20123456780",
    representado_nombre="EMPRESA SA",
    representado_cuit="30876543210",
    contrasena="tu_password",
    descarga_emitidos=True,
    descarga_recibidos=True,
    carga_minio=True,  # URLs de MinIO
    carga_json=True    # Datos JSON
)
```

### Descarga desde MinIO (10 workers)
```python
from bin.consulta import descargar_archivos_minio_concurrente

archivos = [
    {'url': response['mis_comprobantes_emitidos_url_minio'], 
     'destino': './emitidos.zip'},
    {'url': response['mis_comprobantes_recibidos_url_minio'], 
     'destino': './recibidos.zip'}
]

resultados = descargar_archivos_minio_concurrente(archivos)
```

### Procesamiento Masivo desde CSV
```python
from bin.consulta import consulta_mc_csv

consulta_mc_csv()  # Procesa Descarga-Mis-Comprobantes.csv
```

## Endpoints API v1

| Función | Endpoint | Método |
|---------|----------|--------|
| Consulta comprobantes | `/api/v1/mis_comprobantes/consulta` | POST |
| Requests restantes | `/api/v1/user/consultas/{email}` | GET |

## Parámetros Principales

### consulta_mc()

**Requeridos:**
- `desde`, `hasta`: fechas DD/MM/YYYY
- `cuit_inicio_sesion`: CUIT representante
- `representado_nombre`: nombre
- `representado_cuit`: CUIT representado
- `contrasena`: clave fiscal
- `descarga_emitidos`: bool
- `descarga_recibidos`: bool

**Opcionales:**
- `carga_minio=True`: URLs MinIO
- `carga_json=True`: datos JSON
- `b64=False`: archivos base64
- `carga_s3=False`: URLs S3
- `proxy_request=None`: usar proxy

## Response Fields

```python
{
  "success": True,
  "message": "...",
  "mis_comprobantes_emitidos_json": [...],     # Datos
  "mis_comprobantes_recibidos_json": [...],    # Datos
  "mis_comprobantes_emitidos_url_minio": "...", # URL
  "mis_comprobantes_recibidos_url_minio": "..." # URL
}
```

## Configuración .env

```env
URL=https://api-bots.mrbot.com.ar
MAIL=tu_email@ejemplo.com
API_KEY=tu_api_key
```

## CSV Format

```csv
Procesar|Desde|Hasta|CUIT Inicio|Representado|CUIT Representado|Clave|Descarga Emitidos|Descarga Recibidos|Ubicacion Emitidos|Nombre Emitidos|Ubicacion Recibidos|Nombre Recibidos
si|01/01/2024|31/12/2024|20123456780|EMPRESA SA|30876543210|password|si|si|./Descargas|Emitidos|./Descargas|Recibidos
```

**Notas:**
- Encoding: Se intenta cp1252 primero, luego utf-8
- Los archivos se descargan desde MinIO como ZIP y se extraen automáticamente
- Usar "Ubicacion" sin tilde para mayor compatibilidad
- Si la ruta especificada falla, se usa automáticamente: `Descargas/<Representado>/`

## Tests y Ejemplos

```bash
# Verificar instalación
python test_actualizacion.py

# Ver ejemplos
python ejemplos_uso.py
```

## Troubleshooting

**Error: "No module named 'dotenv'"**
```bash
pip install python-dotenv
```

**Error: "API Key inválida"**
- Verifica `.env` tiene `API_KEY` correcto
- Solicita nueva key en api-bots.mrbot.com.ar

**No descarga archivos de MinIO**
- Verifica `carga_minio=True` en request
- Chequea que response incluya URLs MinIO

## Links Útiles

- 📖 [README completo](README.md)
- 🌐 [API Docs](https://api-bots.mrbot.com.ar/docs)
- ☕ [Donaciones](https://cafecito.app/abustos)
