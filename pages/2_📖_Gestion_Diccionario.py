# pages/2_📖_Gestion_Diccionario.py

import streamlit as st
import json
from diccionarios import (
    cargar_diccionario, agregar_filtro, eliminar_filtro_principal, 
    eliminar_filtro_secundario, editar_filtro_principal, editar_filtro_secundario,
    listar_perfiles_guardados, guardar_perfil_como, cargar_perfil, resetear_diccionario_activo
)

st.set_page_config(layout="wide", page_title="Gestión de Diccionarios y Filtros")
st.title("📖 Gestión de Diccionarios y Filtros")

# --- Sección de Gestión de Perfiles ---
st.header("Perfiles de Diccionario")
st.info("Guarda el estado de tu diccionario actual como un perfil para reutilizarlo en el futuro, o carga un perfil existente.")

perfiles = listar_perfiles_guardados()
col1, col2 = st.columns(2)

with col1:
    perfil_a_cargar = st.selectbox("Cargar un perfil existente", options=[""] + perfiles, index=0, help="Selecciona un perfil guardado para que sea el diccionario de trabajo actual.")
    if st.button("Cargar Perfil", disabled=(not perfil_a_cargar)):
        if cargar_perfil(perfil_a_cargar):
            st.cache_data.clear()
            st.rerun()

with col2:
    nuevo_nombre_perfil = st.text_input("Guardar diccionario actual como:", help="Dale un nombre al diccionario actual para guardarlo como un perfil (ej: Maquinaria, Alimentos).")
    if st.button("Guardar como Perfil", disabled=(not nuevo_nombre_perfil)):
        if guardar_perfil_como(nuevo_nombre_perfil):
            st.rerun()

if st.button("🔴 Resetear Diccionario Activo", help="Borra todo el contenido del diccionario actual para empezar un nuevo análisis desde cero."):
    resetear_diccionario_activo()
    st.cache_data.clear()
    st.rerun()

st.markdown("---")

# --- Sección de Edición del Diccionario Activo ---
st.header("Editar Diccionario Activo")
diccionario_activo = cargar_diccionario()

if not diccionario_activo:
    st.warning("El diccionario activo está vacío. Procesa algunos datos en la página principal o carga un perfil para empezar.")

with st.expander("✍️ Agregar Nuevos Filtros Manualmente al Diccionario Activo"):
    with st.form("form_agregar_filtro"):
        nuevo_principal = st.text_input("Nombre del Filtro Principal")
        nuevo_secundario = st.text_input("Nombre del Filtro Secundario")
        submitted = st.form_submit_button("Agregar al Diccionario")
        if submitted:
            agregar_filtro(nuevo_principal, nuevo_secundario)
            st.rerun()

st.subheader("Filtros Existentes en el Diccionario Activo")
if diccionario_activo:
    for principal, secundarios in sorted(list(diccionario_activo.items())):
        with st.expander(f"Filtro Principal: **{principal.title()}** ({len(secundarios)} filtros secundarios)"):
            
            st.subheader(f"Gestionar Filtro Principal '{principal.title()}'")
            col_edit, col_del = st.columns(2)
            with col_edit:
                nuevo_nombre_principal = st.text_input("Nuevo nombre", value=principal.title(), key=f"edit_principal_{principal}")
                if st.button("Guardar Nombre", key=f"btn_edit_principal_{principal}"):
                    if editar_filtro_principal(principal, nuevo_nombre_principal):
                        st.rerun()
            with col_del:
                if st.button("Eliminar Filtro Principal Completo", key=f"del_principal_{principal}", type="primary"):
                    if eliminar_filtro_principal(principal):
                        st.rerun()
            
            st.markdown("---")
            st.subheader("Filtros Secundarios Asociados")
            for secundario in sorted(secundarios):
                col_view, col_edit_sec, col_del_sec = st.columns([2, 2, 1])
                col_view.write(secundario.title())
                
                with col_edit_sec:
                    nuevo_nombre_secundario = st.text_input("Editar", value=secundario.title(), key=f"edit_sec_{principal}_{secundario}", label_visibility="collapsed")
                    if st.button("Guardar", key=f"btn_edit_sec_{principal}_{secundario}"):
                        if editar_filtro_secundario(principal, secundario, nuevo_nombre_secundario):
                            st.rerun()
                
                with col_del_sec:
                    if st.button("Eliminar", key=f"del_sec_{principal}_{secundario}"):
                        if eliminar_filtro_secundario(principal, secundario):
                            st.rerun()