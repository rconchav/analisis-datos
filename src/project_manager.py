# src/project_manager.py

import os
import json
import shutil

PROYECTOS_DIR = "proyectos"
PROYECTOS_FILE = "proyectos.json"

class ProjectManager:
    """
    Class to handle the creation, loading, and management of projects.
    """
    def __init__(self):
        self.proyectos_file_path = PROYECTOS_FILE
        self.proyectos_dir = PROYECTOS_DIR

    def cargar_proyectos(self):
        """Loads the project dictionary from proyectos.json."""
        if os.path.exists(self.proyectos_file_path):
            with open(self.proyectos_file_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {} # File is empty or corrupt
        return {}

    def guardar_proyectos(self, proyectos):
        """Saves the project dictionary to proyectos.json."""
        with open(self.proyectos_file_path, 'w', encoding='utf-8') as f:
            json.dump(proyectos, f, indent=4)

    def inicializar_proyecto(self, nombre_proyecto):
        """Creates the folder and file structure for a new project."""
        if not os.path.exists(self.proyectos_dir):
            os.makedirs(self.proyectos_dir)

        ruta_proyecto = os.path.join(self.proyectos_dir, nombre_proyecto)
        os.makedirs(os.path.join(ruta_proyecto, "data"), exist_ok=True)
        
        # Initialize empty config files for the project
        with open(os.path.join(ruta_proyecto, "config.json"), 'w') as f:
            json.dump({}, f)
        with open(os.path.join(ruta_proyecto, "diccionario.json"), 'w') as f:
            json.dump({}, f)
        with open(os.path.join(ruta_proyecto, "metadata.json"), 'w') as f:
            json.dump({"display_name": nombre_proyecto}, f)
        with open(os.path.join(ruta_proyecto, "segmentacion.json"), 'w') as f:
            json.dump({}, f)
        
        # Update the central project registry
        proyectos = self.cargar_proyectos()
        proyectos[nombre_proyecto] = ruta_proyecto
        self.guardar_proyectos(proyectos)

    def eliminar_proyecto(self, nombre_proyecto):
        """
        Deletes a project's folder and removes it from the registry.
        """
        proyectos = self.cargar_proyectos()
        if nombre_proyecto in proyectos:
            ruta_proyecto = proyectos.pop(nombre_proyecto) # Remove from dictionary
            
            # Physically delete the project folder
            if os.path.exists(ruta_proyecto):
                shutil.rmtree(ruta_proyecto)
            
            # Save the updated project list
            self.guardar_proyectos(proyectos)