# 🤖 Wallapop Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

Bot de Telegram inteligente para automatizar búsquedas en Wallapop con notificaciones en tiempo real y análisis de vendedores.

## ✨ Características Principales

### 🔍 **Búsqueda Inteligente**
- Filtrado preciso solo en títulos de anuncios
- Soporte para múltiples palabras clave
- Búsqueda por categorías predefinidas
- Rangos de precio personalizables

### 📱 **Interfaz Moderna**
- Menús interactivos con botones inline
- Wizard paso a paso para crear búsquedas
- Gestión visual de búsquedas activas
- Feedback inmediato en todas las acciones

### 💰 **Alertas Inteligentes**
- Notificaciones instantáneas de nuevos productos
- Alertas de bajadas de precio
- Monitoreo cada 5 minutos
- Historial de cambios de precios

### 👤 **Análisis de Vendedores**
- **Valoraciones**: Número total y puntuación promedio
- **Indicadores visuales**: ⭐ (>90%), 👍 (>80%)
- **Perfiles destacados**: Identificación de usuarios premium 🌟
- **Sin valoraciones**: Advertencia para vendedores nuevos

## 🚀 Instalación Rápida

### 📋 Requisitos Previos

1. **Token de Bot**: Crear bot con [@BotFather](https://t.me/botfather)
2. **Docker & Docker Compose**: [Instalar Docker](https://docs.docker.com/get-docker/)

### Instalación con Docker

```bash
# 1. Clonar el repositorio
git clone https://github.com/Puntzi/wallapop-bot.git
cd wallapop-bot

# 2. Configurar token del bot
export BOT_TOKEN="tu_token_aqui"

# 3. Iniciar el bot
docker-compose up -d

# 4. Ver logs
docker-compose logs -f wallbot
```

## ⚙️ Configuración

### 🔐 Variables de Entorno

| Variable | Descripción | Requerido | Ejemplo |
|----------|-------------|-----------|---------|
| `BOT_TOKEN` | Token del bot de Telegram | ✅ | `1234567890:ABCdef...` |
| `PROFILE` | Perfil de ejecución | ❌ | `docker` |
| `DB_DIR` | Directorio de base de datos | ❌ | `/app/data` |
| `LOG_DIR` | Directorio de logs | ❌ | `/app/logs` |

### 🐳 Docker Compose Personalizado

```yaml
version: '3.8'

services:
  wallbot:
    build: .
    container_name: wallapop-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - PROFILE=docker
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.8'
    healthcheck:
      test: ["CMD", "pgrep", "-f", "python.*ssbo.py"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## � Uso del Bot

### 🎯 Comandos Principales

| Comando | Descripción |
|---------|-------------|
| `/start` | Mostrar menú principal |
| `/help` | Mostrar ayuda detallada |
| `/add producto,min-max,categoria` | Añadir búsqueda (modo clásico) |
| `/list` | Listar búsquedas activas |
| `/del producto` | Eliminar búsqueda |

### 🎮 Menú Interactivo

1. **➕ Añadir búsqueda**: Wizard paso a paso
2. **📋 Mis búsquedas**: Ver y gestionar búsquedas
3. **📂 Categorías**: Búsquedas rápidas por categoría
4. **❓ Ayuda**: Información detallada

### 💡 Ejemplos de Uso

```
🔍 Búsquedas de ejemplo:
• "iPhone 15 Pro Max" → Busca exactamente este modelo
• "Nintendo Switch" + precio 200-300€ → Con rango de precio
• Categoría "Móviles" + precio hasta 500€ → Búsqueda por categoría
```

## 🐛 Solución de Problemas

### ❌ Problemas Comunes

**Bot no responde:**
```bash
# Verificar logs
docker-compose logs wallbot

# Reiniciar contenedor
docker-compose restart wallbot
```

**Error de token:**
```bash
# Verificar variable de entorno
echo $BOT_TOKEN

# Verificar configuración en docker-compose.yml
```

**Base de datos corrupta:**
```bash
# Eliminar base de datos (perderás las búsquedas)
rm data/db.sqlite
docker-compose restart wallbot
```

### 📋 Logs Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f wallbot

# Ver últimas 50 líneas
docker-compose logs --tail=50 wallbot

# Verificar estado del contenedor
docker-compose ps
```
