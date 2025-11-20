# Cliente API Mr Bot (Mis Comprobantes y módulos AFIP)

Cliente Tkinter y librerías Python para usar los endpoints de api-bots.mrbot.com.ar (Mis Comprobantes, RCEL, SCT, CCMA, Apócrifos y Consulta CUIT). Incluye ejemplos de Excel, descargas desde MinIO y flujo masivo desde archivos.

## Contenido rápido
- Qué necesitas
- Instalación y configuración
- Ejecutar la GUI
- Uso programático
- Estructura del proyecto
- Endpoints y módulos clave
- Tests y soporte

## Qué necesitas
- Python 3.8+
- Cuenta y API key en api-bots.mrbot.com.ar
- Dependencias: `pip install -r requirements.txt`

## Instalación y configuración
```bash
git clone https://github.com/abustosp/bot-mis-comprobantes-cliente.git
cd bot-mis-comprobantes-cliente
python3 -m venv venv
source venv/bin/activate          # en Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # edita con tus credenciales
```

`.env` mínimo:
```env
URL=https://api-bots.mrbot.com.ar
MAIL=tu_email@ejemplo.com
API_KEY=tu_api_key
```

Archivos de entrada:
- `Descarga-Mis-Comprobantes.xlsx` o `.csv` (plantillas en la raíz).
- Excels de ejemplo en `ejemplos_api/` (la GUI los genera si faltan).

## Ejecutar la GUI
```bash
python mrbot.py
```
Desde la GUI puedes:
- Editar base URL, API key y mail.
- Procesar Mis Comprobantes masivo (usa `bin.consulta.consulta_mc_csv`).
- Consultar RCEL, SCT, CCMA, Apócrifos y CUIT (individual/masivo según módulo).
- Previsualizar Excels y descargar archivos desde MinIO.

## Uso programático
```python
from bin.consulta import consulta_mc, consulta_mc_csv

# Consulta individual
resp = consulta_mc(
    desde="01/01/2024",
    hasta="31/01/2024",
    cuit_inicio_sesion="20123456780",
    representado_nombre="EMPRESA SA",
    representado_cuit="30876543210",
    contrasena="clave",
    descarga_emitidos=True,
    descarga_recibidos=True,
    carga_minio=True,
    carga_json=True,
)

# Procesamiento masivo (Excel/CSV)
consulta_mc_csv("./ejemplos_api/mis_comprobantes.xlsx")
```

Descarga desde MinIO con workers concurrentes:
```python
from bin.consulta import descargar_archivos_minio_concurrente

archivos = [
    {"url": resp["mis_comprobantes_emitidos_url_minio"], "destino": "./emitidos.zip"},
    {"url": resp["mis_comprobantes_recibidos_url_minio"], "destino": "./recibidos.zip"},
]
resultados = descargar_archivos_minio_concurrente(archivos, max_workers=10)
```

## Estructura del proyecto
```
.
├── mrbot.py                 # Menú principal GUI
├── mrbot_app/               # Helpers y ventanas Tkinter por módulo
│   ├── helpers.py
│   └── windows/             # mis_comprobantes, rcel, sct, ccma, apocrifos, consulta_cuit
├── bin/consulta.py          # Lógica Mis Comprobantes y descargas MinIO
├── ejemplos_api/            # Excels de ejemplo (autogenerables)
├── Descarga-Mis-Comprobantes.{csv,xlsx}
├── tests/                   # Tests existentes (reubicados)
├── requirements.txt
├── README.md
└── LICENSE
```

## Endpoints y módulos clave
- Mis Comprobantes: `POST /api/v1/mis_comprobantes/consulta` (GUI: “Descarga Mis Comprobantes”, código: `bin.consulta.consulta_mc`)
- RCEL: `POST /api/v1/rcel/consulta` (GUI: ventana RCEL)
- SCT: `POST /api/v1/sct/consulta` (GUI: ventana SCT con descargas MinIO)
- CCMA: `POST /api/v1/ccma/consulta`
- Apócrifos: `GET /api/v1/apoc/consulta/{cuit}`
- Consulta CUIT: `POST /api/v1/consulta_cuit/{individual|masivo}`
- Requests restantes: `GET /api/v1/user/consultas/{email}`

Helpers reutilizables: `mrbot_app/helpers.py` (safe_get/safe_post, previews de DataFrame, parseo de booleanos, etc.).

## Tests y validación
```bash
python -m py_compile mrbot.py mrbot_app/*.py mrbot_app/windows/*.py
# Tests (algunos requieren credenciales/Excels)
pytest tests  # o python tests/test_sct_descarga.py
```

## Soporte, licencia y donaciones
- Issues y soporte: https://github.com/abustosp/bot-mis-comprobantes-cliente/issues
- Licencia: ver `LICENSE`
- Donaciones: https://cafecito.app/abustos
