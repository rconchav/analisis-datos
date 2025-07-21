# 3_룰_Gestion_de_Segmentos.py

import streamlit as st
from segmentador import cargar_reglas, agregar_regla, eliminar_regla

st.set_page_config(layout="wide", page_title="Gestión de Segmentos")

st.title("룰 Gestión de Reglas de Segmentación")

# Verificar si un proyecto está activo
if 'proyecto_activo' not in st.session_state or st.session_state.proyecto_activo is None:
    st.warning("Por favor, selecciona o crea un proyecto en la página de '🏠 Inicio' para comenzar.")
    st.stop()

proyecto_activo = st.session_state.proyecto_activo
st.info(f"**Editando las reglas para el proyecto:** {proyecto_activo.title()}")
st.markdown("Define las categorías y las palabras clave para clasificar los productos. Los cambios se aplicarán la próxima vez que proceses los datos.")

reglas = cargar_reglas(proyecto_activo)

col_form, col_view = st.columns(2)

with col_form:
    st.subheader("Agregar Nueva Regla")
    with st.form("form_segmentacion"):
        categorias_existentes = ["NUEVA CATEGORÍA"] + sorted(list(reglas.keys()))
        categoria_seleccionada = st.selectbox("Elige una Categoría Existente o crea una Nueva", options=categorias_existentes)
        
        nueva_categoria = ""
        if categoria_seleccionada == "NUEVA CATEGORÍA":
            nueva_categoria = st.text_input("Nombre de la Nueva Categoría (ej: INSUMOS)").upper()

        nueva_keyword = st.text_input("Palabra Clave a agregar (ej: aceite)").lower()
        
        submitted = st.form_submit_button("Agregar Regla")
        if submitted:
            categoria_final = nueva_categoria if nueva_categoria else categoria_seleccionada
            agregar_regla(proyecto_activo, categoria_final, nueva_keyword)
            st.rerun()

with col_view:
    st.subheader("Reglas Actuales")
    if not reglas:
        st.write("No hay reglas definidas.")
    else:
        for categoria, keywords in sorted(reglas.items()):
            with st.expander(f"Categoría: **{categoria}** ({len(keywords)} palabras clave)"):
                for keyword in sorted(keywords):
                    col_key, col_del = st.columns([3,1])
                    col_key.write(f"• {keyword}")
                    if col_del.button("Eliminar", key=f"del_regla_{categoria}_{keyword}"):
                        eliminar_regla(proyecto_activo, categoria, keyword)
                        st.rerun()