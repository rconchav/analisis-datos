# microservices/hello_world_api/Dockerfile

# Usar una imagen base de Python 3.10 estándar de Docker Hub (la más confiable y que garantiza Python 3)
FROM python:3.10-slim-buster

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Argumento para forzar invalidación de caché de pip en cada despliegue.
# Este valor se puede pasar con --build-arg CACHE_BUST=$(date +%s) en gcloud run deploy.
ARG CACHE_BUST=1

# Copiar el archivo requirements.txt al directorio de trabajo
COPY requirements.txt .

# Instalar las dependencias de Python.
# --no-cache-dir para no guardar la caché de pip.
# --upgrade pip para asegurar pip actualizado.
# --upgrade -r requirements.txt para asegurar que los paquetes se actualicen si ya existieran y forzar una reinstalación más limpia.
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir --upgrade -r requirements.txt

# Copiar el código de la aplicación
COPY main.py .

# Definir la variable de entorno PORT, que Cloud Run inyectará.
# Tu aplicación debe escuchar en este puerto. Cloud Run usa por defecto 8080.
ENV PORT 8080

# Comando para ejecutar la aplicación con Gunicorn.
# - main:app -> Indica que main.py contiene la instancia 'app' de FastAPI.
# --workers 1 -> Cloud Run gestiona el escalado, 1 worker es suficiente inicialmente.
# --worker-class uvicorn.workers.UvicornWorker -> Usa el worker asíncrono de Uvicorn.
# --bind 0.0.0.0:$PORT -> Asegura que Gunicorn escucha en todas las interfaces en el puerto asignado por Cloud Run.
# --timeout 120 -> Tiempo máximo de espera para que un worker inicie o procese una solicitud.
CMD gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120