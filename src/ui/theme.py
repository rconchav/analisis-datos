# src/ui/theme.py

import streamlit as st

# --- PALETAS DE COLORES PARA GRÁFICOS ---
PALETA_OSCURA = ['#46b1e2', '#95d5f7', '#5e7891', '#d1d4d6', '#a2d9f7', '#526a83']
PALETA_CLARA = ['#406855', '#6A8E7F', '#1A3636', '#93B5A8', '#DCE2DE', '#F8F9FA']

def configurar_tema(tema_actual: str):
    """
    Aplica el tema cambiando el atributo 'data-theme' en el body principal.
    """
    tema_js = "dark" if tema_actual == "Oscuro" else "light"
    
    # Este script busca el <body> principal y le asigna el tema.
    js_script = f"""
    <script>
        const body = window.parent.document.body;
        body.setAttribute('data-theme', '{tema_js}');
    </script>
    """
    st.components.v1.html(js_script, height=0)