# pages/2_Inteligencia.py

import streamlit as st
import pandas as pd
import os
import json

# --- CÓDIGO DE CONFIGURACIÓN DE PATH ---
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.diccionarios import cargar_diccionario, guardar_diccionario, diccionario_a_dataframe
from src.segmentador import cargar_reglas_segmentacion, guardar_reglas_segmentacion, reglas_a_dataframe
from src.limpieza import cargar_y_limpiar_datos
from src.graficos import generar_tabla_resumen_interactiva

st.set_page_config(layout="wide", page_title="Gestión de Inteligencia")

# --- FUNCIONES AUXILIARES DE ESTADO ---
def iniciar_edicion_filtro(filtro_principal):
    st.session_state.filtro_a_editar = filtro_principal

def cancelar_edicion_filtro():
    if 'filtro_a_editar' in st.session_state:
        del st.session_state.filtro_a_editar

def iniciar_edicion_segmento(segmento):
    st.session_state.segmento_a_editar = segmento

def cancelar_edicion_segmento():
    if 'segmento_a_editar' in st.session_state:
        del st.session_state.segmento_a_editar

# --- 1. VERIFICAR PROYECTO ACTIVO ---
if 'proyecto_activo' not in st.session_state or st.session_state.proyecto_activo is None:
    st.warning("Por favor, selecciona o crea un proyecto en la página de '🏠 Inicio'.")
    st.stop()

proyecto_activo_dict = st.session_state.proyecto_activo
proyecto_id = proyecto_activo_dict['id']
proyecto_display_name = proyecto_activo_dict['display_name']
st.title(f"🧠 Gestión de Inteligencia para: `{proyecto_display_name}`")
st.markdown("Entrena a la aplicación para que entienda y clasifique mejor tus datos.")

# --- Contenedor con Pestañas ---
tab1, tab2 = st.tabs(["📖 Gestor del Diccionario de Filtros", "🏷️ Gestor de Reglas de Segmentación"])

# --- Pestaña 1: Gestión del Diccionario ---
with tab1:
    st.header("Estandariza los nombres de productos y marcas")
    diccionario = cargar_diccionario(proyecto_id)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        modo_edicion = 'filtro_a_editar' in st.session_state
        titulo_form = "Editando Filtro Principal" if modo_edicion else "Agregar Nuevo Filtro"
        st.subheader(titulo_form)
        filtro_actual = st.session_state.get('filtro_a_editar', "")
        secundarios_actuales = ", ".join(diccionario.get(filtro_actual, []))

        with st.form("form_diccionario"):
            filtro_principal = st.text_input("Filtro Principal (ej. Marca)", value=filtro_actual)
            filtros_secundarios_str = st.text_area("Filtros Secundarios (separados por coma)", value=secundarios_actuales)
            form_cols = st.columns(2)
            with form_cols[0]:
                if st.form_submit_button("Guardar Cambios", type="primary", use_container_width=True):
                    if filtro_principal and filtros_secundarios_str:
                        principal_limpio = filtro_principal.strip().upper()
                        secundarios_limpios = sorted([s.strip().upper() for s in filtros_secundarios_str.split(',') if s.strip()])
                        diccionario[principal_limpio] = secundarios_limpios
                        if modo_edicion and principal_limpio != filtro_actual: del diccionario[filtro_actual]
                        guardar_diccionario(proyecto_id, diccionario)
                        st.success(f"Filtro '{principal_limpio}' guardado.")
                        cancelar_edicion_filtro()
                        st.rerun()
                    else: st.error("Ambos campos son obligatorios.")
            with form_cols[1]:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    cancelar_edicion_filtro()
                    st.rerun()

    with col2:
        st.subheader("Diccionario Actual")
        if not diccionario:
            st.info("El diccionario está vacío.")
        else:
            for principal, secundarios in sorted(diccionario.items()):
                with st.expander(f"**{principal}** ({len(secundarios)} términos)"):
                    st.write(", ".join(secundarios))
                    btn_cols = st.columns(5)
                    with btn_cols[0]: st.button("Editar", key=f"edit_{principal}", on_click=iniciar_edicion_filtro, args=(principal,), use_container_width=True)
                    with btn_cols[1]:
                        if st.button("Eliminar", key=f"del_{principal}", use_container_width=True):
                            del diccionario[principal]
                            guardar_diccionario(proyecto_id, diccionario)
                            st.rerun()
    
    st.markdown("---")
    path_datos_procesados = os.path.join("proyectos", proyecto_id, "datos_procesados.parquet")
    if os.path.exists(path_datos_procesados):
        df_procesado = pd.read_parquet(path_datos_procesados)
        generar_tabla_resumen_interactiva(df_procesado)
    else:
        st.info("Procesa los datos al menos una vez en la página de 'Configuración' para ver el resumen interactivo aquí.")

