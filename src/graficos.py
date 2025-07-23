# src/graficos.py

import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Importar funciones de utilidad del proyecto
from .utils import formatar_moneda_cl

# --- FUNCIONES DE GRÁFICOS PARA EL DASHBOARD ---

def generar_tabla_resumen(df):
    """Genera la tabla de resumen estática para el dashboard principal."""
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
    """Genera el gráfico de barras del valor CIF mensual."""
    st.subheader("Valor CIF Mensual por Filtro Principal")
    df_barras = df.groupby([pd.Grouper(key='fecha', freq='ME'), 'filtro_principal'])['valor_cif'].sum().reset_index()
    df_barras['filtro_principal'] = df_barras['filtro_principal'].str.title()
    fig = px.bar(df_barras, x='fecha', y='valor_cif', color='filtro_principal', title='Desglose de Valor CIF Mensual')
    fig.update_xaxes(tickformat="%d-%m-%Y")
    st.plotly_chart(fig, use_container_width=True)

def generar_ranking_marcas(df):
    """Genera el gráfico de barras del ranking de filtros principales."""
    st.subheader("Ranking por Filtro Principal")
    ranking = df.groupby('filtro_principal')['valor_cif'].sum().sort_values(ascending=False).nlargest(15)
    ranking.index = ranking.index.str.title()
    fig = px.bar(ranking, x=ranking.values, y=ranking.index, orientation='h', labels={'x': 'Total Valor CIF (USD)', 'y': 'Filtro Principal'}, title='Top 15 Filtros Principales')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

def generar_pie_paises(df):
    """Genera el gráfico de torta de participación por país."""
    st.subheader("Participación de Mercado por País")
    cif_pais = df.groupby('pais_final')['valor_cif'].sum()
    cif_pais.index = cif_pais.index.str.title()
    fig = px.pie(cif_pais, names=cif_pais.index, values=cif_pais.values, title='Participación por País')
    st.plotly_chart(fig, use_container_width=True)

def generar_detalle_repuestos(df):
    """Genera la tabla de detalle por segmento de producto."""
    if 'segmento_producto' in df.columns:
        with st.expander("⚙️ Análisis por Segmento de Producto"):
            segmentos = sorted(df['segmento_producto'].unique())
            segmento_seleccionado = st.selectbox("Selecciona un segmento para ver detalle:", options=segmentos, key="selector_segmento")
            if segmento_seleccionado:
                st.write(f"Mostrando registros para el segmento **{segmento_seleccionado}**")
                df_detalle = df[df['segmento_producto'] == segmento_seleccionado]
                st.dataframe(df_detalle, hide_index=True, use_container_width=True)

def generar_grafico_arancel(df):
    """Genera el gráfico de barras de valor CIF por capítulo arancelario."""
    if 'descripcion_arancel' in df.columns:
        st.subheader("Valor CIF por Clasificación Arancelaria")
        df_filtrado_arancel = df[~df['descripcion_arancel'].isin(['N/A', 'Código no encontrado'])]
        if not df_filtrado_arancel.empty:
            cif_por_arancel = df_filtrado_arancel.groupby('descripcion_arancel')['valor_cif'].sum().sort_values(ascending=False).nlargest(15)
            if not cif_por_arancel.empty:
                cif_por_arancel.index = cif_por_arancel.index.str.title()
                fig = px.bar(cif_por_arancel, x=cif_por_arancel.values, y=cif_por_arancel.index, orientation='h', title='Top 15 Capítulos Arancelarios', labels={'x': 'Total Valor CIF (USD)', 'y': 'Capítulo Arancelario'})
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)

# --- FUNCIÓN DE CLUSTERING BAJO DEMANDA (PARA MEJORAR RENDIMIENTO) ---
def generar_grafico_clusters(df):
    """
    Realiza un análisis de clustering adaptativo y lo visualiza, activado por un botón.
    """
    st.info("El análisis de clusters agrupa tus datos para descubrir patrones ocultos. Es un proceso intensivo, haz clic en el botón para generarlo.")
    
    num_clusters = st.slider(
        "Selecciona el número de clusters a encontrar:", 
        min_value=2, max_value=10, value=4, key="slider_clusters"
    )

    if st.button("🧠 Generar Análisis de Clusters", use_container_width=True):
        caracteristicas_posibles = ['valor_cif', 'filtro_principal', 'pais_final', 'segmento_producto', 'continente']
        features = [col for col in caracteristicas_posibles if col in df.columns]
        
        df_cluster = df[features].copy().dropna()
        if len(df_cluster) < 20:
            st.warning("No hay suficientes datos para generar un análisis de clusters significativo.")
            return

        with st.spinner("Realizando análisis de clustering..."):
            features_categoricas = [col for col in features if pd.api.types.is_object_dtype(df_cluster[col])]
            df_encoded = pd.get_dummies(df_cluster, columns=features_categoricas)
            
            scaler = StandardScaler()
            df_scaled = scaler.fit_transform(df_encoded)

            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
            df_cluster['cluster'] = kmeans.fit_predict(df_scaled)
            
            pca = PCA(n_components=2)
            components = pca.fit_transform(df_scaled)
            df_cluster['pca1'] = components[:, 0]
            df_cluster['pca2'] = components[:, 1]
            
            hover_data_existente = [col for col in ['filtro_principal', 'pais_final', 'valor_cif'] if col in df_cluster.columns]
            
            fig = px.scatter(
                df_cluster, x='pca1', y='pca2', color='cluster',
                color_continuous_scale=px.colors.qualitative.Vivid,
                hover_data=hover_data_existente,
                title=f'Visualización de {num_clusters} Clusters'
            )
            st.plotly_chart(fig, use_container_width=True)

# --- FUNCIÓN DE TABLA INTERACTIVA ---
def generar_tabla_resumen_interactiva(df):
    """Genera una tabla interactiva para la página de inteligencia con indicador de copia."""
    st.subheader("Tabla Resumen del Estado Actual de los Datos")
    st.info("Haz doble clic en cualquier celda para copiar su valor.")
    
    if df.empty:
        st.warning("No hay datos procesados para mostrar.")
        return

    resumen = df.groupby('filtro_principal').agg(
        conteo_registros=('filtro_principal', 'size'),
        valor_total_cif=('valor_cif', 'sum')
    ).sort_values(by='valor_total_cif', ascending=False).reset_index()

    resumen['valor_total_cif'] = resumen['valor_total_cif'].apply(lambda x: f"${x:,.0f}")
    resumen.rename(columns={
        "filtro_principal": "Filtro Principal (Estado Actual)", 
        "conteo_registros": "Nº Registros", 
        "valor_total_cif": "Valor Total CIF"
    }, inplace=True)

    gb = GridOptionsBuilder.from_dataframe(resumen)
    js_copy_cell = JsCode("""
        function(e) {
            navigator.clipboard.writeText(e.value).then(function() {
                e.api.flashCells({
                    rowNodes: [e.node],
                    columns: [e.column.colId],
                    flashDelay: 800
                });
            }).catch(function(err) {
                console.error('Error al copiar texto: ', err);
            });
        }
    """)
    gb.configure_grid_options(onCellDoubleClicked=js_copy_cell)
    
    AgGrid(
        resumen,
        gridOptions=gb.build(),
        height=400,
        width='100%',
        theme='streamlit',
        allow_unsafe_jscode=True
    )