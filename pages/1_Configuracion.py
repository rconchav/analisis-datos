# pages/1_Configuracion.py
# Este archivo contiene el contenido de la página de Configuración,
# encapsulado en una función para ser llamado por el router en 🏠_Inicio.py.

import streamlit as st
import pandas as pd
import json
import io
import hashlib
from datetime import datetime

# No hay bloque sys.path aquí
# No hay llamada a configurar_pagina() aquí directamente, la hará el router

# Importa la configuración centralizada de la página (para sus utilidades si las tuviera)
from src.ui.app_config import configurar_pagina

# Importa los servicios y módulos de datos que usará esta página
from src.services.project_management_service import ProjectManagerService
# from src.services.data_processing_flow_service import DataProcessingFlowService # Aún no implementado
# from src.utils.general_utils import manejar_columnas_duplicadas # Se implementará

# >>> LO IMPORTANTE: TODO EL CONTENIDO DE LA PÁGINA DENTRO DE ESTA FUNCIÓN <<<
def show_configuracion_page():
    # El contenido de la página se ejecuta solo cuando se llama a esta función

    # --- VERIFICACIÓN DE PROYECTO ACTIVO ---
    project_manager_service = ProjectManagerService() 
    if 'proyecto_activo' not in st.session_state or not st.session_state.proyecto_activo:
        st.warning("Por favor, selecciona un proyecto en la página de inicio para continuar.", icon="⚠️")
        st.stop()

    proyecto_id = st.session_state.proyecto_activo
    proyecto_nombre = st.session_state.get('proyecto_activo_nombre', proyecto_id)

    diccionario_proyecto = project_manager_service.storage.load_project_dictionary(proyecto_id)
    mapeo_guardado = diccionario_proyecto.get('mapeo_dinamico', {})

    if 'dynamic_mapping' not in st.session_state:
        st.session_state.dynamic_mapping = {
            "fechas": mapeo_guardado.get('fechas', []),
            "filtros": mapeo_guardado.get('filtros', []),
            "metricas": mapeo_guardado.get('metricas', [])
        }
    if 'confirmar_reemplazo' not in st.session_state:
        st.session_state.confirmar_reemplazo = False

    st.title(f"⚙️ Configuración del Proyecto: {proyecto_nombre}")

    # --- SECCIÓN DE CARGA Y REGISTRO DE ARCHIVOS ---
    with st.container(border=True):
        st.header("1. Carga y Registro de Archivos")

        log_existente = project_manager_service.storage.load_processing_log(proyecto_id)
        if log_existente:
            with st.expander("Ver historial de archivos procesados en este proyecto"):
                df_log = pd.DataFrame(log_existente)
                st.dataframe(df_log, use_container_width=True)

        modo_carga = st.radio(
            "Modo de Carga",
            ["Anexar a datos existentes", "Reemplazar datos existentes"],
            index=0, horizontal=True)

        col1_upload, col2_date = st.columns(2)
        with col1_upload:
            uploaded_file = st.file_uploader("Sube un archivo Excel (.xlsx)", type=['xlsx'])
        with col2_date:
            fecha_archivo = st.date_input("Fecha correspondiente a los datos del archivo")

        if uploaded_file:
            st.info("Archivo cargado. Avanza al mapeo de columnas.")

    # --- LÓGICA PARA OBTENER COLUMNAS DE MUESTRA ---
    df_muestra, columnas_disponibles = None, ["-"]

    if uploaded_file:
        try:
            df_muestra = pd.read_excel(uploaded_file, nrows=50)
            # df_muestra = manejar_columnas_duplicadas(df_muestra) # Futura implementación desde src/utils/general_utils.py
            columnas_disponibles = ["-"] + list(df_muestra.columns)
            uploaded_file.seek(0) # Resetear puntero para re-lectura si es necesario
        except Exception as e:
            st.error(f"No se pudo leer el archivo subido. Error: {e}")
    elif project_manager_service.storage.load_processed_data(proyecto_id) is not None and not project_manager_service.storage.load_processed_data(proyecto_id).empty:
        st.info("No se subió un nuevo archivo. Usando datos procesados existentes para previsualización.")
        df_muestra = project_manager_service.storage.load_processed_data(proyecto_id).head(50)
        # df_muestra = manejar_columnas_duplicadas(df_muestra) # Futura implementación
        columnas_disponibles = ["-"] + list(df_muestra.columns)
    else:
        st.info("Sube un archivo para configurar el mapeo de columnas.")


    # --- SECCIÓN DE MAPEADO ---
    with st.container(border=True):
        st.header("2. Mapeo Dinámico de Columnas")
        if df_muestra is not None and not df_muestra.empty:
            st.markdown("##### Previsualización de datos:")
            st.dataframe(df_muestra.head(3))
        else:
            st.info("Sube un archivo para configurar el mapeo de columnas.")

        if columnas_disponibles != ["-"]:
            # Implementación de mapeo de fechas
            with st.container(border=True):
                st.subheader("Campos de Fecha")
                # Lógica de mapeo de fechas (copiar del original 1_Configuracion.py)
                for i, fecha in enumerate(st.session_state.dynamic_mapping['fechas']):
                    st.markdown(f"---")
                    cols_header = st.columns([3, 1])
                    with cols_header[0]:
                        fecha['nombre_personalizado'] = st.text_input("Nombre del Campo de Fecha", value=fecha.get('nombre_personalizado', f"Fecha_{i+1}"), key=f"fecha_nombre_{i}")
                    with cols_header[1]:
                        if st.button("🗑️", key=f"fecha_del_{i}", use_container_width=True):
                            st.session_state.dynamic_mapping['fechas'].pop(i)
                            st.rerun()
                    formato_guardado = fecha.get('formato', 'una_columna')
                    formato_index = 1 if formato_guardado == 'tres_columnas' else 0
                    formato = st.radio("Formato", ["Una columna", "Tres columnas"], index=formato_index, horizontal=True, key=f"fecha_formato_{i}")
                    fecha['formato'] = "una_columna" if formato == "Una columna" else "tres_columnas"
                    columnas_guardadas = fecha.get('columnas', {})
                    if fecha['formato'] == "una_columna":
                        sel_fecha = columnas_guardadas.get('fecha', '-')
                        idx_fecha = columnas_disponibles.index(sel_fecha) if sel_fecha in columnas_disponibles else 0
                        fecha['columnas'] = {'fecha': st.selectbox("Columna de Fecha", columnas_disponibles, index=idx_fecha, key=f"fecha_col_{i}")}
                    else:
                        sel_dia, sel_mes, sel_ano = columnas_guardadas.get('dia', '-'), columnas_guardadas.get('mes', '-'), columnas_guardadas.get('año', '-')
                        idx_dia = columnas_disponibles.index(sel_dia) if sel_dia in columnas_disponibles else 0
                        idx_mes = columnas_disponibles.index(sel_mes) if sel_mes in columnas_disponibles else 0
                        idx_ano = columnas_disponibles.index(sel_ano) if sel_ano in columnas_disponibles else 0
                        cols_fecha_select = st.columns(3)
                        fecha['columnas'] = {
                            'dia': cols_fecha_select[0].selectbox("Día", columnas_disponibles, index=idx_dia, key=f"fecha_dia_{i}"),
                            'mes': cols_fecha_select[1].selectbox("Mes", columnas_disponibles, index=idx_mes, key=f"fecha_mes_{i}"),
                            'año': cols_fecha_select[2].selectbox("Año", columnas_disponibles, index=idx_ano, key=f"fecha_ano_{i}")
                        }
                if st.button("Añadir Campo de Fecha", use_container_width=True, key="add_fecha_btn"):
                    st.session_state.dynamic_mapping['fechas'].append({'nombre_personalizado': '', 'formato': 'una_columna', 'columnas': {}})
                    st.rerun()

            with st.container(border=True):
                st.subheader("Filtros (Dimensiones)")
                for i, filtro in enumerate(st.session_state.dynamic_mapping['filtros']):
                    cols = st.columns([2, 2, 2, 1])
                    filtro['nombre_personalizado'] = cols[0].text_input("Nombre del Filtro", value=filtro.get('nombre_personalizado', ''), key=f"filtro_nombre_{i}")
                    sel_col = filtro.get('columna_original', '-')
                    idx_col = columnas_disponibles.index(sel_col) if sel_col in columnas_disponibles else 0
                    filtro['columna_original'] = cols[1].selectbox("Columna del Archivo", columnas_disponibles, index=idx_col, key=f"filtro_col_{i}")
                    sel_tipo = filtro.get('tipo_dato', 'Texto')
                    tipos_filtro = ["Texto", "País", "Arancel", "Latitud", "Longitud"]
                    idx_tipo = tipos_filtro.index(sel_tipo) if sel_tipo in tipos_filtro else 0
                    filtro['tipo_dato'] = cols[2].selectbox("Tipo de Dato", tipos_filtro, index=idx_tipo, key=f"filtro_tipo_{i}")
                    if cols[3].button("🗑️", key=f"filtro_del_{i}"):
                        st.session_state.dynamic_mapping['filtros'].pop(i)
                        st.rerun()
                if st.button("Añadir Filtro", use_container_width=True, key="add_filtro_btn"):
                    st.session_state.dynamic_mapping['filtros'].append({})
                    st.rerun()

            with st.container(border=True):
                st.subheader("Métricas (Valores Numéricos)")
                for i, metrica in enumerate(st.session_state.dynamic_mapping['metricas']):
                    cols = st.columns([2, 2, 2, 2, 1])
                    metrica['nombre_personalizado'] = cols[0].text_input("Nombre de la Métrica", value=metrica.get('nombre_personalizado', ''), key=f"metrica_nombre_{i}")
                    sel_col = metrica.get('columna_original', '-')
                    idx_col = columnas_disponibles.index(sel_col) if sel_col in columnas_disponibles else 0
                    metrica['columna_original'] = cols[1].selectbox("Columna del Archivo", columnas_disponibles, index=idx_col, key=f"metrica_col_{i}")
                    sel_tipo = metrica.get('tipo_dato', 'Número')
                    tipos_metrica = ["Número", "Moneda"]
                    idx_tipo = tipos_metrica.index(sel_tipo) if sel_tipo in tipos_metrica else 0
                    metrica['tipo_dato'] = cols[2].selectbox("Tipo de Dato", tipos_metrica, index=idx_tipo, key=f"metrica_tipo_{i}")
                    opciones_agregacion = ["Sumar (Ej: Total Ventas)", "Promediar (Ej: Precio Unitario)"]
                    agregacion_guardada = metrica.get('agregacion', opciones_agregacion[0])
                    idx_agg = opciones_agregacion.index(agregacion_guardada) if agregacion_guardada in opciones_agregacion else 0
                    metrica['agregacion'] = cols[3].selectbox("Agregación en Resumen", opciones_agregacion, index=idx_agg, key=f"metrica_agg_{i}")
                    if cols[4].button("🗑️", key=f"metrica_del_{i}"):
                        st.session_state.dynamic_mapping['metricas'].pop(i)
                        st.rerun()
                if st.button("Añadir Métrica", use_container_width=True, key="add_metrica_btn"):
                    st.session_state.dynamic_mapping['metricas'].append({})
                    st.rerun()


        # --- SECCIÓN DE ACCIÓN ÚNICA: PROCESAR DATOS ---
        st.markdown("---")
        if st.button("Procesar Datos (En Desarrollo)", type="primary", use_container_width=True):
            st.info("La lógica de procesamiento de datos se implementará aquí en los próximos pasos.")