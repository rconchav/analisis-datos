# src/file_manager.py

import streamlit as st
import pandas as pd
import os
import json

def cargar_y_procesar_archivos(uploaded_files, proyecto_id, desde_ruta=False):
    """
    Carga y combina archivos Excel.
    
    Args:
        uploaded_files (list): Lista de archivos subidos por st.file_uploader.
        proyecto_id (str): El ID del proyecto activo.
        desde_ruta (bool): Si es True, lee los archivos desde la carpeta del proyecto
                             en lugar de los archivos subidos.
    """
    lista_dfs = []
    path_data = os.path.join("proyectos", proyecto_id, "data")
    os.makedirs(path_data, exist_ok=True)

    if not desde_ruta:
        # Modo 1: Procesar archivos recién subidos
        if not uploaded_files or uploaded_files[0] is None:
            st.warning("No se ha subido ningún archivo para procesar.")
            return pd.DataFrame()

        # Limpia archivos anteriores para no mezclar datos
        for f in os.listdir(path_data):
            os.remove(os.path.join(path_data, f))
            
        for uploaded_file in uploaded_files:
            file_path = os.path.join(path_data, uploaded_file.name)
            try:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                df = pd.read_excel(file_path)
                lista_dfs.append(df)
            except Exception as e:
                st.error(f"Error al procesar el archivo '{uploaded_file.name}': {e}")

    else:
        # Modo 2: Re-procesar archivos existentes desde la ruta
        if not os.path.exists(path_data) or not os.listdir(path_data):
            st.error("No se encontraron archivos de datos existentes para re-procesar.")
            return pd.DataFrame()

        for nombre_archivo in os.listdir(path_data):
            if nombre_archivo.endswith('.xlsx'):
                ruta_completa = os.path.join(path_data, nombre_archivo)
                try:
                    df = pd.read_excel(ruta_completa)
                    lista_dfs.append(df)
                except Exception as e:
                    st.error(f"Error al leer el archivo existente '{nombre_archivo}': {e}")

    if not lista_dfs:
        return pd.DataFrame()

    return pd.concat(lista_dfs, ignore_index=True)
    # Concatenar todos los DataFrames
    try:
        df_combinado = pd.concat(lista_dfs, ignore_index=True)
        return df_combinado
    except Exception as e:
        st.error(f"Error al combinar los archivos: {e}")
        return pd.DataFrame()