# 🏠_Inicio.py

import streamlit as st
import os
import re
import json
import shutil

PROYECTOS_DIR = "proyectos"

st.set_page_config(layout="wide", page_title="Portal de Proyectos")

# --- Funciones de Gestión ---
def cargar_proyectos():
    if not os.path.exists(PROYECTOS_DIR): os.makedirs(PROYECTOS_DIR)
    lista_proyectos = []
    for nombre_carpeta in sorted(os.listdir(PROYECTOS_DIR)):
        path_proyecto = os.path.join(PROYECTOS_DIR, nombre_carpeta)
        if os.path.isdir(path_proyecto):
            path_meta = os.path.join(path_proyecto, "metadata.json")
            if os.path.exists(path_meta):
                with open(path_meta, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    lista_proyectos.append({
                        "id": nombre_carpeta,
                        "display_name": meta.get("display_name", nombre_carpeta.replace('_', ' ').title()),
                        "description": meta.get("description", "Sin descripción.")
                    })
    return lista_proyectos

def sanitizar_nombre_proyecto(nombre):
    nombre = nombre.strip().lower().replace(" ", "_")
    nombre = re.sub(r'(?u)[^-\w.]', '', nombre)
    return nombre

# --- Estado de la Sesión ---
if 'proyecto_activo' not in st.session_state: st.session_state.proyecto_activo = None
if 'confirmar_eliminacion' not in st.session_state: st.session_state.confirmar_eliminacion = None

# --- Interfaz de Usuario ---
st.title("📈 Plataforma de Análisis de Datos v3.0")

# --- NUEVA LÓGICA DE BARRA DE ESTADO / CREACIÓN ---
if st.session_state.proyecto_activo:
    # Si hay un proyecto activo, muestra el estado y el botón '+'
    col1, col2 = st.columns([4, 1])
    with col1:
        display_name = st.session_state.proyecto_activo.get("display_name", st.session_state.proyecto_activo.get("id"))
        st.success(f"**Proyecto Activo:** `{display_name}`", icon="✅")
    with col2:
        with st.popover("➕ Crear Otro Proyecto", use_container_width=True):
            # Formulario idéntico al de abajo
            with st.form("form_nuevo_proyecto_popover"):
                nombre_ingresado = st.text_input("Nombre del Nuevo Proyecto")
                descripcion_ingresada = st.text_area("Breve Descripción")
                submitted = st.form_submit_button("Crear")
                if submitted and nombre_ingresado:
                    # (Lógica de creación de proyecto)
                    nombre_sanitizado = sanitizar_nombre_proyecto(nombre_ingresado)
                    path_proyecto = os.path.join(PROYECTOS_DIR, nombre_sanitizado)
                    if os.path.exists(path_proyecto): st.error("Ya existe un proyecto con ese nombre.")
                    else:
                        os.makedirs(path_proyecto)
                        metadata = {"display_name": nombre_ingresado, "description": descripcion_ingresada}
                        with open(os.path.join(path_proyecto, 'metadata.json'), 'w', encoding='utf-8') as f: json.dump(metadata, f, indent=4)
                        # (Crear otros archivos vacíos)
                        st.session_state.proyecto_activo = {"id": nombre_sanitizado, "display_name": nombre_ingresado}
                        st.switch_page("pages/1_Configuracion.py")

else:
    # Si NO hay proyecto activo, muestra el formulario de creación directamente
    with st.container(border=True):
        st.subheader("➕ Crear tu Primer Proyecto")
        with st.form("form_nuevo_proyecto_main"):
            col1, col2 = st.columns(2)
            with col1:
                nombre_ingresado = st.text_input("Nombre del Proyecto", placeholder="Ej: Análisis Trimestral")
            with col2:
                descripcion_ingresada = st.text_input("Breve Descripción", placeholder="Ej: Importaciones de maquinaria agrícola Q1.")
            
            submitted = st.form_submit_button("Crear y Empezar a Configurar")
            if submitted and nombre_ingresado:
                # (Lógica de creación de proyecto - idéntica a la del popover)
                nombre_sanitizado = sanitizar_nombre_proyecto(nombre_ingresado)
                path_proyecto = os.path.join(PROYECTOS_DIR, nombre_sanitizado)
                if os.path.exists(path_proyecto): st.error("Ya existe un proyecto con ese nombre.")
                else:
                    os.makedirs(path_proyecto)
                    metadata = {"display_name": nombre_ingresado, "description": descripcion_ingresada}
                    with open(os.path.join(path_proyecto, 'metadata.json'), 'w', encoding='utf-8') as f: json.dump(metadata, f, indent=4)
                    with open(os.path.join(path_proyecto, 'config.json'), 'w') as f: json.dump({}, f)
                    with open(os.path.join(path_proyecto, 'diccionario.json'), 'w') as f: json.dump({}, f)
                    with open(os.path.join(path_proyecto, 'segmentacion.json'), 'w') as f: json.dump({}, f)
                    
                    st.session_state.proyecto_activo = {"id": nombre_sanitizado, "display_name": nombre_ingresado}
                    st.switch_page("pages/1_Configuracion.py")

st.markdown("---")
st.header("📚 Biblioteca de Proyectos")
proyectos = cargar_proyectos()

if not proyectos:
    st.info("Tu biblioteca está vacía. ¡Crea tu primer proyecto para empezar!")
else:
    # El listado de proyectos no cambia
    for proyecto in proyectos:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(f"📂 {proyecto['display_name']}")
                st.caption(proyecto['description'])
            with col2:
                btn_cols = st.columns(2)
                with btn_cols[0]:
                    if st.button("Cargar", key=f"load_{proyecto['id']}", use_container_width=True, type="primary"):
                        st.session_state.proyecto_activo = proyecto
                        st.session_state.confirmar_eliminacion = None
                        st.switch_page("pages/1_Configuracion.py")
                with btn_cols[1]:
                    if st.button("🗑️", key=f"delete_{proyecto['id']}", use_container_width=True):
                        st.session_state.confirmar_eliminacion = proyecto
                        st.rerun()

        if st.session_state.confirmar_eliminacion and st.session_state.confirmar_eliminacion['id'] == proyecto['id']:
            st.error(f"**ADVERTENCIA:** ¿Estás seguro de que quieres eliminar el proyecto '{proyecto['display_name']}'?")
            confirm_cols = st.columns(6)
            with confirm_cols[0]:
                if st.button("✅ Sí, eliminar", key=f"confirm_del_{proyecto['id']}", use_container_width=True):
                    shutil.rmtree(os.path.join(PROYECTOS_DIR, proyecto['id']))
                    if st.session_state.proyecto_activo and st.session_state.proyecto_activo['id'] == proyecto['id']:
                        st.session_state.proyecto_activo = None
                    st.session_state.confirmar_eliminacion = None
                    st.success(f"Proyecto eliminado.")
                    st.rerun()
            with confirm_cols[1]:
                if st.button("❌ Cancelar", key=f"cancel_del_{proyecto['id']}", use_container_width=True):
                    st.session_state.confirmar_eliminacion = None
                    st.rerun()