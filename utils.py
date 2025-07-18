# utils.py

import streamlit as st # <-- LÍNEA FALTANTE AÑADIDA
import io
import pandas as pd
import re
import unicodedata
import json

def to_excel(df):
    """Convierte un DataFrame a un archivo Excel en memoria para su descarga."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    processed_data = output.getvalue()
    return processed_data

def limpiar_codigo_arancel(codigo):
    """Función robusta para limpiar y estandarizar códigos arancelarios."""
    if pd.isna(codigo):
        return ""
    s_codigo = str(int(float(codigo))) if isinstance(codigo, float) else str(codigo)
    return re.sub(r'\D', '', s_codigo)

def normalizar_texto(texto):
    """Normaliza un texto eliminando tildes y convirtiéndolo a minúsculas."""
    if not isinstance(texto, str):
        return ""
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.lower()

def validar_y_limpiar_nombre(texto):
    """Función de validación estándar para marcas, modelos y productos."""
    if not isinstance(texto, str):
        return ""
    texto_normalizado = normalizar_texto(texto)
    texto_con_espacios = re.sub(r'[^a-z0-9]+', ' ', texto_normalizado)
    return "".join(texto_con_espacios.split())

def formatar_moneda_cl(valor):
    """Formatea un número como moneda con '.' para miles y ',' para decimales."""
    if pd.isna(valor):
        return "$ 0,00"
    formato_intermedio = f"${valor:,.2f}"
    formato_final = formato_intermedio.replace(',', 'X').replace('.', ',').replace('X', '.')
    return formato_final

def cargar_mapeo_paises():
    """Carga el archivo paises_continentes.json y crea los diccionarios de mapeo."""
    try:
        with open("datos/paises_continentes.json", 'r', encoding='utf-8') as f:
            data_paises = json.load(f)
        
        mapa_pais_continente = {}
        mapa_reemplazo_paises = {}
        
        for pais_info in data_paises:
            nombre_pais = pais_info['nombre']
            mapa_pais_continente[nombre_pais] = pais_info['continente']
            for alias in pais_info.get('alias', []):
                mapa_reemplazo_paises[alias] = nombre_pais
        
        return mapa_pais_continente, mapa_reemplazo_paises
    except FileNotFoundError:
        return {}, {}

def inject_custom_css(file_path):
    """Función para inyectar CSS personalizado desde un archivo."""
    try:
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Archivo CSS no encontrado en la ruta: {file_path}")