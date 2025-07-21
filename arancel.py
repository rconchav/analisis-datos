# arancel.py

import json
import streamlit as st
import pandas as pd
from utils import limpiar_codigo_arancel, normalizar_texto

@st.cache_data
def cargar_arancel_df():
    """Carga el archivo JSON del arancel y lo convierte en un DataFrame de Pandas."""
    ruta_arancel = 'datos/arancel_clasificacion.json'
    try:
        with open(ruta_arancel, 'r', encoding='utf-8') as f:
            data = json.load(f)
        rows = []
        for _, value in data.items():
            desc_partida = value.get('descripcion_partida', '')
            subcategorias = value.get('subcategorias', {})
            if isinstance(subcategorias, dict):
                for codigo, glosa in subcategorias.items():
                    rows.append([desc_partida, str(codigo), glosa.strip()])
        
        df_plano = pd.DataFrame(rows, columns=['descripcion_partida', 'codigo_arancel', 'glosa_original'])
        df_plano['codigo_arancel'] = df_plano['codigo_arancel'].apply(limpiar_codigo_arancel)
        df_plano['glosa_normalizada'] = df_plano['glosa_original'].apply(normalizar_texto)
        df_plano.dropna(subset=['codigo_arancel', 'glosa_original'], inplace=True)
        return df_plano[df_plano['codigo_arancel'] != '']
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

ARANCEL_DF = cargar_arancel_df()

def obtener_descripcion_arancel(codigo):
    """Recibe un código arancelario y devuelve su descripción original."""
    if ARANCEL_DF.empty or pd.isna(codigo): return "N/A"
    codigo_limpio = limpiar_codigo_arancel(codigo)
    resultado = ARANCEL_DF[ARANCEL_DF['codigo_arancel'] == codigo_limpio]
    if not resultado.empty: return resultado.iloc[0]['glosa_original']
    return "Código no encontrado"

def buscar_por_glosa(termino_busqueda):
    """Busca un término en la columna de glosas normalizadas."""
    if ARANCEL_DF.empty or not termino_busqueda: return pd.DataFrame()
    termino_normalizado = normalizar_texto(termino_busqueda)
    return ARANCEL_DF[ARANCEL_DF['glosa_normalizada'].str.contains(termino_normalizado, na=False)]