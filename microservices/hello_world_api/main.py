# microservices/hello_world_api/main.py

from fastapi import FastAPI
import os
import logging

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Hello World Cloud Run API")

@app.get("/")
async def read_root():
    logger.info("Endpoint '/' accessed: Returning Hello World message.")
    return {"message": "¡Hola Mundo desde Cloud Run!"}

@app.get("/healthz")
async def health_check():
    logger.info("Endpoint '/healthz' accessed: Health check successful.")
    return {"status": "ok"}

# Para ejecución local con Uvicorn (opcional para pruebas)
if __name__ == "__main__":
    import uvicorn
    logger.info("Running Hello World API locally with Uvicorn.")
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))