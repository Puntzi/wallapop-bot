[![commit_freq](https://img.shields.io/github/commit-activity/m/IceFox2/wallbot?style=flat-square)](https://github.com/IceFox2/wallbot/commits) [![last_commit](https://img.shields.io/github/last-commit/IceFox2/wallbot?style=flat-square)](https://github.com/IceFox2/wallbot/commits) ![GitHub](https://img.shields.io/github/license/IceFox2/wallbot)


# Wallbot
Wallapop Search Bot

🤖 Bot de Telegram inteligente para gestionar búsquedas en Wallapop

## ✨ Características Principales

- 🔍 **Búsqueda por título**: Filtra resultados solo en títulos de anuncios
- 📢 **Notificaciones instantáneas**: Avisa cuando encuentra nuevos anuncios
- 💰 **Alertas de precios**: Notifica cuando algún ítem baja de precio
- ⭐ **Información del vendedor**: Muestra valoraciones y credibilidad
- 📊 **Gestión de búsquedas**: Permite gestionar tu lista de búsquedas
- 🌟 **Perfiles destacados**: Identifica vendedores con perfil premium
- 📱 **Confirmaciones**: Respuesta al añadir búsquedas exitosamente

## 👤 Información del Vendedor

El bot ahora incluye información valiosa sobre cada vendedor:
- **Número de valoraciones** recibidas
- **Puntuación promedio** (porcentaje)
- **Indicadores visuales**: ⭐ (>90%), 👍 (>80%), 🌟 (perfil destacado)

# 🚀 Instalación y Configuración

## 📋 Requisitos Previos

1. **Token de Bot de Telegram**: Crear un bot con [@BotFather](https://t.me/botfather)
2. **Docker y Docker Compose** instalados en tu sistema

## 🐳 Instalación con Docker (Recomendado)

### 1. Clonar el repositorio
```bash
git clone https://github.com/IceFox2/wallbot
cd wallbot
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env y añadir tu BOT_TOKEN
```

### 3. Ejecutar con Docker Compose
```bash
docker-compose up -d
```

### 4. Verificar que está funcionando
```bash
docker-compose logs -f wallbot
```

## 📁 Estructura de Volúmenes

- `/app/data` - Base de datos SQLite (persistente)
- `/app/logs` - Archivos de log con rotación automática

## 🛠️ Docker Compose Personalizado

```yaml
version: '3.8'

services:
  wallbot:
    build: .
    container_name: wallapop-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=tu_bot_token_aqui
      - PROFILE=docker
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```