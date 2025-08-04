# 🏠_Inicio.py
# Este es el script principal de la aplicación Streamlit, ubicado en la raíz del proyecto.

# NO HAY Bloque sys.path ni import sys, os aquí. Streamlit lo maneja automáticamente cuando está en la raíz.

import streamlit as st
import time

# Importa la configuración centralizada de la página (desde src.ui)
from src.ui.app_config import configurar_pagina

# Importa el nuevo servicio de gestión de proyectos
from src.services.project_management_service import ProjectManagerService

# >>> LO NUEVO: Importa las funciones de contenido de las páginas desde la carpeta 'pages/' <<<
# Asegúrate de que estas funciones existan en los archivos correspondientes en 'pages/'
from pages.1_Configuracion import show_configuracion_page
from pages.2_Reportes import show_reportes_page
from pages.3_Analisis_Avanzado import show_analisis_avanzado_page
from pages.4_Inteligencia import show_inteligencia_page
from pages.5_Extractor_PDF import show_extractor_pdf_page
from pages.6_Centro_de_Calidad import show_centro_calidad_page


# --- INICIALIZAR EL GESTOR DE PROYECTOS (SERVICIO) ---
project_manager_service = ProjectManagerService()

# >>> LO NUEVO: Inicializar la variable de estado para el enrutamiento manual <<<
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home" # Página por defecto


# --- BARRA LATERAL ---
with st.sidebar:
    st.title("Navegación")
    # Botones de navegación con asignación de estado
    if st.button("🏠 Inicio", use_container_width=True, key="nav_home"):
        st.session_state.current_page = "home"
        st.rerun()
    if st.session_state.proyecto_activo: # Solo muestra opciones si hay un proyecto activo
        if st.button("⚙️ Configuración", use_container_width=True, key="nav_config"):
            st.session_state.current_page = "configuracion"
            st.rerun()
        # Se habilita solo si hay datos procesados (lógica del botón "Ver Reportes" en home)
        existen_datos_procesados_sidebar = not project_manager_service.storage.load_processed_data(st.session_state.proyecto_activo).empty
        if st.button("📊 Reportes", use_container_width=True, disabled=not existen_datos_procesados_sidebar, key="nav_reportes"):
            st.session_state.current_page = "reportes"
            st.rerun()
        if st.button("🔬 Análisis Avanzado", use_container_width=True, disabled=not existen_datos_procesados_sidebar, key="nav_analisis"):
            st.session_state.current_page = "analisis_avanzado"
            st.rerun()
        if st.button("🧠 Inteligencia", use_container_width=True, disabled=not existen_datos_procesados_sidebar, key="nav_inteligencia"):
            st.session_state.current_page = "inteligencia"
            st.rerun()
        if st.button("📄 Extractor PDF", use_container_width=True, key="nav_extractor"):
            st.session_state.current_page = "extractor_pdf"
            st.rerun()
        if st.button("✅ Centro de Calidad", use_container_width=True, disabled=not existen_datos_procesados_sidebar, key="nav_calidad"):
            st.session_state.current_page = "centro_calidad"
            st.rerun()

    st.markdown("---") # Separador para acciones del proyecto
    st.title("Acciones del Proyecto")
    # Resto de la lógica de sidebar para eliminar proyecto (sin cambios)
    if st.session_state.proyecto_activo:
        st.info(f"Activo: **{st.session_state.proyecto_activo_nombre}**")
        if st.button("Eliminar Proyecto Activo", use_container_width=True, type="secondary"):
            st.session_state.confirmar_eliminacion = st.session_state.proyecto_activo
            st.rerun()


