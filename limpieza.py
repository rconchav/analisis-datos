# limpieza.py

import pandas as pd
import glob
import os
import streamlit as st
import json
from fuzzywuzzy import process
from arancel import obtener_descripcion_arancel
from utils import limpiar_codigo_arancel, validar_y_limpiar_nombre, cargar_mapeo_paises
from config import DICCIONARIO_JSON

def cargar_y_limpiar_datos(input_path='input/'):
    archivos_excel = glob.glob(os.path.join("input", '*.xlsx'))
    if not archivos_excel:
        st.warning("No se encontraron archivos .xlsx en la carpeta 'input/'.")
        return None

    df = pd.concat([pd.read_excel(f, engine='openpyxl') for f in archivos_excel], ignore_index=True)
    df_limpio = df.copy()

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

    if not nombre_col_arancel or not nombre_col_cif:
        st.error("Error Crítico: Asegúrese de que el archivo Excel contenga 'PARTIDA ARANCELARIA' y una columna con 'CIF' y 'USD'.")
        return None

    df_limpio[nombre_col_arancel] = df_limpio[nombre_col_arancel].apply(limpiar_codigo_arancel)
    df_limpio['descripcion_arancel'] = df_limpio[nombre_col_arancel].apply(obtener_descripcion_arancel)
    
    MAPA_PAIS_CONTINENTE, MAPA_REEMPLAZO_PAISES = cargar_mapeo_paises()
    if nombre_col_pais:
        df_limpio[nombre_col_pais] = df_limpio[nombre_col_pais].astype(str).str.lower()
        df_limpio['pais_estandarizado'] = df_limpio[nombre_col_pais].replace(MAPA_REEMPLAZO_PAISES)
        df_limpio['continente'] = df_limpio['pais_estandarizado'].map(MAPA_PAIS_CONTINENTE).fillna('Otros')
    else:
        df_limpio['continente'] = 'Desconocido'
        nombre_col_pais = 'pais_original_placeholder'
        df_limpio[nombre_col_pais] = 'Desconocido'
        df_limpio['pais_estandarizado'] = 'Desconocido'

    for col in df_limpio.select_dtypes(include=['object']).columns:
        if col in df_limpio.columns:
            df_limpio[col] = df_limpio[col].str.strip().str.lower()

    if 'producto' in df_limpio.columns:
        df_limpio['filtro_secundario'] = df_limpio['producto'].apply(validar_y_limpiar_nombre)
    else:
        df_limpio['filtro_secundario'] = ''

    if 'marca' in df_limpio.columns:
        try:
            with open(DICCIONARIO_JSON, 'r', encoding='utf-8') as f:
                marcas_validas_dict = json.load(f)
            MARCAS_VALIDAS = set(marcas_validas_dict.keys())
        except (FileNotFoundError, json.JSONDecodeError):
            MARCAS_VALIDAS = set()
            
        df_limpio['marca'] = df_limpio['marca'].fillna('').astype(str)
        df_limpio['marca_original'] = df_limpio['marca']
        mapa_errores_comunes = {'khun': 'kuhn', 'class': 'claas'}
        df_limpio['marca'] = df_limpio['marca'].replace(mapa_errores_comunes)
        
        # --- MEJORA: Se utiliza el valor del slider ---
        # Si el slider no existe en el estado de la sesión, se usa 90 por defecto.
        sensibilidad = st.session_state.get('sensibilidad_fuzzy', 90)
        
        lista_marcas_validas = list(MARCAS_VALIDAS)
        if lista_marcas_validas:
            marcas_a_revisar = df_limpio[~df_limpio['marca'].isin(MARCAS_VALIDAS)]['marca'].dropna().unique()
            mapa_correccion_fuzzy = {}
            for marca_sucia in marcas_a_revisar:
                if marca_sucia:
                    mejor_match, puntaje = process.extractOne(marca_sucia, lista_marcas_validas)
                    # La comparación ahora es dinámica
                    if puntaje >= sensibilidad:
                        mapa_correccion_fuzzy[marca_sucia] = mejor_match
            df_limpio['marca'] = df_limpio['marca'].replace(mapa_correccion_fuzzy)
            df_limpio['filtro_principal'] = df_limpio['marca'].apply(lambda x: x if x in MARCAS_VALIDAS else 'otras marcas')
        else:
            df_limpio['filtro_principal'] = df_limpio['marca']
    else:
        df_limpio['filtro_principal'] = 'sin_marca'

    columnas_numericas = [col for col in df_limpio.columns if 'cantidad' in col or 'total' in col] + [nombre_col_cif]
    for col in columnas_numericas:
        if col in df_limpio.columns:
            df_limpio[col] = pd.to_numeric(df_limpio[col], errors='coerce')
    
    df_limpio.dropna(subset=['fecha', nombre_col_cif], inplace=True)
    df_limpio.drop_duplicates(inplace=True)
    
    columnas_a_renombrar = {
        'fecha': 'fecha', 
        'numero_de_aceptacion': 'id_aceptacion', 
        'marca_original': 'marca_original',
        'filtro_principal': 'filtro_principal',
        'filtro_secundario': 'filtro_secundario',
        'pais_estandarizado': 'pais_final', 
        'continente': 'continente',
        'cantidad': 'cantidad', 
        'producto': 'producto',
        'descripcion': 'descripcion',
        'descripcion_arancel': 'descripcion_arancel',
        nombre_col_arancel: 'codigo_arancel',
        nombre_col_cif: 'valor_cif',
        nombre_col_pais: 'pais_original'
    }
    
    columnas_existentes = {k: v for k, v in columnas_a_renombrar.items() if k in df_limpio.columns}
    df_final = df_limpio[list(columnas_existentes.keys())].rename(columns=columnas_existentes)
    
    return df_final