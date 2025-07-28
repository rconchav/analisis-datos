# 🏠_Inicio.py

import streamlit as st
import os
import shutil
import sys
import json
import time

# --- CÓDIGO DE CONFIGURACIÓN DE RUTA ---
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# --- Importaciones de Módulos Propios ---
from src.utils import configurar_pagina
from src.project_manager import ProjectManager
from src.theme import configurar_tema

# --- CONFIGURACIÓN INICIAL DE LA PÁGINA ---
configurar_pagina(titulo_pagina="Portal de Proyectos")

# --- INICIALIZAR EL GESTOR DE PROYECTOS ---
project_manager = ProjectManager()

# --- ESTADO DE LA SESIÓN Y TEMA ---
if 'theme_toggle' not in st.session_state:
    st.session_state.theme_toggle = True

if 'session_initialized' not in st.session_state:
    st.session_state.proyecto_activo = None
    st.session_state.proyecto_activo_nombre = None
    st.session_state.confirmar_eliminacion = None
    st.session_state.session_initialized = True

tema_actual = "Oscuro" if st.session_state.theme_toggle else "Claro"
configurar_tema(tema_actual)

# --- FUNCIÓN CALLBACK ---
def actualizar_proyecto_activo():
    seleccion = st.session_state.selector_proyecto
    if seleccion == "--- Crear Nuevo Proyecto ---":
        st.session_state.proyecto_activo = None
        st.session_state.proyecto_activo_nombre = None
        return

    st.session_state.proyecto_activo = seleccion
    metadata_path = os.path.join("proyectos", seleccion, "metadata.json")
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        st.session_state.proyecto_activo_nombre = metadata.get("display_name", seleccion)
    except (FileNotFoundError, json.JSONDecodeError):
        st.session_state.proyecto_activo_nombre = seleccion

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("Acciones del Proyecto")
    if st.session_state.proyecto_activo:
        st.info(f"Activo: **{st.session_state.proyecto_activo_nombre}**")
        if st.button("Eliminar Proyecto Activo", use_container_width=True, type="secondary"):
            st.session_state.confirmar_eliminacion = st.session_state.proyecto_activo
            st.rerun()

# --- LAYOUT SUPERIOR: TÍTULO Y BOTÓN DE TEMA ---
col_titulo, col_boton_tema = st.columns([3, 1])
with col_titulo:
    st.title("🏠 Portal de Proyectos")
with col_boton_tema:
    def cambiar_tema():
        st.session_state.theme_toggle = not st.session_state.theme_toggle

    texto_boton = "Modo Claro ⚪" if st.session_state.theme_toggle else "Modo Oscuro ⚫"
    st.button(texto_boton, on_click=cambiar_tema, use_container_width=True)

# --- CONTENIDO PRINCIPAL ---
st.markdown("### Bienvenido al Dashboard de Análisis de Datos")
st.markdown("---")

with st.container(border=True):
    proyectos = project_manager.cargar_proyectos()

    col_header1, col_header2 = st.columns([2, 1])
    with col_header1:
        st.header("Gestión de Proyectos")
    with col_header2:
        st.markdown(f"<p style='text-align: right;'><b>{len(proyectos)}</b> Proyectos Existentes</p>", unsafe_allow_html=True)

    opcion_nuevo = "--- Crear Nuevo Proyecto ---"
    opciones_display = [opcion_nuevo] + list(proyectos.keys())

    if st.session_state.proyecto_activo:
        try:
            index_activo = opciones_display.index(st.session_state.proyecto_activo)
        except ValueError:
            index_activo = 0
    else:
        index_activo = 0

    st.selectbox(
        "Selecciona un Proyecto o Crea uno Nuevo",
        options=opciones_display,
        index=index_activo,
        key='selector_proyecto',
        on_change=actualizar_proyecto_activo,
    )

    if st.session_state.get('selector_proyecto') == opcion_nuevo:
        with st.form("nuevo_proyecto_form", clear_on_submit=True):
            nuevo_nombre_proyecto = st.text_input("Nombre del Nuevo Proyecto")
            if st.form_submit_button("Crear Proyecto ✨", type="primary", use_container_width=True):
                if nuevo_nombre_proyecto:
                    if nuevo_nombre_proyecto not in proyectos:
                        project_manager.inicializar_proyecto(nuevo_nombre_proyecto)
                        st.session_state.proyecto_activo = nuevo_nombre_proyecto 
                        st.success(f"Proyecto '{nuevo_nombre_proyecto}' creado y seleccionado.")
                        st.rerun()
                    else:
                        st.error("Ya existe un proyecto con ese nombre.")

# --- SECCIÓN DE SIGUIENTES PASOS ---
if st.session_state.proyecto_activo:
    nombre_display = st.session_state.proyecto_activo_nombre or st.session_state.proyecto_activo
    st.success(f"Proyecto activo: **{nombre_display}**")

    with st.container(border=True):
        st.markdown("#### Siguientes Pasos")

        path_datos_procesados = os.path.join("proyectos", st.session_state.proyecto_activo, "datos_procesados.parquet")
        existen_datos = os.path.exists(path_datos_procesados)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cargar / Configurar Datos ⚙️", use_container_width=True):
                st.switch_page("pages/1_Configuracion.py")
        with col2:
            if st.button("Ver Reportes 📊", use_container_width=True, disabled=not existen_datos):
                st.switch_page("pages/2_Reportes.py")

        if not existen_datos:
            st.info("El siguiente paso es cargar y configurar los datos de tu proyecto.")

# --- LÓGICA DE CONFIRMACIÓN DE ELIMINACIÓN ---
if st.session_state.confirmar_eliminacion:
    proyecto_para_borrar = st.session_state.confirmar_eliminacion
    nombre_display_borrar = ""

    proyectos_cargados = project_manager.cargar_proyectos()
    ruta_proyecto = proyectos_cargados.get(proyecto_para_borrar)
    if ruta_proyecto:
        metadata_path = os.path.join(ruta_proyecto, "metadata.json")
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            nombre_display_borrar = metadata.get("display_name", proyecto_para_borrar)
        except:
            nombre_display_borrar = proyecto_para_borrar
    else:
        nombre_display_borrar = proyecto_para_borrar

    st.error(f"¿Estás seguro de que quieres eliminar el proyecto **'{nombre_display_borrar}'**? Esta acción no se puede deshacer.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sí, eliminar para siempre", type="primary", use_container_width=True):
            if proyecto_para_borrar in project_manager.cargar_proyectos():
                project_manager.eliminar_proyecto(proyecto_para_borrar)
                st.success(f"Proyecto '{nombre_display_borrar}' eliminado.")

                st.session_state.confirmar_eliminacion = None
                st.session_state.proyecto_activo = None
                st.session_state.proyecto_activo_nombre = None
                time.sleep(1)
                st.rerun()
    with col2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.confirmar_eliminacion = None
            st.rerun()