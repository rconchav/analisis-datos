# graficos.py

import streamlit as st
import pandas as pd
import plotly.express as px
from utils import formatar_moneda_cl

def generar_tabla_resumen(df):
    with st.expander("Ver Tabla Resumen por Filtro Principal", expanded=True):
        resumen = df.groupby('filtro_principal').agg(
            conteo_registros=('filtro_principal', 'size'),
            valor_total_cif=('valor_cif', 'sum')
        ).sort_values(by='valor_total_cif', ascending=False).reset_index()
        
        resumen['filtro_principal'] = resumen['filtro_principal'].str.title()
        resumen['valor_total_cif'] = resumen['valor_total_cif'].apply(formatar_moneda_cl)
        
        resumen = resumen.rename(columns={
            "filtro_principal": "Filtro Principal", "conteo_registros": "Nº Registros", "valor_total_cif": "Valor Total CIF"
        })
        st.dataframe(resumen, hide_index=True, use_container_width=True)

def generar_grafico_barras_mensual(df):
    st.subheader("Valor CIF Mensual por Filtro Principal")
    df_barras = df.groupby([pd.Grouper(key='fecha', freq='ME'), 'filtro_principal'])['valor_cif'].sum().reset_index()
    df_barras['filtro_principal'] = df_barras['filtro_principal'].str.title()
    fig = px.bar(df_barras, x='fecha', y='valor_cif', color='filtro_principal', title='Desglose de Valor CIF Mensual')
    fig.update_xaxes(tickformat="%d-%m-%Y"); st.plotly_chart(fig, use_container_width=True)

def generar_ranking_marcas(df):
    st.subheader("Ranking por Filtro Principal")
    ranking = df.groupby('filtro_principal')['valor_cif'].sum().sort_values(ascending=False).nlargest(15)
    ranking.index = ranking.index.str.title()
    fig = px.bar(ranking, x=ranking.values, y=ranking.index, orientation='h', labels={'x': 'Total Valor CIF (USD)', 'y': 'Filtro Principal'}, title='Top 15 Filtros Principales')
    fig.update_layout(yaxis={'categoryorder':'total ascending'}); st.plotly_chart(fig, use_container_width=True)

def generar_pie_paises(df):
    st.subheader("Participación de Mercado por País")
    cif_pais = df.groupby('pais_final')['valor_cif'].sum()
    cif_pais.index = cif_pais.index.str.title()
    fig = px.pie(cif_pais, names=cif_pais.index, values=cif_pais.values, title='Participación por País')
    st.plotly_chart(fig, use_container_width=True)

def generar_analisis_otras_marcas(df):
    # Esta función podría reevaluarse o adaptarse a la nueva lógica de 'sin_marca' o 'otras marcas'
    pass

def generar_detalle_repuestos(df):
    with st.expander("⚙️ Análisis por Segmento de Producto"):
        if 'segmento_producto' in df.columns:
            segmentos = sorted(df['segmento_producto'].unique())
            segmento_seleccionado = st.selectbox("Selecciona un segmento para ver detalle:", options=segmentos, key="selector_segmento")
            if segmento_seleccionado:
                st.write(f"Mostrando registros para el segmento **{segmento_seleccionado}**")
                df_detalle = df[df['segmento_producto'] == segmento_seleccionado]
                # ... (resto de la lógica de la tabla)
                st.dataframe(df_detalle, hide_index=True, use_container_width=True)

def generar_grafico_arancel(df):
    st.subheader("Valor CIF por Clasificación Arancelaria")
    if 'descripcion_arancel' in df.columns:
        df_filtrado_arancel = df[~df['descripcion_arancel'].isin(['N/A', 'Código no encontrado'])]
        if not df_filtrado_arancel.empty:
            cif_por_arancel = df_filtrado_arancel.groupby('descripcion_arancel')['valor_cif'].sum().sort_values(ascending=False).nlargest(15)
            if not cif_por_arancel.empty:
                cif_por_arancel.index = cif_por_arancel.index.str.title()
                fig = px.bar(cif_por_arancel, x=cif_por_arancel.values, y=cif_por_arancel.index, orientation='h', title='Top 15 Capítulos Arancelarios', labels={'x': 'Total Valor CIF (USD)', 'y': 'Capítulo Arancelario'})
                fig.update_layout(yaxis={'categoryorder':'total ascending'}); st.plotly_chart(fig, use_container_width=True)