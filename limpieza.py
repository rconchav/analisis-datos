# limpieza.py

import pandas as pd
import glob
import os
import streamlit as st
from fuzzywuzzy import process
from config import MARCAS_VALIDAS, MAPA_PAIS_CONTINENTE, MAPA_REEMPLAZO_PAISES
from arancel import obtener_descripcion_arancel
from utils import limpiar_codigo_arancel, validar_y_limpiar_nombre

def cargar_y_limpiar_datos(input_path='input/'):
    archivos_excel = glob.glob(os.path.join(input_path, '*.xlsx'))
    if not archivos_excel:
        st.warning("No se encontraron archivos .xlsx en la carpeta 'input/'.")
        return None

    try:
        df = pd.concat([pd.read_excel(f, engine='openpyxl') for f in archivos_excel], ignore_index=True)
        df_limpio = df.copy()
    except Exception as e:
        st.error(f"Error al leer los archivos Excel: {e}")
        return None

    try:
        df_limpio['fecha'] = pd.to_datetime(df_limpio[['AÑO', 'MES', 'DIA']].rename(columns={'AÑO':'year', 'MES':'month', 'DIA':'day'}), errors='coerce')
        df_limpio.drop(['AÑO', 'MES', 'DIA'], axis=1, inplace=True)
    except KeyError:
        st.error("Error: Los archivos Excel deben contener las columnas 'AÑO', 'MES' y 'DIA'.")
        return None

    df_limpio.columns = [str(col).strip().lower().replace(' ', '_').replace('.', '_') for col in df_limpio.columns]
    
    nombre_col_arancel = 'partida_arancelaria'
    nombre_col_cif = next((col for col in df_limpio.columns if 'cif' in col and ('usd' in col or 'us$' in col)), None)
    nombre_col_pais = next((col for col in df_limpio.columns if 'país' in col and 'origen' in col), None)

    if nombre_col_arancel not in df_limpio.columns:
        st.error(f"Error Crítico: No se encontró la columna '{nombre_col_arancel}'. Revisa tu archivo Excel.")
        return None

    if nombre_col_pais:
        df_limpio[nombre_col_pais] = df_limpio[nombre_col_pais].astype(str).str.lower()
        df_limpio['pais_estandarizado'] = df_limpio[nombre_col_pais].replace(MAPA_REEMPLAZO_PAISES)
        df_limpio['continente'] = df_limpio['pais_estandarizado'].map(MAPA_PAIS_CONTINENTE).fillna('Otros')
    else:
        df_limpio['continente'] = 'Desconocido'
        nombre_col_pais = 'pais_original_placeholder'
        df_limpio[nombre_col_pais] = 'Desconocido'
        df_limpio['pais_estandarizado'] = 'Desconocido'
    
    df_limpio[nombre_col_arancel] = df_limpio[nombre_col_arancel].apply(limpiar_codigo_arancel)
    df_limpio['descripcion_arancel'] = df_limpio[nombre_col_arancel].apply(obtener_descripcion_arancel)

    if 'producto' in df_limpio.columns:
        df_limpio['producto_limpio'] = df_limpio['producto'].apply(validar_y_limpiar_nombre)
    else:
        df_limpio['producto_limpio'] = ''
            
    if 'marca' in df_limpio.columns:
        df_limpio['marca'] = df_limpio['marca'].fillna('').astype(str)
        df_limpio['marca_original'] = df_limpio['marca']
        mapa_errores_comunes = {'khun': 'kuhn', 'class': 'claas'}
        df_limpio['marca'] = df_limpio['marca'].replace(mapa_errores_comunes)
        lista_marcas_validas = list(MARCAS_VALIDAS)
        marcas_a_revisar = df_limpio[~df_limpio['marca'].isin(MARCAS_VALIDAS)]['marca'].dropna().unique()
        mapa_correccion_fuzzy = {}
        for marca_sucia in marcas_a_revisar:
            if marca_sucia:
                mejor_match, puntaje = process.extractOne(marca_sucia, lista_marcas_validas)
                if puntaje >= 90:
                    mapa_correccion_fuzzy[marca_sucia] = mejor_match
        df_limpio['marca'] = df_limpio['marca'].replace(mapa_correccion_fuzzy)
        df_limpio['marca_estandarizada'] = df_limpio['marca'].apply(lambda x: x if x in MARCAS_VALIDAS else 'otras marcas')
    
    columnas_numericas = [col for col in df_limpio.columns if 'cantidad' in col or 'total' in col]
    if nombre_col_cif:
        columnas_numericas.append(nombre_col_cif)
    else:
        st.error("Error Crítico: No se pudo encontrar la columna de valor CIF.")
        return None

    for col in columnas_numericas:
        if col in df_limpio.columns:
            df_limpio[col] = pd.to_numeric(df_limpio[col], errors='coerce')

    df_limpio.dropna(subset=['fecha', nombre_col_cif], inplace=True)
    df_limpio.drop_duplicates(inplace=True)
    
    columnas_a_renombrar = {
        'fecha': 'fecha', 'numero_de_aceptacion': 'id_aceptacion', 'marca_original': 'marca_original',
        'marca_estandarizada': 'marca_final', 'pais_estandarizado': 'pais_final', 'continente': 'continente',
        'cantidad': 'cantidad', 'categoria_bulto': 'categoria_bulto', 'producto': 'producto',
        'producto_limpio': 'producto_limpio', 'variedad': 'variedad', 'descripcion': 'descripcion',
        'descripcion_arancel': 'descripcion_arancel', nombre_col_arancel: 'codigo_arancel',
        nombre_col_cif: 'valor_cif', nombre_col_pais: 'pais_original'
    }
    
    columnas_existentes = {k: v for k, v in columnas_a_renombrar.items() if k in df_limpio.columns}
    df_final = df_limpio[list(columnas_existentes.keys())].rename(columns=columnas_existentes)
    
    return df_final