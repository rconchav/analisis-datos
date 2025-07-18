FROM python:3.11-slim

# Instalar dependencias del sistema operativo para Camelot
RUN apt-get update && apt-get install -y \
    ghostscript \
    tk-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

RUN mkdir -p input catalogos datos logs

EXPOSE 8501

CMD ["streamlit", "run", "1_📊_Analisis_datos.py"]