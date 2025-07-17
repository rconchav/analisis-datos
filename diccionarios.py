# diccionarios.py

import pandas as pd
import glob
import os
import json
import streamlit as st
import camelot
from utils import validar_y_limpiar_nombre

def cargar_diccionario():
    path_diccionario = 'diccionario_referencia.json'
    if os.path.exists(path_diccionario) and os.path.getsize(path_diccionario) > 0:
        try:
            with open(path_diccionario, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def guardar_diccionario(diccionario):
    with open('diccionario_referencia.json', 'w', encoding='utf-8') as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=4)

def generar_diccionario_desde_datos(df):
    st.write("Generando diccionario a partir de los datos de importación...")
    diccionario_marcas = cargar_diccionario()
    df_agrupado = df.groupby('marca_final')['producto_limpio'].unique().apply(list)
    for marca, modelos in df_agrupado.items():
        marca_limpia = validar_y_limpiar_nombre(marca)
        if marca_limpia not in diccionario_marcas:
            diccionario_marcas[marca_limpia] = []
        for modelo in modelos:
            if modelo not in diccionario_marcas[marca_limpia]:
                diccionario_marcas[marca_limpia].append(modelo)
    guardar_diccionario(diccionario_marcas)
    st.success("Diccionario generado/actualizado desde los datos principales.")

def procesar_catalogos_externos(input_path='catalogos/'):
    archivos_catalogos = glob.glob(os.path.join(input_path, '*'))
    if not archivos_catalogos:
        st.info("No hay catálogos externos para procesar.")
        return
    diccionario_marcas = cargar_diccionario()
    # ... (lógica para leer catálogos) ...
    guardar_diccionario(diccionario_marcas)
    st.success("Diccionario enriquecido con catálogos externos.")

def agregar_marca_modelo(marca, modelo):
    if not marca or not modelo:
        st.error("Tanto la marca como el modelo son campos obligatorios.")
        return
    marca_limpia = validar_y_limpiar_nombre(marca)
    modelo_limpio = validar_y_limpiar_nombre(modelo)
    diccionario_marcas = cargar_diccionario()
    if marca_limpia not in diccionario_marcas:
        diccionario_marcas[marca_limpia] = []
    if modelo_limpio not in diccionario_marcas[marca_limpia]:
        diccionario_marcas[marca_limpia].append(modelo_limpio)
        guardar_diccionario(diccionario_marcas)
        st.success(f"Se agregó el modelo '{modelo_limpio}' a la marca '{marca_limpia}'.")
    else:
        st.warning(f"El modelo '{modelo_limpio}' ya existe para la marca '{marca_limpia}'.")

# --- NUEVAS FUNCIONES DE GESTIÓN ---
def eliminar_marca(marca_a_eliminar):
    """Elimina una marca completa del diccionario."""
    diccionario = cargar_diccionario()
    if marca_a_eliminar in diccionario:
        del diccionario[marca_a_eliminar]
        guardar_diccionario(diccionario)
        st.success(f"Marca '{marca_a_eliminar}' eliminada correctamente.")
        return True
    return False

def eliminar_modelo(marca, modelo_a_eliminar):
    """Elimina un modelo específico de una marca."""
    diccionario = cargar_diccionario()
    if marca in diccionario and modelo_a_eliminar in diccionario[marca]:
        diccionario[marca].remove(modelo_a_eliminar)
        # Si la marca se queda sin modelos, se elimina la marca
        if not diccionario[marca]:
            del diccionario[marca]
        guardar_diccionario(diccionario)
        st.success(f"Modelo '{modelo_a_eliminar}' eliminado de la marca '{marca}'.")
        return True
    return False

def editar_nombre_marca(marca_antigua, marca_nueva):
    """Edita el nombre de una marca."""
    marca_nueva_limpia = validar_y_limpiar_nombre(marca_nueva)
    if not marca_nueva_limpia:
        st.error("El nuevo nombre de la marca no puede estar vacío.")
        return False
    
    diccionario = cargar_diccionario()
    if marca_antigua in diccionario:
        # Si la nueva marca ya existe, fusionamos los modelos
        if marca_nueva_limpia in diccionario:
            modelos_existentes = set(diccionario[marca_nueva_limpia])
            modelos_a_fusionar = set(diccionario[marca_antigua])
            diccionario[marca_nueva_limpia] = sorted(list(modelos_existentes.union(modelos_a_fusionar)))
        else:
            diccionario[marca_nueva_limpia] = diccionario[marca_antigua]
        
        del diccionario[marca_antigua]
        guardar_diccionario(diccionario)
        st.success(f"Marca '{marca_antigua}' renombrada a '{marca_nueva_limpia}'.")
        return True
    return False