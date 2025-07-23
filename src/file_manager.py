# file_manager.py

import json
import os

def cargar_log_procesados(proyecto_activo):
    """Carga el registro de archivos procesados para un proyecto específico."""
    path_log = f"proyectos/{proyecto_activo}/processed_files.json"
    if os.path.exists(path_log) and os.path.getsize(path_log) > 0:
        try:
            with open(path_log, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def guardar_log_procesados(proyecto_activo, log):
    """Guarda el registro actualizado para un proyecto específico."""
    path_proyecto = f"proyectos/{proyecto_activo}"
    os.makedirs(path_proyecto, exist_ok=True)
    path_log = os.path.join(path_proyecto, "processed_files.json")
    with open(path_log, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=4)

def ha_sido_procesado(nombre_archivo, tamano_archivo, log_seccion):
    """Verifica si un archivo ya ha sido procesado basado en nombre y tamaño."""
    return nombre_archivo in log_seccion and log_seccion[nombre_archivo]['size'] == tamano_archivo

def actualizar_log(nombre_archivo, tamano_archivo, log_seccion):
    """Añade o actualiza la entrada de un archivo en una sección del log."""
    log_seccion[nombre_archivo] = {'size': tamano_archivo}