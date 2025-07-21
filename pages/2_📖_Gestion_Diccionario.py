# pages/2_📖_Gestion_Diccionario.py

import streamlit as st
import json
# --- MEJORA: Se añaden todas las importaciones necesarias ---
from diccionarios import (
    cargar_diccionario, agregar_filtro, eliminar_filtro_principal, 
    eliminar_filtro_secundario, editar_filtro_principal, editar_filtro_secundario
)

st.set_page_config(layout="wide", page_title="Gestión de Filtros")
st.title("📖 Gestión de Diccionarios de Filtros")

# --- Verificación de Proyecto Activo ---
if 'proyecto_activo' not in st.session_state or st.session_state.proyecto_activo is None:
    st.warning("Por favor, selecciona o crea un proyecto en la página de '🏠 Inicio' para comenzar.")
    st.stop()

proyecto_activo = st.session_state.proyecto_activo
st.info(f"**Editando el diccionario para el proyecto:** {proyecto_activo.title()}")

# --- Lógica de la Página ---
with st.expander("✍️ Agregar Nuevos Filtros Manualmente"):
    with st.form("form_agregar_filtro_gestion"):
        nuevo_principal = st.text_input("Nombre del Filtro Principal")
        nuevo_secundario = st.text_input("Nombre del Filtro Secundario")
        submitted = st.form_submit_button("Agregar al Diccionario")
        if submitted:
            # Ahora se pasa el proyecto activo a la función
            agregar_filtro(proyecto_activo, nuevo_principal, nuevo_secundario)
            st.rerun()

diccionario = cargar_diccionario(proyecto_activo)

if not diccionario:
    st.warning("El diccionario para este proyecto está vacío.")
else:
    json_string = json.dumps(diccionario, indent=4, ensure_ascii=False)
    st.download_button(
        label="📥 Descargar Diccionario Completo (.json)",
        data=json_string,
        file_name=f"diccionario_{proyecto_activo}.json",
        mime="application/json",
    )
    
    st.markdown("---")
    st.header("Filtros Existentes")

    for principal, secundarios in sorted(list(diccionario.items())):
        with st.expander(f"Filtro Principal: **{principal.title()}** ({len(secundarios)} filtros secundarios)"):
            
            st.subheader(f"Gestionar Filtro Principal '{principal.title()}'")
            col_edit, col_del = st.columns(2)
            with col_edit:
                nuevo_nombre_principal = st.text_input("Nuevo nombre", value=principal.title(), key=f"edit_principal_{principal}")
                if st.button("Guardar Nombre", key=f"btn_edit_principal_{principal}"):
                    if editar_filtro_principal(proyecto_activo, principal, nuevo_nombre_principal):
                        st.rerun()
            with col_del:
                if st.button("Eliminar Filtro Principal Completo", key=f"del_principal_{principal}", type="primary"):
                    if eliminar_filtro_principal(proyecto_activo, principal):
                        st.rerun()
            
            st.markdown("---")
            st.subheader("Filtros Secundarios Asociados")
            for secundario in sorted(secundarios):
                col_view, col_edit_sec, col_del_sec = st.columns([2, 2, 1])
                col_view.write(secundario.title())
                
                with col_edit_sec:
                    nuevo_nombre_secundario = st.text_input("Editar", value=secundario.title(), key=f"edit_sec_{principal}_{secundario}", label_visibility="collapsed")
                    if st.button("Guardar", key=f"btn_edit_sec_{principal}_{secundario}"):
                        if editar_filtro_secundario(proyecto_activo, principal, secundario, nuevo_nombre_secundario):
                            st.rerun()
                
                with col_del_sec:
                    if st.button("Eliminar", key=f"del_sec_{principal}_{secundario}"):
                        if eliminar_filtro_secundario(proyecto_activo, principal, secundario):
                            st.rerun()