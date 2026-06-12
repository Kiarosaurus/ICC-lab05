# Imagen de la aplicación web (capas de Presentación, Negocio y Datos).
# Base ligera de Python; la base de datos corre en su propio contenedor.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias primero, para aprovechar la caché de capas de Docker:
# si solo cambia el código no se reinstala nada.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# La app no necesita privilegios: usuario sin permisos de root.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
