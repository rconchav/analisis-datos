# segmentador.py

import json
import os
import streamlit as st

def cargar_reglas(proyecto_activo):
    """Carga las reglas de segmentación del proyecto activo."""
    path_segmentacion = f"proyectos/{proyecto_activo}/segmentacion.json"
    if os.path.exists(path_segmentacion) and os.path.getsize(path_segmentacion) > 0:
        try:
            with open(path_segmentacion, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def guardar_reglas(proyecto_activo, reglas):
    """Guarda las reglas de segmentación del proyecto activo."""
    path_proyecto = f"proyectos/{proyecto_activo}"
    os.makedirs(path_proyecto, exist_ok=True)
    path_segmentacion = os.path.join(path_proyecto, "segmentacion.json")
    with open(path_segmentacion, 'w', encoding='utf-8') as f:
        json.dump(reglas, f, indent=4, ensure_ascii=False, sort_keys=True)

def agregar_regla(proyecto_activo, categoria, keyword):
    """Agrega una nueva palabra clave a una categoría para el proyecto activo."""
    if not categoria or not keyword:
        st.error("La categoría y la palabra clave son obligatorias.")
        return
    
    reglas = cargar_reglas(proyecto_activo)
    categoria_upper = categoria.strip().upper()
    keyword_lower = keyword.strip().lower()

    if categoria_upper not in reglas:
        reglas[categoria_upper] = []
    
    if keyword_lower not in reglas[categoria_upper]:
        reglas[categoria_upper].append(keyword_lower)
        reglas[categoria_upper] = sorted(reglas[categoria_upper])
        guardar_reglas(proyecto_activo, reglas)
        st.success(f"Palabra clave '{keyword_lower}' agregada a la categoría '{categoria_upper}'.")
    else:
        st.warning(f"La palabra clave '{keyword_lower}' ya existe en la categoría '{categoria_upper}'.")

def eliminar_regla(proyecto_activo, categoria, keyword):
    """Elimina una palabra clave de una categoría para el proyecto activo."""
    reglas = cargar_reglas(proyecto_activo)
    if categoria in reglas and keyword in reglas[categoria]:
        reglas[categoria].remove(keyword)
        if not reglas[categoria]:
            del reglas[categoria]
        guardar_reglas(proyecto_activo, reglas)
        return True
    return False