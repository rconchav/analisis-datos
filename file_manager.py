import json
import os

LOG_FILE = 'datos/processed_files.json'

def cargar_log_procesados():
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError: return {}
    return {}

def guardar_log_procesados(log):
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=4)

def ha_sido_procesado(nombre_archivo, tamano_archivo, log_seccion):
    if nombre_archivo in log_seccion and log_seccion[nombre_archivo]['size'] == tamano_archivo:
        return True
    return False

def actualizar_log(nombre_archivo, tamano_archivo, log_seccion):
    log_seccion[nombre_archivo] = {'size': tamano_archivo}