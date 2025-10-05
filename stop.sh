#!/bin/bash

# Script para parar Wallbot
# Uso: ./stop.sh [--force]

echo "🛑 Parando Wallbot..."

if [ "$1" = "--force" ]; then
    echo "🔧 Parada forzada con limpieza..."
    docker-compose down --rmi local
    docker system prune -f
    echo "✅ Bot parado y limpieza completada"
else
    echo "⏸️ Parada normal..."
    docker-compose stop
    echo "✅ Bot parado (usa 'docker-compose start' para reanudar)"
fi

echo ""
echo "📊 Estado actual:"
docker-compose ps