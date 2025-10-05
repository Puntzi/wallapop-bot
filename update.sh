#!/bin/bash

# Script para actualizar y reiniciar Wallbot
# 
# MODO DE USO:
#   ./update.sh                    - Actualización automática (git pull + rebuild si es necesario)
#   ./update.sh --restart-only     - Solo reiniciar el contenedor (sin git pull ni rebuild)
#   ./update.sh --force-rebuild    - Forzar reconstrucción completa de la imagen
#   ./update.sh --no-git          - Actualizar sin hacer git pull
#
# EJEMPLOS:
#   ./update.sh                    # Actualización normal
#   ./update.sh --force-rebuild    # Cuando cambias Dockerfile o requirements.txt
#   ./update.sh --restart-only     # Reinicio rápido sin cambios

echo "🔄 Actualizando Wallbot..."

# Variables
REBUILD_NEEDED=false
GIT_CHANGES=false

# Verificar si hay cambios en Git (opcional)
if [ -d ".git" ] && [ "$2" != "--no-git" ] && [ "$1" != "--no-git" ]; then
    echo "📥 Verificando cambios en Git..."
    
    # Obtener hash actual
    OLD_HASH=$(git rev-parse HEAD)
    
    # Hacer git pull
    git pull
    
    # Obtener nuevo hash
    NEW_HASH=$(git rev-parse HEAD)
    
    # Verificar si hubo cambios
    if [ "$OLD_HASH" != "$NEW_HASH" ]; then
        echo "✅ Se encontraron cambios en Git"
        GIT_CHANGES=true
        REBUILD_NEEDED=true
    else
        echo "ℹ️  No hay cambios nuevos en Git"
    fi
else
    echo "⚠️  Saltando verificación de Git"
fi

# Verificar si hay cambios en archivos locales
echo "📁 Verificando cambios en archivos locales..."
if [ -f "ssbo.py" ] || [ -f "dbhelper.py" ] || [ -f "requirements.txt" ] || [ -f "Dockerfile" ]; then
    # Verificar si la imagen necesita reconstrucción
    if [ ! "$(docker images -q wallapop-bot_wallbot 2> /dev/null)" ] || [ "$GIT_CHANGES" = true ]; then
        REBUILD_NEEDED=true
    fi
fi

# Decidir acción basada en argumentos y cambios
if [ "$1" = "--restart-only" ]; then
    echo "🔄 Reiniciando contenedor solamente..."
    docker-compose restart wallbot
elif [ "$REBUILD_NEEDED" = true ] || [ "$1" = "--force-rebuild" ]; then
    echo "🏗️  Reconstruyendo imagen con cambios..."
    echo "📋 Deteniendo contenedor actual..."
    docker-compose down
    
    echo "🔨 Construyendo nueva imagen..."
    docker-compose build --no-cache
    
    echo "🚀 Iniciando contenedor actualizado..."
    docker-compose up -d
else
    echo "🔄 Reiniciando contenedor..."
    docker-compose restart wallbot
fi

# Verificar que el contenedor esté funcionando
echo ""
echo "⏳ Esperando que el contenedor inicie..."
sleep 5

# Verificar estado del contenedor
if docker-compose ps | grep -q "Up"; then
    echo "✅ Actualización completada exitosamente!"
    echo ""
    echo "📊 Estado actual:"
    docker-compose ps
    
    echo ""
    echo "� Health check:"
    docker-compose exec wallbot pgrep -f "python.*ssbo.py" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Bot está funcionando correctamente"
    else
        echo "⚠️  Bot podría no estar funcionando. Revisa los logs."
    fi
else
    echo "❌ Error: El contenedor no está funcionando correctamente"
    echo "�📋 Logs del contenedor:"
    docker-compose logs --tail=20 wallbot
    exit 1
fi

echo ""
echo "📋 Comandos útiles:"
echo "  Ver logs en tiempo real: docker-compose logs -f wallbot"
echo "  Detener bot:            docker-compose down"
echo "  Ver estado:             docker-compose ps"
echo "  Reconstruir forzado:    ./update.sh --force-rebuild"
echo "  Solo reiniciar:         ./update.sh --restart-only"