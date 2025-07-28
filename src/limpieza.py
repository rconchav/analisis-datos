# src/limpieza.py

import streamlit as st
import pandas as pd
from src.arancel import buscar_descripcion_arancel
from src.utils import cargar_mapeo_paises
# --- CORRECCIÓN DE IMPORTACIÓN ---
# Se elimina la importación de la función que no existe
from src.diccionarios import cargar_diccionario_global

def limpiar_dataframe(df: pd.DataFrame, mapeo_dinamico: dict) -> pd.DataFrame:
    """
     Motor de limpieza que ahora aplica el diccionario de estandarización global.
    """
    st.progress(0, text="Iniciando motor de limpieza...")
    df_procesado = df.copy()
    diccionario_global = cargar_diccionario_global()

    # --- PASO 1: RENOMBRAR COLUMNAS ---
    mapa_renombrado = {}
    todos_los_campos = mapeo_dinamico.get('fechas', []) + mapeo_dinamico.get('filtros', []) + mapeo_dinamico.get('metricas', [])
    
    for campo in todos_los_campos:
        nombre_personalizado = campo.get('nombre_personalizado')
        if 'columna_original' in campo: # Para filtros y métricas
            columna_original = campo.get('columna_original')
            if nombre_personalizado and columna_original and columna_original != "-":
                mapa_renombrado[columna_original] = nombre_personalizado
        elif 'columnas' in campo: # Para fechas
            for nombre_interno, columna_original in campo.get('columnas', {}).items():
                if nombre_personalizado and columna_original and columna_original != "-":
                    mapa_renombrado[columna_original] = f"_{nombre_personalizado}_{nombre_interno}"

    df_procesado.rename(columns=mapa_renombrado, inplace=True)
    st.progress(15, text="Columnas renombradas según mapeo.")

    # --- PASO 2: PROCESAMIENTO DE FECHAS ---
    for fecha_info in mapeo_dinamico.get('fechas', []):
        nombre_fecha = fecha_info.get('nombre_personalizado')
        if not nombre_fecha: continue

        if fecha_info.get('formato') == 'una_columna':
            col_fecha_renombrada = f"_{nombre_fecha}_fecha"
            if col_fecha_renombrada in df_procesado.columns:
                df_procesado[nombre_fecha] = pd.to_datetime(df_procesado[col_fecha_renombrada], errors='coerce')
                df_procesado.drop(columns=[col_fecha_renombrada], inplace=True)
        
        elif fecha_info.get('formato') == 'tres_columnas':
            col_dia = f"_{nombre_fecha}_dia"
            col_mes = f"_{nombre_fecha}_mes"
            col_ano = f"_{nombre_fecha}_año"
            if all(c in df_procesado.columns for c in [col_dia, col_mes, col_ano]):
                try:
                    df_procesado[nombre_fecha] = pd.to_datetime(
                        df_procesado[col_ano].astype(int).astype(str) + '-' +
                        df_procesado[col_mes].astype(int).astype(str) + '-' +
                        df_procesado[col_dia].astype(int).astype(str),
                        errors='coerce'
                    )
                    df_procesado.drop(columns=[col_dia, col_mes, col_ano], inplace=True)
                except Exception as e:
                    st.warning(f"No se pudieron combinar las columnas para la fecha '{nombre_fecha}'. Error: {e}")
    st.progress(30, text="Campos de fecha procesados.")

    # --- PASO 3: ESTANDARIZACIÓN Y ENRIQUECIMIENTO DE FILTROS ---
    pais_continente, reemplazo_paises, pais_coordenadas = cargar_mapeo_paises()
    columna_pais_estandarizada = None

    for filtro_info in mapeo_dinamico.get('filtros', []):
        nombre_filtro = filtro_info.get('nombre_personalizado')
        tipo_dato = filtro_info.get('tipo_dato')
        if not nombre_filtro or nombre_filtro not in df_procesado.columns: continue

        # APLICAR DICCIONARIO GLOBAL DE ESTANDARIZACIÓN
        if nombre_filtro in diccionario_global:
            df_procesado[nombre_filtro] = df_procesado[nombre_filtro].replace(diccionario_global[nombre_filtro])
         
        # Enriquecimiento para tipo 'País'
        if tipo_dato == 'País':
            df_procesado[nombre_filtro] = df_procesado[nombre_filtro].astype(str).str.strip().str.upper()
            df_procesado[nombre_filtro] = df_procesado[nombre_filtro].replace(reemplazo_paises)
            df_procesado[f'Continente'] = df_procesado[nombre_filtro].map(pais_continente).fillna('Desconocido')
            columna_pais_estandarizada = nombre_filtro

        # Enriquecimiento para tipo 'Arancel'
        elif tipo_dato == 'Arancel':
            df_procesado[f'Descripción Arancel'] = df_procesado[nombre_filtro].apply(
                lambda x: buscar_descripcion_arancel(str(x)) if pd.notna(x) else 'N/A'
            )
    st.progress(60, text="Filtros procesados y enriquecidos.")

    # --- PASO 4: PROCESAMIENTO DE MÉTRICAS ---
    for metrica_info in mapeo_dinamico.get('metricas', []):
        nombre_metrica = metrica_info.get('nombre_personalizado')
        if nombre_metrica and nombre_metrica in df_procesado.columns:
            df_procesado[nombre_metrica] = pd.to_numeric(df_procesado[nombre_metrica], errors='coerce')
    st.progress(80, text="Métricas procesadas.")

    # --- PASO 5: GEO-ENRIQUECIMIENTO AUTOMÁTICO ---
    nombres_filtros_mapeados = {f.get('nombre_personalizado').lower(): f.get('tipo_dato') for f in mapeo_dinamico.get('filtros', [])}
    if 'latitud' not in nombres_filtros_mapeados and 'longitud' not in nombres_filtros_mapeados and columna_pais_estandarizada:
        df_procesado['lat'] = df_procesado[columna_pais_estandarizada].map(lambda p: pais_coordenadas.get(p, {}).get('lat'))
        df_procesado['lon'] = df_procesado[columna_pais_estandarizada].map(lambda p: pais_coordenadas.get(p, {}).get('lon'))
        st.info("Se han añadido coordenadas geográficas automáticas basadas en la columna de País.")
    
    # --- PASO 6: LIMPIEZA FINAL ---
    metricas_clave = [m.get('nombre_personalizado') for m in mapeo_dinamico.get('metricas', []) if m.get('nombre_personalizado')]
    df_procesado.dropna(subset=metricas_clave, inplace=True)
    st.progress(100, text="Limpieza final completada.")
    
    return df_procesado