# >>> LO NUEVO: Contenido principal condicional basado en current_page <<<
# Esto actúa como el "router" manual
if st.session_state.current_page == "home":
    # --- CONFIGURACIÓN DE PÁGINA PARA HOME (Se llama aquí para Home) ---
    configurar_pagina(titulo_pagina="Portal de Proyectos")

    # --- LAYOUT SUPERIOR: TÍTULO Y BOTÓN DE TEMA (Solo para Home) ---
    col_titulo, col_boton_tema = st.columns([3, 1])
    with col_titulo:
        st.title("🏠 Portal de Proyectos (Fase_S)")
    with col_boton_tema:
        def toggle_theme():
            st.session_state.theme_toggle = not st.session_state.theme_toggle
        texto_boton = "Modo Claro ⚪" if st.session_state.theme_toggle else "Modo Oscuro ⚫"
        st.button(texto_boton, on_click=toggle_theme, use_container_width=True)

    # --- CONTENIDO PRINCIPAL DE HOME ---
    st.markdown("### Bienvenido al Dashboard de Análisis de Datos")
    st.markdown("---")

    with st.container(border=True):
        proyectos = project_manager_service.get_all_projects()

        col_header1, col_header2 = st.columns([2, 1])
        with col_header1:
            st.header("Gestión de Proyectos")
        with col_header2:
            st.markdown(f"<p style='text-align: right;'><b>{len(proyectos)}</b> Proyectos Existentes</p>", unsafe_allow_html=True)

        opcion_nuevo = "--- Crear Nuevo Proyecto ---"
        opciones_display = [opcion_nuevo] + list(proyectos.keys())

        index_activo = 0
        if st.session_state.proyecto_activo and st.session_state.proyecto_activo in opciones_display:
            index_activo = opciones_display.index(st.session_state.proyecto_activo)

        seleccion_usuario = st.selectbox(
            "Selecciona un Proyecto o Crea uno Nuevo",
            options=opciones_display,
            index=index_activo,
            key='selector_proyecto_widget'
        )

        proyecto_deseado_id = seleccion_usuario if seleccion_usuario != opcion_nuevo else None

        if st.session_state.proyecto_activo != proyecto_deseado_id:
            if proyecto_deseado_id:
                project_manager_service.set_active_project(proyecto_deseado_id)
            else:
                st.session_state.proyecto_activo = None
                st.session_state.proyecto_activo_nombre = None
            st.rerun()

        if not st.session_state.proyecto_activo:
            with st.form("nuevo_proyecto_form", clear_on_submit=True):
                nuevo_nombre_proyecto = st.text_input("Nombre del Nuevo Proyecto")
                if st.form_submit_button("Crear Proyecto ✨", type="primary", use_container_width=True):
                    if nuevo_nombre_proyecto:
                        if project_manager_service.create_project(nuevo_nombre_proyecto, nuevo_nombre_proyecto):
                            st.rerun()
                    else:
                        st.error("El nombre del proyecto no puede estar vacío.")

    # --- LÓGICA DE CONFIRMACIÓN DE ELIMINACIÓN (MANTENER EN HOME) ---
    if st.session_state.confirmar_eliminacion:
        proyecto_para_borrar_id = st.session_state.confirmar_eliminacion
        nombre_display_borrar = project_manager_service.get_project_display_name(proyecto_para_borrar_id)

        st.error(f"¿Estás seguro de que quieres eliminar el proyecto **'{nombre_display_borrar}'**? Esta acción es irreversible.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí, eliminar para siempre", type="primary", use_container_width=True):
                if project_manager_service.delete_project(proyecto_para_borrar_id):
                    st.session_state.confirmar_eliminacion = None
                    time.sleep(1)
                    st.rerun()
        with col2:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.confirmar_eliminacion = None
                st.rerun()

    # --- SECCIÓN DE SIGUIENTES PASOS (Ajustado para el router) ---
    if st.session_state.proyecto_activo:
        nombre_display_activo = st.session_state.proyecto_activo_nombre
        st.success(f"Proyecto activo: **{nombre_display_activo}**")

        with st.container(border=True):
            st.markdown("#### Siguientes Pasos")

            existen_datos_procesados = not project_manager_service.storage.load_processed_data(st.session_state.proyecto_activo).empty

            col1, col2 = st.columns(2)
            with col1:
                # Botón para navegar a configuración
                if st.button("Cargar / Configurar Datos ⚙️", use_container_width=True, key="home_nav_config_btn"):
                    st.session_state.current_page = "configuracion"
                    st.rerun()
            with col2:
                # Botón para navegar a reportes
                if st.button("Ver Reportes 📊", use_container_width=True, disabled=not existen_datos_procesados, key="home_nav_reportes_btn"):
                    st.session_state.current_page = "reportes"
                    st.rerun()

            if not existen_datos_procesados:
                st.info("El siguiente paso es cargar y configurar los datos de tu proyecto.")

# >>> LO NUEVO: Lógica de renderizado condicional de páginas <<<
elif st.session_state.current_page == "configuracion":
    configurar_pagina(titulo_pagina="Configuración Dinámica")
    show_configuracion_page()

elif st.session_state.current_page == "reportes":
    configurar_pagina(titulo_pagina="Dashboard de Reportes")
    show_reportes_page()

elif st.session_state.current_page == "analisis_avanzado":
    configurar_pagina(titulo_pagina="Análisis Avanzado")
    show_analisis_avanzado_page()

elif st.session_state.current_page == "inteligencia":
    configurar_pagina(titulo_pagina="Centro de Inteligencia Global")
    show_inteligencia_page()

elif st.session_state.current_page == "extractor_pdf":
    configurar_pagina(titulo_pagina="Extractor de Tablas PDF")
    show_extractor_pdf_page()

elif st.session_state.current_page == "centro_calidad":
    configurar_pagina(titulo_pagina="Centro de Calidad de Datos")
    show_centro_calidad_page()