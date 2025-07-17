# utils.py

import io
import pandas as pd
import re
import unicodedata

def to_excel(df):
    """Convierte un DataFrame a un archivo Excel en memoria para su descarga."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    processed_data = output.getvalue()
    return processed_data

def limpiar_codigo_arancel(codigo):
    """Función robusta para limpiar y estandarizar códigos arancelarios."""
    if pd.isna(codigo):
        return ""
    s_codigo = str(int(float(codigo))) if isinstance(codigo, float) else str(codigo)
    return re.sub(r'\D', '', s_codigo)

def normalizar_texto(texto):
    """Normaliza un texto eliminando tildes y convirtiéndolo a minúsculas."""
    if not isinstance(texto, str):
        return ""
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.lower()

def validar_y_limpiar_nombre(texto):
    """Función de validación estándar para marcas, modelos y productos."""
    if not isinstance(texto, str):
        return ""
    texto_normalizado = normalizar_texto(texto)
    texto_con_espacios = re.sub(r'[^a-z0-9]+', ' ', texto_normalizado)
    return "".join(texto_con_espacios.split())

# --- NUEVA FUNCIÓN ---
def formatar_moneda_cl(valor):
    """
    Formatea un número como moneda con '.' para miles y ',' para decimales.
    Ejemplo: 12345.67 -> $ 1.234,56
    """
    if pd.isna(valor):
        return "$ 0,00"
    # Formateamos con el estándar de EE.UU. como paso intermedio
    formato_intermedio = f"${valor:,.2f}"
    # Intercambiamos los separadores
    formato_final = formato_intermedio.replace(',', 'X').replace('.', ',').replace('X', '.')
    return formato_final