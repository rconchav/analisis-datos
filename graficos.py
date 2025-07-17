# graficos.py

import streamlit as st
import pandas as pd
import plotly.express as px
from utils import formatar_moneda_cl

def generar_tabla_resumen(df):
    with st.expander("Ver Tabla Resumen por Marca", expanded=True):
        resumen = df.groupby('marca_final').agg(
            conteo_registros=('marca_final', 'size'),
            valor_total_cif=('valor_cif', 'sum')
        ).sort_values(by='valor_total_cif', ascending=False).reset_index()
        
        # MEJORA: Formato Título para la marca
        resumen['marca_final'] = resumen['marca_final'].str.title()
        
        st.data_editor(
            resumen,
            column_config={
                "valor_total_cif": st.column_config.NumberColumn(
                    "Valor Total CIF",
                    format="%.2f"
                ),
                "marca_final": "Marca",
                "conteo_registros": "Nº Registros"
            },
            hide_index=True,
            disabled=True
        )

def generar_grafico_barras_mensual(df):
    st.subheader("Valor CIF Mensual por Marca")
    df_barras = df.groupby([pd.Grouper(key='fecha', freq='ME'), 'marca_final'])['valor_cif'].sum().reset_index()
    
    # MEJORA: Formato Título para la leyenda del gráfico
    df_barras['marca_final'] = df_barras['marca_final'].str.title()
    
    fig = px.bar(df_barras, x='fecha', y='valor_cif', color='marca_final', title='Desglose de Valor CIF Mensual')
    fig.update_xaxes(tickformat="%d-%m-%Y")
    st.plotly_chart(fig, use_container_width=True, key="barras_mensuales")

def generar_ranking_marcas(df):
    st.subheader("Ranking de Marcas por Valor CIF")
    ranking = df.groupby('marca_final')['valor_cif'].sum().sort_values(ascending=False).nlargest(15)
    
    # MEJORA: Formato Título para las etiquetas del eje Y
    ranking.index = ranking.index.str.title()
    
    fig = px.bar(ranking, x=ranking.values, y=ranking.index, orientation='h', labels={'x': 'Total Valor CIF (USD)', 'y': 'Marca'}, title='Top 15 Marcas')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True, key="ranking_marcas")

def generar_pie_paises(df):
    st.subheader("Participación de Mercado por País")
    cif_pais = df.groupby('pais_final')['valor_cif'].sum()
    
    # MEJORA: Formato Título para las etiquetas del gráfico
    cif_pais.index = cif_pais.index.str.title()
    
    fig = px.pie(cif_pais, names=cif_pais.index, values=cif_pais.values, title='Participación por País')
    st.plotly_chart(fig, use_container_width=True, key="participacion_pais")

def generar_analisis_otras_marcas(df):
    with st.expander("🕵️‍♂️ Análisis Profundo de 'Otras Marcas'"):
        df_otras = df[df['marca_final'] == 'otras marcas']
        if df_otras.empty or 'marca_original' not in df_otras.columns:
            st.info("No hay registros en 'Otras Marcas' para los filtros seleccionados.")
        else:
            columnas_a_mostrar = ['marca_original', 'pais_final', 'continente', 'producto', 'descripcion', 'valor_cif']
            columnas_existentes = [col for col in columnas_a_mostrar if col in df_otras.columns]
            
            df_display = df_otras[columnas_existentes].copy()
            
            # MEJORA: Formato Título para las columnas de texto
            for col in ['marca_original', 'pais_final', 'continente', 'producto', 'descripcion']:
                if col in df_display.columns:
                    df_display[col] = df_display[col].str.title()
            
            df_display = df_display.sort_values(by='valor_cif', ascending=False)
            df_display['valor_cif'] = df_display['valor_cif'].apply(formatar_moneda_cl)
            st.dataframe(df_display, hide_index=True)

def generar_detalle_repuestos(df):
    with st.expander("⚙️ Análisis de Repuestos por Marca"):
        if 'categoria_bulto' in df.columns:
            df_repuestos = df[df['categoria_bulto'] == 'REPUESTOS']
            if df_repuestos.empty:
                st.info("No se encontraron registros de 'REPUESTOS' para los filtros seleccionados.")
                return
            
            lista_marcas_repuestos = sorted(df_repuestos['marca_final'].unique())
            # MEJORA: Formato Título para las opciones del selector
            opciones_marcas = {marca.title(): marca for marca in lista_marcas_repuestos}
            marca_display_seleccionada = st.selectbox("Selecciona una marca para ver sus repuestos:", options=opciones_marcas.keys(), key="selector_repuestos")
            
            if marca_display_seleccionada:
                marca_seleccionada = opciones_marcas[marca_display_seleccionada]
                st.write(f"Mostrando registros de repuestos para **{marca_display_seleccionada.upper()}**")
                df_detalle = df_repuestos[df_repuestos['marca_final'] == marca_seleccionada]
                columnas_a_mostrar = ['fecha', 'id_aceptacion', 'producto', 'variedad', 'descripcion', 'cantidad', 'valor_cif']
                columnas_existentes = [col for col in columnas_a_mostrar if col in df_detalle.columns]
                
                df_display = df_detalle[columnas_existentes].copy()
                df_display = df_display.sort_values(by='valor_cif', ascending=False)
                df_display['fecha'] = pd.to_datetime(df_display['fecha']).dt.strftime('%d-%m-%Y')
                df_display['valor_cif'] = df_display['valor_cif'].apply(formatar_moneda_cl)
                
                # MEJORA: Formato Título para las columnas de texto
                for col in ['producto', 'variedad', 'descripcion']:
                    if col in df_display.columns:
                        df_display[col] = df_display[col].str.title()

                st.dataframe(df_display, hide_index=True)

def generar_grafico_arancel(df):
    st.subheader("Valor CIF por Clasificación Arancelaria")
    if 'descripcion_arancel' in df.columns:
        # Filtramos descripciones vacías o no encontradas
        df_filtrado_arancel = df[~df['descripcion_arancel'].isin(['N/A', 'Código no encontrado'])]
        if not df_filtrado_arancel.empty:
            cif_por_arancel = df_filtrado_arancel.groupby('descripcion_arancel')['valor_cif'].sum().sort_values(ascending=False).nlargest(15)
            if not cif_por_arancel.empty:
                
                # MEJORA: Formato Título para las etiquetas del eje Y
                cif_por_arancel.index = cif_por_arancel.index.str.title()

                fig = px.bar(
                    cif_por_arancel, x=cif_por_arancel.values, y=cif_por_arancel.index, orientation='h',
                    title='Top 15 Capítulos Arancelarios por Valor CIF',
                    labels={'x': 'Total Valor CIF (USD)', 'y': 'Capítulo Arancelario'}
                )
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True, key="arancel_ranking")