# Dockerfile para MADEIN Image Processing API
FROM python:3.11-slim

# Información del mantenedor
LABEL maintainer="MADEIN API Team"
LABEL description="API FastAPI para procesamiento de PDFs y extracción de comprobantes con OCR"
LABEL version="1.0.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para OpenCV, Tesseract y procesamiento de imágenes
RUN apt-get update && apt-get install -y \
    # Dependencias para OpenCV
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Dependencias para Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    # Utilidades del sistema
    wget \
    curl \
    git \
    # Librerías para procesamiento de imágenes
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    # Herramientas de build (pueden ser necesarias para algunas dependencias)
    build-essential \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no-root para seguridad
RUN groupadd -r apiuser && useradd -r -g apiuser apiuser

# Crear directorio de trabajo
WORKDIR /app

# Crear directorios necesarios para la aplicación
RUN mkdir -p /app/uploads /app/outputs /app/temp \
    && chown -R apiuser:apiuser /app

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Asegurar que los directorios tienen permisos correctos
RUN chown -R apiuser:apiuser /app \
    && chmod +x main.py

# Cambiar a usuario no-root
USER apiuser

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 