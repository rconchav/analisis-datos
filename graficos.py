# graficos.py

import streamlit as st
import pandas as pd
import plotly.express as px
from utils import formatar_moneda_cl

def generar_tabla_resumen(df):
    with st.expander("Ver Tabla Resumen por Filtro Principal", expanded=True):
        # CORRECCIÓN: Se usa 'filtro_principal'
        resumen = df.groupby('filtro_principal').agg(
            conteo_registros=('filtro_principal', 'size'),
            valor_total_cif=('valor_cif', 'sum')
        ).sort_values(by='valor_total_cif', ascending=False).reset_index()
        
        resumen['filtro_principal'] = resumen['filtro_principal'].str.title()
        resumen['valor_total_cif'] = resumen['valor_total_cif'].apply(formatar_moneda_cl)
        
        resumen = resumen.rename(columns={
            "filtro_principal": "Filtro Principal",
            "conteo_registros": "Nº Registros",
            "valor_total_cif": "Valor Total CIF"
        })
        st.dataframe(resumen, hide_index=True)

def generar_grafico_barras_mensual(df):
    st.subheader("Valor CIF Mensual por Filtro Principal")
    # CORRECCIÓN: Se usa 'filtro_principal'
    df_barras = df.groupby([pd.Grouper(key='fecha', freq='ME'), 'filtro_principal'])['valor_cif'].sum().reset_index()
    
    df_barras['filtro_principal'] = df_barras['filtro_principal'].str.title()
    
    fig = px.bar(df_barras, x='fecha', y='valor_cif', color='filtro_principal', title='Desglose de Valor CIF Mensual')
    fig.update_xaxes(tickformat="%d-%m-%Y")
    st.plotly_chart(fig, use_container_width=True, key="barras_mensuales")

def generar_ranking_marcas(df):
    st.subheader("Ranking por Filtro Principal")
    # CORRECCIÓN: Se usa 'filtro_principal'
    ranking = df.groupby('filtro_principal')['valor_cif'].sum().sort_values(ascending=False).nlargest(15)
    
    ranking.index = ranking.index.str.title()
    
    fig = px.bar(ranking, x=ranking.values, y=ranking.index, orientation='h', labels={'x': 'Total Valor CIF (USD)', 'y': 'Filtro Principal'}, title='Top 15 Filtros Principales')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True, key="ranking_marcas")

def generar_pie_paises(df):
    st.subheader("Participación de Mercado por País")
    cif_pais = df.groupby('pais_final')['valor_cif'].sum()
    cif_pais.index = cif_pais.index.str.title()
    fig = px.pie(cif_pais, names=cif_pais.index, values=cif_pais.values, title='Participación por País')
    st.plotly_chart(fig, use_container_width=True, key="participacion_pais")

def generar_analisis_otras_marcas(df):
    # CORRECCIÓN: Se usa 'filtro_principal'
    with st.expander("🕵️‍♂️ Análisis Profundo de 'Otras Marcas'"):
        df_otras = df[df['filtro_principal'] == 'otras marcas']
        if df_otras.empty or 'marca_original' not in df_otras.columns:
            st.info("No hay registros en 'Otras Marcas' para los filtros seleccionados.")
        else:
            columnas_a_mostrar = ['marca_original', 'pais_final', 'continente', 'producto', 'descripcion', 'valor_cif']
            columnas_existentes = [col for col in columnas_a_mostrar if col in df_otras.columns]
            df_display = df_otras[columnas_existentes].copy()
            for col in ['marca_original', 'pais_final', 'continente', 'producto', 'descripcion']:
                if col in df_display.columns: df_display[col] = df_display[col].str.title()
            df_display = df_display.sort_values(by='valor_cif', ascending=False)
            df_display['valor_cif'] = df_display['valor_cif'].apply(formatar_moneda_cl)
            st.dataframe(df_display, hide_index=True)

def generar_detalle_repuestos(df):
    with st.expander("⚙️ Análisis de Repuestos por Filtro Principal"):
        # CORRECCIÓN: Se usa 'filtro_principal'
        if 'categoria_bulto' in df.columns:
            df_repuestos = df[df['categoria_bulto'] == 'REPUESTOS']
            if df_repuestos.empty: st.info("No se encontraron registros de 'REPUESTOS'."); return
            
            lista_filtros = sorted(df_repuestos['filtro_principal'].unique())
            opciones_filtros = {f.title(): f for f in lista_filtros}
            filtro_display_seleccionado = st.selectbox("Selecciona un Filtro Principal:", options=opciones_filtros.keys(), key="selector_repuestos")
            
            if filtro_display_seleccionado:
                filtro_seleccionado = opciones_filtros[filtro_display_seleccionado]
                st.write(f"Mostrando registros de repuestos para **{filtro_display_seleccionado.upper()}**")
                df_detalle = df_repuestos[df_repuestos['filtro_principal'] == filtro_seleccionado]
                columnas_a_mostrar = ['fecha', 'id_aceptacion', 'producto', 'descripcion', 'cantidad', 'valor_cif']
                columnas_existentes = [col for col in columnas_a_mostrar if col in df_detalle.columns]
                df_display = df_detalle[columnas_existentes].copy()
                df_display = df_display.sort_values(by='valor_cif', ascending=False)
                df_display['fecha'] = pd.to_datetime(df_display['fecha']).dt.strftime('%d-%m-%Y')
                df_display['valor_cif'] = df_display['valor_cif'].apply(formatar_moneda_cl)
                for col in ['producto', 'descripcion']:
                    if col in df_display.columns: df_display[col] = df_display[col].str.title()
                st.dataframe(df_display, hide_index=True)

def generar_grafico_arancel(df):
    st.subheader("Valor CIF por Clasificación Arancelaria")
    if 'descripcion_arancel' in df.columns:
        df_filtrado_arancel = df[~df['descripcion_arancel'].isin(['N/A', 'Código no encontrado'])]
        if not df_filtrado_arancel.empty:
            cif_por_arancel = df_filtrado_arancel.groupby('descripcion_arancel')['valor_cif'].sum().sort_values(ascending=False).nlargest(15)
            if not cif_por_arancel.empty:
                cif_por_arancel.index = cif_por_arancel.index.str.title()
                fig = px.bar(cif_por_arancel, x=cif_por_arancel.values, y=cif_por_arancel.index, orientation='h', title='Top 15 Capítulos Arancelarios por Valor CIF', labels={'x': 'Total Valor CIF (USD)', 'y': 'Capítulo Arancelario'})
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True, key="arancel_ranking")