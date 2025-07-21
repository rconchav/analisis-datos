# app.py

import streamlit as st
import os
import json
import pandas as pd
import re
from limpieza import cargar_y_limpiar_datos
from arancel import ARANCEL_DF, buscar_por_glosa
from graficos import (
    generar_tabla_resumen, generar_grafico_barras_mensual,
    generar_ranking_marcas, generar_pie_paises,
    generar_analisis_otras_marcas, generar_detalle_repuestos,
    generar_grafico_arancel
)
from utils import limpiar_codigo_arancel, to_excel, highlight_headers
from diccionarios import generar_diccionario_desde_datos, procesar_catalogos_externos
from file_manager import cargar_log_procesados, ha_sido_procesado, actualizar_log, guardar_log_procesados
from segmentador import cargar_reglas

# --- Configuración de la Página y Estado Inicial ---
st.set_page_config(layout="wide", page_title="Plataforma de Análisis")

def inicializar_estado():
    """Define el estado inicial de la aplicación."""
    if 'app_stage' not in st.session_state:
        st.session_state.app_stage = 'inicio'
    if 'proyecto_activo' not in st.session_state:
        st.session_state.proyecto_activo = None
    if 'df_ejemplo' not in st.session_state:
        st.session_state.df_ejemplo = None
    if 'df_final' not in st.session_state:
        st.session_state.df_final = None

inicializar_estado()

# --- Constantes y Funciones de Gestión ---
PROYECTOS_DIR = "proyectos"
os.makedirs(PROYECTOS_DIR, exist_ok=True)
os.makedirs("input", exist_ok=True)
os.makedirs("catalogos", exist_ok=True)
os.makedirs("datos", exist_ok=True)

def listar_proyectos():
    return [d for d in os.listdir(PROYECTOS_DIR) if os.path.isdir(os.path.join(PROYECTOS_DIR, d))]

