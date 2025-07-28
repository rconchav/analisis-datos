# src/diccionarios.py

import json
import os
import pandas as pd

# --- CONSTANTES PARA LOS ARCHIVOS GLOBALES ---
DICCIONARIO_GLOBAL_FILE = os.path.join("datos", "diccionario_global.json")
REGLAS_SEGMENTACION_GLOBAL_FILE = os.path.join("datos", "reglas_segmentacion_global.json")

# --- FUNCIONES PARA DICCIONARIO GLOBAL ---
def cargar_diccionario_global():
    if os.path.exists(DICCIONARIO_GLOBAL_FILE):
        with open(DICCIONARIO_GLOBAL_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def guardar_diccionario_global(diccionario):
    os.makedirs("datos", exist_ok=True)
    with open(DICCIONARIO_GLOBAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(diccionario, f, indent=4)

def diccionario_global_a_dataframe(diccionario):
    lista_mapeos = []
    for filtro, mapeos in diccionario.items():
        for original, estandarizado in mapeos.items():
            lista_mapeos.append({"Filtro": filtro, "Valor Original": original, "Valor Estandarizado": estandarizado})
    if not lista_mapeos:
        return pd.DataFrame(columns=["Filtro", "Valor Original", "Valor Estandarizado"])
    return pd.DataFrame(lista_mapeos)

# --- FUNCIONES PARA REGLAS DE SEGMENTACIÓN GLOBALES ---
def cargar_reglas_segmentacion_global():
    if os.path.exists(REGLAS_SEGMENTACION_GLOBAL_FILE):
        with open(REGLAS_SEGMENTACION_GLOBAL_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def guardar_reglas_segmentacion_global(reglas):
    os.makedirs("datos", exist_ok=True)
    with open(REGLAS_SEGMENTACION_GLOBAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(reglas, f, indent=4)

# --- NUEVO: Función movida desde segmentador.py para centralizar ---
def reglas_a_dataframe(reglas):
    """Convierte el diccionario de reglas de segmentación a un DataFrame para edición."""
    if not reglas:
        return pd.DataFrame(columns=['Segmento', 'Palabras Clave'])

    lista_reglas = []
    for segmento, palabras in reglas.items():
        lista_reglas.append({'Segmento': segmento, 'Palabras Clave': ', '.join(palabras)})
    return pd.DataFrame(lista_reglas)

# --- FUNCIONES LEGACY (POR PROYECTO) ---
def cargar_diccionario(proyecto_id):
    path = os.path.join("proyectos", proyecto_id, "diccionario.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def guardar_diccionario(proyecto_id, diccionario):
    path = os.path.join("proyectos", proyecto_id, "diccionario.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(diccionario, f, indent=4)