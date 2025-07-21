# configurador_solara.py

import solara
# --- CORRECCIÓN DEFINITIVA: Importar componentes desde sus submódulos correctos ---
from solara.components.file_drop import FileDrop
from solara import Card, Button, Select, InputText, Info, Success, H1, H3, H4, Markdown, Pre
import pandas as pd
import os
import json
import io
from pathlib import Path

# --- Constantes y Funciones de Gestión (Puro Python) ---
PROYECTOS_DIR = Path("proyectos")
PROYECTOS_DIR.mkdir(exist_ok=True)

def listar_proyectos():
    return [d.name for d in PROYECTOS_DIR.iterdir() if d.is_dir()]

def guardar_config_proyecto(nombre_proyecto, config):
    path_proyecto = PROYECTOS_DIR / nombre_proyecto
    path_proyecto.mkdir(exist_ok=True)
    with open(path_proyecto / 'config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

# --- Definición de los Pasos del Asistente ---
ROLES_MAPEADOS = [
    {'key': 'filtro_principal', 'label': 'Filtro Principal (ej: Marca)'},
    {'key': 'filtro_secundario_base', 'label': 'Filtro Secundario (ej: Producto)'},
    {'key': 'valor_numerico', 'label': 'Valor Numérico (ej: CIF)'},
    {'key': 'pais', 'label': 'País de Origen'},
    {'key': 'ano', 'label': 'Año'},
    {'key': 'mes', 'label': 'Mes'},
    {'key': 'dia', 'label': 'Día'}
]

# --- Estado Reactivo Global de la Aplicación ---
proyecto_activo = solara.reactive(None)
df_ejemplo = solara.reactive(None)
mapeo_actual = solara.reactive({})
mapeo_step = solara.reactive(0)

@solara.component
def Page():
    # Hooks de Estado (siempre al principio, sin condiciones)
    nuevo_proyecto_val, set_nuevo_proyecto = solara.use_state("")
    current_selection, set_current_selection = solara.use_state(None)

    # Lógica de la Interfaz
    with Card("Asistente de Configuración de Proyectos v3.0", margin=0):
        
        # Vista 1: Selección de Proyecto
        if proyecto_activo.value is None:
            Info("Selecciona un proyecto existente o crea uno nuevo para comenzar.")
            
            proyectos = listar_proyectos()
            Select(label="Cargar Proyecto Existente", values=[""] + proyectos, value=proyecto_activo)
            
            InputText("Nombre del Nuevo Proyecto", value=nuevo_proyecto_val, on_value=set_nuevo_proyecto)
            
            def on_create():
                if nuevo_proyecto_val and nuevo_proyecto_val not in proyectos:
                    guardar_config_proyecto(nuevo_proyecto_val, {})
                    proyecto_activo.value = nuevo_proyecto_val
            
            Button("Crear Proyecto", on_click=on_create, disabled=(not nuevo_proyecto_val))
        
        # Vistas 2 y 3: Carga de Archivo y Mapeo
        else:
            path_config = PROYECTOS_DIR / proyecto_activo.value / "config.json"
            
            try:
                with open(path_config, 'r') as f: config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                config = {}
            
            if config.get("mapeo_columnas"):
                Success(f"El proyecto '{proyecto_activo.value}' ya está configurado.")
                Info("Puedes cerrar esta herramienta y usar la aplicación de análisis, o seleccionar otro proyecto.")
                if Button("Configurar otro proyecto"):
                    proyecto_activo.value = None
                    mapeo_step.value = 0
                    mapeo_actual.value = {}
                    df_ejemplo.value = None

            elif df_ejemplo.value is None:
                # Vista 2: Cargar Archivo de Ejemplo
                def on_file(file_info):
                    content = file_info["data"]
                    df = pd.read_excel(io.BytesIO(content), nrows=10)
                    df_ejemplo.value = df
                    mapeo_step.value = 1

                Info(f"El proyecto '{proyecto_activo.value}' no está configurado. Sube un archivo de ejemplo.")
                FileDrop(label="Arrastra un archivo .xlsx aquí", on_file=on_file, lazy=False)

            else:
                # Vista 3: Asistente de Mapeo Secuencial
                if mapeo_step.value > len(ROLES_MAPEADOS):
                    H3("Mapeo Completado")
                    Pre(json.dumps(mapeo_actual.value, indent=2))
                    
                    def on_save():
                        guardar_config_proyecto(proyecto_activo.value, {"mapeo_columnas": mapeo_actual.value})
                        proyecto_activo.value = None
                        mapeo_step.value = 0
                        mapeo_actual.value = {}
                        df_ejemplo.value = None

                    Button("Guardar Configuración Definitiva", on_click=on_save, color="success")
                else:
                    current_role = ROLES_MAPEADOS[mapeo_step.value - 1]
                    if df_ejemplo.value is not None:
                        columnas = df_ejemplo.value.columns.tolist()
                        
                        H3(f"Paso {mapeo_step.value}/{len(ROLES_MAPEADOS)}: Asigna el rol para '{current_role['label']}'")
                        
                        def on_next():
                            if current_selection:
                                new_map = mapeo_actual.value.copy()
                                new_map[current_role['key']] = current_selection
                                mapeo_actual.value = new_map
                                set_current_selection(None)
                                mapeo_step.value += 1
                        
                        Select(label="Selecciona una columna...", values=[""] + columnas, value=current_selection, on_value=set_current_selection)
                        Button("Siguiente Paso", on_click=on_next, disabled=(not current_selection))
                        
                        Markdown("---")
                        H4("Mapeo Actual:")
                        Pre(json.dumps(mapeo_actual.value, indent=2))