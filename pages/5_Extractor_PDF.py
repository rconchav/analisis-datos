# pages/5_Extractor_PDF.py

import streamlit as st
import os
import sys

# --- CÓDIGO DE CONFIGURACIÓN DE PATH ---
# Añade el directorio raíz del proyecto a la ruta de búsqueda de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Importaciones de la aplicación ---
from src.pdf_extractor import extraer_tablas_de_pdf
from src.utils import to_excel, configurar_pagina
from src.theme import configurar_tema

# --- CONFIGURACIÓN CENTRALIZADA DE LA PÁGINA ---
configurar_pagina(titulo_pagina="Extractor de Tablas PDF")

# --- LÓGICA DEL TEMA (CONSISTENTE CON EL RESTO DE LA APP) ---
# Inicializa el estado del tema si no existe
if 'theme_toggle' not in st.session_state:
    st.session_state.theme_toggle = True

# Aplica el tema guardado en la sesión
tema_actual = "Oscuro" if st.session_state.theme_toggle else "Claro"
configurar_tema(tema_actual)

# --- CONTENIDO DE LA PÁGINA ---
st.title("📄 Extractor de Tablas desde PDF")
st.markdown("Sube un informe o documento en formato PDF para extraer automáticamente las tablas que contenga.")

# --- COMPONENTE DE CARGA DE ARCHIVO ---
with st.container(border=True):
    st.markdown("#### Cargar Archivo PDF")
    
    archivo_subido = st.file_uploader(
        "Arrastra o selecciona un archivo PDF para analizar.",
        type="pdf",
        label_visibility="collapsed"
    )

if archivo_subido is not None:
    st.markdown("---")
    st.header("Tablas Encontradas en el Documento")
    
    with st.spinner("Analizando el PDF y extrayendo tablas..."):
        # Llamamos a la función de backend para procesar el archivo
        tablas_extraidas = extraer_tablas_de_pdf(archivo_subido)

    if not tablas_extraidas:
        st.warning("No se encontraron tablas en el documento o no se pudieron extraer.")
    else:
        st.success(f"¡Se encontraron {len(tablas_extraidas)} tabla(s)!")
        
        # Iteramos sobre cada tabla encontrada para mostrarla y ofrecer la descarga
        for i, df_tabla in enumerate(tablas_extraidas):
            with st.container(border=True):
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
                    mime="application/vnd.ms-excel"
                )