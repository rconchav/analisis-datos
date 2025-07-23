# src/segmentador.py

import json
import os
import pandas as pd

def get_path_segmentacion(proyecto_activo):
    """Construye la ruta al archivo de segmentación del proyecto."""
    return os.path.join("proyectos", proyecto_activo, "segmentacion.json")

def cargar_reglas_segmentacion(proyecto_activo):
    """Carga las reglas de segmentación del proyecto activo."""
    path = get_path_segmentacion(proyecto_activo)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def guardar_reglas_segmentacion(proyecto_activo, reglas):
    """Guarda las reglas de segmentación del proyecto activo."""
    path = get_path_segmentacion(proyecto_activo)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(reglas, f, indent=4, ensure_ascii=False, sort_keys=True)

def reglas_a_dataframe(reglas):
    """Convierte las reglas a un DataFrame para visualizarlas."""
    if not reglas:
        return pd.DataFrame(columns=["Segmento", "Palabras Clave"])
        
    lista_para_df = []
    for segmento, palabras in reglas.items():
        lista_para_df.append({"Segmento": segmento, "Palabras Clave": ", ".join(palabras)})
    return pd.DataFrame(lista_para_df)