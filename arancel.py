# arancel.py

import json
import streamlit as st
import pandas as pd
from utils import limpiar_codigo_arancel, normalizar_texto

@st.cache_data
def cargar_arancel_df():
    """
    Carga el archivo JSON del arancel y lo convierte en un DataFrame de Pandas.
    Usa funciones de utils.py para estandarizar códigos y glosas.
    """
    try:
        with open('arancel_clasificacion.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rows = []
        for _, value in data.items():
            desc_partida = value.get('descripcion_partida', '')
            subcategorias = value.get('subcategorias', {})
            if isinstance(subcategorias, dict):
                for codigo, glosa in subcategorias.items():
                    rows.append([desc_partida, str(codigo), glosa.strip()])
        
        df_plano = pd.DataFrame(rows, columns=['descripcion_partida', 'codigo_arancel', 'glosa_original'])
        
        # Limpieza y estandarización usando utils.py
        df_plano['codigo_arancel'] = df_plano['codigo_arancel'].apply(limpiar_codigo_arancel)
        df_plano['glosa_normalizada'] = df_plano['glosa_original'].apply(normalizar_texto)
        
        # Eliminar filas donde el código o la glosa quedaron vacíos
        df_plano.dropna(subset=['codigo_arancel', 'glosa_original'], inplace=True)
        df_plano = df_plano[df_plano['codigo_arancel'] != '']

        print("✓ DataFrame de aranceles creado y estandarizado en memoria.")
        return df_plano
    except FileNotFoundError:
        st.warning("El archivo 'arancel_clasificacion.json' no se encontró.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al procesar arancel_clasificacion.json: {e}")
        return pd.DataFrame()

ARANCEL_DF = cargar_arancel_df()

def obtener_descripcion_arancel(codigo):
    """
    Recibe un código arancelario y devuelve su descripción original.
    """
    if ARANCEL_DF.empty or pd.isna(codigo):
        return "N/A"
    
    codigo_limpio = limpiar_codigo_arancel(codigo)
    resultado = ARANCEL_DF[ARANCEL_DF['codigo_arancel'] == codigo_limpio]
    
    if not resultado.empty:
        return resultado.iloc[0]['glosa_original']
    return "Código no encontrado"

def buscar_por_glosa(termino_busqueda):
    """
    Busca un término en la columna de glosas normalizadas.
    """
    if ARANCEL_DF.empty or not termino_busqueda:
        return pd.DataFrame()
    
    termino_normalizado = normalizar_texto(termino_busqueda)
    # Busca en la columna normalizada
    resultados = ARANCEL_DF[ARANCEL_DF['glosa_normalizada'].str.contains(termino_normalizado, na=False)]
    return resultados