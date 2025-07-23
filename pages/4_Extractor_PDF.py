# pages/4_📄_Extractor_de_PDFs.py

import streamlit as st
import sys
import os

from src.pdf_extractor import extraer_tablas_de_pdf
from src.utils import to_excel # Reutilizamos nuestra función para descargar Excel

# Añade el directorio raíz del proyecto al path de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
st.set_page_config(layout="wide", page_title="Extractor de Tablas PDF")

st.title("📄 Extractor de Tablas desde PDF")
st.markdown("Sube un informe o documento en formato PDF para extraer automáticamente las tablas que contenga.")

# Componente para subir el archivo
archivo_subido = st.file_uploader(
    "Selecciona un archivo PDF",
    type="pdf",
    help="Sube un PDF que contenga tablas estructuradas."
)

if archivo_subido is not None:
    st.markdown("---")
    st.subheader("Tablas Encontradas en el Documento")
    
    with st.spinner("Analizando el PDF y extrayendo tablas..."):
        # Llamamos a nuestra función de backend
        tablas_extraidas = extraer_tablas_de_pdf(archivo_subido)

    if not tablas_extraidas:
        st.warning("No se encontraron tablas en el documento o no se pudieron extraer.")
    else:
        st.success(f"¡Se encontraron {len(tablas_extraidas)} tabla(s)!")
        
        # Iteramos sobre cada tabla encontrada para mostrarla y ofrecer la descarga
        for i, df_tabla in enumerate(tablas_extraidas):
            st.markdown(f"**Tabla {i+1}**")
            
            # Mostramos un preview de la tabla
            st.dataframe(df_tabla)
            
            # Preparamos el archivo Excel en memoria para la descarga
            excel_data = to_excel(df_tabla)
            
            # Botón para descargar la tabla específica
            st.download_button(
                label=f"📥 Descargar Tabla {i+1} como Excel",
                data=excel_data,
                file_name=f"tabla_{i+1}_{archivo_subido.name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.markdown("---")