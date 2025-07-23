# pages/3_Reportes.py

import streamlit as st
import pandas as pd
import os
import re

# --- CÓDIGO DE CONFIGURACIÓN DE PATH (SOLUCIÓN AL ERROR) ---
# Este bloque DEBE estar al principio de todo.
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Importaciones de la aplicación ---
from src.graficos import (
    generar_tabla_resumen, generar_grafico_barras_mensual,
    generar_ranking_marcas, generar_pie_paises,
    generar_detalle_repuestos, generar_grafico_arancel,
    generar_grafico_clusters, generar_grafico_pareto_principal
)
from src.utils import to_excel
from src.diccionarios import cargar_diccionario

st.set_page_config(layout="wide", page_title="Dashboard de Análisis")

# --- Inicializar estado para el expander ---
if 'run_cluster_analysis' not in st.session_state:
    st.session_state.run_cluster_analysis = False

# --- 1. VERIFICAR PROYECTO ACTIVO ---
if 'proyecto_activo' not in st.session_state or st.session_state.proyecto_activo is None:
    st.warning("Por favor, selecciona o crea un proyecto en la página de '🏠 Inicio'.")
    st.stop()

proyecto_activo_dict = st.session_state.proyecto_activo
proyecto_id = proyecto_activo_dict['id']
proyecto_display_name = proyecto_activo_dict['display_name']
st.title(f"📊 Constructor de Reportes: `{proyecto_display_name}`")

# --- 2. CARGAR DATOS PROCESADOS ---
path_datos = os.path.join("proyectos", proyecto_id, "datos_procesados.parquet")
if not os.path.exists(path_datos):
    st.error("No se han procesado los datos para este proyecto.")
    st.info("Por favor, ve a la página de 'Configuración y Mapeo' y ejecuta el proceso de limpieza.")
    st.stop()

@st.cache_data
def cargar_dataframe(path):
    return pd.read_parquet(path)

df_final = cargar_dataframe(path_datos)
diccionario_filtros = cargar_diccionario(proyecto_id)

# --- 3. BARRA LATERAL DE FILTROS ---
with st.sidebar:
    st.title("⚙️ Filtros")
    if st.button("🔄 Refrescar Datos", use_container_width=True, help="Haz clic aquí si los datos parecen desactualizados."):
        st.cache_data.clear()
        st.rerun()

    segmentos_seleccionados = []
    if 'segmento_producto' in df_final.columns and not df_final['segmento_producto'].empty:
        opciones_segmento = sorted(list(df_final['segmento_producto'].unique()))
        segmentos_seleccionados = st.multiselect("Segmento(s) de Producto", options=opciones_segmento, default=opciones_segmento)
    
    filtros_secundarios_seleccionados = []
    filtro_principal_seleccionado = None
    if diccionario_filtros:
        opciones_principales = ["Todos"] + sorted([k.title() for k in diccionario_filtros.keys()])
        filtro_principal_display = st.selectbox("Filtro Principal", options=opciones_principales)
        if filtro_principal_display != "Todos":
            filtro_principal_seleccionado = filtro_principal_display.upper()
            opciones_secundarias = sorted([s.title() for s in diccionario_filtros.get(filtro_principal_seleccionado, [])])
            filtros_secundarios_display = st.multiselect("Filtro Secundario", options=opciones_secundarias)
            filtros_secundarios_seleccionados = [s.upper() for s in filtros_secundarios_display]
    
    lista_continentes = sorted([c for c in df_final['continente'].unique() if c])
    continentes_seleccionados = st.multiselect("Continente(s)", options=lista_continentes, default=lista_continentes)
    
    min_fecha = df_final['fecha'].min().date()
    max_fecha = df_final['fecha'].max().date()
    fecha_inicio, fecha_fin = st.date_input("Rango de Fechas", value=[min_fecha, max_fecha], min_value=min_fecha, max_value=max_fecha)
    
    st.markdown("---")
    st.subheader("Exportar")
    # Se crea una copia para aplicar los filtros de descarga.
    df_para_descargar = df_final.copy() 
    if segmentos_seleccionados: df_para_descargar = df_para_descargar[df_para_descargar['segmento_producto'].isin(segmentos_seleccionados)]
    if filtro_principal_seleccionado:
        df_para_descargar = df_para_descargar[df_para_descargar['filtro_principal'] == filtro_principal_seleccionado]
        if filtros_secundarios_seleccionados:
            patron = '|'.join(map(re.escape, filtros_secundarios_seleccionados))
            df_para_descargar = df_para_descargar[df_para_descargar['filtro_secundario'].str.contains(patron, na=False, case=False)]
    if continentes_seleccionados: df_para_descargar = df_para_descargar[df_para_descargar['continente'].isin(continentes_seleccionados)]
    if fecha_inicio and fecha_fin: df_para_descargar = df_para_descargar[(df_para_descargar['fecha'].dt.date >= fecha_inicio) & (df_para_descargar['fecha'].dt.date <= fecha_fin)]
    
    if not df_para_descargar.empty:
        excel_data = to_excel(df_para_descargar)
        st.download_button(
            label="📥 Descargar Vista Actual", data=excel_data,
            file_name=f"reporte_{proyecto_id}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# --- 4. APLICAR FILTROS AL DATAFRAME PARA VISUALIZACIÓN ---
df_filtrado = df_para_descargar.copy()

# --- 5. MOSTRAR RESULTADOS ---
if df_filtrado.empty:
    st.warning("No se encontraron datos para los filtros seleccionados.")
else:
    st.header("Resultados del Análisis")
    st.caption(f"Período: `{fecha_inicio.strftime('%d-%m-%Y')}` a `{fecha_fin.strftime('%d-%m-%Y')}`")
    
    with st.expander("🔬 Ver Análisis de Clusters", expanded=st.session_state.run_cluster_analysis):
        generar_grafico_clusters(df_filtrado)

    st.markdown("---")
    
    generar_tabla_resumen(df_filtrado)
    generar_grafico_pareto_principal(df_filtrado) 
    generar_grafico_barras_mensual(df_filtrado)
    col_g1, col_g2 = st.columns(2)
    with col_g1: generar_ranking_marcas(df_filtrado)
    with col_g2: generar_pie_paises(df_filtrado)
    generar_grafico_arancel(df_filtrado)
    generar_detalle_repuestos(df_filtrado)