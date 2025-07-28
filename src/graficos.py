# src/graficos.py

import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode

def _configurar_grafico_altair(chart, titulo: str, paleta_colores: list):
    """Aplica configuraciones comunes a los gráficos de Altair."""
    return chart.properties(
        title=alt.Title(
            text=titulo,
            anchor='start',
            fontSize=18,
            fontWeight=600,
            dy=-10
        ),
        height=350
    ).configure_axis(
        labelFontSize=11,
        titleFontSize=13
    ).configure_legend(
        titleFontSize=12,
        labelFontSize=11,
        orient='bottom'
    ).configure_range(
        category=paleta_colores
    ).configure_view(
        strokeWidth=0
    )

def generar_tabla_resumen(df, metricas_seleccionadas):
    """Muestra el total de registros y un resumen de las métricas clave."""
    st.subheader("Resumen General de Datos")
    
    metricas_validas = [m for m in metricas_seleccionadas if m in df.columns]
    if not metricas_validas:
        st.warning("No se encontraron métricas válidas para mostrar en el resumen.")
        return
        
    num_columnas = len(metricas_validas) + 1
    cols = st.columns(num_columnas)

    cols[0].metric("Total Registros", f"{len(df):,}")

    for i, metrica in enumerate(metricas_validas):
        valor_total = df[metrica].sum()
        is_currency = any(sub in metrica.lower() for sub in ['usd', 'valor', 'precio', 'cif'])
        format_string = "${:,.0f}" if is_currency else "{:,.0f}"
        cols[i+1].metric(f"Total {metrica}", format_string.format(valor_total))

def generar_grafico_pareto(df, filtro, metrica, paleta):
    """Genera un gráfico de Pareto dinámico con el color del 80% actualizado."""
    if filtro not in df.columns or metrica not in df.columns:
        st.warning(f"No se pudo generar el gráfico de Pareto. Verifica que las columnas '{filtro}' y '{metrica}' existan.")
        return
    
    pareto_data = df.groupby(filtro)[metrica].sum().reset_index().nlargest(15, metrica)
    pareto_data = pareto_data.sort_values(by=metrica, ascending=False)
    
    total_metrica = df[metrica].sum()
    if total_metrica == 0: return

    pareto_data['Acumulado'] = pareto_data[metrica].cumsum()
    pareto_data['Porcentaje Acumulado'] = 100 * pareto_data['Acumulado'] / total_metrica
    pareto_data['Grupo'] = np.where(pareto_data['Porcentaje Acumulado'] <= 80, 'Representa el 80%', 'Resto')

    color_principal = '#DD2F1C'
    color_secundario = paleta[2] if len(paleta) > 2 else '#f58518'
    color_linea = paleta[3] if len(paleta) > 3 else '#e45756'

    base = alt.Chart(pareto_data).encode(x=alt.X(f'{filtro}:N', sort='-y', title=filtro))
    
    barras = base.mark_bar().encode(
        y=alt.Y(f'{metrica}:Q', title=metrica),
        tooltip=[alt.Tooltip(f'{filtro}:N', title=filtro), alt.Tooltip(f'{metrica}:Q', title=metrica, format='$,.0f'), alt.Tooltip('Porcentaje Acumulado:Q', title='% Acumulado', format='.1f')],
        color=alt.Color('Grupo:N',
            scale=alt.Scale(domain=['Representa el 80%', 'Resto'], range=[color_principal, color_secundario]),
            legend=alt.Legend(title="Grupo Pareto")
        )
    )
    
    linea = base.mark_line(color=color_linea, point=True).encode(
        y=alt.Y('Porcentaje Acumulado:Q', title='Porcentaje Acumulado (%)', axis=alt.Axis(format='.0f')),
        tooltip=[alt.Tooltip('Porcentaje Acumulado:Q', title='% Acumulado', format='.2f')]
    )
    
    chart = alt.layer(barras, linea).resolve_scale(y='independent')
    st.altair_chart(_configurar_grafico_altair(chart, f"Análisis de Pareto por {filtro}", paleta), use_container_width=True)

