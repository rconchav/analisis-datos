import io
import pandas as pd
import re
import unicodedata
import json
from config import PAISES_JSON

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

def limpiar_codigo_arancel(codigo):
    if pd.isna(codigo): return ""
    s_codigo = str(int(float(codigo))) if isinstance(codigo, float) else str(codigo)
    return re.sub(r'\D', '', s_codigo)

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.lower()

def validar_y_limpiar_nombre(texto):
    if not isinstance(texto, str): return ""
    texto_normalizado = normalizar_texto(texto)
    texto_con_espacios = re.sub(r'[^a-z0-9]+', ' ', texto_normalizado)
    return "".join(texto_con_espacios.split())

def formatar_moneda_cl(valor):
    if pd.isna(valor): return "$ 0,00"
    formato_intermedio = f"${valor:,.2f}"
    return formato_intermedio.replace(',', 'X').replace('.', ',').replace('X', '.')

def cargar_mapeo_paises():
    try:
        with open(PAISES_JSON, 'r', encoding='utf-8') as f: data_paises = json.load(f)
        mapa_pais_continente = {pais_info['nombre']: pais_info['continente'] for pais_info in data_paises}
        mapa_reemplazo_paises = {alias: pais_info['nombre'] for pais_info in data_paises for alias in pais_info['alias']}
        return mapa_pais_continente, mapa_reemplazo_paises
    except FileNotFoundError: return {}, {}