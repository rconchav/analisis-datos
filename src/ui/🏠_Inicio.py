# src/ui/🏠_Inicio.py

import sys
import os

# --- INICIO: SOLUCIÓN PARA PYTHON PATH (MANTENER ACTIVA PARA DESARROLLO LOCAL) ---
# Calcula la raíz del proyecto (Fase_S) dinámicamente.
# __file__ es la ruta de este script.
# os.path.dirname(__file__) es src\ui\
# '..' es para subir un nivel (a src\)
# '..' es para subir otro nivel (a Fase_S\)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Si la raíz del proyecto no está ya en sys.path, la inserta al principio.
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- FIN: SOLUCIÓN PARA PYTHON PATH ---

import streamlit as st
import time

# Importa la configuración centralizada de la página (Ahora sí debería encontrar src.ui)
from src.ui.app_config import configurar_pagina

# Importa el nuevo servicio de gestión de proyectos
from src.services.project_management_service import ProjectManagerService


import streamlit as st
import time

# Importa la configuración centralizada de la página
from src.ui.app_config import configurar_pagina

# Importa el nuevo servicio de gestión de proyectos
from src.services.project_management_service import ProjectManagerService

# --- CONFIGURACIÓN INICIAL DE LA PÁGINA ---
# Llama a la función centralizada para configurar el título, layout y tema
configurar_pagina(titulo_pagina="Portal de Proyectos")

# --- INICIALIZAR EL GESTOR DE PROYECTOS (SERVICIO) ---
# Se instancia el servicio que maneja la lógica de negocio de los proyectos
project_manager_service = ProjectManagerService()

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("Acciones del Proyecto")
    
    # Muestra el proyecto activo y la opción de eliminar, gestionado por el servicio
    if st.session_state.proyecto_activo:
        # El nombre a mostrar ya viene actualizado por el servicio al activar el proyecto
        st.info(f"Activo: **{st.session_state.proyecto_activo_nombre}**")
        
        # Botón para activar la confirmación de eliminación
        if st.button("Eliminar Proyecto Activo", use_container_width=True, type="secondary"):
            # Almacena el ID del proyecto a eliminar en la sesión para el paso de confirmación
            st.session_state.confirmar_eliminacion = st.session_state.proyecto_activo
            st.rerun() # Dispara un rerun para mostrar la confirmación

# --- LAYOUT SUPERIOR: TÍTULO Y BOTÓN DE TEMA ---
col_titulo, col_boton_tema = st.columns([3, 1])
with col_titulo:
    st.title("🏠 Portal de Proyectos (Fase_S)")
with col_boton_tema:
    # El estado del tema se maneja en app_config.py, aquí solo el toggle
    def toggle_theme():
        st.session_state.theme_toggle = not st.session_state.theme_toggle
    texto_boton = "Modo Claro ⚪" if st.session_state.theme_toggle else "Modo Oscuro ⚫"
    st.button(texto_boton, on_click=toggle_theme, use_container_width=True)

# --- CONTENIDO PRINCIPAL ---
st.markdown("### Bienvenido al Dashboard de Análisis de Datos")
st.markdown("---")

