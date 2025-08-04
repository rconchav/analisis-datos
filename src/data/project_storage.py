# src/data/project_storage.py

import os
import json
import shutil
import pandas as pd
import pyarrow # Asegura que pandas puede manejar parquet
import pyarrow.parquet as pq # Para operaciones específicas de Parquet

PROYECTOS_DIR = "proyectos"
PROYECTOS_FILE = "proyectos.json" # Archivo para listar todos los proyectos

class ProjectStorage:
    def __init__(self):
        self.proyectos_file_path = PROYECTOS_FILE
        self.proyectos_dir = PROYECTOS_DIR
        os.makedirs(self.proyectos_dir, exist_ok=True) # Asegura que la carpeta 'proyectos' exista

    def _get_project_path(self, project_id: str) -> str:
        """Retorna la ruta completa a la carpeta de un proyecto."""
        return os.path.join(self.proyectos_dir, project_id)

    def _get_project_file_path(self, project_id: str, file_name: str) -> str:
        """Retorna la ruta completa a un archivo dentro de la carpeta del proyecto."""
        return os.path.join(self._get_project_path(project_id), file_name)

    # --- Gestión de la lista global de proyectos ---
    def load_all_projects_metadata(self) -> dict:
        """Carga el diccionario de todos los proyectos registrados."""
        if os.path.exists(self.proyectos_file_path):
            with open(self.proyectos_file_path, 'r', encoding='utf-8') as f:
                try: return json.load(f)
                except json.JSONDecodeError: return {}
        return {}

    def save_all_projects_metadata(self, projects_metadata: dict):
        """Guarda el diccionario de todos los proyectos registrados."""
        with open(self.proyectos_file_path, 'w', encoding='utf-8') as f:
            json.dump(projects_metadata, f, indent=4, ensure_ascii=False)

    # --- Gestión de la estructura de carpetas de un proyecto individual ---
    def create_project_structure(self, project_id: str, display_name: str):
        """Crea la estructura de carpetas y archivos base para un nuevo proyecto."""
        ruta_proyecto = self._get_project_path(project_id)

        os.makedirs(os.path.join(ruta_proyecto, "data"), exist_ok=True)
        os.makedirs(os.path.join(ruta_proyecto, "reprocesos"), exist_ok=True) # Carpeta para archivos de error

        # Inicializa archivos de configuración vacíos específicos del proyecto
        with open(self._get_project_file_path(project_id, "diccionario.json"), 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        with open(self._get_project_file_path(project_id, "metadata.json"), 'w', encoding='utf-8') as f:
            json.dump({"display_name": display_name}, f, indent=4, ensure_ascii=False)
        with open(self._get_project_file_path(project_id, "log_procesados.json"), 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4, ensure_ascii=False)

    def delete_project_structure(self, project_id: str):
        """Elimina la carpeta completa de un proyecto."""
        ruta_proyecto = self._get_project_path(project_id)
        if os.path.exists(ruta_proyecto):
            shutil.rmtree(ruta_proyecto)

    # --- Gestión de archivos específicos de un proyecto ---

    def load_project_metadata(self, project_id: str) -> dict:
        """Carga el archivo metadata.json de un proyecto."""
        path = self._get_project_file_path(project_id, "metadata.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                try: return json.load(f)
                except json.JSONDecodeError: return {}
        return {}

    def save_project_metadata(self, project_id: str, metadata: dict):
        """Guarda el archivo metadata.json de un proyecto."""
        path = self._get_project_file_path(project_id, "metadata.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

    def load_project_dictionary(self, project_id: str) -> dict:
        """Carga el diccionario.json de mapeo de un proyecto."""
        path = self._get_project_file_path(project_id, "diccionario.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                try: return json.load(f)
                except json.JSONDecodeError: return {}
        return {}

    def save_project_dictionary(self, project_id: str, data: dict):
        """Guarda el diccionario.json de mapeo de un proyecto."""
        path = self._get_project_file_path(project_id, "diccionario.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_processed_data(self, project_id: str) -> pd.DataFrame:
        """Carga el DataFrame de datos procesados (parquet) de un proyecto."""
        path = self._get_project_file_path(project_id, "datos_procesados.parquet")
        if os.path.exists(path):
            try:
                return pd.read_parquet(path)
            except Exception as e:
                # st.error(f"Error al cargar datos procesados: {e}") # No usar st en capa data
                return pd.DataFrame() # Retorna DF vacío en caso de error
        return pd.DataFrame()

    def save_processed_data(self, project_id: str, df: pd.DataFrame):
        """Guarda el DataFrame de datos procesados (parquet) de un proyecto."""
        path = self._get_project_file_path(project_id, "datos_procesados.parquet")
        df.to_parquet(path, index=False) # index=False para no guardar el índice de pandas

    def load_processing_log(self, project_id: str) -> list:
        """Lee el log_procesados.json de un proyecto."""
        log_path = self._get_project_file_path(project_id, "log_procesados.json")
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def save_processing_log(self, project_id: str, log_data: list):
        """Escribe en el log de archivos, ya sea reemplazando o anexando."""
        log_path = self._get_project_file_path(project_id, "log_procesados.json")

        # Añadir el nuevo registro y asegurarse de que no haya duplicados exactos
        # Este es un copy-paste del código original, que se refactorizará en la lógica del flujo de datos
        # Por ahora, simplemente sobrescribe el log si no se maneja "anexar" desde la UI

        # TODO: La lógica de anexar/reemplazar el log debe ser manejada por la capa de servicio
        # que orquesta el procesamiento de datos, no directamente por el storage.
        # Aquí, solo guardamos el listado que nos pasa el servicio.

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=4, ensure_ascii=False)