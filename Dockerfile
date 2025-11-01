# syntax=docker/dockerfile:1

# Usar imagen base compatible con ARM64 (Raspberry Pi 5)
FROM python:3.13-slim

# Variables de entorno para optimización
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Configurar locale español
RUN apt-get update && \
    apt-get install -y locales sqlite3 && \
    sed -i -e 's/# es_ES.UTF-8 UTF-8/es_ES.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV LANG es_ES.UTF-8
ENV LC_ALL es_ES.UTF-8
ENV TZ Europe/Madrid

WORKDIR /app

# Copiar archivos de configuración primero (para cache de Docker)
COPY requirements.txt VERSION ./

# Instalar dependencias de Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY ssbo.py dbhelper.py ./

# Crear directorios para datos y logs con permisos
RUN mkdir -p /app/data /app/logs

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    chmod +x ssbo.py

# Cambiar a usuario no-root
USER app

# Health check para verificar que el bot esté funcionando
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python.*ssbo.py" > /dev/null || exit 1

CMD [ "python3", "./ssbo.py"]