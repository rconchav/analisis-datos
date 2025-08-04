# src/data/static_data_manager.py

import os
import json
import streamlit as st # Necesario para st.cache_data y st.warning

@st.cache_data
def cargar_mapeo_paises_estatico():
    """
    Carga los datos de mapeo de países, continentes y coordenadas.
    """
    path_paises = os.path.join("datos", "paises_continentes.json") # Ruta relativa a la raíz del proyecto
    pais_continente = {}
    reemplazo_paises = {}
    pais_coordenadas = {}

    if os.path.exists(path_paises):
        try:
            with open(path_paises, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "nombre" in item:
                        nombre_canonico = item["nombre"].upper()
                        if "continente" in item:
                            pais_continente[nombre_canonico] = item["continente"]
                        reemplazo_paises[nombre_canonico] = nombre_canonico
                        for alias in item.get("alias", []):
                            reemplazo_paises[alias.upper()] = nombre_canonico
                        if "latitud" in item and "longitud" in item:
                            pais_coordenadas[nombre_canonico] = {
                                "lat": item["latitud"],
                                "lon": item["longitud"]
                            }
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Usar st.error aquí es temporal, en un servicio real se usaría un logger estándar
            st.error(f"Error al cargar paises_continentes.json: {e}. Asegúrate de que el archivo exista y esté bien formado.")
            return {}, {}, {}
    return pais_continente, reemplazo_paises, pais_coordenadas


@st.cache_data
def cargar_arancel_json_estatico():
    """
    Función para cargar el JSON de clasificación arancelaria.
    """
    path_arancel = os.path.join("datos", "arancel_clasificacion.json") # Ruta relativa a la raíz del proyecto
    if os.path.exists(path_arancel):
        try:
            with open(path_arancel, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Usar st.error aquí es temporal, en un servicio real se usaría un logger estándar
            st.error(f"Error al cargar arancel_clasificacion.json: {e}. Asegúrate de que el archivo exista y esté bien formado.")
            return {}
    return {}

def buscar_descripcion_arancel_estatico(codigo_arancel: str) -> str:
    """
    Busca la descripción de un código arancelario en la estructura JSON anidada.
    """
    arancel_data = cargar_arancel_json_estatico()
    if not arancel_data:
        return "N/A (Datos arancelarios no cargados)"

    codigo_str = str(codigo_arancel)

    # Itera a través de cada partida principal en el JSON
    for partida_info in arancel_data.values():
        # Busca el código dentro de las subcategorías de la partida
        if codigo_str in partida_info.get("subcategorias", {}):
            return partida_info["subcategorias"][codigo_str]

    return "Descripción no encontrada"