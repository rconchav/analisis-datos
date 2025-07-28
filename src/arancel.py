# src/arancel.py

import streamlit as st
import os
import json

@st.cache_data
def _cargar_arancel_json():
    """Función interna para cargar el JSON y cachearlo."""
    path_arancel = os.path.join("datos", "arancel_clasificacion.json")
    if os.path.exists(path_arancel):
        with open(path_arancel, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def buscar_descripcion_arancel(codigo_arancel: str) -> str:
    """
    Busca la descripción de un código arancelario en la estructura JSON anidada.
    """
    arancel_data = _cargar_arancel_json()
    if not arancel_data:
        st.warning("No se pudo cargar el archivo de clasificación arancelaria.")
        return "N/A"

    codigo_str = str(codigo_arancel)

    # Itera a través de cada partida principal en el JSON
    for partida_info in arancel_data.values():
        # Busca el código dentro de las subcategorías de la partida
        if codigo_str in partida_info.get("subcategorias", {}):
            return partida_info["subcategorias"][codigo_str]

    return "Descripción no encontrada"