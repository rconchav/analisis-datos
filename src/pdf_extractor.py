# src/pdf_extractor.py

import camelot
import streamlit as st
import io

# Cacheamos la función para que no se re-ejecute en cada interacción de Streamlit
# si el archivo no ha cambiado.
@st.cache_data
def extraer_tablas_de_pdf(archivo_pdf_bytes):
    """
    Usa Camelot para extraer todas las tablas de un archivo PDF.
    
    Args:
        archivo_pdf_bytes (BytesIO): El contenido del archivo PDF subido.

    Returns:
        list: Una lista de DataFrames de pandas, donde cada DataFrame es una tabla.
              Devuelve una lista vacía si no se encuentran tablas o hay un error.
    """
    try:
        # Camelot necesita una ruta a un archivo, así que guardamos temporalmente el contenido en un archivo en memoria
        # Para evitar problemas con rutas, pasamos el contenido directamente a un buffer
        with io.BytesIO(archivo_pdf_bytes.read()) as f:
            # Usamos flavor='lattice' que es mejor para tablas con líneas claras.
            # Se podría añadir lógica para probar también con 'stream' si 'lattice' falla.
            tablas = camelot.read_pdf(f, flavor='lattice', pages='all')
        
        # Camelot devuelve un objeto TableList. Extraemos los DataFrames.
        dataframes = [tabla.df for tabla in tablas]
        return dataframes
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el PDF: {e}")
        return []