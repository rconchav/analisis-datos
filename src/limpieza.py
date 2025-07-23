# src/limpieza.py

import pandas as pd
import glob
import os
import streamlit as st
import json
import re
from fuzzywuzzy import process

from .arancel import obtener_descripcion_arancel
from .utils import limpiar_codigo_arancel, validar_y_limpiar_nombre, cargar_mapeo_paises
from .segmentador import cargar_reglas_segmentacion
from .diccionarios import cargar_diccionario

def cargar_y_limpiar_datos(proyecto_id, sensibilidad_fuzzy=90):
    path_config = os.path.join("proyectos", proyecto_id, "config.json")
    try:
        with open(path_config, 'r', encoding='utf-8') as f: config = json.load(f)
        mapeo = config['mapeo_columnas']
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        st.error(f"Configuración para '{proyecto_id}' no encontrada o incompleta.")
        return None

    # --- CAMBIO CLAVE AQUÍ: VERIFICACIÓN DE ARCHIVOS ---
    path_datos_proyecto = os.path.join("proyectos", proyecto_id, "data")
    if not os.path.exists(path_datos_proyecto):
        st.error("No se encontró la carpeta de datos para este proyecto.")
        st.info("Por favor, vuelve a la página de 'Configuración' y carga los archivos de datos para este proyecto.")
        return None
        
    archivos_excel = glob.glob(os.path.join(path_datos_proyecto, '*.xlsx'))
    if not archivos_excel:
        st.error("No se encontraron archivos .xlsx en la carpeta de datos de este proyecto.")
        st.info("Por favor, vuelve a la página de 'Configuración' y carga los archivos de datos que deseas analizar.")
        return None
    # --- FIN DEL CAMBIO ---
    
    try:
        df = pd.concat([pd.read_excel(f, engine='openpyxl') for f in archivos_excel], ignore_index=True)
        df_limpio = df.copy()
    except Exception as e:
        st.error(f"Error al leer los archivos Excel: {e}")
        return None

    col_principal = mapeo.get('filtro_principal')
    col_secundario = mapeo.get('filtro_secundario_base')
    col_valor = mapeo.get('valor_numerico')
    col_pais = mapeo.get('pais')
    config_fecha = mapeo.get('config_fecha', {})

    if not all([col_principal, col_secundario, col_valor, col_pais]):
        st.error("El mapeo de columnas es inválido o está incompleto en el archivo de configuración.")
        return None

    col_segmentacion = mapeo.get('segmentacion_base', col_secundario)
    
    try:
        if config_fecha.get('tipo') == 'Columnas separadas':
            col_ano = config_fecha['ano']; col_mes = config_fecha['mes']; col_dia = config_fecha['dia']
            df_limpio['fecha'] = pd.to_datetime(df_limpio[[col_ano, col_mes, col_dia]].rename(columns={col_ano:'year', col_mes:'month', col_dia:'day'}))
        elif config_fecha.get('tipo') == 'Una sola columna':
            col_fecha_completa = config_fecha['fecha_completa']
            df_limpio['fecha'] = pd.to_datetime(df_limpio[col_fecha_completa])
    except Exception as e:
        st.error(f"Error al procesar las fechas: {e}")
        return None
    
    df_limpio.columns = [str(col).strip().lower() for col in df_limpio.columns]
    
    MAPA_PAIS_CONTINENTE, MAPA_REEMPLAZO_PAISES = cargar_mapeo_paises()
    reglas_segmentacion = cargar_reglas_segmentacion(proyecto_id)
    diccionario_proyecto = cargar_diccionario(proyecto_id)
    MARCAS_VALIDAS = set(diccionario_proyecto.keys())
    
    columnas_renombrar = {
        col_principal.lower(): 'filtro_principal',
        col_secundario.lower(): 'producto',
        col_valor.lower(): 'valor_cif',
        col_pais.lower(): 'pais_origen_raw'
    }
    if "partida arancelaria" in df_limpio.columns:
        columnas_renombrar["partida arancelaria"] = 'codigo_arancel'
    df_limpio.rename(columns=columnas_renombrar, inplace=True)
    
    columnas_de_texto_a_limpiar = ['filtro_principal', 'producto', 'pais_origen_raw']
    for col in columnas_de_texto_a_limpiar:
        if col in df_limpio.columns:
            df_limpio[col] = df_limpio[col].astype(str).str.strip()

    df_limpio['filtro_secundario'] = df_limpio['producto'].apply(validar_y_limpiar_nombre)
    if 'codigo_arancel' in df_limpio.columns:
        df_limpio['codigo_arancel'] = df_limpio['codigo_arancel'].apply(limpiar_codigo_arancel)
        df_limpio['descripcion_arancel'] = df_limpio['codigo_arancel'].apply(obtener_descripcion_arancel)
    
    df_limpio['valor_cif'] = pd.to_numeric(df_limpio['valor_cif'], errors='coerce')
    
    if 'pais_origen_raw' in df_limpio.columns:
        df_limpio['pais_estandarizado'] = df_limpio['pais_origen_raw'].str.lower().replace(MAPA_REEMPLAZO_PAISES)
        df_limpio['continente'] = df_limpio['pais_estandarizado'].map(MAPA_PAIS_CONTINENTE).fillna('Otros')
    else:
        df_limpio['continente'] = 'Desconocido'

    if col_segmentacion.lower() in df_limpio.columns and reglas_segmentacion:
        df_limpio['segmento_producto'] = 'NO CLASIFICADO'
        for categoria, keywords in reversed(list(reglas_segmentacion.items())):
            patron = '|'.join(map(re.escape, keywords))
            if patron:
                mask = df_limpio[col_segmentacion.lower()].str.contains(patron, na=False, case=False)
                df_limpio.loc[mask, 'segmento_producto'] = categoria
    
    if MARCAS_VALIDAS:
        lista_marcas_validas = list(MARCAS_VALIDAS)
        marcas_a_revisar = df_limpio[~df_limpio['filtro_principal'].isin(MARCAS_VALIDAS)]['filtro_principal'].dropna().unique()
        mapa_correccion_fuzzy = {}
        for marca_sucia in marcas_a_revisar:
            if marca_sucia:
                mejor_match, puntaje = process.extractOne(marca_sucia, lista_marcas_validas)
                if puntaje >= sensibilidad_fuzzy:
                    mapa_correccion_fuzzy[marca_sucia] = mejor_match
        df_limpio['filtro_principal'] = df_limpio['filtro_principal'].replace(mapa_correccion_fuzzy)

    columnas_finales = [
        'fecha', 'continente', 'pais_estandarizado', 'codigo_arancel', 'descripcion_arancel',
        'filtro_principal', 'filtro_secundario', 'segmento_producto', 'valor_cif', 'producto'
    ]
    columnas_existentes = [col for col in columnas_finales if col in df_limpio.columns]
    df_final = df_limpio[columnas_existentes].copy()
    df_final = df_final.rename(columns={'pais_estandarizado': 'pais_final'})
    df_final.dropna(subset=['fecha', 'valor_cif'], inplace=True)
    df_final.drop_duplicates(inplace=True)
    
    return df_final