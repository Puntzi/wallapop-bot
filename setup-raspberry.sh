#!/bin/bash

# Script de instalación para Raspberry Pi 5
# Instala y configura Wallbot en Raspberry Pi OS

set -e

echo "🍓 Wallbot - Instalación en Raspberry Pi 5"
echo "=========================================="

# Verificar que estamos en una Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Advertencia: No se detectó una Raspberry Pi"
    echo "   Este script está optimizado para Raspberry Pi OS"
fi

# Actualizar el sistema
echo "📦 Actualizando el sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar Docker si no está presente
if ! command -v docker &> /dev/null; then
    echo "🐳 Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker instalado. Necesitas reiniciar la sesión para usar Docker sin sudo"
    echo "   Ejecuta: newgrp docker"
else
    echo "✅ Docker ya está instalado"
fi

# Instalar Docker Compose si no está presente
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Instalando Docker Compose..."
    sudo apt install -y docker-compose
else
    echo "✅ Docker Compose ya está instalado"
fi

# Verificar arquitectura
ARCH=$(uname -m)
echo "🏗️  Arquitectura detectada: $ARCH"

if [ "$ARCH" != "aarch64" ] && [ "$ARCH" != "armv7l" ]; then
    echo "⚠️  Advertencia: Arquitectura no típica para Raspberry Pi"
fi

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p data logs

# Configurar .env si no existe
if [ ! -f .env ]; then
    echo "📝 Configurando archivo .env..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANTE: Necesitas editar .env con tu BOT_TOKEN"
    echo "   Ejecuta: nano .env"
    echo "   Y reemplaza el token por el tuyo"
    echo ""
    read -p "Presiona Enter cuando hayas configurado el token..."
fi

# Verificar token
if ! grep -q "8255364367:" .env; then
    echo "❌ Error: Parece que no has configurado tu BOT_TOKEN en .env"
    echo "   Edita .env y añade tu token de Telegram"
    exit 1
fi

echo "🚀 Construyendo imagen Docker para ARM64..."
docker-compose build --no-cache

echo "🚀 Iniciando Wallbot..."
docker-compose up -d

echo ""
echo "✅ Wallbot iniciado en Raspberry Pi!"
echo ""
echo "📊 Para ver los logs:"
echo "   docker-compose logs -f wallbot"
echo ""
echo "🛑 Para detener:"
echo "   docker-compose down"
echo ""
echo "🔄 Para reiniciar:"
echo "   docker-compose restart"
echo ""
echo "💡 Para que se inicie automáticamente al reiniciar:"
echo "   sudo systemctl enable docker"