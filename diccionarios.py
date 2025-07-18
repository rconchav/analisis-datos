# diccionarios.py

import pandas as pd
import glob
import os
import json
import streamlit as st
import shutil
from utils import validar_y_limpiar_nombre

# --- Rutas ---
DATOS_DIR = 'datos'
DICCIONARIOS_DIR = 'diccionarios' # Nueva carpeta para perfiles
os.makedirs(DICCIONARIOS_DIR, exist_ok=True)
PATH_DICCIONARIO_ACTIVO = os.path.join(DATOS_DIR, 'diccionario_referencia.json')

def cargar_diccionario():
    """Carga el diccionario ACTIVO desde el archivo JSON de forma segura."""
    if os.path.exists(PATH_DICCIONARIO_ACTIVO) and os.path.getsize(PATH_DICCIONARIO_ACTIVO) > 0:
        try:
            with open(PATH_DICCIONARIO_ACTIVO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def guardar_diccionario(diccionario):
    """Guarda el diccionario ACTIVO en el archivo JSON."""
    with open(PATH_DICCIONARIO_ACTIVO, 'w', encoding='utf-8') as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=4)

# --- Funciones de Gestión de Perfiles ---

def listar_perfiles_guardados():
    """Devuelve una lista de los perfiles de diccionario guardados."""
    perfiles = [f.replace('.json', '') for f in os.listdir(DICCIONARIOS_DIR) if f.endswith('.json')]
    return sorted(perfiles)

def guardar_perfil_como(nombre_perfil):
    """Guarda el diccionario activo como un nuevo perfil."""
    nombre_limpio = validar_y_limpiar_nombre(nombre_perfil)
    if not nombre_limpio:
        st.error("El nombre del perfil no puede estar vacío.")
        return False
    
    ruta_destino = os.path.join(DICCIONARIOS_DIR, f"{nombre_limpio}.json")
    if os.path.exists(PATH_DICCIONARIO_ACTIVO) and os.path.getsize(PATH_DICCIONARIO_ACTIVO) > 0:
        shutil.copyfile(PATH_DICCIONARIO_ACTIVO, ruta_destino)
        st.success(f"Diccionario guardado como el perfil '{nombre_limpio}'.")
        return True
    else:
        st.warning("El diccionario activo está vacío. No se ha guardado ningún perfil.")
        return False

def cargar_perfil(nombre_perfil):
    """Carga un perfil guardado como el diccionario activo."""
    ruta_origen = os.path.join(DICCIONARIOS_DIR, f"{nombre_perfil}.json")
    if os.path.exists(ruta_origen):
        shutil.copyfile(ruta_origen, PATH_DICCIONARIO_ACTIVO)
        st.success(f"Perfil '{nombre_perfil}' cargado como diccionario activo.")
        return True
    st.error(f"No se encontró el perfil '{nombre_perfil}'.")
    return False

def resetear_diccionario_activo():
    """Limpia el diccionario activo creando un archivo JSON vacío."""
    guardar_diccionario({})
    st.success("Diccionario activo reseteado. Listo para empezar un nuevo análisis.")

# --- Funciones de Procesamiento y Edición (sin cambios en la lógica interna) ---

def generar_diccionario_desde_datos(df):
    diccionario = cargar_diccionario()
    df_agrupado = df.groupby('filtro_principal')['filtro_secundario'].unique().apply(list)
    for principal, secundarios in df_agrupado.items():
        principal_limpio = validar_y_limpiar_nombre(principal)
        if principal_limpio and principal_limpio not in diccionario:
            diccionario[principal_limpio] = []
        for secundario in secundarios:
            if secundario and secundario not in diccionario[principal_limpio]:
                diccionario[principal_limpio].append(secundario)
    guardar_diccionario(diccionario)

def procesar_catalogos_externos(input_path='catalogos/'):
    pass # Mantén tu lógica existente aquí

def agregar_filtro(principal, secundario):
    if not principal or not secundario: st.error("Ambos filtros son obligatorios."); return
    principal_limpio = validar_y_limpiar_nombre(principal)
    secundario_limpio = validar_y_limpiar_nombre(secundario)
    diccionario = cargar_diccionario()
    if principal_limpio not in diccionario: diccionario[principal_limpio] = []
    if secundario_limpio not in diccionario[principal_limpio]:
        diccionario[principal_limpio].append(secundario_limpio)
        guardar_diccionario(diccionario)
        st.success(f"Filtro '{secundario_limpio}' agregado a '{principal_limpio}'.")
    else: st.warning(f"El filtro secundario '{secundario_limpio}' ya existe.")

def eliminar_filtro_principal(principal):
    diccionario = cargar_diccionario()
    if principal in diccionario:
        del diccionario[principal]; guardar_diccionario(diccionario); return True
    return False

def eliminar_filtro_secundario(principal, secundario):
    diccionario = cargar_diccionario()
    if principal in diccionario and secundario in diccionario[principal]:
        diccionario[principal].remove(secundario)
        if not diccionario[principal]: del diccionario[principal]
        guardar_diccionario(diccionario); return True
    return False

def editar_filtro_principal(antiguo, nuevo):
    nuevo_limpio = validar_y_limpiar_nombre(nuevo)
    if not nuevo_limpio: st.error("El nuevo nombre no puede estar vacío."); return False
    diccionario = cargar_diccionario()
    if antiguo in diccionario:
        if nuevo_limpio in diccionario:
            modelos_existentes = set(diccionario[nuevo_limpio])
            modelos_a_fusionar = set(diccionario[antiguo])
            diccionario[nuevo_limpio] = sorted(list(modelos_existentes.union(modelos_a_fusionar)))
        else:
            diccionario[nuevo_limpio] = diccionario[antiguo]
        del diccionario[antiguo]; guardar_diccionario(diccionario); return True
    return False

def editar_filtro_secundario(principal, antiguo, nuevo):
    nuevo_limpio = validar_y_limpiar_nombre(nuevo)
    if not nuevo_limpio: st.error("El nuevo nombre no puede estar vacío."); return False
    diccionario = cargar_diccionario()
    if principal in diccionario and antiguo in diccionario[principal]:
        if nuevo_limpio in diccionario[principal] and nuevo_limpio != antiguo:
            st.warning(f"El filtro '{nuevo_limpio}' ya existe. Se eliminará el antiguo.")
            diccionario[principal].remove(antiguo)
        else:
            diccionario[principal] = [nuevo_limpio if item == antiguo else item for item in diccionario[principal]]
        guardar_diccionario(diccionario)
        st.success(f"Filtro secundario '{antiguo}' actualizado a '{nuevo_limpio}'.")
        return True
    return False