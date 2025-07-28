# pages/4_Inteligencia.py

import streamlit as st
import pandas as pd
import os

# --- CÓDIGO DE CONFIGURACIÓN DE RUTA ---
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Importaciones ---
from src.diccionarios import (
    cargar_diccionario_global, guardar_diccionario_global, diccionario_global_a_dataframe, 
    cargar_diccionario, cargar_reglas_segmentacion_global, guardar_reglas_segmentacion_global,
    reglas_a_dataframe
)
from src.limpieza import limpiar_dataframe
from src.file_manager import cargar_y_procesar_archivos
from src.utils import configurar_pagina
from src.theme import configurar_tema
from src.graficos import generar_tabla_interactiva

# --- CONFIGURACIÓN DE PÁGINA Y TEMA ---
configurar_pagina(titulo_pagina="Inteligencia Global")
if 'theme_toggle' not in st.session_state:
    st.session_state.theme_toggle = True
tema_actual = "Oscuro" if st.session_state.theme_toggle else "Claro"
configurar_tema(tema_actual)

# --- TÍTULO Y VERIFICACIÓN DE PROYECTO ---
st.title("🧠 Centro de Inteligencia Global")
st.info("Las reglas definidas aquí se aplicarán a todos los proyectos durante el procesamiento de datos.")

if 'proyecto_activo' not in st.session_state or not st.session_state.proyecto_activo:
    st.warning("Selecciona un proyecto en la página de Inicio para continuar.", icon="⚠️")
    st.stop()

proyecto_id = st.session_state.proyecto_activo
proyecto_nombre = st.session_state.get('proyecto_activo_nombre', proyecto_id)

# --- SECCIÓN DE PREVISUALIZACIÓN DE DATOS (RESTAURADA Y MEJORADA) ---
st.markdown("---")
st.subheader(f"Previsualización de Datos: {proyecto_nombre}")

path_datos_procesados = os.path.join("proyectos", proyecto_id, "datos_procesados.parquet")
if os.path.exists(path_datos_procesados):
    df_procesado = pd.read_parquet(path_datos_procesados)
    st.markdown("Doble clic en una celda para copiar su contenido.")
    generar_tabla_interactiva(df_procesado)
else:
    st.info("Aún no hay datos procesados para este proyecto. Ve a la página de 'Configuración' para cargarlos.")


# --- INTERFAZ CON PESTAÑAS (TABS) ---
st.markdown("---")
tab1, tab2 = st.tabs(["📚 Diccionario de Estandarización", "✂️ Reglas de Segmentación"])

with tab1:
    st.header("Diccionario de Estandarización Global")
    df_diccionario = diccionario_global_a_dataframe(cargar_diccionario_global())

    edited_df = st.data_editor(df_diccionario, num_rows="dynamic", key="editor_diccionario", use_container_width=True)

    if st.button("Guardar Diccionario Global", type="primary", key="guardar_dicc"):
        nuevo_diccionario = {}
        for _, row in edited_df.iterrows():
            filtro, original, estandarizado = row["Filtro"], row["Valor Original"], row["Valor Estandarizado"]
            if filtro and original and estandarizado:
                if filtro not in nuevo_diccionario:
                    nuevo_diccionario[filtro] = {}
                nuevo_diccionario[filtro][original] = estandarizado
        guardar_diccionario_global(nuevo_diccionario)
        st.success("Diccionario global guardado.")

with tab2:
    st.header("Reglas de Segmentación Global")
    st.markdown("Define segmentos de negocio y las palabras clave asociadas (separadas por comas).")

    reglas_segmentacion = cargar_reglas_segmentacion_global()
    df_reglas = reglas_a_dataframe(reglas_segmentacion)

    edited_reglas_df = st.data_editor(df_reglas, num_rows="dynamic", key="editor_reglas", use_container_width=True,
        column_config={
            "Segmento": st.column_config.TextColumn(required=True),
            "Palabras Clave": st.column_config.TextColumn(required=True)
        }
    )

    if st.button("Guardar Reglas de Segmentación", type="primary", key="guardar_reglas"):
        nuevas_reglas = {}
        for _, row in edited_reglas_df.iterrows():
            segmento = row['Segmento']
            palabras = [p.strip() for p in row['Palabras Clave'].split(',') if p.strip()]
            if segmento and palabras:
                nuevas_reglas[segmento] = palabras
        guardar_reglas_segmentacion_global(nuevas_reglas)
        st.success("Reglas de segmentación guardadas.")

st.markdown("---")
if st.button("Reprocesar Datos del Proyecto Activo con Reglas Actualizadas", use_container_width=True):
    with st.spinner(f"Reprocesando datos para '{proyecto_nombre}'..."):
        df_original = cargar_y_procesar_archivos([], proyecto_id, desde_ruta=True)
        if not df_original.empty:
            diccionario_proyecto = cargar_diccionario(proyecto_id)
            mapeo_dinamico = diccionario_proyecto.get('mapeo_dinamico')
            if mapeo_dinamico:
                df_reprocesado = limpiar_dataframe(df_original, mapeo_dinamico)
                path_salida = os.path.join("proyectos", proyecto_id, "datos_procesados.parquet")
                df_reprocesado.to_parquet(path_salida)
                st.cache_data.clear()
                st.success(f"¡Reproceso completado para '{proyecto_nombre}'!")
            else:
                st.error(f"No se encontró un mapeo para el proyecto '{proyecto_nombre}'.")
        else:
            st.error(f"No se encontraron datos originales para reprocesar en el proyecto '{proyecto_nombre}'.")