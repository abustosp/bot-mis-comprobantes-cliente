import os

from dotenv import load_dotenv

ENV_FILE = os.getenv("MRBOT_ENV_FILE", ".env")
_BASE_URL_FALLBACK = "https://api-bots.mrbot.com.ar/"


def _load_env() -> None:
    # Permite recargar valores si el usuario edita el .env mientras la app está abierta
    load_dotenv(ENV_FILE, override=True)


# Cargar variables de entorno para valores por defecto
_load_env()
DEFAULT_BASE_URL = os.getenv("URL", _BASE_URL_FALLBACK)
DEFAULT_API_KEY = os.getenv("API_KEY", "")
DEFAULT_EMAIL = os.getenv("MAIL", "")


def reload_env_defaults() -> tuple[str, str, str]:
    """
    Recarga el archivo .env y devuelve los valores actuales.
    """
    _load_env()
    return (
        os.getenv("URL", _BASE_URL_FALLBACK),
        os.getenv("API_KEY", ""),
        os.getenv("MAIL", ""),
    )
