# Consulta de Mis Comprobantes vía API

## Descripción
Este proyecto te permite descargar y gestionar tus comprobantes mediante una interfaz gráfica. Utiliza datos almacenados en un archivo CSV y permite realizar descargas tanto de comprobantes emitidos como recibidos.

## Características
- Interfaz gráfica para facilitar la navegación y gestión de archivos.
- Posibilidad de descargar archivos CSV de comprobantes.
- Función para abrir y editar archivos CSV en una ventana emergente.
- Opción para realizar donaciones.

## Instalación y uso sencillo
1. Descarga la última versión desde la sección de [releases](https://github.com/abustosp/bot-mis-comprobantes-cliente/releases).
2. Descomprime el archivo descargado.
3. Navega al directorio descomprimido.
4. Abrir el ejecutable.


## Requisitos para correlo desde terminal
- Python 3.x
- Librerías: `tkinter`, `ttk`, `os`, `webbrowser`, `dotenv`, y otras necesarias para la ejecución del script. (todas se encuentas en el requirements.txt)

## Instalación
1. Clona el repositorio:
   ```bash
   git clone https://github.com/abustosp/bot-mis-comprobantes-cliente.git
   ```
   
2. Navega al directorio del proyecto:
   ```bash
   cd bot-mis-comprobantes-cliente
   ```

3. Crea un entorno virtual:
   ```bash
    python -m venv venv
    ```

4. Activa el entorno virtual:
    ```bash
    source venv/bin/activate
    ```
    ```powershell
    .\venv\Scripts\Activate
    ```

5. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso por terminal
1. Asegúrate de tener un archivo llamado `Descarga-Mis-Comprobantes.csv` en el directorio del proyecto con el formato adecuado.
2. Ejecuta el programa:
   ```bash
   python3 consulta-mc-gui.py
   ```
   ```powershell
    py .\consulta-mc-gui.py
    ```
3. Sigue las instrucciones en la interfaz gráfica para descargar tus comprobantes.

## Contribuciones
Se agradecen las contribuciones. Por favor, sigue estos pasos:
1. Haz un "fork" del proyecto.
2. Crea tu rama de características (`git checkout -b feature/nuevaCaracteristica`).
3. Realiza tus cambios y "commitea" (`git commit -m 'Agrega nueva característica'`).
4. Envía un "push" a tu rama (`git push origin feature/nuevaCaracteristica`).
5. Abre un "pull request".

## Licencia
Este proyecto está bajo la Licencia propia. Para más detalles, consulta el archivo LICENSE.

## Donaciones
Si deseas apoyar el desarrollo de este proyecto, puedes hacerlo en ☕ [Cafecito](https://cafecito.app/abustos).

## Contacto
Para preguntas o inquietudes, puedes abrir un "issue" en este repositorio.