#!/bin/bash

# Script de inicio rápido para Wallbot
# Uso: ./start.sh [tu_bot_token]

set -e

echo "🤖 Wallbot - Inicio rápido"
echo "=========================="

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado"
    echo "Instala Docker desde: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar si Docker Compose está disponible
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose no está disponible"
    echo "Instala Docker Compose desde: https://docs.docker.com/compose/install/"
    exit 1
fi

# Verificar si existe .env
if [ ! -f .env ]; then
    echo "📝 Configurando archivo .env..."
    cp .env.example .env
    
    if [ "$1" ]; then
        echo "BOT_TOKEN=$1" > .env
        echo "✅ Token configurado desde parámetro"
    else
        echo "⚠️  Necesitas editar .env y añadir tu BOT_TOKEN"
        echo "   Puedes obtener un token de @BotFather en Telegram"
        echo ""
        echo "   Ejecuta: nano .env"
        echo "   Y añade: BOT_TOKEN=tu_token_aqui"
        exit 1
    fi
fi

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p data logs

# Verificar token en .env
if ! grep -q "BOT_TOKEN=.*[a-zA-Z0-9]" .env; then
    echo "❌ Error: BOT_TOKEN no configurado en .env"
    echo "   Edita .env y añade tu token de Telegram"
    exit 1
fi

echo "🚀 Iniciando Wallbot..."

# Usar docker compose (nuevo) o docker-compose (legacy)
if docker compose version &> /dev/null; then
    docker compose up -d
else
    docker-compose up -d
fi

echo ""
echo "✅ Wallbot iniciado correctamente!"
echo ""
echo "📊 Para ver los logs:"
echo "   docker-compose logs -f wallbot"
echo ""
echo "🛑 Para detener:"
echo "   docker-compose down"
echo ""
echo "🔄 Para reiniciar:"
echo "   docker-compose restart"