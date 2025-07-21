# diccionarios.py

import os
import json
import streamlit as st
from utils import validar_y_limpiar_nombre

def cargar_diccionario(proyecto_activo):
    """Carga el diccionario del proyecto activo desde su archivo JSON."""
    path_diccionario = f"proyectos/{proyecto_activo}/diccionario.json"
    if os.path.exists(path_diccionario) and os.path.getsize(path_diccionario) > 0:
        try:
            with open(path_diccionario, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def guardar_diccionario(proyecto_activo, diccionario):
    """Guarda el diccionario del proyecto activo en su archivo JSON."""
    path_proyecto = f"proyectos/{proyecto_activo}"
    os.makedirs(path_proyecto, exist_ok=True)
    path_diccionario = os.path.join(path_proyecto, "diccionario.json")
    with open(path_diccionario, 'w', encoding='utf-8') as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=4, sort_keys=True)

def generar_diccionario_desde_datos(proyecto_activo, df):
    """Genera y actualiza el diccionario a partir del DataFrame de datos limpios."""
    diccionario = cargar_diccionario(proyecto_activo)
    if 'filtro_principal' in df.columns and 'filtro_secundario' in df.columns:
        df_agrupado = df.groupby('filtro_principal')['filtro_secundario'].unique().apply(list)
        for principal, secundarios in df_agrupado.items():
            principal_limpio = validar_y_limpiar_nombre(principal)
            if principal_limpio and principal_limpio not in diccionario:
                diccionario[principal_limpio] = []
            for secundario in secundarios:
                if secundario and secundario not in diccionario[principal_limpio]:
                    diccionario[principal_limpio].append(secundario)
    guardar_diccionario(proyecto_activo, diccionario)

def procesar_catalogos_externos(proyecto_activo, input_path='catalogos/'):
    """Procesa archivos externos para AÑADIR información al diccionario del proyecto."""
    # Esta función puede expandirse en el futuro si es necesario
    pass

def agregar_filtro(proyecto_activo, principal, secundario):
    """Agrega una nueva entrada de filtro al diccionario del proyecto."""
    if not principal or not secundario:
        st.error("Ambos filtros son obligatorios."); return
    principal_limpio = validar_y_limpiar_nombre(principal)
    secundario_limpio = validar_y_limpiar_nombre(secundario)
    diccionario = cargar_diccionario(proyecto_activo)
    if principal_limpio not in diccionario: diccionario[principal_limpio] = []
    if secundario_limpio not in diccionario[principal_limpio]:
        diccionario[principal_limpio].append(secundario_limpio)
        guardar_diccionario(proyecto_activo, diccionario)
        st.success(f"Filtro '{secundario_limpio}' agregado a '{principal_limpio}'.")
    else: st.warning(f"El filtro secundario '{secundario_limpio}' ya existe.")

def eliminar_filtro_principal(proyecto_activo, principal):
    diccionario = cargar_diccionario(proyecto_activo)
    if principal in diccionario:
        del diccionario[principal]; guardar_diccionario(proyecto_activo, diccionario); return True
    return False

def eliminar_filtro_secundario(proyecto_activo, principal, secundario):
    diccionario = cargar_diccionario(proyecto_activo)
    if principal in diccionario and secundario in diccionario[principal]:
        diccionario[principal].remove(secundario)
        if not diccionario[principal]: del diccionario[principal]
        guardar_diccionario(proyecto_activo, diccionario); return True
    return False

def editar_filtro_principal(proyecto_activo, antiguo, nuevo):
    nuevo_limpio = validar_y_limpiar_nombre(nuevo)
    if not nuevo_limpio: st.error("El nuevo nombre no puede estar vacío."); return False
    diccionario = cargar_diccionario(proyecto_activo)
    if antiguo in diccionario:
        if nuevo_limpio in diccionario and nuevo_limpio != antiguo:
            items_existentes = set(diccionario[nuevo_limpio])
            items_a_fusionar = set(diccionario[antiguo])
            diccionario[nuevo_limpio] = sorted(list(items_existentes.union(items_a_fusionar)))
        else:
            diccionario[nuevo_limpio] = diccionario[antiguo]
        if nuevo_limpio != antiguo: del diccionario[antiguo]
        guardar_diccionario(proyecto_activo, diccionario); return True
    return False

def editar_filtro_secundario(proyecto_activo, principal, antiguo, nuevo):
    nuevo_limpio = validar_y_limpiar_nombre(nuevo)
    if not nuevo_limpio: st.error("El nuevo nombre no puede estar vacío."); return False
    diccionario = cargar_diccionario(proyecto_activo)
    if principal in diccionario and antiguo in diccionario[principal]:
        if nuevo_limpio in diccionario[principal] and nuevo_limpio != antiguo:
            diccionario[principal].remove(antiguo)
        else:
            diccionario[principal] = [nuevo_limpio if item == antiguo else item for item in diccionario[principal]]
        guardar_diccionario(proyecto_activo, diccionario); return True
    return False