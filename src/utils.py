# src/utils.py

import streamlit as st
import os
import pandas as pd
import io
import json
import re
import unicodedata
import locale

def configurar_pagina(titulo_pagina: str, layout: str = "wide"):
    st.set_page_config(layout=layout, page_title=titulo_pagina)
    estilos_fuentes = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;700&display=swap');
        [data-testid="stAppViewContainer"] {
            font-family: 'Figtree', sans-serif;
        }
        </style>
    """
    st.markdown(estilos_fuentes, unsafe_allow_html=True)
    path_css = os.path.join(".streamlit", "assets", "style.css")
    if os.path.exists(path_css):
        with open(path_css) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Advertencia: No se encontró el archivo de estilos en la ruta: {path_css}")

def manejar_columnas_duplicadas(df: pd.DataFrame) -> pd.DataFrame:
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        nuevos_nombres = [dup + f'_{i}' if i != 0 else dup for i in range(sum(cols == dup))]
        cols[cols[cols == dup].index] = nuevos_nombres
    df.columns = cols
    return df

@st.cache_data
def cargar_mapeo_paises():
    """
    Carga los datos de mapeo de países, continentes y coordenadas.
    CORREGIDO: Ahora devuelve TRES diccionarios, incluyendo las coordenadas.
    """
    path_paises = os.path.join("datos", "paises_continentes.json")
    pais_continente = {}
    reemplazo_paises = {}
    pais_coordenadas = {} # Diccionario para latitud y longitud

    if os.path.exists(path_paises):
        with open(path_paises, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "nombre" in item:
                    nombre_canonico = item["nombre"].upper()
                    
                    # Mapeo para continentes
                    if "continente" in item:
                        pais_continente[nombre_canonico] = item["continente"]
                    
                    # Mapeo para alias y reemplazos
                    reemplazo_paises[nombre_canonico] = nombre_canonico
                    for alias in item.get("alias", []):
                        reemplazo_paises[alias.upper()] = nombre_canonico
                    
                    # Mapeo para coordenadas
                    if "latitud" in item and "longitud" in item:
                        pais_coordenadas[nombre_canonico] = {
                            "lat": item["latitud"],
                            "lon": item["longitud"]
                        }
                        
    return pais_continente, reemplazo_paises, pais_coordenadas


def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

try:
    locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')

def formatar_moneda_cl(valor):
    if pd.isna(valor): return "$ 0"
    try:
        return locale.currency(valor, grouping=True, symbol=True)
    except (ValueError, TypeError):
        return "$ 0"