# pages/3_Analisis_Avanzado.py

import streamlit as st
import pandas as pd
import os
import altair as alt

# --- CÓDIGO DE CONFIGURACIÓN DE RUTA ---
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Importaciones ---
from src.graficos import (
    generar_grafico_clusters, generar_regresion_lineal,
    generar_proyeccion_temporal, generar_heatmap_correlacion
)
from src.logic.segmentation import Segmentador
from src.utils import configurar_pagina
from src.diccionarios import cargar_diccionario
from src.theme import PALETA_OSCURA, PALETA_CLARA, configurar_tema

# --- CONFIGURACIÓN DE PÁGINA Y TEMA ---
configurar_pagina(titulo_pagina="Análisis Avanzado")
if 'theme_toggle' not in st.session_state:
    st.session_state.theme_toggle = True
tema_actual = "Oscuro" if st.session_state.theme_toggle else "Claro"
configurar_tema(tema_actual)

# --- CARGA DE DATOS ---
if 'proyecto_activo' not in st.session_state or not st.session_state.proyecto_activo:
    st.warning("Por favor, selecciona un proyecto en la página de inicio para continuar.")
    st.stop()

proyecto_id = st.session_state.proyecto_activo
proyecto_nombre = st.session_state.get('proyecto_activo_nombre', proyecto_id)

@st.cache_data
def cargar_datos_procesados(proyecto_id):
    path_datos = os.path.join("proyectos", proyecto_id, "datos_procesados.parquet")
    if os.path.exists(path_datos):
        return pd.read_parquet(path_datos)
    return pd.DataFrame()

df_procesado = cargar_datos_procesados(proyecto_id)
diccionario = cargar_diccionario(proyecto_id)
mapeo = diccionario.get('mapeo_dinamico', {})

if df_procesado.empty:
    st.error(f"No se encontraron datos procesados para el proyecto '{proyecto_nombre}'.")
    st.stop()

# --- LÓGICA DINÁMICA DE COLUMNAS ---
metricas_mapeadas = [m.get('nombre_personalizado') for m in mapeo.get('metricas', []) if m.get('nombre_personalizado')]
filtros_mapeados = [f.get('nombre_personalizado') for f in mapeo.get('filtros', []) if f.get('nombre_personalizado')]

def encontrar_columna_por_tipo(tipo):
    return next((f.get('nombre_personalizado') for f in mapeo.get('filtros', []) if f.get('tipo_dato') == tipo), None)

nombre_col_pais = encontrar_columna_por_tipo('País')
nombre_col_fecha = next((f.get('nombre_personalizado') for f in mapeo.get('fechas', [])), None)
nombre_col_marca = next((f for f in filtros_mapeados if 'marca' in f.lower()), None)

# --- BARRA LATERAL CON FILTROS ---
with st.sidebar:
    st.title(f"Proyecto: {proyecto_nombre}")
    paleta_actual = PALETA_OSCURA if st.session_state.theme_toggle else "Claro"

    st.header("Filtros de Datos")
    df_filtrado = df_procesado.copy()

    if 'Continente' in df_filtrado.columns:
        continentes_unicos = [c for c in df_filtrado['Continente'].unique() if c != 'Desconocido']
        continentes_seleccionados = st.multiselect("Continentes", sorted(continentes_unicos), default=sorted(continentes_unicos))
        df_filtrado = df_filtrado[df_filtrado['Continente'].isin(continentes_seleccionados)]

    if nombre_col_pais and nombre_col_pais in df_filtrado.columns:
        paises_seleccionados = st.multiselect(f"{nombre_col_pais}", sorted(df_filtrado[nombre_col_pais].unique()), default=sorted(df_filtrado[nombre_col_pais].unique()))
        df_filtrado = df_filtrado[df_filtrado[nombre_col_pais].isin(paises_seleccionados)]

    if nombre_col_marca and nombre_col_marca in df_filtrado.columns:
        marcas_seleccionadas = st.multiselect(f"{nombre_col_marca}", sorted(df_filtrado[nombre_col_marca].unique()), default=sorted(df_filtrado[nombre_col_marca].unique()))
        df_filtrado = df_filtrado[df_filtrado[nombre_col_marca].isin(marcas_seleccionadas)]

    if nombre_col_fecha and nombre_col_fecha in df_filtrado.columns and not df_filtrado.empty:
        df_filtrado[nombre_col_fecha] = pd.to_datetime(df_filtrado[nombre_col_fecha])
        fecha_min, fecha_max = df_filtrado[nombre_col_fecha].min(), df_filtrado[nombre_col_fecha].max()

        if fecha_min == fecha_max:
            st.info(f"Todos los registros son del día: {fecha_min.strftime('%d/%m/%Y')}")
        else:
            fecha_inicio, fecha_fin = st.slider("Rango de Fechas", min_value=fecha_min.to_pydatetime(), max_value=fecha_max.to_pydatetime(), value=(fecha_min.to_pydatetime(), fecha_max.to_pydatetime()), format="DD/MM/YYYY")
            df_filtrado = df_filtrado[df_filtrado[nombre_col_fecha].between(pd.to_datetime(fecha_inicio), pd.to_datetime(fecha_fin))]

