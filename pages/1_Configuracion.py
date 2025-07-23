# pages/1_Configuracion.py

import streamlit as st
import pandas as pd
import os
import json
import time

# --- CÓDIGO DE CONFIGURACIÓN DE PATH ---
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.limpieza import cargar_y_limpiar_datos
from src.utils import manejar_columnas_duplicadas

st.set_page_config(layout="wide", page_title="Configuración de Proyecto")

# --- FUNCIÓN PARA RESALTAR COLUMNAS ---
def resaltar_columnas_mapeadas(df, mapeo):
    df_estilizado = df.copy()
    columnas_asignadas = [v for v in mapeo.values() if isinstance(v, str)]
    if 'config_fecha' in mapeo and isinstance(mapeo.get('config_fecha'), dict):
        columnas_asignadas.extend([v for k, v in mapeo['config_fecha'].items() if k != 'tipo' and isinstance(v, str)])
    def resaltar(columna):
        if columna.name in columnas_asignadas and columna.name != "":
            return ['background-color: #d3f4d3'] * len(columna)
        return [''] * len(columna)
    return df_estilizado.style.apply(resaltar, axis=0)

# --- 1. VERIFICAR PROYECTO ACTIVO ---
if 'proyecto_activo' not in st.session_state or st.session_state.proyecto_activo is None:
    st.warning("Por favor, selecciona o crea un proyecto en la página de '🏠 Inicio'.")
    st.stop()
proyecto_id = st.session_state.proyecto_activo['id']
proyecto_display_name = st.session_state.proyecto_activo['display_name']
st.title(f"⚙️ Configuración y Mapeo para: `{proyecto_display_name}`")

# --- CARGAR MAPEO GUARDADO ---
path_config_existente = os.path.join("proyectos", proyecto_id, "config.json")
mapeo_guardado = {}
if os.path.exists(path_config_existente):
    with open(path_config_existente, 'r', encoding='utf-8') as f:
        try:
            mapeo_guardado = json.load(f).get("mapeo_columnas", {})
        except json.JSONDecodeError:
            mapeo_guardado = {}

# --- 2. GESTIÓN DE ARCHIVOS DE DATOS ---
path_datos_proyecto = os.path.join("proyectos", proyecto_id, "data")
os.makedirs(path_datos_proyecto, exist_ok=True)

with st.container(border=True):
    st.markdown("<p style='color: #4682B4; font-weight: bold;'>Gestión de Archivos de Datos</p>", unsafe_allow_html=True)
    archivos_actuales = [f for f in os.listdir(path_datos_proyecto) if f.endswith('.xlsx')]
    if not archivos_actuales:
        st.info("Este proyecto aún no tiene archivos de datos.")
    else:
        st.write("**Archivos actuales en el proyecto:**")
        for archivo in archivos_actuales: st.text(f"- {archivo}")
    
    nuevos_archivos = st.file_uploader("Arrastra o selecciona nuevos archivos .xlsx para añadir al proyecto:", type="xlsx", accept_multiple_files=True)
    if nuevos_archivos:
        for archivo in nuevos_archivos:
            with open(os.path.join(path_datos_proyecto, archivo.name), "wb") as f: f.write(archivo.getbuffer())
        st.success(f"{len(nuevos_archivos)} archivo(s) añadido(s) con éxito.")
        st.rerun()

# --- 3. INTERFAZ DE MAPEO ---
df_ejemplo = None
if archivos_actuales:
    try:
        lista_dfs = [pd.read_excel(os.path.join(path_datos_proyecto, f), nrows=5) for f in archivos_actuales]
        df_ejemplo_full = pd.concat(lista_dfs, ignore_index=True)
        df_ejemplo = manejar_columnas_duplicadas(df_ejemplo_full.copy())
    except Exception as e:
        st.error(f"Error al leer los archivos de ejemplo: {e}")

