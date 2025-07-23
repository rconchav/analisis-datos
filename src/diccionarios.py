# src/diccionarios.py

import json
import os
import pandas as pd

def get_path_diccionario(proyecto_activo):
    """Construye la ruta al archivo de diccionario del proyecto."""
    return os.path.join("proyectos", proyecto_activo, "diccionario.json")

def cargar_diccionario(proyecto_activo):
    """Carga el diccionario del proyecto activo."""
    path = get_path_diccionario(proyecto_activo)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def guardar_diccionario(proyecto_activo, diccionario):
    """Guarda el diccionario del proyecto activo."""
    path = get_path_diccionario(proyecto_activo)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(diccionario, f, indent=4, ensure_ascii=False, sort_keys=True)

def diccionario_a_dataframe(diccionario):
    """Convierte el diccionario a un DataFrame para visualizarlo."""
    if not diccionario:
        return pd.DataFrame(columns=["Filtro Principal", "Filtro Secundario"])
    
    lista_para_df = []
    for principal, secundarios in diccionario.items():
        for secundario in secundarios:
            lista_para_df.append({"Filtro Principal": principal, "Filtro Secundario": secundario})
    return pd.DataFrame(lista_para_df)