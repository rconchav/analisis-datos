# app.py

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
from diccionarios import (
    generar_diccionario_desde_datos, procesar_catalogos_externos, 
    agregar_marca_modelo, cargar_diccionario, eliminar_marca, 
    eliminar_modelo, editar_nombre_marca
)
from file_manager import cargar_log_procesados, ha_sido_procesado, actualizar_log, guardar_log_procesados

# --- Configuración de la Página y Funciones de Caché ---
st.set_page_config(layout="wide", page_title="📈 Análisis de Importaciones")

@st.cache_data
def cargar_diccionario_marcas():
    """Carga el diccionario de marcas y modelos desde el archivo JSON."""
    return cargar_diccionario()

# --- Título Principal y Creación de Carpetas ---
st.title("📈 Análisis de Importaciones")
os.makedirs("input", exist_ok=True)
os.makedirs("catalogos", exist_ok=True)

# --- Definición de Pestañas (Tabs) ---
tab_carga, tab_gestion, tab_analisis = st.tabs([
    "🗂️ Carga y Procesamiento", 
    "📖 Gestión del Diccionario", 
    "📊 Análisis Principal"
])

# --- Pestaña de Carga y Procesamiento ---
with tab_carga:
    log_procesados = cargar_log_procesados()
    st.header("Carga y Configuración de Datos")

    with st.expander("📁 Cargar Archivos", expanded=True):
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
                        with open(os.path.join("input", uploaded_file.name), "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        actualizar_log(uploaded_file.name, uploaded_file.size, log_seccion_input)
                        nuevos_archivos += 1
                if nuevos_archivos > 0:
                    st.success(f"{nuevos_archivos} nuevo(s) archivo(s) de importación guardado(s).")
                    log_procesados["input"] = log_seccion_input
                    guardar_log_procesados(log_procesados)
                else:
                    st.info("No se agregaron archivos nuevos de importación.")

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
                        with open(os.path.join("catalogos", uploaded_file.name), "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        actualizar_log(uploaded_file.name, uploaded_file.size, log_seccion_catalogos)
                        nuevos_catalogos += 1
                if nuevos_catalogos > 0:
                    st.success(f"{nuevos_catalogos} nuevo(s) catálogo(s) guardado(s).")
                    log_procesados["catalogos"] = log_seccion_catalogos
                    guardar_log_procesados(log_procesados)
                else:
                    st.info("No se agregaron catálogos nuevos.")

    st.markdown("---")
    with st.expander("✍️ Agregar Marca y Modelo Manualmente"):
        st.subheader("Añadir al Diccionario de Referencia")
        with st.form("form_agregar_modelo"):
            nueva_marca = st.text_input("Nombre de la Marca")
            nuevo_modelo = st.text_input("Nombre del Modelo")
            submitted = st.form_submit_button("Agregar al Diccionario")
            if submitted:
                agregar_marca_modelo(nueva_marca, nuevo_modelo)

    st.markdown("---")
    st.header("Procesar y Analizar")
    st.info("Una vez que hayas cargado/agregado todos los datos, haz clic en este botón para iniciar o actualizar el análisis.")

    if st.button("🔄 Ejecutar Proceso Completo de Datos"):
        if 'df_final' in st.session_state: del st.session_state['df_final']
        
        with st.spinner("Limpiando y analizando registros de importación..."):
            df_procesado = cargar_y_limpiar_datos()

        if df_procesado is not None and not df_procesado.empty:
            st.session_state['df_final'] = df_procesado
            
            with st.spinner("Enriqueciendo diccionario con catálogos externos..."):
                procesar_catalogos_externos()
            
            with st.spinner("Generando diccionario final desde los datos procesados..."):
                generar_diccionario_desde_datos(df_procesado)
            
            st.success("¡Proceso completado! Ve a la pestaña 'Análisis Principal'.")
            st.cache_data.clear()
        else:
            st.error("El procesamiento de datos falló o no generó datos.")

# --- Pestaña de Gestión del Diccionario ---
with tab_gestion:
    st.header("📖 Gestión del Diccionario de Marcas y Modelos")
    
    diccionario = cargar_diccionario_marcas()
    
    if not diccionario:
        st.info("El diccionario está vacío. Procesa algunos datos en la primera pestaña para generarlo.")
    else:
        json_string = json.dumps(diccionario, indent=4, ensure_ascii=False)
        st.download_button(
            label="📥 Descargar Diccionario Completo (.json)",
            data=json_string,
            file_name="diccionario_referencia.json",
            mime="application/json",
        )
        
        st.markdown("---")

        for marca, modelos in sorted(list(diccionario.items())):
            with st.expander(f"Marca: **{marca}** ({len(modelos)} modelos)"):
                
                st.subheader(f"Editar o Eliminar Marca '{marca}'")
                col_edit, col_del = st.columns(2)
                with col_edit:
                    nuevo_nombre_marca = st.text_input("Nuevo nombre", key=f"edit_marca_{marca}")
                    if st.button("Guardar Nombre", key=f"btn_edit_marca_{marca}"):
                        if editar_nombre_marca(marca, nuevo_nombre_marca):
                            st.cache_data.clear()
                            st.rerun()
                with col_del:
                    if st.button("Eliminar Marca Completa", key=f"del_marca_{marca}", type="primary"):
                        if eliminar_marca(marca):
                            st.cache_data.clear()
                            st.rerun()
                
                st.markdown("---")
                st.subheader("Modelos Asociados")
                for modelo in sorted(modelos):
                    col_mod, col_del_mod = st.columns([4, 1])
                    col_mod.write(modelo)
                    if col_del_mod.button("Eliminar", key=f"del_modelo_{marca}_{modelo}"):
                        if eliminar_modelo(marca, modelo):
                            st.cache_data.clear()
                            st.rerun()

# --- Pestaña de Análisis ---
with tab_analisis:
    st.header("Visualización y Análisis de Datos")

    if 'df_final' not in st.session_state:
        st.info("⬅️ Primero debes cargar y procesar los archivos en la pestaña 'Carga y Configuración'.")
    else:
        df_final = st.session_state['df_final']
        diccionario_marcas = cargar_diccionario_marcas()

        with st.sidebar:
            st.header("Filtros Globales 📄")
            modelos_seleccionados = []
            if diccionario_marcas:
                st.subheader("Filtro por Producto")
                marcas_disponibles = ["Todas"] + sorted(list(diccionario_marcas.keys()))
                marca_seleccionada_filtro = st.selectbox("Selecciona una Marca", options=marcas_disponibles)
                if marca_seleccionada_filtro != "Todas":
                    modelos_disponibles = sorted(diccionario_marcas.get(marca_seleccionada_filtro, []))
                    modelos_seleccionados = st.multiselect("Selecciona Modelo(s)", options=modelos_disponibles)
                st.markdown("---")

            lista_continentes = sorted([c for c in df_final['continente'].unique() if c])
            continentes_seleccionados = st.multiselect("Selecciona Continente(s):", options=lista_continentes, default=lista_continentes)
            min_fecha = df_final['fecha'].min().date()
            max_fecha = df_final['fecha'].max().date()
            fecha_inicio = st.date_input("Fecha de inicio", value=min_fecha, min_value=min_fecha, max_value=max_fecha)
            fecha_fin = st.date_input("Fecha de fin", value=max_fecha, min_value=min_fecha, max_value=max_fecha)

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
            if codigos_a_filtrar:
                st.success(f"{len(codigos_a_filtrar)} código(s) arancelario(s) aplicados.")

        df_filtrado = df_final.copy()
        
        if continentes_seleccionados:
            df_filtrado = df_filtrado[df_filtrado['continente'].isin(continentes_seleccionados)]
        if fecha_inicio <= fecha_fin:
            df_filtrado = df_filtrado[(df_filtrado['fecha'] >= pd.to_datetime(fecha_inicio)) & (df_filtrado['fecha'] <= pd.to_datetime(fecha_fin))]
        if codigos_a_filtrar:
            df_filtrado = df_filtrado[df_filtrado['codigo_arancel'].isin(codigos_a_filtrar)]
        if modelos_seleccionados:
            patron_modelos = '|'.join(map(re.escape, modelos_seleccionados))
            df_filtrado = df_filtrado[df_filtrado['producto_limpio'].str.contains(patron_modelos, case=False, na=False)]

        st.subheader(f"Análisis para: {', '.join(continentes_seleccionados)}")
        st.caption(f"Período: `{fecha_inicio.strftime('%d-%m-%Y')}` a `{fecha_fin.strftime('%d-%m-%Y')}`")
        
        if not df_filtrado.empty:
            with st.expander("📥 Descargar Datos Filtrados", expanded=False):
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
            st.markdown("---")
            generar_grafico_barras_mensual(df_filtrado)
            st.markdown("---")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                generar_ranking_marcas(df_filtrado)
            with col_g2:
                generar_pie_paises(df_filtrado)
            st.markdown("---")
            generar_grafico_arancel(df_filtrado)
            st.markdown("---")
            generar_detalle_repuestos(df_filtrado)
            st.markdown("---")
            generar_analisis_otras_marcas(df_filtrado)