if df_ejemplo is not None:
    st.header("Paso 1: Asignar Roles a las Columnas")
    mapeo_actual = {}
    columnas_disponibles = [""] + df_ejemplo.columns.tolist()

    st.markdown("##### Roles de Datos Principales")
    roles_datos_keys = ["filtro_principal", "filtro_secundario_base", "segmentacion_base", "valor_numerico", "pais"]
    cols_datos = st.columns(len(roles_datos_keys))
    for i, rol in enumerate(roles_datos_keys):
        with cols_datos[i]:
            valor_actual = mapeo_guardado.get(rol, "")
            indice = columnas_disponibles.index(valor_actual) if valor_actual in columnas_disponibles else 0
            valor_seleccionado = st.selectbox(rol.replace("_", " ").title(), columnas_disponibles, index=indice)
            if valor_seleccionado: mapeo_actual[rol] = valor_seleccionado

    st.markdown("---")
    st.markdown("##### Configuración de Fecha")
    config_fecha_actual = mapeo_guardado.get('config_fecha', {})
    tipo_guardado = config_fecha_actual.get("tipo")
    index_radio = 0
    if tipo_guardado == 'Una sola columna': index_radio = 1
    elif tipo_guardado == 'Columnas separadas': index_radio = 2
    tipo_fecha = st.radio("Formato de fecha:", ("No usar fechas", "En una sola columna", "En columnas separadas"), index=index_radio, horizontal=True)
    
    mapeo_actual['config_fecha'] = {}
    if tipo_fecha == "En una sola columna":
        mapeo_actual['config_fecha']['tipo'] = 'Una sola columna'
        valor = config_fecha_actual.get("fecha_completa", "")
        indice = columnas_disponibles.index(valor) if valor in columnas_disponibles else 0
        mapeo_actual['config_fecha']['fecha_completa'] = st.selectbox("Columna de Fecha Única", columnas_disponibles, index=indice)
    elif tipo_fecha == "En columnas separadas":
        mapeo_actual['config_fecha']['tipo'] = 'Columnas separadas'
        cols_fecha = st.columns(3)
        roles_fecha = {"Día": "dia", "Mes": "mes", "Año": "ano"}
        for i, (display_name, key_name) in enumerate(roles_fecha.items()):
            with cols_fecha[i]:
                valor = config_fecha_actual.get(key_name, "")
                indice = columnas_disponibles.index(valor) if valor in columnas_disponibles else 0
                valor_sel_fecha = st.selectbox(display_name, columnas_disponibles, index=indice)
                if valor_sel_fecha: mapeo_actual['config_fecha'][key_name] = valor_sel_fecha

    st.header("Paso 2: Vista Previa de los Datos con Resaltado Interactivo")
    df_resaltado = resaltar_columnas_mapeadas(df_ejemplo.head(10), mapeo_actual)
    st.dataframe(df_resaltado)
    st.markdown("---")
    
    st.header("Paso 3: Guardar y Ejecutar")
    col1, col2, col3, col4 = st.columns([2.5, 2, 0.5, 0.5])
    with col1:
        sensibilidad = st.slider("Ajuste la sensibilidad de limpieza de datos", 70, 100, 90, help="Define qué tan parecidas deben ser las palabras para agruparlas (Fuzzy).")
    with col3:
        if st.button("💾", type="primary", use_container_width=True, help="Guardar la configuración de mapeo actual"):
            with open(path_config_existente, 'w', encoding='utf-8') as f: json.dump({"mapeo_columnas": mapeo_actual}, f, indent=4)
            st.session_state.status_message = "¡Mapeo guardado!"; st.session_state.status_type = "success"
            st.rerun()
    with col4:
        if st.button("🚀", use_container_width=True, help="Iniciar el proceso de limpieza y procesamiento de datos"):
            if not os.path.exists(path_config_existente) or os.path.getsize(path_config_existente) < 10:
                st.session_state.status_message = "Error: Guarda el mapeo primero."; st.session_state.status_type = "error"
            else:
                try:
                    with st.spinner("Procesando datos..."):
                        df_final = cargar_y_limpiar_datos(proyecto_id, sensibilidad_fuzzy=sensibilidad)
                    if df_final is not None and not df_final.empty:
                        path_salida = os.path.join("proyectos", proyecto_id, "datos_procesados.parquet")
                        df_final.to_parquet(path_salida)
                        st.cache_data.clear()
                        st.session_state.status_message = f"¡Proceso completado! Se procesaron {len(df_final)} registros. Redirigiendo a reportes..."
                        st.session_state.status_type = "success"
                        st.session_state.navigate_to_reports = True
                    else:
                        st.session_state.status_message = "El proceso de limpieza no generó datos. Revisa la configuración y los archivos."; st.session_state.status_type = "warning"
                except Exception as e:
                    st.session_state.status_message = f"Ocurrió un error: {e}"; st.session_state.status_type = "error"
            st.rerun()

# --- RECUADRO DE MENSAJES Y NAVEGACIÓN ---
st.markdown("---")
status_placeholder = st.empty()
if "status_message" in st.session_state and st.session_state.status_message:
    message = st.session_state.status_message
    msg_type = st.session_state.status_type
    if msg_type == "success": status_placeholder.success(message, icon="✅")
    elif msg_type == "error": status_placeholder.error(message, icon="🚨")
    elif msg_type == "warning": status_placeholder.warning(message, icon="⚠️")
    else: status_placeholder.info(message, icon="ℹ️")
    st.session_state.status_message = None
    st.session_state.status_type = None

if st.session_state.get("navigate_to_reports"):
    del st.session_state.navigate_to_reports
    time.sleep(1)
    st.switch_page("pages/3_Reportes.py")