# 🐳 Dockerfile para JET OCR (SaaS)

FROM python:3.10-slim

# Instalar dependencias del sistema para procesamiento de imágenes (OpenCV / EasyOCR)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar dependencias y cachear
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copiar código fuente
COPY . .

# Variables de entorno por defecto
ENV FLASK_ENV=production

# Crear carpeta de subidas por si no existe
RUN mkdir -p uploads

EXPOSE 5000

# Arrancar con Gunicorn para producción
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
