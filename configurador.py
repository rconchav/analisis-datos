# configurador.py

import dash
from dash import dcc, html, Input, Output, State, dash_table, callback, no_update
import dash_bootstrap_components as dbc
import pandas as pd
import os
import json
import io
import base64

# --- Inicialización de la App Dash ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# --- Constantes y Funciones de Gestión ---
PROYECTOS_DIR = "proyectos"
os.makedirs(PROYECTOS_DIR, exist_ok=True)

def listar_proyectos():
    return [d for d in os.listdir(PROYECTOS_DIR) if os.path.isdir(os.path.join(PROYECTOS_DIR, d))]

def guardar_config_proyecto(nombre_proyecto, config):
    path_proyecto = os.path.join(PROYECTOS_DIR, nombre_proyecto)
    os.makedirs(path_proyecto, exist_ok=True)
    with open(os.path.join(path_proyecto, 'config.json'), 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

# --- LAYOUT ESTÁTICO Y COMPLETO DE LA APLICACIÓN ---
app.layout = dbc.Container([
    # Store central para manejar el estado de la aplicación
    dcc.Store(id='store-state', data={
        'proyecto_activo': None,
        'mapeo': {},
        'df_columnas': [],
        'df_records': []
    }),

    html.H1("Asistente de Configuración de Proyectos v3.0"),
    html.Hr(),

    # --- Vista 1: Selección de Proyectos (siempre existe en el layout) ---
    html.Div(id='vista-proyectos', children=[
        dbc.Row([
            dbc.Col([
                html.H4("1. Selecciona o Crea un Proyecto"),
                dcc.Dropdown(id='dropdown-proyectos', options=listar_proyectos(), placeholder="Cargar Proyecto..."),
                dbc.Input(id='input-nuevo-proyecto', placeholder="Nombre del Nuevo Proyecto...", type="text", className="mt-2"),
                dbc.Button("Crear Proyecto", id='btn-crear-proyecto', color="primary", className="mt-2")
            ], width=6),
            dbc.Col(id='proyecto-activo-info', width=6, className="d-flex align-items-center")
        ])
    ]),

    # --- Vista 2: Asistente de Mapeo (siempre existe, pero se muestra/oculta) ---
    html.Div(id='vista-mapeo', style={'display': 'none'}, children=[
        html.Hr(),
        html.H4(id='titulo-asistente'),
        dcc.Upload(id='upload-data', children=html.Div(['Arrastra o ', html.A('Selecciona un Archivo de Ejemplo (.xlsx)')]),
                   style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px 0'}),
        html.Div(id='panel-interactivo') # Contenedor para la tabla y los controles
    ]),

    # --- Vista 3: Mensaje de Éxito Final ---
    html.Div(id='vista-exito', style={'display': 'none'})

], fluid=True)


# --- CALLBACKS ---

# Callback 1: Orquestador Principal de Vistas
@callback(
    Output('vista-proyectos', 'style'),
    Output('vista-mapeo', 'style'),
    Output('vista-exito', 'style'),
    Output('store-state', 'data'),
    Output('proyecto-activo-info', 'children'),
    Input('dropdown-proyectos', 'value'),
    Input('btn-crear-proyecto', 'n_clicks'),
    Input('btn-guardar-mapeo', 'n_clicks'),
    State('input-nuevo-proyecto', 'value'),
    State('store-state', 'data')
)
def orquestador_vistas(proyecto_sel, n_crear, n_guardar, nuevo_proyecto_val, state):
    ctx = dash.callback_context
    triggered_id = ctx.triggered_id if ctx.triggered else None

    # Lógica para crear o seleccionar un proyecto
    if triggered_id in ['dropdown-proyectos', 'btn-crear-proyecto']:
        proyecto_activo = None
        if triggered_id == 'dropdown-proyectos':
            proyecto_activo = proyecto_sel
        elif triggered_id == 'btn-crear-proyecto' and nuevo_proyecto_val:
            if nuevo_proyecto_val not in listar_proyectos():
                guardar_config_proyecto(nuevo_proyecto_val, {})
                proyecto_activo = nuevo_proyecto_val
        
        if proyecto_activo:
            state['proyecto_activo'] = proyecto_activo
            state['mapeo'] = {} # Resetear mapeo
    
    proyecto_activo = state.get('proyecto_activo')
    
    # Decidir qué vista mostrar
    if not proyecto_activo:
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, state, dbc.Alert("Ningún proyecto activo.", color="warning")
    
    path_config = os.path.join(PROYECTOS_DIR, proyecto_activo, 'config.json')
    try:
        with open(path_config, 'r') as f: config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): config = {}

    if triggered_id == 'btn-guardar-mapeo':
        guardar_config_proyecto(proyecto_activo, {"mapeo_columnas": state['mapeo']})
        return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}, state, dash.no_update

    if config.get("mapeo_columnas"):
        return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}, state, dash.no_update
    else:
        alert = dbc.Alert(f"Proyecto Activo: {proyecto_activo}", color="success")
        return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}, state, alert


