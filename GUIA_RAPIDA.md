# Guía Rápida

Todo el detalle vive ahora en `README.md`. Usa esto como recordatorio corto:

```bash
python3 -m venv venv
source venv/bin/activate          # en Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # completa URL, MAIL, API_KEY
python mrbot.py                   # abre la GUI
```

Uso programático mínimo:
```python
from bin.consulta import consulta_mc, consulta_mc_csv
consulta_mc(...)                  # consulta individual
consulta_mc_csv("ejemplos_api/mis_comprobantes.xlsx")  # masivo
```

Más ejemplos, estructura y endpoints: ver `README.md`.
