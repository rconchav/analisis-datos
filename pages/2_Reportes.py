# pages/2_Reportes.py
# Este archivo contiene el contenido de la página de Reportes,
# encapsulado en una función para ser llamado por el router en 🏠_Inicio.py.

import streamlit as st
# No hay bloque sys.path aquí
# No hay llamada a configurar_pagina() aquí directamente, la hará el router

# Importa la configuración centralizada de la página (para sus utilidades si las tuviera)
from src.ui.app_config import configurar_pagina

def show_reportes_page():
    st.title("📊 Dashboard de Reportes (En Desarrollo - Router Manual)")
    st.info("Contenido de la página de Reportes. Funcionalidad en desarrollo.")