# 1. Usar una imagen base oficial de Python
FROM python:3.11-slim

# 2. Instalar dependencias del sistema operativo
# Esto es CRUCIAL para que Camelot funcione, ya que necesita Ghostscript.
RUN apt-get update && apt-get install -y \
    ghostscript \
    tk-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 4. Copiar el archivo de requerimientos e instalar las librerías de Python
# Se hace en un paso separado para aprovechar el caché de Docker y acelerar futuras construcciones.
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 5. Copiar todos los archivos de la aplicación al contenedor
COPY . .

# 6. Crear las carpetas para los archivos que subirá el usuario
RUN mkdir -p input catalogos

# 7. Exponer el puerto por defecto de Streamlit
EXPOSE 8501

# 8. El comando para ejecutar la aplicación cuando el contenedor se inicie
CMD ["streamlit", "run", "app.py"]