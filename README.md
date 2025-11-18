# Consulta de Mis Comprobantes vía API

Cliente para descargar y gestionar comprobantes de AFIP/ARCA mediante la API de Mr. Bot. Permite realizar consultas masivas, descargar archivos desde MinIO con múltiples workers concurrentes y gestionar tus comprobantes emitidos y recibidos.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#️-configuración)
- [Uso](#-uso)
- [API Reference](#-api-reference)
- [Contribuciones](#-contribuciones)
- [Licencia](#-licencia)
- [Donaciones](#-donaciones)

## ✨ Características

- 🚀 **Consultas masivas**: Procesa múltiples consultas desde un archivo CSV
- ⚡ **Descargas concurrentes**: Descarga archivos desde MinIO con 10 workers simultáneos
- 🔄 **API v1 actualizada**: Utiliza los últimos endpoints de api-bots.mrbot.com.ar
- 💾 **Múltiples formatos**: Soporta JSON, CSV y archivos ZIP desde MinIO
- 🖥️ **Interfaz gráfica**: GUI simple con Tkinter para facilitar el uso
- 📊 **Gestión de errores**: Registro detallado de errores en archivos JSON y TXT
- 🔐 **Configuración segura**: Variables de entorno con dotenv

## 📁 Estructura del Proyecto

```
mis-comprobantes-cliente/
├── bin/
│   ├── consulta.py              # Lógica principal de consultas y descargas
│   ├── ABP-blanco-en-fondo-negro.ico
│   └── ABP blanco sin fondo.png
├── Descargas/                   # Directorio para archivos descargados
│   ├── Emitidos.csv
│   ├── Emitidos.json
│   ├── Recibidos.csv
│   └── Recibidos.json
├── Ejecutable/                  # Versión compilada (release)
│   ├── bin/
│   ├── consulta-mc-gui          # Ejecutable Linux
│   ├── Descarga-Mis-Comprobantes.csv
│   ├── Descarga-Mis-Comprobantes.xlsx
│   ├── LICENSE
│   └── README.md
├── cliente_api_mrbot.py         # Ejemplo de cliente con Streamlit
├── consulta-mc-gui.py           # GUI con Tkinter
├── Descarga-Mis-Comprobantes.csv   # Plantilla CSV para consultas masivas
├── Descarga-Mis-Comprobantes.xlsx  # Plantilla Excel
├── .env                         # Variables de entorno (no versionado)
├── .env.example                 # Ejemplo de configuración
├── autopyLinux.json             # Configuración auto-py-to-exe Linux
├── autopyWindows.json           # Configuración auto-py-to-exe Windows
├── requirements.txt             # Dependencias Python
├── LICENSE                      # Licencia del proyecto
└── README.md                    # Este archivo
```

## 📦 Requisitos

- Python 3.8 o superior
- Cuenta activa en api-bots.mrbot.com.ar
- API Key válida

### Dependencias

```txt
requests>=2.32.3
python-dotenv>=1.0.1
certifi>=2024.12.14
charset-normalizer>=3.4.1
idna>=3.10
urllib3>=2.3.0
```

## 🔧 Instalación

### Opción 1: Ejecutable (Recomendado para usuarios finales)

1. Descarga la última versión desde [releases](https://github.com/abustosp/bot-mis-comprobantes-cliente/releases)
2. Descomprime el archivo
3. Ejecuta el archivo `consulta-mc-gui` (Linux) o `consulta-mc-gui.exe` (Windows)

### Opción 2: Desde código fuente

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/abustosp/bot-mis-comprobantes-cliente.git
   cd bot-mis-comprobantes-cliente
   ```

2. **Crear entorno virtual**:
   ```bash
   python -m venv venv
   ```

3. **Activar entorno virtual**:
   
   Linux/Mac:
   ```bash
   source venv/bin/activate
   ```
   
   Windows PowerShell:
   ```powershell
   .\venv\Scripts\Activate
   ```
   
   Windows CMD:
   ```cmd
   .\venv\Scripts\activate.bat
   ```

4. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuración

1. **Crear archivo `.env`** en la raíz del proyecto con las siguientes variables:

```env
URL=https://api-bots.mrbot.com.ar
MAIL=tu_email@ejemplo.com
API_KEY=tu_api_key_aqui
```

2. **Configurar el archivo CSV** `Descarga-Mis-Comprobantes.csv`:

```csv
Procesar|Desde|Hasta|CUIT Inicio|Representado|CUIT Representado|Clave|Descarga Emitidos|Descarga Recibidos|Ubicacion Emitidos|Nombre Emitidos|Ubicacion Recibidos|Nombre Recibidos
si|01/01/2024|31/12/2024|20123456780|EMPRESA EJEMPLO SA|30876543210|MiClave123|si|si|./Descargas|Emitidos|./Descargas|Recibidos
```

**Columnas del CSV:**
- `Procesar`: "si" o "no" para procesar la fila
- `Desde`: Fecha inicio (DD/MM/YYYY)
- `Hasta`: Fecha fin (DD/MM/YYYY)
- `CUIT Inicio`: CUIT del representante
- `Representado`: Nombre del representado
- `CUIT Representado`: CUIT del representado
- `Clave`: Contraseña fiscal
- `Descarga Emitidos`: "si" o "no"
- `Descarga Recibidos`: "si" o "no"
- `Ubicacion Emitidos`: Carpeta destino (sin tilde para compatibilidad)
- `Nombre Emitidos`: Nombre base del archivo
- `Ubicacion Recibidos`: Carpeta destino (sin tilde para compatibilidad)
- `Nombre Recibidos`: Nombre base del archivo

**Notas importantes:**
- El CSV se lee automáticamente con encoding cp1252, si falla intenta utf-8
- Los archivos se descargan desde MinIO como ZIP
- Se extrae automáticamente el CSV del ZIP con el nombre especificado
- Los archivos ZIP temporales se eliminan después de la extracción
- **Creación inteligente de directorios:**
  - Primero intenta crear el directorio especificado
  - Si falla (permisos, ruta inválida), usa: `Descargas/<Nombre_Representado>/`
  - Si todo falla, usa: `Descargas/`

## 🚀 Uso

### Interfaz Gráfica (GUI)

```bash
python consulta-mc-gui.py
```

Desde la interfaz podrás:
- Editar la configuración (.env)
- Ver requests restantes
- Editar el CSV de descargas
- Iniciar el proceso de descarga
- Realizar donaciones

### Modo Programático

```python
from bin.consulta import consulta_mc, descargar_archivos_minio_concurrente

# Realizar una consulta
response = consulta_mc(
    desde="01/01/2024",
    hasta="31/01/2024",
    cuit_inicio_sesion="20123456780",
    representado_nombre="EMPRESA SA",
    representado_cuit="30876543210",
    contrasena="MiClave123",
    descarga_emitidos=True,
    descarga_recibidos=True,
    carga_minio=True,
    carga_json=True
)

# Descargar archivos desde MinIO (10 workers concurrentes)
archivos = [
    {'url': response['mis_comprobantes_emitidos_url_minio'], 'destino': './emitidos.zip'},
    {'url': response['mis_comprobantes_recibidos_url_minio'], 'destino': './recibidos.zip'}
]
resultados = descargar_archivos_minio_concurrente(archivos, max_workers=10)
```

### Procesamiento Masivo desde CSV

```python
from bin.consulta import consulta_mc_csv

# Procesa todas las filas del CSV con Procesar='si'
consulta_mc_csv()
```

## 📚 API Reference

### Endpoints Utilizados

#### 1. Consulta de Mis Comprobantes
```
POST https://api-bots.mrbot.com.ar/api/v1/mis_comprobantes/consulta
```

**Headers:**
- `x-api-key`: Tu API key
- `email`: Tu email registrado
- `Content-Type`: application/json

**Body:**
```json
{
  "desde": "01/01/2024",
  "hasta": "31/12/2024",
  "cuit_inicio_sesion": "20123456780",
  "representado_nombre": "EMPRESA SA",
  "representado_cuit": "30876543210",
  "contrasena": "password",
  "descarga_emitidos": true,
  "descarga_recibidos": true,
  "carga_minio": true,
  "carga_json": true,
  "b64": false,
  "carga_s3": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Consulta exitosa",
  "mis_comprobantes_emitidos_url_minio": "https://minio.example.com/...",
  "mis_comprobantes_recibidos_url_minio": "https://minio.example.com/...",
  "mis_comprobantes_emitidos_json": [...],
  "mis_comprobantes_recibidos_json": [...]
}
```

#### 2. Consultas Disponibles
```
GET https://api-bots.mrbot.com.ar/api/v1/user/consultas/{email}
```

**Headers:**
- `x-api-key`: Tu API key

**Response:**
```json
{
  "consultas_disponibles": 95,
  "maximas_consultas_mensuales": 100,
  "consultas_realizadas_mes_actual": 5
}
```

### Funciones Principales

#### `consulta_mc()`
Realiza una consulta de Mis Comprobantes.

**Parámetros:**
- `desde` (str): Fecha inicio DD/MM/YYYY
- `hasta` (str): Fecha fin DD/MM/YYYY
- `cuit_inicio_sesion` (str): CUIT del representante
- `representado_nombre` (str): Nombre del representado
- `representado_cuit` (str): CUIT del representado
- `contrasena` (str): Contraseña fiscal
- `descarga_emitidos` (bool): Descargar emitidos
- `descarga_recibidos` (bool): Descargar recibidos
- `carga_minio` (bool): Subir a MinIO (default: True)
- `carga_json` (bool): Obtener JSON (default: True)
- `b64` (bool): Archivos en base64 (default: False)
- `carga_s3` (bool): Subir a S3 (default: False)
- `proxy_request` (bool|None): Usar proxy (default: None)

#### `descargar_archivos_minio_concurrente()`
Descarga múltiples archivos desde MinIO con workers concurrentes.

**Parámetros:**
- `urls` (List[Dict]): Lista de {'url': str, 'destino': str}
- `max_workers` (int): Número de workers (default: 10)

**Retorna:** Lista de resultados con status de cada descarga

#### `consulta_requests_restantes()`
Consulta las requests disponibles del usuario.

**Parámetros:**
- `mail` (str): Email del usuario

**Retorna:** Dict con información de consultas

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork del proyecto
2. Crea tu rama de características (`git checkout -b feature/NuevaCaracteristica`)
3. Commit de tus cambios (`git commit -m 'Agrega nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia propia. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## ☕ Donaciones

Si este proyecto te resulta útil, considera apoyar su desarrollo:

[![Cafecito](https://cdn.cafecito.app/imgs/buttons/button_2.svg)](https://cafecito.app/abustos)

## 📧 Contacto

- **Autor**: Agustín Bustos Piasentini
- **Web**: [https://www.Agustin-Bustos-Piasentini.com.ar/](https://www.Agustin-Bustos-Piasentini.com.ar/)
- **Issues**: [GitHub Issues](https://github.com/abustosp/bot-mis-comprobantes-cliente/issues)

---

**Nota**: Este cliente utiliza la API v1 de api-bots.mrbot.com.ar. Para más información sobre la API, visita [https://api-bots.mrbot.com.ar/docs](https://api-bots.mrbot.com.ar/docs)