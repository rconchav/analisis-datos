# config.py

import os

# --- RUTAS DE CARPETAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")
CATALOGOS_DIR = os.path.join(BASE_DIR, "catalogos")
DATOS_DIR = os.path.join(BASE_DIR, "datos")

# --- ARCHIVOS DE DATOS ---
ARANCEL_JSON = os.path.join(DATOS_DIR, "arancel_clasificacion.json")
DICCIONARIO_JSON = os.path.join(DATOS_DIR, "diccionario_referencia.json")
LOG_PROCESADOS_JSON = os.path.join(DATOS_DIR, "processed_files.json")
PAISES_JSON = os.path.join(DATOS_DIR, "paises_continentes.json") # <- Nueva ruta