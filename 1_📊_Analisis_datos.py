# 1_📊_Analisis_datos.py

import streamlit as st
import pandas as pd
import re
import os
import json
from limpieza import cargar_y_limpiar_datos
from arancel import ARANCEL_DF, buscar_por_glosa
from graficos import (
    generar_tabla_resumen, generar_grafico_barras_mensual,
    generar_ranking_marcas, generar_pie_paises,
    generar_analisis_otras_marcas, generar_detalle_repuestos,
    generar_grafico_arancel
)
from utils import limpiar_codigo_arancel, to_excel
from diccionarios import generar_diccionario_desde_datos, procesar_catalogos_externos
from file_manager import cargar_log_procesados, ha_sido_procesado, actualizar_log, guardar_log_procesados

# --- Configuración de la Página ---
st.set_page_config(layout="wide", page_title="Análisis de Importaciones")

# --- Rutas y Constantes ---
PATH_DATOS_PROCESADOS = "datos/datos_procesados.parquet"

# --- Funciones de Caché y Lógica de Procesamiento ---
@st.cache_data
def cargar_diccionario_filtros():
    """Carga el diccionario de filtros desde el archivo JSON."""
    if os.path.exists('datos/diccionario_referencia.json'):
        with open('datos/diccionario_referencia.json', 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def ejecutar_proceso_completo():
    """Encapsula la lógica de procesamiento para ser llamada desde múltiples botones."""
    with st.spinner("Limpiando y analizando registros..."):
        df_procesado = cargar_y_limpiar_datos()
    if df_procesado is not None and not df_procesado.empty:
        with st.spinner("Enriqueciendo y generando diccionario..."):
            procesar_catalogos_externos()
            generar_diccionario_desde_datos(df_procesado)
        
        try:
            df_procesado.to_parquet(PATH_DATOS_PROCESADOS)
            st.session_state['df_final'] = df_procesado
            st.cache_data.clear()
            st.success("¡Proceso completado y guardado para futuras sesiones!")
        except Exception as e:
            st.error(f"Error al guardar los datos procesados: {e}")
            st.session_state['df_final'] = df_procesado
    else:
        st.error("El procesamiento de datos falló o no generó datos.")

# --- Inicialización de Session State y Carga Persistente ---
if 'df_final' not in st.session_state:
    if os.path.exists(PATH_DATOS_PROCESADOS):
        try:
            st.session_state['df_final'] = pd.read_parquet(PATH_DATOS_PROCESADOS)
        except Exception as e:
            st.session_state['df_final'] = None
    else:
        st.session_state['df_final'] = None

# --- Título Principal ---
st.title("📈 Análisis de Importaciones")

# --- LÓGICA DE RENDERIZADO CONDICIONAL ---

# CASO 1: No hay datos cargados, se muestra la pantalla de bienvenida y carga.
if st.session_state['df_final'] is None:
    st.header("Bienvenido al Analizador de Datos")
    st.info("Para comenzar, carga tus archivos de importación y presiona el botón para procesar.")
    
    os.makedirs("input", exist_ok=True)
    os.makedirs("catalogos", exist_ok=True)
    os.makedirs("datos", exist_ok=True)

    with st.expander("▶️ Cargar y Procesar Datos", expanded=True):
        log_procesados = cargar_log_procesados()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. Cargar Registros de Importación")
            archivos_input = st.file_uploader(
                "Selecciona archivos (.xlsx)", type="xlsx", accept_multiple_files=True, key="uploader_input"
            )
            if archivos_input:
                nuevos_archivos = 0
                log_seccion_input = log_procesados.get("input", {})
                for uploaded_file in archivos_input:
                    if not ha_sido_procesado(uploaded_file.name, uploaded_file.size, log_seccion_input):
                        with open(os.path.join("input", uploaded_file.name), "wb") as f: f.write(uploaded_file.getbuffer())
                        actualizar_log(uploaded_file.name, uploaded_file.size, log_seccion_input)
                        nuevos_archivos += 1
                if nuevos_archivos > 0:
                    st.success(f"{nuevos_archivos} nuevo(s) archivo(s) guardado(s).")
                    log_procesados["input"] = log_seccion_input
                    guardar_log_procesados(log_procesados)

        with col2:
            st.subheader("2. Cargar Catálogos (Opcional)")
            archivos_catalogos = st.file_uploader(
                "Selecciona catálogos (PDF, XLSX, CSV)", type=["pdf", "xlsx", "csv"], accept_multiple_files=True, key="uploader_catalogos"
            )
            if archivos_catalogos:
                nuevos_catalogos = 0
                log_seccion_catalogos = log_procesados.get("catalogos", {})
                for uploaded_file in archivos_catalogos:
                    if not ha_sido_procesado(uploaded_file.name, uploaded_file.size, log_seccion_catalogos):
                        with open(os.path.join("catalogos", uploaded_file.name), "wb") as f: f.write(uploaded_file.getbuffer())
                        actualizar_log(uploaded_file.name, uploaded_file.size, log_seccion_catalogos)
                        nuevos_catalogos += 1
                if nuevos_catalogos > 0:
                    st.success(f"{nuevos_catalogos} nuevo(s) catálogo(s) guardado(s).")
                    log_procesados["catalogos"] = log_seccion_catalogos
                    guardar_log_procesados(log_procesados)
        
        st.markdown("---")
        st.header("Procesar Datos")
        if st.button("Ejecutar Proceso Completo"):
            ejecutar_proceso_completo()
            st.rerun()

# CASO 2: Los datos ya están cargados, se muestra el dashboard de análisis.
else:
    df_final = st.session_state['df_final']
    diccionario_filtros = cargar_diccionario_filtros()

    with st.sidebar:
        st.title("⚙️ Filtros y Acciones")
        
        st.subheader("Acciones")
        if st.button("🔄 Reprocesar Datos Actuales", help="Vuelve a ejecutar el análisis sobre los archivos ya cargados."):
            ejecutar_proceso_completo()
            st.rerun()
            
        if st.button("📁 Cargar Nuevos Archivos (Reiniciar)", help="Vuelve a la pantalla inicial para cargar un nuevo set de datos."):
            if os.path.exists(PATH_DATOS_PROCESADOS):
                os.remove(PATH_DATOS_PROCESADOS)
            st.session_state['df_final'] = None
            st.cache_data.clear()
            st.rerun()
        st.markdown("---")
        
        filtros_secundarios_seleccionados = []
        filtro_principal_seleccionado = None
        
        if diccionario_filtros:
            st.subheader("Filtro por Producto")
            opciones_principales = ["Todas"] + sorted([k.title() for k in diccionario_filtros.keys()])
            filtro_principal_display = st.selectbox("Filtro Principal", options=opciones_principales)
            if filtro_principal_display != "Todas":
                filtro_principal_seleccionado = filtro_principal_display.lower()
                opciones_secundarias = sorted([s.title() for s in diccionario_filtros.get(filtro_principal_seleccionado, [])])
                filtros_secundarios_display = st.multiselect("Filtro Secundario", options=opciones_secundarias)
                filtros_secundarios_seleccionados = [s.lower() for s in filtros_secundarios_display]
            st.markdown("---")

        lista_continentes = sorted([c for c in df_final['continente'].unique() if c])
        continentes_seleccionados = st.multiselect("Continente(s)", options=lista_continentes, default=lista_continentes)
        min_fecha = df_final['fecha'].min().date()
        max_fecha = df_final['fecha'].max().date()
        fecha_inicio, fecha_fin = st.date_input("Rango de Fechas", value=[min_fecha, max_fecha], min_value=min_fecha, max_value=max_fecha)
        st.markdown("---")
        
        st.subheader("Buscador de Aranceles 🔎")
        busqueda_glosa = st.text_input("Buscar por descripción de arancel:", key="busqueda_glosa")
        codigos_seleccionados_glosa = []
        if busqueda_glosa:
            resultados_glosa = buscar_por_glosa(busqueda_glosa)
            if not resultados_glosa.empty:
                opciones_glosa = {f"{row['codigo_arancel']} - {row['glosa_original'][:60]}...": row['codigo_arancel'] for _, row in resultados_glosa.iterrows()}
                claves_seleccionadas_glosa = st.multiselect("Selecciona aranceles:", options=opciones_glosa.keys(), key="seleccion_glosa")
                codigos_seleccionados_glosa = [opciones_glosa[k] for k in claves_seleccionadas_glosa]
        
        busqueda_codigo = st.text_area("Ingresar código de arancel:", key="busqueda_codigo")
        codigos_directos = []
        if busqueda_codigo:
            codigos_brutos = re.split('[,\n]', busqueda_codigo)
            codigos_directos = [limpiar_codigo_arancel(c) for c in codigos_brutos if c.strip()]
        codigos_a_filtrar = list(set(codigos_seleccionados_glosa + codigos_directos))

        st.markdown("---")
        st.subheader("Configuración de Limpieza")
        st.slider(
            "Nivel de Sensibilidad para Coincidencias",
            min_value=70, max_value=100, value=90, key='sensibilidad_fuzzy',
            help="Define qué tan 'parecidas' deben ser las palabras para considerarse una coincidencia. Un valor más alto es más estricto. Para que el cambio aplique, debes volver a ejecutar el proceso completo."
        )

    df_filtrado = df_final.copy()
    if continentes_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['continente'].isin(continentes_seleccionados)]
    if fecha_inicio and fecha_fin and fecha_inicio <= fecha_fin:
        df_filtrado = df_filtrado[(df_filtrado['fecha'] >= pd.to_datetime(fecha_inicio)) & (df_filtrado['fecha'] <= pd.to_datetime(fecha_fin))]
    if codigos_a_filtrar:
        df_filtrado = df_filtrado[df_filtrado['codigo_arancel'].isin(codigos_a_filtrar)]
    
    if filtro_principal_seleccionado:
        df_filtrado = df_filtrado[df_filtrado['filtro_principal'] == filtro_principal_seleccionado]
        if filtros_secundarios_seleccionados:
            patron_secundario = '|'.join(map(re.escape, filtros_secundarios_seleccionados))
            df_filtrado = df_filtrado[df_filtrado['filtro_secundario'].str.contains(patron_secundario, na=False)]

    st.header("Resultados del Análisis")
    st.subheader(f"Análisis para: {', '.join(continentes_seleccionados)}")
    st.caption(f"Período: `{fecha_inicio.strftime('%d-%m-%Y')}` a `{fecha_fin.strftime('%d-%m-%Y')}`")
    
    if not df_filtrado.empty:
        with st.expander("📥 Descargar Datos Filtrados"):
            df_para_descargar = df_filtrado.copy()
            if 'fecha' in df_para_descargar.columns:
                df_para_descargar['fecha'] = pd.to_datetime(df_para_descargar['fecha']).dt.strftime('%d-%m-%Y')
            excel_data = to_excel(df_para_descargar)
            csv_data = df_para_descargar.to_csv(index=False).encode('utf-8')
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(label="Descargar en Excel (.xlsx)", data=excel_data, file_name="analisis_filtrado.xlsx")
            with col_dl2:
                st.download_button(label="Descargar en CSV (.csv)", data=csv_data, file_name="analisis_filtrado.csv")

    if df_filtrado.empty:
        st.warning("No se encontraron datos para los filtros seleccionados.")
    else:
        st.markdown("---")
        generar_tabla_resumen(df_filtrado)
        generar_grafico_barras_mensual(df_filtrado)
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            generar_ranking_marcas(df_filtrado)
        with col_g2:
            generar_pie_paises(df_filtrado)
        generar_grafico_arancel(df_filtrado)
        generar_detalle_repuestos(df_filtrado)
        generar_analisis_otras_marcas(df_filtrado)