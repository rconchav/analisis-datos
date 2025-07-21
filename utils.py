# utils.py

import streamlit as st
import io
import pandas as pd
import re
import unicodedata
import json
import base64

def to_excel(df):
    """Convierte un DataFrame a un archivo Excel en memoria para su descarga."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

def limpiar_codigo_arancel(codigo):
    """Limpia y estandariza códigos arancelarios."""
    if pd.isna(codigo): return ""
    s_codigo = str(int(float(codigo))) if isinstance(codigo, float) else str(codigo)
    return re.sub(r'\D', '', s_codigo)

def normalizar_texto(texto):
    """Elimina tildes y convierte a minúsculas."""
    if not isinstance(texto, str): return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

def validar_y_limpiar_nombre(texto):
    """Estandariza nombres para filtros (quita tildes, caracteres especiales y espacios)."""
    if not isinstance(texto, str): return ""
    texto_normalizado = normalizar_texto(texto)
    texto_con_espacios = re.sub(r'[^a-z0-9]+', ' ', texto_normalizado)
    return "".join(texto_con_espacios.split())

def formatar_moneda_cl(valor):
    """Formatea un número como moneda con '.' para miles y ',' para decimales."""
    if pd.isna(valor): return "$ 0,00"
    formato_intermedio = f"${valor:,.2f}"
    return formato_intermedio.replace(',', 'X').replace('.', ',').replace('X', '.')

def cargar_mapeo_paises():
    """Carga el archivo paises_continentes.json y crea los diccionarios de mapeo."""
    try:
        with open("datos/paises_continentes.json", 'r', encoding='utf-8') as f:
            data_paises = json.load(f)
        mapa_pais_continente = {pais['nombre']: pais['continente'] for pais in data_paises}
        mapa_reemplazo_paises = {alias: pais['nombre'] for pais in data_paises for alias in pais.get('alias', [])}
        return mapa_pais_continente, mapa_reemplazo_paises
    except FileNotFoundError:
        return {}, {}

def highlight_headers(styler, selections):
    """Aplica estilo a las cabeceras de las columnas seleccionadas en el asistente."""
    styler.set_table_styles([{'selector': 'th', 'props': [('background-color', '#F0F2F6'), ('color', 'black')]}], overwrite=False)
    colors = {'principal': '#4F8BF9', 'secundario': '#17A589', 'valor': '#F39C12', 'pais': '#9B59B6', 'fecha': '#E74C3C'}
    for role, col_name in selections.items():
        if col_name and col_name in styler.columns:
            color = colors.get(role, '#34495E')
            col_idx = styler.columns.get_loc(col_name)
            styler.set_table_styles([{'selector': f'th.col_heading.level0.col{col_idx}', 'props': [('background-color', color), ('color', 'white')]}], overwrite=False)
    return styler