def generar_grafico_temporal(df, fecha_col, metrica_col, frecuencia, paleta):
    """Genera un gráfico de evolución temporal dinámico."""
    freq_map = {'Mensual': 'ME', 'Trimestral': 'QE', 'Anual': 'YE'}
    df_temporal = df.set_index(fecha_col).resample(freq_map[frecuencia])[metrica_col].sum().reset_index()
    base = alt.Chart(df_temporal).encode(x=alt.X(f'{fecha_col}:T', title=fecha_col, axis=alt.Axis(format="%b %Y")))
    linea = base.mark_line(point=True).encode(
        y=alt.Y(f'{metrica_col}:Q', title=metrica_col, axis=alt.Axis(format='$,.0f')),
        tooltip=[alt.Tooltip(f'{fecha_col}:T', title='Periodo', format='%Y-%m'), alt.Tooltip(f'{metrica_col}:Q', title=metrica_col, format='$,.0f')]
    )
    st.altair_chart(_configurar_grafico_altair(linea, f"Evolución de {metrica_col} ({frecuencia})", paleta), use_container_width=True)

def generar_grafico_ranking(df, eje_x, eje_y, paleta):
    """Genera un gráfico de ranking dinámico, limitado al Top 15."""
    ranking_data = df.groupby(eje_x)[eje_y].sum().reset_index().nlargest(15, eje_y)
    chart = alt.Chart(ranking_data).mark_bar().encode(
        x=alt.X(f'{eje_y}:Q', title=eje_y),
        y=alt.Y(f'{eje_x}:N', title=eje_x, sort='-x'),
        tooltip=[alt.Tooltip(f'{eje_x}:N', title=eje_x), alt.Tooltip(f'{eje_y}:Q', title=eje_y, format='{",.0f"}')]
    )
    st.altair_chart(_configurar_grafico_altair(chart, f"Top 15 {eje_x} por {eje_y}", paleta), use_container_width=True)

