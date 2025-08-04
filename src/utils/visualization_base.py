# src/utils/visualization_base.py

import altair as alt
import pandas as pd
import numpy as np

def _configurar_grafico_altair(chart, titulo: str, paleta_colores: list):
    """
    Aplica configuraciones comunes a los gráficos de Altair.
    """
    return chart.properties(
        title=alt.Title(
            text=titulo,
            anchor='start',
            fontSize=18,
            fontWeight=600,
            dy=-10
        ),
        height=350
    ).configure_axis(
        labelFontSize=11,
        titleFontSize=13
    ).configure_legend(
        titleFontSize=12,
        labelFontSize=11,
        orient='bottom'
    ).configure_range(
        category=paleta_colores
    ).configure_view(
        strokeWidth=0
    )

def _format_large_number(num, is_currency=False):
    """
    Formatea un número grande a un formato legible (K, M, B) y opcionalmente como moneda.
    """
    if pd.isna(num):
        return "$ 0" if is_currency else "0"

    prefix = "$" if is_currency else ""

    if abs(num) < 1_000:
        return f"{prefix}{num:,.0f}"

    magnitudes = ['', 'K', 'M', 'B', 'T']
    magnitude = 0
    while abs(num) >= 1_000 and magnitude < len(magnitudes) - 1:
        magnitude += 1
        num /= 1_000.0

    format_str = "{:,.1f}"
    return f"{prefix}{format_str.format(num)}{magnitudes[magnitude]}"