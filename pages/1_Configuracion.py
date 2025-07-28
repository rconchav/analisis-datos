# pages/1_Configuracion.py

import streamlit as st
import pandas as pd
import os
import json
import time

# --- CÓDIGO DE CONFIGURACIÓN DE RUTA ---
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Importaciones de la aplicación ---
from src.file_manager import cargar_y_procesar_archivos
from src.limpieza import limpiar_dataframe
from src.utils import configurar_pagina
from src.theme import configurar_tema
from src.diccionarios import cargar_diccionario, guardar_diccionario

# --- CONFIGURACIÓN DE PÁGINA Y TEMA ---
configurar_pagina(titulo_pagina="Configuración Dinámica")
if 'theme_toggle' not in st.session_state:
    st.session_state.theme_toggle = True
tema_actual = "Oscuro" if st.session_state.theme_toggle else "Claro"
configurar_tema(tema_actual)

# --- VERIFICACIÓN DE PROYECTO ACTIVO ---
if 'proyecto_activo' not in st.session_state or not st.session_state.proyecto_activo:
    st.warning("Por favor, selecciona un proyecto en la página de inicio para continuar.", icon="⚠️")
    st.stop()

proyecto_id = st.session_state.proyecto_activo
proyecto_nombre = st.session_state.get('proyecto_activo_nombre', proyecto_id)
diccionario = cargar_diccionario(proyecto_id)
mapeo_guardado = diccionario.get('mapeo_dinamico', {})

# --- INICIALIZACIÓN DEL ESTADO DE LA SESIÓN ---
if 'dynamic_mapping' not in st.session_state:
    st.session_state.dynamic_mapping = {
        "fechas": mapeo_guardado.get('fechas', []),
        "filtros": mapeo_guardado.get('filtros', []),
        "metricas": mapeo_guardado.get('metricas', [])
    }

st.title(f"⚙️ Configuración del Proyecto: {proyecto_nombre}")

# --- SECCIÓN DE CARGA DE ARCHIVOS ---
with st.container(border=True):
    st.header("1. Carga de Archivos")
    path_datos_procesados = os.path.join("proyectos", proyecto_id, "datos_procesados.parquet")

    modo_carga = st.radio(
        "Modo de Carga",
        ["Reemplazar datos existentes", "Anexar a datos existentes"],
        index=0,
        horizontal=True,
        help="**Reemplazar**: Borra los datos anteriores. **Anexar**: Añade los nuevos datos a los ya procesados."
    )

    if os.path.exists(path_datos_procesados):
        st.info(f"Este proyecto ya tiene datos procesados. El modo seleccionado es **{modo_carga.split(' ')[0]}**.")
    else:
        st.info("Este proyecto aún no tiene datos. Sube un archivo para comenzar.")

    uploaded_file = st.file_uploader("Sube un archivo Excel (.xlsx)", type=['xlsx'])

# --- LÓGICA PARA OBTENER COLUMNAS DE MUESTRA ---
df_muestra = None
columnas_disponibles = ["-"]
path_datos_originales = os.path.join("proyectos", proyecto_id, "data")

if uploaded_file:
    try:
        df_muestra = pd.read_excel(uploaded_file, nrows=50)
        columnas_disponibles = ["-"] + list(df_muestra.columns)
    except Exception as e:
        st.error(f"No se pudo leer el archivo subido. Error: {e}")
        st.stop()
elif os.path.exists(path_datos_originales) and os.listdir(path_datos_originales):
    try:
        primer_archivo = os.path.join(path_datos_originales, os.listdir(path_datos_originales)[0])
        df_muestra = pd.read_excel(primer_archivo, nrows=50)
        columnas_disponibles = ["-"] + list(df_muestra.columns)
    except Exception as e:
        st.warning(f"No se pudo leer el archivo de datos existente para la previsualización. Sube un archivo para continuar. Error: {e}")