# --- PÁGINA PRINCIPAL ---
st.title("🔬 Análisis Avanzado")
st.markdown("""
Esta sección contiene herramientas de análisis estadístico para descubrir patrones profundos y relaciones en tus datos **filtrados**.
- **Análisis de Clusters:** Agrupa tus datos en segmentos con características similares de forma automática.
- **Regresión Lineal:** Analiza la relación e influencia entre dos variables numéricas.
- **Proyección Temporal:** Estima el comportamiento futuro de una métrica basándose en su tendencia histórica.
- **Heatmap de Correlación:** Muestra visualmente la fuerza de la relación entre todas tus métricas.
""")

if df_filtrado.empty:
    st.warning("No hay datos para analizar con los filtros seleccionados.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["Análisis de Clusters", "Regresión Lineal", "Proyección Temporal", "Heatmap de Correlación"])

with tab1:
    st.header("Análisis de Clusters (KMeans)")
    metricas_cluster = st.multiselect("Métricas para clustering:", options=metricas_mapeadas, default=metricas_mapeadas[:2])

    with st.expander("Encontrar k óptimo (Método del Codo)"):
        max_k = st.slider("Max k:", 2, 15, 8, key="slider_k_codo")
        if st.button("Calcular Gráfico del Codo"):
            if len(metricas_cluster) < 2:
                st.warning("Selecciona al menos dos métricas.")
            else:
                s = Segmentador()
                df_codo = s.encontrar_k_optimo(df_filtrado, metricas_cluster, max_k)
                st.altair_chart(alt.Chart(df_codo).mark_line(point=True).encode(x='k:O', y='inercia:Q').properties(title="Método del Codo"), use_container_width=True)

    num_clusters = st.number_input("Número de clusters (k):", 2, 20, 5, key="num_k_cluster")

    if st.button("Realizar Análisis de Clusters"):
        if len(metricas_cluster) < 2:
            st.warning("Selecciona al menos dos métricas.")
        else:
            s = Segmentador(n_clusters=num_clusters)
            df_clusters = s.segmentar_dataframe(df_filtrado, metricas_cluster)
            generar_grafico_clusters(df_clusters, paleta_actual)

with tab2:
    st.header("Regresión Lineal")
    col1, col2 = st.columns(2)
    var_independiente = col1.selectbox("Variable Independiente (X):", metricas_mapeadas)
    var_dependiente = col2.selectbox("Variable Dependiente (Y):", metricas_mapeadas, index=min(1, len(metricas_mapeadas)-1))
    if st.button("Calcular Regresión"):
        generar_regresion_lineal(df_filtrado, var_independiente, var_dependiente, paleta_actual)

with tab3:
    st.header("Proyección Temporal Lineal")

    if not nombre_col_fecha or nombre_col_fecha not in df_filtrado.columns:
        st.warning("No se ha configurado un campo de fecha en la página de Configuración. Esta función requiere una columna de fecha.")
    else:
        metrica_proyeccion = st.selectbox("Métrica a proyectar:", metricas_mapeadas)
        periodos = st.number_input("Meses a proyectar:", 1, 24, 6)
        if st.button("Generar Proyección"):
            generar_proyeccion_temporal(df_filtrado, nombre_col_fecha, metrica_proyeccion, periodos, paleta_actual)

with tab4:
    st.header("Heatmap de Correlación")
    st.markdown("Visualiza la relación lineal entre todas las métricas. Valores cercanos a 1 o -1 indican una correlación fuerte.")
    if st.button("Generar Heatmap"):
        generar_heatmap_correlacion(df_filtrado, metricas_mapeadas)