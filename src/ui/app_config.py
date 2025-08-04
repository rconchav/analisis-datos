# src/ui/app_config.py

import streamlit as st
import os
from src.ui.theme import configurar_tema

def configurar_pagina(titulo_pagina: str, layout: str = "wide"):
    st.set_page_config(layout=layout, page_title=titulo_pagina)

    # Inyección de fuentes
    estilos_fuentes = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;700&display=swap');
        [data-testid="stAppViewContainer"] {
            font-family: 'Figtree', sans-serif;
        }
        </style>
    """
    st.markdown(estilos_fuentes, unsafe_allow_html=True)

    # Carga de style.css
    path_css = os.path.join(".streamlit", "assets", "style.css") # Esto asumirá .streamlit está en la raíz
    if os.path.exists(path_css):
        with open(path_css) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Advertencia: No se encontró el archivo de estilos en la ruta: {path_css}")

    # Gestión del estado del tema
    if 'theme_toggle' not in st.session_state:
        st.session_state.theme_toggle = True

    tema_actual = "Oscuro" if st.session_state.theme_toggle else "Claro"
    configurar_tema(tema_actual)