def guardar_config_proyecto(nombre_proyecto, config):
    path_proyecto = os.path.join(PROYECTOS_DIR, nombre_proyecto)
    with open(os.path.join(path_proyecto, 'config.json'), 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def ejecutar_proceso_completo(proyecto):
    path_datos_procesados = f"proyectos/{proyecto}/datos_procesados.parquet"
    with st.spinner("Limpiando y analizando registros..."):
        df_procesado = cargar_y_limpiar_datos(proyecto)
    if df_procesado is not None and not df_procesado.empty:
        with st.spinner("Generando inteligencia de datos..."):
            procesar_catalogos_externos(proyecto)
            generar_diccionario_desde_datos(proyecto, df_procesado)
        df_procesado.to_parquet(path_datos_procesados)
        st.session_state.df_final = df_procesado
        st.session_state.app_stage = 'dashboard'
        st.cache_data.clear()
        st.success("¡Proceso completado!")
    else:
        st.error("El procesamiento de datos falló.")

# --- Renderizado de la Interfaz basado en el Estado ---

st.title("📈 Plataforma de Análisis de Datos")

# --- ETAPA 1: Inicio y Selección de Proyectos ---
if st.session_state.app_stage == 'inicio':
    st.header("Bienvenido")
    st.info(f"Proyecto Activo: **{st.session_state.proyecto_activo or 'Ninguno'}**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cargar un Proyecto Existente")
        proyecto_sel = st.selectbox("Selecciona un proyecto", options=[""] + listar_proyectos(), key="sel_proyecto")
        if st.button("Cargar Proyecto", disabled=(not proyecto_sel)):
            st.session_state.proyecto_activo = proyecto_sel
            path_config = os.path.join(PROYECTOS_DIR, proyecto_sel, 'config.json')
            try:
                with open(path_config, 'r') as f: config = json.load(f)
                if config.get("mapeo_columnas"):
                    st.session_state.app_stage = 'dashboard'
                else:
                    st.session_state.app_stage = 'mapeo'
            except (FileNotFoundError, json.JSONDecodeError):
                st.session_state.app_stage = 'mapeo'
            st.rerun()

    with col2:
        st.subheader("Crear un Nuevo Proyecto")
        with st.form("form_nuevo_proyecto", clear_on_submit=True):
            nombre_proyecto = st.text_input("Nombre del Nuevo Proyecto")
            if st.form_submit_button("Crear"):
                if nombre_proyecto and nombre_proyecto not in listar_proyectos():
                    st.session_state.proyecto_activo = nombre_proyecto
                    guardar_config_proyecto(nombre_proyecto, {})
                    st.session_state.app_stage = 'mapeo'
                    st.rerun()
                elif nombre_proyecto in listar_proyectos():
                    st.error("Ya existe un proyecto con ese nombre.")
                else:
                    st.error("El nombre del proyecto no puede estar vacío.")

# --- ETAPA 2: Asistente de Mapeo de Columnas ---
elif st.session_state.app_stage == 'mapeo':
    proyecto = st.session_state.proyecto_activo
    st.header(f"Asistente de Configuración para: '{proyecto}'")
    
    path_ejemplo = os.path.join(PROYECTOS_DIR, proyecto, 'ejemplo_mapeo.xlsx')
    if os.path.exists(path_ejemplo) and st.session_state.df_ejemplo is None:
        st.session_state.df_ejemplo = pd.read_excel(path_ejemplo, nrows=10)

    if st.session_state.df_ejemplo is None:
        archivo_subido = st.file_uploader("Sube un archivo de ejemplo (.xlsx) para iniciar", type="xlsx")
        if archivo_subido:
            with open(path_ejemplo, "wb") as f: f.write(archivo_subido.getbuffer())
            st.session_state.df_ejemplo = pd.read_excel(path_ejemplo, nrows=10)
            st.rerun()
    else:
        df = st.session_state.df_ejemplo
        columnas = [""] + df.columns.tolist()
        
        with st.form("form_mapeo"):
            st.info("Asigna un rol a cada columna. La tabla de abajo se resaltará para confirmar tu selección.")
            
            # Recopilar selecciones para el resaltado
            sel_fp = st.session_state.get('sel_fp_form', '')
            sel_fs = st.session_state.get('sel_fs_form', '')
            sel_val = st.session_state.get('sel_val_form', '')
            sel_pais = st.session_state.get('sel_pais_form', '')
            tipo_fecha = st.session_state.get('tipo_fecha_form', 'Columnas separadas')
            sel_ano = st.session_state.get('sel_ano_form', '')
            sel_mes = st.session_state.get('sel_mes_form', '')
            sel_dia = st.session_state.get('sel_dia_form', '')
            sel_fecha = st.session_state.get('sel_fecha_form', '')

            selections = {
                'principal': sel_fp, 'secundario': sel_fs, 'valor': sel_val, 'pais': sel_pais,
                'fecha': sel_fecha if tipo_fecha == "Una sola columna" else (sel_ano or sel_mes or sel_dia)
            }
            styled_df = df.style.pipe(highlight_headers, selections)
            st.dataframe(styled_df)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Roles de Filtro")
                st.selectbox("Rol: Filtro Principal", options=columnas, key="sel_fp_form")
                st.selectbox("Rol: Filtro Secundario / Segmentación", options=columnas, key="sel_fs_form")
            with col2:
                st.subheader("Roles de Datos")
                st.selectbox("Rol: Valor Numérico Principal", options=columnas, key="sel_val_form")
                st.selectbox("Rol: País de Origen", options=columnas, key="sel_pais_form")
            
            st.subheader("Configuración de Fechas")
            st.radio("Formato de Fecha", ("Columnas separadas", "Una sola columna"), key="tipo_fecha_form")
            if st.session_state.tipo_fecha_form == "Columnas separadas":
                c1, c2, c3 = st.columns(3)
                c1.selectbox("Columna AÑO", options=columnas, key="sel_ano_form")
                c2.selectbox("Columna MES", options=columnas, key="sel_mes_form")
                c3.selectbox("Columna DIA", options=columnas, key="sel_dia_form")
            else:
                st.selectbox("Columna de FECHA Única", options=columnas, key="sel_fecha_form")
            
            if st.form_submit_button("Guardar Mapeo"):
                mapeo = {
                    "filtro_principal": st.session_state.sel_fp_form, "filtro_secundario_base": st.session_state.sel_fs_form,
                    "segmentacion_base": st.session_state.sel_fs_form, "valor_numerico": st.session_state.sel_val_form,
                    "pais": st.session_state.sel_pais_form, "config_fecha": {'tipo': st.session_state.tipo_fecha_form}
                }
                if st.session_state.tipo_fecha_form == "Columnas separadas":
                    mapeo['config_fecha'].update({'ano': st.session_state.sel_ano_form, 'mes': st.session_state.sel_mes_form, 'dia': st.session_state.sel_dia_form})
                else:
                    mapeo['config_fecha']['fecha_completa'] = st.session_state.sel_fecha_form
                
                guardar_config_proyecto(proyecto, {"mapeo_columnas": mapeo})
                st.session_state.df_ejemplo = None
                st.session_state.app_stage = 'dashboard'
                st.success("¡Mapeo guardado!")
                st.rerun()

# --- ETAPA 3: Dashboard de Análisis ---
elif st.session_state.app_stage == 'dashboard':
    proyecto_activo = st.session_state.proyecto_activo
    path_datos_procesados = f"proyectos/{proyecto_activo}/datos_procesados.parquet"
    
    if os.path.exists(path_datos_procesados) and st.session_state.df_final is None:
        st.session_state.df_final = pd.read_parquet(path_datos_procesados)
    
    if st.session_state.df_final is None:
        st.header(f"Cargar Datos para '{proyecto_activo}'")
        if st.button("🔄 Ejecutar Proceso de Carga y Limpieza"):
            ejecutar_proceso_completo(proyecto_activo)
            st.rerun()
    else:
        df_final = st.session_state.df_final
        diccionario_filtros = cargar_diccionario(proyecto_activo)
        reglas_segmentacion = cargar_reglas(proyecto_activo)

        with st.sidebar:
            st.title(f"⚙️ Filtros: {proyecto_activo}")
            if st.button("<< Volver a Inicio", type="primary"):
                st.session_state.app_stage = 'inicio'
                st.session_state.proyecto_activo = None
                st.session_state.df_final = None
                st.rerun()
            st.markdown("---")

            filtros_secundarios_seleccionados = []
            filtro_principal_seleccionado = None
            segmentos_seleccionados = []
            
            if 'segmento_producto' in df_final.columns and not df_final['segmento_producto'].empty:
                st.subheader("Segmentación de Producto")
                opciones_segmento = sorted(list(df_final['segmento_producto'].unique()))
                segmentos_seleccionados = st.multiselect("Selecciona Segmento(s)", options=opciones_segmento, default=opciones_segmento)
                st.markdown("---")
            
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
            busqueda_glosa = st.text_input("Buscar por descripción de arancel:", key="busqueda_glosa_dash")
            codigos_seleccionados_glosa = []
            if busqueda_glosa:
                resultados_glosa = buscar_por_glosa(busqueda_glosa)
                if not resultados_glosa.empty:
                    opciones_glosa = {f"{row['codigo_arancel']} - {row['glosa_original'][:60]}...": row['codigo_arancel'] for _, row in resultados_glosa.iterrows()}
                    claves_seleccionadas_glosa = st.multiselect("Selecciona aranceles:", options=opciones_glosa.keys(), key="seleccion_glosa_dash")
                    codigos_seleccionados_glosa = [opciones_glosa[k] for k in claves_seleccionadas_glosa]
            
            busqueda_codigo = st.text_area("Ingresar código de arancel:", key="busqueda_codigo_dash")
            codigos_directos = []
            if busqueda_codigo:
                codigos_brutos = re.split('[,\n]', busqueda_codigo)
                codigos_directos = [limpiar_codigo_arancel(c) for c in codigos_brutos if c.strip()]
            codigos_a_filtrar = list(set(codigos_seleccionados_glosa + codigos_directos))

        df_filtrado = df_final.copy()
        if continentes_seleccionados: df_filtrado = df_filtrado[df_filtrado['continente'].isin(continentes_seleccionados)]
        if fecha_inicio and fecha_fin and fecha_inicio <= fecha_fin: df_filtrado = df_filtrado[(df_filtrado['fecha'] >= pd.to_datetime(fecha_inicio)) & (df_filtrado['fecha'] <= pd.to_datetime(fecha_fin))]
        if codigos_a_filtrar: df_filtrado = df_filtrado[df_filtrado['codigo_arancel'].isin(codigos_a_filtrar)]
        if segmentos_seleccionados: df_filtrado = df_filtrado[df_filtrado['segmento_producto'].isin(segmentos_seleccionados)]
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
                st.download_button(label="Descargar en Excel (.xlsx)", data=excel_data, file_name="analisis_filtrado.xlsx")
        
        if df_filtrado.empty:
            st.warning("No se encontraron datos para los filtros seleccionados.")
        else:
            st.markdown("---")
            generar_tabla_resumen(df_filtrado)
            generar_grafico_barras_mensual(df_filtrado)
            col_g1, col_g2 = st.columns(2)
            with col_g1: generar_ranking_marcas(df_filtrado)
            with col_g2: generar_pie_paises(df_filtrado)
            generar_grafico_arancel(df_filtrado)
            generar_detalle_repuestos(df_filtrado)
            generar_analisis_otras_marcas(df_filtrado)