with st.container(border=True):
    # Carga la lista de proyectos desde el servicio
    proyectos = project_manager_service.get_all_projects()

    col_header1, col_header2 = st.columns([2, 1])
    with col_header1:
        st.header("Gestión de Proyectos")
    with col_header2:
        st.markdown(f"<p style='text-align: right;'><b>{len(proyectos)}</b> Proyectos Existentes</p>", unsafe_allow_html=True)

    opcion_nuevo = "--- Crear Nuevo Proyecto ---"
    # Las opciones a mostrar en el selectbox, incluyendo la opción de crear nuevo
    opciones_display = [opcion_nuevo] + list(proyectos.keys())

    # Establece el índice pre-seleccionado si hay un proyecto activo
    index_activo = 0
    if st.session_state.proyecto_activo and st.session_state.proyecto_activo in opciones_display:
        index_activo = opciones_display.index(st.session_state.proyecto_activo)

    # Widget de selección de proyecto
    seleccion_usuario = st.selectbox(
        "Selecciona un Proyecto o Crea uno Nuevo",
        options=opciones_display,
        index=index_activo,
        key='selector_proyecto_widget'
    )

    # Lógica de sincronización de la selección del selectbox con el estado de la sesión
    proyecto_deseado_id = seleccion_usuario if seleccion_usuario != opcion_nuevo else None
    
    # Solo actualiza si la selección ha cambiado para evitar bucles de rerun innecesarios
    if st.session_state.proyecto_activo != proyecto_deseado_id:
        # El servicio maneja la activación del proyecto y la actualización de st.session_state
        if proyecto_deseado_id:
            project_manager_service.set_active_project(proyecto_deseado_id)
        else: # Si se seleccionó "Crear Nuevo Proyecto" o no hay selección
            st.session_state.proyecto_activo = None
            st.session_state.proyecto_activo_nombre = None
        st.rerun() # Dispara un rerun para reflejar el cambio de proyecto activo

    # Formulario para crear un nuevo proyecto, visible solo si no hay proyecto activo o se seleccionó la opción "Crear Nuevo"
    if not st.session_state.proyecto_activo:
        with st.form("nuevo_proyecto_form", clear_on_submit=True):
            nuevo_nombre_proyecto = st.text_input("Nombre del Nuevo Proyecto")
            if st.form_submit_button("Crear Proyecto ✨", type="primary", use_container_width=True):
                if nuevo_nombre_proyecto:
                    # Llama al servicio para crear el proyecto
                    if project_manager_service.create_project(nuevo_nombre_proyecto, nuevo_nombre_proyecto): # ID y display_name son iguales por ahora
                        st.rerun() # Dispara un rerun si la creación fue exitosa
                else:
                    st.error("El nombre del proyecto no puede estar vacío.")

# --- LÓGICA DE CONFIRMACIÓN DE ELIMINACIÓN ---
# Este bloque se activa si el usuario ha pulsado "Eliminar Proyecto Activo"
if st.session_state.confirmar_eliminacion:
    proyecto_para_borrar_id = st.session_state.confirmar_eliminacion
    nombre_display_borrar = project_manager_service.get_project_display_name(proyecto_para_borrar_id)
    
    st.error(f"¿Estás seguro de que quieres eliminar el proyecto **'{nombre_display_borrar}'**? Esta acción es irreversible.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sí, eliminar para siempre", type="primary", use_container_width=True):
            # Llama al servicio para eliminar el proyecto
            if project_manager_service.delete_project(proyecto_para_borrar_id):
                st.session_state.confirmar_eliminacion = None # Limpia el estado de confirmación
                time.sleep(1) # Pequeña pausa para que el toast de éxito se vea
                st.rerun()
    with col2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.confirmar_eliminacion = None # Limpia el estado de confirmación
            st.rerun()

# --- SECCIÓN DE SIGUIENTES PASOS ---
# Visible solo si un proyecto está activo
if st.session_state.proyecto_activo:
    nombre_display_activo = st.session_state.proyecto_activo_nombre
    st.success(f"Proyecto activo: **{nombre_display_activo}**")

    with st.container(border=True):
        st.markdown("#### Siguientes Pasos")
        
        # Verifica si existen datos procesados para el proyecto activo usando el servicio de almacenamiento
        existen_datos_procesados = not project_manager_service.storage.load_processed_data(st.session_state.proyecto_activo).empty

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cargar / Configurar Datos ⚙️", use_container_width=True):
                # Usar la ruta absoluta dentro de src/ui/
                st.switch_page("src/ui/1_Configuracion.py")
        with col2:
            # Habilita el botón de Reportes solo si hay datos procesados
            if st.button("Ver Reportes 📊", use_container_width=True, disabled=not existen_datos_procesados):
                # Usar la ruta absoluta dentro de src/ui/
                st.switch_page("src/ui/2_Reportes.py")

        # Mensaje informativo si no hay datos
        if not existen_datos_procesados:
            st.info("El siguiente paso es cargar y configurar los datos de tu proyecto.")