# --- Pestaña 2: Gestión de Segmentos ---
with tab2:
    st.header("Crea categorías de negocio de alto nivel")
    reglas = cargar_reglas_segmentacion(proyecto_id)

    col3, col4 = st.columns([1, 2])
    with col3:
        modo_edicion_seg = 'segmento_a_editar' in st.session_state
        titulo_form_seg = "Editando Regla" if modo_edicion_seg else "Agregar Nueva Regla"
        st.subheader(titulo_form_seg)
        segmento_actual = st.session_state.get('segmento_a_editar', "")
        palabras_actuales = ", ".join(reglas.get(segmento_actual, []))

        with st.form("form_segmentos"):
            segmento = st.text_input("Nombre del Segmento", value=segmento_actual)
            palabras_clave_str = st.text_area("Palabras Clave (separadas por coma)", value=palabras_actuales)
            form_cols_seg = st.columns(2)
            with form_cols_seg[0]:
                if st.form_submit_button("Guardar Cambios", type="primary", use_container_width=True):
                    if segmento and palabras_clave_str:
                        segmento_limpio = segmento.strip().upper()
                        palabras_clave = sorted([p.strip().upper() for p in palabras_clave_str.split(',') if p.strip()])
                        reglas[segmento_limpio] = palabras_clave
                        if modo_edicion_seg and segmento_limpio != segmento_actual: del reglas[segmento_actual]
                        guardar_reglas_segmentacion(proyecto_id, reglas)
                        st.success(f"Regla para '{segmento_limpio}' guardada.")
                        cancelar_edicion_segmento()
                        st.rerun()
                    else: st.error("Ambos campos son obligatorios.")
            with form_cols_seg[1]:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    cancelar_edicion_segmento()
                    st.rerun()

    with col4:
        st.subheader("Reglas Actuales")
        if not reglas: st.info("No hay reglas de segmentación.")
        else:
            for seg, keywords in sorted(reglas.items()):
                with st.expander(f"**{seg}** ({len(keywords)} palabras)"):
                    st.write(", ".join(keywords))
                    btn_cols_seg = st.columns(5)
                    with btn_cols_seg[0]: st.button("Editar", key=f"edit_seg_{seg}", on_click=iniciar_edicion_segmento, args=(seg,), use_container_width=True)
                    with btn_cols_seg[1]:
                        if st.button("Eliminar", key=f"del_seg_{seg}", use_container_width=True):
                            del reglas[seg]
                            guardar_reglas_segmentacion(proyecto_id, reglas)
                            st.rerun()

# --- SECCIÓN DE RE-ANÁLISIS ---
st.markdown("---")
st.header("Actualizar Reportes")
st.info("Después de modificar el diccionario o las reglas, puedes re-procesar los datos para que los reportes reflejen tus cambios.")

path_config_existente = os.path.join("proyectos", proyecto_id, "config.json")
if st.button("🚀 Re-procesar Datos con Inteligencia Actualizada", use_container_width=True):
    if not os.path.exists(path_config_existente) or os.path.getsize(path_config_existente) < 10:
         st.session_state.status_message = "Error: No se encontró un mapeo."
         st.session_state.status_type = "error"
    else:
        try:
            with st.spinner("Re-procesando datos..."):
                df_final = cargar_y_limpiar_datos(proyecto_id, sensibilidad_fuzzy=90)
            if df_final is not None and not df_final.empty:
                path_salida = os.path.join("proyectos", proyecto_id, "datos_procesados.parquet")
                df_final.to_parquet(path_salida)
                st.cache_data.clear()
                st.session_state.status_message = f"¡Re-procesamiento completado! Se actualizaron {len(df_final)} registros."
                st.session_state.status_type = "success"
            else:
                st.session_state.status_message = "El re-procesamiento no generó datos."
                st.session_state.status_type = "warning"
        except Exception as e:
            st.session_state.status_message = f"Ocurrió un error: {e}"; st.session_state.status_type = "error"
    st.rerun()

# --- RECUADRO DE MENSAJES AL PIE DE LA PÁGINA ---
st.markdown("---")
status_placeholder = st.empty()
if "status_message" in st.session_state:
    message = st.session_state.status_message; msg_type = st.session_state.status_type
    if msg_type == "success": status_placeholder.success(message, icon="✅")
    elif msg_type == "error": status_placeholder.error(message, icon="🚨")
    elif msg_type == "warning": status_placeholder.warning(message, icon="⚠️")
    else: status_placeholder.info(message, icon="ℹ️")
    del st.session_state.status_message; del st.session_state.status_type