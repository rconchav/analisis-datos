# src/utils/general_utils.py

import pandas as pd
import io
import locale
import re
import unicodedata

def manejar_columnas_duplicadas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maneja columnas duplicadas en un DataFrame de pandas, añadiendo un sufijo numérico.
    """
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        nuevos_nombres = [dup + f'_{i}' if i != 0 else dup for i in range(sum(cols == dup))]
        cols[cols[cols == dup].index] = nuevos_nombres
    df.columns = cols
    return df

def to_excel(df: pd.DataFrame) -> bytes:
    """
    Convierte un DataFrame de pandas a un archivo Excel en formato de bytes.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

# Configuración de locale para formato de moneda (se mantiene aquí por ser una utilidad general de formato)
try:
    locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')

def formatar_moneda_cl(valor):
    """
    Formatea un valor numérico como moneda chilena.
    """
    if pd.isna(valor): return "$ 0"
    try:
        return locale.currency(valor, grouping=True, symbol=True)
    except (ValueError, TypeError):
        return "$ 0"