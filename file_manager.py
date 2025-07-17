# file_manager.py

import json
import os

LOG_FILE = 'processed_files.json'

def cargar_log_procesados():
    """Carga el registro de archivos procesados de forma segura."""
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def guardar_log_procesados(log):
    """Guarda el registro actualizado en el archivo JSON."""
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=4)

def ha_sido_procesado(nombre_archivo, tamano_archivo, log_seccion):
    """Verifica si un archivo ya ha sido procesado basado en nombre y tamaño."""
    if nombre_archivo in log_seccion and log_seccion[nombre_archivo]['size'] == tamano_archivo:
        return True
    return False

def actualizar_log(nombre_archivo, tamano_archivo, log_seccion):
    """Añade o actualiza la entrada de un archivo en el log."""
    log_seccion[nombre_archivo] = {
        'size': tamano_archivo
    }