# Callback 2: Lógica del Asistente de Mapeo
@callback(
    Output('panel-interactivo', 'children'),
    Output('store-state', 'data', allow_duplicate=True),
    Input('upload-data', 'contents'),
    Input('tabla-mapeo', 'active_cell'),
    State('radio-rol-seleccionado', 'value'),
    State('store-state', 'data'),
    prevent_initial_call=True
)
def asistente_interactivo(contents, active_cell, rol_seleccionado, state):
    df = None
    if contents:
        content_type, content_string = contents.split(',')
        df = pd.read_excel(io.BytesIO(base64.b64decode(content_string)), nrows=10)
        state['df_columnas'] = df.columns.tolist()
        state['df_records'] = df.to_dict('records')
    elif state.get('df_records'):
        df = pd.DataFrame(state['df_records'])

    if df is None:
        return html.P("Sube un archivo para comenzar."), no_update

    if active_cell:
        columna_clicada = state['df_columnas'][active_cell['column']]
        state['mapeo'][rol_seleccionado] = columna_clicada

    roles_a_mapear = ['Filtro Principal', 'Filtro Secundario', 'Valor Numérico', 'País', 'Año', 'Mes', 'Día']
    
    style_header_conditional = []
    colors = {'Filtro Principal': '#4F8BF9', 'Filtro Secundario': '#17A589', 'Valor Numérico': '#F39C12', 'País': '#9B59B6', 'Año': '#E74C3C', 'Mes': '#E74C3C', 'Día': '#E74C3C'}
    for rol, columna in state['mapeo'].items():
        style_header_conditional.append({'if': {'column_id': columna}, 'backgroundColor': colors.get(rol, '#34495E'), 'color': 'white'})
        
    panel = html.Div([
        dbc.Alert("La selección se realiza sobre la columna, no importa en qué fila hagas clic.", color="info"),
        html.H5("Paso 1: Selecciona un Rol"),
        dbc.RadioItems(id='radio-rol-seleccionado', options=roles_a_mapear, value=roles_a_mapear[0], inline=True, className="mb-3"),
        html.H5("Paso 2: Haz Clic en cualquier celda de la Columna Correspondiente"),
        dash_table.DataTable(
            id='tabla-mapeo',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_header={'fontWeight': 'bold'},
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header_conditional=style_header_conditional
        ),
        html.Hr(),
        dbc.Row([dbc.Col(html.H5("Mapeo Actual:"), width='auto'), dbc.Col(html.Pre(json.dumps(state['mapeo'], indent=2)))]),
        dbc.Button("Guardar Mapeo", id='btn-guardar-mapeo', color="success", className="mt-3")
    ])
    return panel, state

# Callback para el mensaje de éxito final
@callback(
    Output('vista-exito', 'children'),
    Input('store-state', 'data')
)
def render_exito(state):
    proyecto_activo = state.get('proyecto_activo')
    if proyecto_activo:
        path_config = os.path.join(PROYECTOS_DIR, proyecto_activo, 'config.json')
        try:
            with open(path_config, 'r') as f: config = json.load(f)
            if config.get("mapeo_columnas"):
                return dbc.Alert(f"¡Configuración para '{proyecto_activo}' guardada/cargada con éxito! Ya puedes cerrar esta ventana y usar la aplicación de Streamlit.", color="success")
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    return ""


# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    app.run(debug=True)