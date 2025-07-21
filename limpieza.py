# limpieza.py

import pandas as pd
import glob
import os
import streamlit as st
import json
from fuzzywuzzy import process
from arancel import obtener_descripcion_arancel
from utils import limpiar_codigo_arancel, validar_y_limpiar_nombre, cargar_mapeo_paises
from segmentador import cargar_reglas

def cargar_y_limpiar_datos(proyecto_activo):
    """
    Lee archivos Excel, aplica limpieza y estandarización basándose en la
    configuración de mapeo de columnas del proyecto activo.
    """
    path_config = f"proyectos/{proyecto_activo}/config.json"
    try:
        with open(path_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        mapeo = config['mapeo_columnas']
    except (FileNotFoundError, KeyError):
        st.error(f"Configuración para '{proyecto_activo}' no encontrada o incompleta. Por favor, configúrala en 'Inicio'.")
        return None

    archivos_excel = glob.glob(os.path.join("input", '*.xlsx'))
    if not archivos_excel:
        st.warning("No se encontraron archivos .xlsx en la carpeta 'input/'.")
        return None
    try:
        df = pd.concat([pd.read_excel(f, engine='openpyxl') for f in archivos_excel], ignore_index=True)
        df_limpio = df.copy()
    except Exception as e:
        st.error(f"Error al leer los archivos Excel: {e}")
        return None

    # Mapeo de columnas esenciales desde la configuración
    col_principal = mapeo['filtro_principal']
    col_secundario = mapeo['filtro_secundario_base']
    col_segmentacion = mapeo.get('segmentacion_base', col_secundario) # Usar secundario si no está definido
    col_valor = mapeo['valor_numerico']
    col_pais = mapeo['pais']
    config_fecha = mapeo['config_fecha']

    # Procesamiento de Fecha flexible
    try:
        if config_fecha.get('tipo') == 'Columnas separadas':
            col_ano = config_fecha['ano']; col_mes = config_fecha['mes']; col_dia = config_fecha['dia']
            df_limpio['fecha'] = pd.to_datetime(df_limpio[[col_ano, col_mes, col_dia]].rename(columns={col_ano:'year', col_mes:'month', col_dia:'day'}))
        else: # Una sola columna
            col_fecha_completa = config_fecha['fecha_completa']
            df_limpio['fecha'] = pd.to_datetime(df_limpio[col_fecha_completa])
    except Exception as e:
        st.error(f"Error al procesar las fechas con la configuración proporcionada: {e}")
        return None
    
    # Estandarización de nombres de columna restantes a minúsculas
    df_limpio.columns = [str(col).strip().lower() for col in df_limpio.columns]
    
    # Carga de configuraciones externas
    MAPA_PAIS_CONTINENTE, MAPA_REEMPLAZO_PAISES = cargar_mapeo_paises()
    reglas_segmentacion = cargar_reglas(proyecto_activo)
    path_diccionario_proyecto = f"proyectos/{proyecto_activo}/diccionario.json"
    try:
        with open(path_diccionario_proyecto, 'r', encoding='utf-8') as f:
            diccionario_proyecto = json.load(f)
        MARCAS_VALIDAS = set(diccionario_proyecto.keys())
    except (FileNotFoundError, json.JSONDecodeError):
        MARCAS_VALIDAS = set()
    
    # Renombrar columnas mapeadas a los nombres internos estándar de la aplicación
    columnas_renombrar = {
        col_principal.lower(): 'filtro_principal',
        col_secundario.lower(): 'producto',
        col_valor.lower(): 'valor_cif',
        col_pais.lower(): 'pais_origen_raw',
        "partida arancelaria": 'codigo_arancel' # Nombre común esperado tras pasar a minúsculas
    }
    df_limpio.rename(columns=columnas_renombrar, inplace=True)
    
    # Procesamiento de columnas internas
    df_limpio['filtro_secundario'] = df_limpio['producto'].apply(validar_y_limpiar_nombre)
    df_limpio['codigo_arancel'] = df_limpio['codigo_arancel'].apply(limpiar_codigo_arancel)
    df_limpio['descripcion_arancel'] = df_limpio['codigo_arancel'].apply(obtener_descripcion_arancel)
    df_limpio['valor_cif'] = pd.to_numeric(df_limpio['valor_cif'], errors='coerce')
    
    if 'pais_origen_raw' in df_limpio.columns:
        df_limpio['pais_estandarizado'] = df_limpio['pais_origen_raw'].astype(str).str.lower().replace(MAPA_REEMPLAZO_PAISES)
        df_limpio['continente'] = df_limpio['pais_estandarizado'].map(MAPA_PAIS_CONTINENTE).fillna('Otros')
    else:
        df_limpio['continente'] = 'Desconocido'

    # Segmentación de Productos
    if col_segmentacion.lower() in df_limpio.columns:
        df_limpio['segmento_producto'] = 'NO CLASIFICADO'
        for categoria, keywords in reversed(list(reglas_segmentacion.items())):
            patron = '|'.join(keywords)
            if patron:
                mask = df_limpio[col_segmentacion.lower()].str.contains(patron, na=False, case=False)
                df_limpio.loc[mask, 'segmento_producto'] = categoria
    
    # Limpieza con FuzzyWuzzy
    sensibilidad = st.session_state.get('sensibilidad_fuzzy', 90)
    if MARCAS_VALIDAS:
        lista_marcas_validas = list(MARCAS_VALIDAS)
        marcas_a_revisar = df_limpio[~df_limpio['filtro_principal'].isin(MARCAS_VALIDAS)]['filtro_principal'].dropna().unique()
        mapa_correccion_fuzzy = {}
        for marca_sucia in marcas_a_revisar:
            if marca_sucia:
                mejor_match, puntaje = process.extractOne(marca_sucia, lista_marcas_validas)
                if puntaje >= sensibilidad:
                    mapa_correccion_fuzzy[marca_sucia] = mejor_match
        df_limpio['filtro_principal'] = df_limpio['filtro_principal'].replace(mapa_correccion_fuzzy)

    # Selección final y limpieza de nulos
    columnas_finales = [
        'fecha', 'continente', 'pais_estandarizado', 'codigo_arancel', 'descripcion_arancel',
        'filtro_principal', 'filtro_secundario', 'segmento_producto', 'valor_cif', 'producto'
    ]
    columnas_existentes = [col for col in columnas_finales if col in df_limpio.columns]
    df_final = df_limpio[columnas_existentes]
    df_final = df_final.rename(columns={'pais_estandarizado': 'pais_final'})
    df_final.dropna(subset=['fecha', 'valor_cif'], inplace=True)
    df_final.drop_duplicates(inplace=True)
    
    return df_final