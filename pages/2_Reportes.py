# pages/2_Reportes.py

import streamlit as st
import pandas as pd
import os
import json
import altair as alt

# --- CÓDIGO DE CONFIGURACIÓN DE RUTA ---
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Importaciones ---
from src.graficos import (
    generar_tabla_resumen, generar_grafico_pareto, generar_grafico_temporal,
    generar_grafico_ranking, generar_grafico_sunburst, generar_grafico_treemap,
    generar_mapa_distribucion
)
from src.utils import to_excel, configurar_pagina
from src.diccionarios import cargar_diccionario
from src.theme import PALETA_OSCURA, PALETA_CLARA, configurar_tema

# --- CONFIGURACIÓN DE PÁGINA Y TEMA ---
configurar_pagina(titulo_pagina="Dashboard de Análisis")
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
nombre_col_lat = encontrar_columna_por_tipo('Latitud')
nombre_col_lon = encontrar_columna_por_tipo('Longitud')

coordenadas_disponibles = (nombre_col_lat and nombre_col_lat in df_procesado.columns and nombre_col_lon and nombre_col_lon in df_procesado.columns) or ('lat' in df_procesado.columns and 'lon' in df_procesado.columns)
pais_disponible = nombre_col_pais and nombre_col_pais in df_procesado.columns

# --- BARRA LATERAL ---
with st.sidebar:
    st.title(f"Proyecto: {proyecto_nombre}")
    paleta_actual = PALETA_OSCURA if st.session_state.theme_toggle else "Claro"

    st.header("Filtros de Datos")
    df_filtrado = df_procesado.copy()

    if 'Continente' in df_filtrado.columns:
        continentes_unicos = [c for c in df_filtrado['Continente'].unique() if c != 'Desconocido']
        continentes_seleccionados = st.multiselect("Continentes", sorted(continentes_unicos), default=sorted(continentes_unicos))
        df_filtrado = df_filtrado[df_filtrado['Continente'].isin(continentes_seleccionados)]

    if nombre_col_pais:
        paises_seleccionados = st.multiselect(f"{nombre_col_pais}", sorted(df_filtrado[nombre_col_pais].unique()), default=sorted(df_filtrado[nombre_col_pais].unique()))
        df_filtrado = df_filtrado[df_filtrado[nombre_col_pais].isin(paises_seleccionados)]

    if nombre_col_marca:
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

    st.header("Configuración de Gráficos")

    graficos_base = ["Tabla Resumen", "Análisis de Pareto", "Evolución Temporal", "Ranking Dinámico", "Diagrama de Árbol"]
    graficos_geo_opcionales = []
    if pais_disponible:
        graficos_geo_opcionales.append("Distribución Geográfica")
    if coordenadas_disponibles:
        graficos_geo_opcionales.append("Mapa Geográfico")

    graficos_posibles = graficos_base + graficos_geo_opcionales
    graficos_seleccionados = st.multiselect("Gráficos a Mostrar", options=graficos_posibles, default=graficos_posibles)

    with st.expander("Opciones de Gráficos Específicos"):
        filtro_pareto = st.selectbox("Pareto por:", filtros_mapeados)
        metrica_pareto = st.selectbox("Métrica para Pareto:", metricas_mapeadas)
        metrica_temporal = st.selectbox("Métrica para Evolución:", metricas_mapeadas)
        frecuencia_temporal = st.selectbox("Frecuencia:", ['Mensual', 'Trimestral', 'Anual'])
        eje_y_ranking = st.selectbox("Valor para Ranking (Eje Y):", metricas_mapeadas)
        eje_x_ranking = st.selectbox("Categoría para Ranking (Eje X):", filtros_mapeados)
        path_treemap = st.multiselect("Jerarquía para Diagrama de Árbol:", options=filtros_mapeados, default=[f for f in ['Continente', nombre_col_pais] if f in filtros_mapeados])
        metrica_treemap = st.selectbox("Métrica para Diagrama de Árbol:", options=metricas_mapeadas)

        # CORREGIDO: Seleccionar la primera métrica por defecto para el mapa
        default_index = 1 if metricas_mapeadas else 0
        metrica_mapa = st.selectbox(
            "Métrica para tamaño en Mapa:", 
            options=[None] + metricas_mapeadas, 
            index=default_index,
            help="Selecciona una métrica para variar el tamaño de los puntos en el mapa. Elige 'None' para puntos de tamaño uniforme."
        )

# --- PÁGINA PRINCIPAL ---
if df_filtrado.empty:
    st.warning("No hay datos para los filtros seleccionados.")
else:
    if "Tabla Resumen" in graficos_seleccionados:
        generar_tabla_resumen(df_filtrado, metricas_mapeadas)

    if "Análisis de Pareto" in graficos_seleccionados and filtro_pareto and metrica_pareto:
        st.markdown("---")
        generar_grafico_pareto(df_filtrado, filtro_pareto, metrica_pareto, paleta_actual)

    if "Evolución Temporal" in graficos_seleccionados and nombre_col_fecha and metrica_temporal:
        st.markdown("---")
        generar_grafico_temporal(df_filtrado, nombre_col_fecha, metrica_temporal, frecuencia_temporal, paleta_actual)

    if "Ranking Dinámico" in graficos_seleccionados and eje_x_ranking and eje_y_ranking:
        st.markdown("---")
        generar_grafico_ranking(df_filtrado, eje_x_ranking, eje_y_ranking, paleta_actual)

    if "Distribución Geográfica" in graficos_seleccionados:
        st.markdown("---")
        metrica_dist = next((m for m in metricas_mapeadas if 'cif' in m.lower()), None)
        if nombre_col_pais and metrica_dist:
             generar_grafico_sunburst(df_filtrado, ['Continente', nombre_col_pais], metrica_dist, f"Distribución Geográfica ({metrica_dist})", paleta_actual)

    if "Diagrama de Árbol" in graficos_seleccionados and path_treemap and metrica_treemap:
        st.markdown("---")
        titulo = f"Treemap por {', '.join(path_treemap)} según {metrica_treemap}"
        generar_grafico_treemap(df_filtrado, path_treemap, metrica_treemap, titulo)

    if "Mapa Geográfico" in graficos_seleccionados:
        st.markdown("---")
        latitud = nombre_col_lat if nombre_col_lat else 'lat'
        longitud = nombre_col_lon if nombre_col_lon else 'lon'
        generar_mapa_distribucion(df_filtrado, latitud, longitud, size_col=metrica_mapa)