def generar_grafico_sunburst(df, path, values, title, paleta):
    """Genera un gráfico Sunburst (Nested Pie) dinámico usando Plotly."""
    st.subheader(title)
    fig = px.sunburst(df, path=path, values=values, color=values, color_continuous_scale=px.colors.sequential.deep)
    fig.update_layout(margin=dict(t=30, l=10, r=10, b=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

def generar_grafico_treemap(df, path, values, title):
    """Genera un gráfico Treemap dinámico usando Plotly."""
    if not all(col in df.columns for col in path) or values not in df.columns:
        st.warning("Verifica que las dimensiones y la métrica seleccionadas para el Treemap existan en los datos.")
        return
    st.subheader(title)
    fig = px.treemap(df, path=path, values=values, color=values, 
                   color_continuous_scale=px.colors.sequential.Blues_r)
    fig.update_layout(margin=dict(t=50, l=10, r=10, b=10), title_text=title)
    st.plotly_chart(fig, use_container_width=True)

def generar_mapa_distribucion(df, lat_col, lon_col, size_col=None):
    """
    Genera un mapa de puntos. El tamaño se escala a un radio en metros
    para una correcta visualización en st.map.
    """
    st.subheader("Mapa de Distribución Geográfica")

    if lat_col not in df.columns or lon_col not in df.columns:
        st.info("No se han configurado columnas de latitud y longitud.")
        return

    cols_to_use = [lat_col, lon_col]
    if size_col and size_col in df.columns:
        cols_to_use.append(size_col)

    df_mapa = df[cols_to_use].copy().dropna()

    if not df_mapa.empty:
        df_mapa.rename(columns={lat_col: 'lat', lon_col: 'lon'}, inplace=True)

        size_param = None
        if size_col and size_col in df_mapa.columns:
            df_mapa[size_col] = pd.to_numeric(df_mapa[size_col], errors='coerce')
            df_mapa.dropna(subset=[size_col], inplace=True)

            min_val = df_mapa[size_col].min()
            max_val = df_mapa[size_col].max()

            if max_val > min_val:
                # --- LÓGICA DE ESCALADO A METROS ---
                # Se escala a un rango de radios visibles (ej: 50km a 500km)
                min_radius_meters = 50000
                max_radius_meters = 500000

                df_mapa['size_scaled'] = min_radius_meters + \
                    ((df_mapa[size_col] - min_val) / (max_val - min_val)) * (max_radius_meters - min_radius_meters)

                size_param = 'size_scaled'

        st.map(df_mapa, latitude='lat', longitude='lon', size=size_param)
    else:
        st.warning("⚠️ No hay datos geográficos para mostrar con los filtros actuales.")

def generar_grafico_clusters(df_clusters, paleta):
    """Visualiza los resultados del clustering de forma interactiva."""
    if 'PC1' in df_clusters.columns and 'PC2' in df_clusters.columns:
        chart = alt.Chart(df_clusters).mark_circle(size=80, opacity=0.7).encode(
            x=alt.X('PC1:Q', title='Componente Principal 1', scale=alt.Scale(zero=False)),
            y=alt.Y('PC2:Q', title='Componente Principal 2', scale=alt.Scale(zero=False)),
            color=alt.Color('Cluster:N', title='Cluster'),
            tooltip=[col for col in df_clusters.columns if col not in ['PC1', 'PC2']]
        ).interactive()
        st.altair_chart(_configurar_grafico_altair(chart, "Visualización de Clusters (PCA)", paleta), use_container_width=True)

def generar_regresion_lineal(df, x_var, y_var, paleta):
    """Genera un gráfico de dispersión con una línea de regresión."""
    st.subheader(f"Regresión Lineal: {y_var} vs. {x_var}")
    chart = alt.Chart(df).mark_circle(size=60, opacity=0.5).encode(
        x=alt.X(f'{x_var}:Q', scale=alt.Scale(zero=False)),
        y=alt.Y(f'{y_var}:Q', scale=alt.Scale(zero=False)),
        tooltip=[x_var, y_var]
    ).interactive()
    linea_regresion = chart.transform_regression(x_var, y_var).mark_line(color=paleta[1] if len(paleta) > 1 else 'orange')
    st.altair_chart(chart + linea_regresion, use_container_width=True)

def generar_proyeccion_temporal(df, fecha_col, metrica_col, periodos, paleta):
    """Genera una proyección lineal simple para una serie temporal."""
    st.subheader(f"Proyección Lineal de {metrica_col}")
    df_temporal = df.set_index(fecha_col).resample('ME')[metrica_col].sum().reset_index()
    df_temporal['time'] = (df_temporal[fecha_col] - df_temporal[fecha_col].min()).dt.days

    coef = np.polyfit(df_temporal['time'], df_temporal[metrica_col], 1)
    poly1d_fn = np.poly1d(coef)

    ultima_fecha = df_temporal[fecha_col].max()
    fechas_futuras = pd.to_datetime([ultima_fecha + pd.DateOffset(months=i) for i in range(1, periodos + 2)])
    df_futuro = pd.DataFrame({fecha_col: fechas_futuras})
    df_futuro['time'] = (df_futuro[fecha_col] - df_temporal[fecha_col].min()).dt.days
    df_futuro['proyeccion'] = poly1d_fn(df_futuro['time'])
    
    chart_hist = alt.Chart(df_temporal).mark_line().encode(x=f'{fecha_col}:T', y=f'{metrica_col}:Q')
    chart_proy = alt.Chart(df_futuro).mark_line(strokeDash=[5,5], color=paleta[1] if len(paleta) > 1 else 'orange').encode(x=f'{fecha_col}:T', y='proyeccion:Q')
    st.altair_chart((chart_hist + chart_proy).properties(title=f"Proyección a {periodos} meses").interactive(), use_container_width=True)

def generar_heatmap_correlacion(df, metricas):
    """Genera un heatmap de correlación entre las métricas."""
    st.subheader("Heatmap de Correláción de Métricas")
    corr_matrix = df[metricas].corr()
    fig = px.imshow(corr_matrix, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
    fig.update_layout(title="Correlación entre Variables Numéricas")
    st.plotly_chart(fig, use_container_width=True)

def generar_tabla_interactiva(df):
    """Muestra un DataFrame usando AgGrid con copiado de celda."""
    gb = GridOptionsBuilder.from_dataframe(df)
    js_copy_cell = JsCode("function(e) { if(e.value != null) { navigator.clipboard.writeText(e.value); } }")
    gb.configure_grid_options(onCellDoubleClicked=js_copy_cell)
    gb.configure_default_column(editable=False, groupable=True)
    gb.configure_side_bar()
    grid_options = gb.build()
    AgGrid(df, gridOptions=grid_options, height=400, width='100%', update_mode=GridUpdateMode.MODEL_CHANGED, allow_unsafe_jscode=True, theme="alpine")