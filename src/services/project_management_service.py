# src/services/project_management_service.py

import streamlit as st # Todavía necesario para st.session_state en servicio, pero se refactorizará
from src.data.project_storage import ProjectStorage

class ProjectManagerService:
    def __init__(self):
        self.storage = ProjectStorage()
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Inicializa las variables de sesión de Streamlit para la gestión de proyectos."""
        if 'proyecto_activo' not in st.session_state:
            st.session_state.proyecto_activo = None
        if 'proyecto_activo_nombre' not in st.session_state:
            st.session_state.proyecto_activo_nombre = None
        if 'confirmar_eliminacion' not in st.session_state:
            st.session_state.confirmar_eliminacion = None

    def get_all_projects(self) -> dict:
        """Retorna un diccionario de todos los proyectos disponibles."""
        return self.storage.load_all_projects_metadata()

    def get_project_display_name(self, project_id: str) -> str:
        """Retorna el nombre de visualización de un proyecto."""
        if not project_id:
            return "Ninguno"
        metadata = self.storage.load_project_metadata(project_id)
        return metadata.get("display_name", project_id)

    def create_project(self, project_id: str, display_name: str) -> bool:
        """Crea un nuevo proyecto y lo registra."""
        all_projects = self.storage.load_all_projects_metadata()
        if project_id in all_projects:
            st.error("Ya existe un proyecto con ese nombre.") # Temporalmente usamos st.error aquí
            return False

        try:
            self.storage.create_project_structure(project_id, display_name)
            all_projects[project_id] = self.storage._get_project_path(project_id) # Registra la ruta
            self.storage.save_all_projects_metadata(all_projects)
            self.set_active_project(project_id, display_name)
            st.success(f"Proyecto '{display_name}' creado y seleccionado.") # Temporalmente usamos st.success aquí
            return True
        except Exception as e:
            st.error(f"Error al crear el proyecto: {e}") # Temporalmente usamos st.error aquí
            return False

    def set_active_project(self, project_id: str, display_name: str = None):
        """Establece el proyecto activo en la sesión de Streamlit."""
        st.session_state.proyecto_activo = project_id
        st.session_state.proyecto_activo_nombre = display_name if display_name else self.get_project_display_name(project_id)
        st.cache_data.clear() # Limpia caché al cambiar de proyecto para recargar datos

    def delete_project(self, project_id: str) -> bool:
        """Elimina un proyecto y su estructura."""
        all_projects = self.storage.load_all_projects_metadata()
        if project_id not in all_projects:
            st.error("El proyecto no existe.") # Temporalmente usamos st.error aquí
            return False

        try:
            self.storage.delete_project_structure(project_id)
            del all_projects[project_id]
            self.storage.save_all_projects_metadata(all_projects)

            if st.session_state.proyecto_activo == project_id:
                st.session_state.proyecto_activo = None
                st.session_state.proyecto_activo_nombre = None

            st.toast(f"Proyecto '{self.get_project_display_name(project_id)}' eliminado.", icon="🗑️") # Temporalmente usamos st.toast aquí
            return True
        except Exception as e:
            st.error(f"Error al eliminar el proyecto: {e}") # Temporalmente usamos st.error aquí
            return False