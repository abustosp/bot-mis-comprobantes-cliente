import os

from dotenv import load_dotenv

# Cargar variables de entorno para valores por defecto
load_dotenv()

DEFAULT_BASE_URL = os.getenv("URL", "https://api-bots.mrbot.com.ar/")
DEFAULT_API_KEY = os.getenv("API_KEY", "")
DEFAULT_EMAIL = os.getenv("MAIL", "")