# --- SECCIÓN DE MAPEADO ---
with st.container(border=True):
    st.header("2. Mapeo Dinámico de Columnas")

    if df_muestra is not None:
        st.markdown("##### Previsualización de datos:")
        st.dataframe(df_muestra.head(3))
    else:
        st.info("Sube un archivo para ver una previsualización y configurar el mapeo de columnas.")

    if columnas_disponibles != ["-"]:
        with st.container(border=True):
            st.subheader("Campos de Fecha")
            for i, fecha in enumerate(st.session_state.dynamic_mapping['fechas']):
                st.markdown(f"---")

                cols_header = st.columns([3, 1])
                with cols_header[0]:
                    fecha['nombre_personalizado'] = st.text_input(
                        "Nombre del Campo de Fecha", 
                        value=fecha.get('nombre_personalizado', f"Fecha_{i+1}"), 
                        key=f"fecha_nombre_{i}"
                    )
                with cols_header[1]:
                    if st.button("🗑️", key=f"fecha_del_{i}", use_container_width=True):
                        st.session_state.dynamic_mapping['fechas'].pop(i)
                        st.rerun()

                formato_guardado = fecha.get('formato', 'una_columna')
                formato_index = 1 if formato_guardado == 'tres_columnas' else 0
                formato = st.radio(
                    "Formato", 
                    ["Una columna", "Tres columnas"], 
                    index=formato_index, 
                    horizontal=True, 
                    key=f"fecha_formato_{i}"
                )
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

            if st.button("Añadir Campo de Fecha", use_container_width=True):
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
            if st.button("Añadir Filtro", use_container_width=True):
                st.session_state.dynamic_mapping['filtros'].append({})
                st.rerun()

        with st.container(border=True):
            st.subheader("Métricas (Valores Numéricos)")
            for i, metrica in enumerate(st.session_state.dynamic_mapping['metricas']):
                cols = st.columns([2, 2, 2, 1])
                metrica['nombre_personalizado'] = cols[0].text_input("Nombre de la Métrica", value=metrica.get('nombre_personalizado', ''), key=f"metrica_nombre_{i}")
                sel_col = metrica.get('columna_original', '-')
                idx_col = columnas_disponibles.index(sel_col) if sel_col in columnas_disponibles else 0
                metrica['columna_original'] = cols[1].selectbox("Columna del Archivo", columnas_disponibles, index=idx_col, key=f"metrica_col_{i}")
                sel_tipo = metrica.get('tipo_dato', 'Número')
                tipos_metrica = ["Número", "Moneda"]
                idx_tipo = tipos_metrica.index(sel_tipo) if sel_tipo in tipos_metrica else 0
                metrica['tipo_dato'] = cols[2].selectbox("Tipo de Dato", tipos_metrica, index=idx_tipo, key=f"metrica_tipo_{i}")
                if cols[3].button("🗑️", key=f"metrica_del_{i}"):
                    st.session_state.dynamic_mapping['metricas'].pop(i)
                    st.rerun()
            if st.button("Añadir Métrica", use_container_width=True):
                st.session_state.dynamic_mapping['metricas'].append({})
                st.rerun()

# --- SECCIÓN DE ACCIÓN ÚNICA: PROCESAR DATOS ---
st.markdown("---")
if st.button("Procesar Datos", type="primary", use_container_width=True):

    mapeo_actual = st.session_state.dynamic_mapping
    diccionario['mapeo_dinamico'] = mapeo_actual
    guardar_diccionario(proyecto_id, diccionario)
    st.success("Configuración de mapeo guardada.")

    if df_muestra is None and uploaded_file is None:
        st.error("Debes subir un archivo o tener uno existente para poder procesar.", icon="🚨")
        st.stop()

    errores = []
    advertencias = []

    df_para_validar = df_muestra if df_muestra is not None else pd.DataFrame()

    for tipo_campo, campos in mapeo_actual.items():
        for i, campo in enumerate(campos):
            columnas_a_chequear = list(campo.get('columnas', {}).values()) if tipo_campo == 'fechas' else [campo.get('columna_original')]
            for col_name in columnas_a_chequear:
                if col_name and col_name != "-" and col_name not in df_para_validar.columns:
                    nombre = campo.get('nombre_personalizado') or f"Campo #{i+1}"
                    errores.append(f"La columna '{col_name}' (mapeada en '{nombre}') no se encuentra en el archivo.")

    if not errores:
        for metrica in mapeo_actual['metricas']:
            col_name = metrica.get('columna_original')
            if col_name and col_name != "-" and col_name in df_para_validar.columns:
                numericos = pd.to_numeric(df_para_validar[col_name], errors='coerce').notna()
                if not numericos.all():
                    porcentaje_no_numerico = (1 - numericos.mean()) * 100
                    nombre = metrica.get('nombre_personalizado')
                    advertencias.append(f"La columna **'{col_name}'** (en '{nombre}') contiene **{porcentaje_no_numerico:.1f}%** de valores no numéricos. Estas filas serán descartadas.")

    if errores:
        for error in errores: st.error(error, icon="🚨")
    else:
        confirmacion_necesaria = bool(advertencias)
        confirmado = False
        if confirmacion_necesaria:
            for warning in advertencias: st.warning(warning, icon="⚠️")
            if st.checkbox("Entiendo los riesgos y confirmo que deseo continuar con el procesamiento.", key="confirm_process"):
                confirmado = True
        else:
            st.success("¡Validación exitosa! No se encontraron problemas.")
            confirmado = True

        if confirmado:
            with st.spinner("Iniciando procesamiento..."):

                df_a_procesar = cargar_y_procesar_archivos(
                    [uploaded_file] if uploaded_file else [], 
                    proyecto_id, 
                    desde_ruta=(uploaded_file is None)
                )

                if modo_carga == "Anexar a datos existentes" and os.path.exists(path_datos_procesados):
                    st.info("Modo 'Anexar' seleccionado. Combinando con datos existentes...")
                    df_existente = pd.read_parquet(path_datos_procesados)
                    df_a_procesar = pd.concat([df_existente, df_a_procesar], ignore_index=True)

                if not df_a_procesar.empty:
                    df_final = limpiar_dataframe(df_a_procesar, mapeo_actual)
                    path_salida = os.path.join("proyectos", proyecto_id, "datos_procesados.parquet")
                    df_final.to_parquet(path_salida)
                    st.cache_data.clear()
                    st.success(f"¡Proceso completado! Se guardaron {len(df_final)} registros.")
                    st.info("Serás redirigido a la página de Reportes en 2 segundos...")
                    time.sleep(2)
                    st.switch_page("pages/2_Reportes.py")
                else:
                    st.error("No se pudieron cargar los datos para el procesamiento.")