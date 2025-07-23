# crear_json_arancel.py

import pandas as pd
import json
import os
import re

def convertir_arancel_a_json_estructurado(excel_path, json_path):
    """
    Lee un archivo Excel con la clasificación arancelaria en formato de tabla
    y lo convierte a un archivo JSON con una estructura anidada y detallada.
    """
    try:
        # Lee el archivo Excel, especificando que los datos son de tipo texto
        df = pd.read_excel(excel_path, dtype=str)
        print("Archivo Excel leído correctamente.")

        # Nombres de columna esperados
        columna_partida = "Partida"
        columna_codigo = "Código del S.A."
        columna_glosa = "Glosa"
        
        required_columns = [columna_partida, columna_codigo, columna_glosa]
        if not all(col in df.columns for col in required_columns):
            print(f"Error: El archivo Excel debe contener las columnas: {required_columns}")
            print(f"Columnas encontradas: {df.columns.to_list()}")
            return

        # Rellenamos los valores vacíos en la columna 'Partida'
        df[columna_partida] = df[columna_partida].ffill()
        
        arancel_json = {}

        # Agrupamos los datos por la columna 'Partida'
        for partida, group in df.groupby(columna_partida):
            partida_str = str(partida)
            
            # La primera fila del grupo usualmente contiene la descripción principal de la partida
            descripcion_partida = ""
            # Filtramos para encontrar la fila que describe la partida (suele tener código NaN)
            fila_descripcion = group[group[columna_codigo].isna()]
            if not fila_descripcion.empty:
                descripcion_partida = fila_descripcion.iloc[0][columna_glosa]

            # Creamos la estructura principal para esta partida
            arancel_json[partida_str] = {
                "descripcion_partida": descripcion_partida,
                "subcategorias": {}
            }
            
            # Ahora procesamos las subcategorías (filas con código)
            df_subcategorias = group.dropna(subset=[columna_codigo])
            
            for _, row in df_subcategorias.iterrows():
                codigo_sa = row[columna_codigo]
                glosa_sa = row[columna_glosa]
                arancel_json[partida_str]["subcategorias"][codigo_sa] = glosa_sa
        
        # Guardamos el diccionario completo como un archivo JSON formateado
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(arancel_json, f, ensure_ascii=False, indent=4)
            
        print(f"¡Éxito! El archivo '{json_path}' ha sido creado correctamente con la nueva estructura detallada.")

    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo Excel en la ruta especificada: '{excel_path}'.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

# --- Configuración y Ejecución ---
archivo_excel_entrada = os.path.join('bd_Aranceles', 'arancel_aduanero_cl.xlsx')
archivo_json_salida = 'arancel_clasificacion.json'

convertir_arancel_a_json_estructurado(archivo_excel_entrada, archivo_json_salida)