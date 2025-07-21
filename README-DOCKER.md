# 🐳 MADEIN Image Processing API - Docker Deployment

Documentación completa para desplegar la API de procesamiento de imágenes usando Docker.

## 📋 **Prerequisitos**

### **🖥️ Software Requerido:**
- **Docker Desktop** instalado y corriendo
- **Docker Compose** (incluido con Docker Desktop)
- **Git** (para clonar el repositorio)

### **💾 Recursos Mínimos:**
- **RAM**: 2GB disponibles para el contenedor
- **CPU**: 1 core dedicado
- **Disco**: 5GB espacio libre
- **Red**: Puerto 8000 disponible

## 🚀 **Deployment Rápido**

### **1. 📥 Clonar Repositorio**
```bash
git clone <tu-repositorio>
cd APIMadein
```

### **2. 🏗️ Construir y Ejecutar**

#### **Opción A: Scripts Automáticos (Recomendado)**

**🐧 Linux/Mac:**
```bash
chmod +x docker-start.sh
./docker-start.sh build
./docker-start.sh start
```

**🪟 Windows:**
```cmd
docker-start.bat build
docker-start.bat start
```

#### **Opción B: Comandos Docker Directos**
```bash
# Construir imagen
docker-compose build

# Iniciar servicios
docker-compose up -d

# Verificar estado
docker-compose ps
```

### **3. ✅ Verificar Deployment**
- 🌐 **API Docs**: http://localhost:8000/docs
- 🔧 **Health Check**: http://localhost:8000/health
- 📊 **Redoc**: http://localhost:8000/redoc

## 🛠️ **Comandos Disponibles**

### **📜 Scripts de Gestión**

| Comando | Linux/Mac | Windows | Descripción |
|---------|-----------|---------|-------------|
| **Construir** | `./docker-start.sh build` | `docker-start.bat build` | Construye la imagen Docker |
| **Iniciar** | `./docker-start.sh start` | `docker-start.bat start` | Inicia los servicios |
| **Detener** | `./docker-start.sh stop` | `docker-start.bat stop` | Detiene los servicios |
| **Reiniciar** | `./docker-start.sh restart` | `docker-start.bat restart` | Reinicia los servicios |
| **Logs** | `./docker-start.sh logs` | `docker-start.bat logs` | Muestra logs en tiempo real |
| **Estado** | `./docker-start.sh status` | `docker-start.bat status` | Estado de contenedores |
| **Limpiar** | `./docker-start.sh cleanup` | `docker-start.bat cleanup` | Elimina todo |

### **🐳 Comandos Docker Manuales**
```bash
# Construir imagen
docker-compose build --no-cache

# Iniciar en background
docker-compose up -d

# Ver logs
docker-compose logs -f madein-api

# Detener servicios
docker-compose down

# Entrar al contenedor
docker-compose exec madein-api bash

# Reconstruir completamente
docker-compose down --rmi all --volumes --remove-orphans
docker-compose build --no-cache
docker-compose up -d
```

## ⚙️ **Configuración**

### **📁 Variables de Entorno**
```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar configuraciones
nano .env  # o tu editor preferido
```

### **🔧 Configuraciones Principales**
```env
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info
MIN_AREA=50000
PDF_DPI=300
OCR_LANGUAGES=es,en
MAX_FILE_SIZE=50
```

### **💾 Volúmenes Persistentes**
Los siguientes directorios se mantienen entre reinicios:
- **`uploads/`** - Archivos subidos temporalmente
- **`outputs/`** - Resultados procesados

## 🔧 **Personalización Avanzada**

### **📝 Modificar docker-compose.yml**
```yaml
services:
  madein-api:
    # Cambiar puertos
    ports:
      - "9000:8000"  # Puerto externo:interno
    
    # Límites de recursos
    deploy:
      resources:
        limits:
          memory: 4G    # Más memoria
          cpus: '2.0'   # Más CPUs
    
    # Variables de entorno
    environment:
      - LOG_LEVEL=debug
      - MAX_FILE_SIZE=100
```

### **🏗️ Modificar Dockerfile**
```dockerfile
# Instalar dependencias adicionales
RUN apt-get update && apt-get install -y \
    tu-dependencia-extra

# Cambiar usuario
USER root  # si necesitas permisos especiales

# Cambiar comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--workers", "4"]
```

## 🧪 **Testing del Deployment**

### **1. ✅ Health Check**
```bash
curl http://localhost:8000/health
# Respuesta esperada: {"status": "ok", "timestamp": "..."}
```

### **2. 📤 Test de Upload**
```bash
curl -X POST "http://localhost:8000/extract-individual-comprobantes" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@tu-imagen.png"
```

### **3. 📋 Verificar Logs**
```bash
# Ver logs en tiempo real
docker-compose logs -f madein-api

# Buscar errores
docker-compose logs madein-api | grep ERROR
```

## 🐛 **Troubleshooting**

### **❌ Problemas Comunes**

#### **1. Puerto Ocupado**
```bash
# Error: port is already allocated
docker ps | grep :8000
docker stop <container-id>
# O cambiar puerto en docker-compose.yml
```

#### **2. Memoria Insuficiente**
```bash
# Error: out of memory
# Aumentar límites en docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

#### **3. Dependencias Faltantes**
```bash
# Error: module not found
docker-compose build --no-cache
# Verificar requirements.txt
```

#### **4. Permisos de Archivos**
```bash
# Error: permission denied
docker-compose exec madein-api chown -R apiuser:apiuser /app
```

### **🔍 Comandos de Diagnóstico**
```bash
# Ver estado detallado
docker-compose ps -a

# Inspeccionar contenedor
docker inspect madein-image-processing-api

# Ver recursos utilizados
docker stats madein-image-processing-api

# Verificar red
docker network ls
docker network inspect apimadein_madein-network
```

## 🚀 **Deployment en Producción**

### **🔒 Consideraciones de Seguridad**
```yaml
# docker-compose.prod.yml
services:
  madein-api:
    restart: always
    environment:
      - DEBUG=false
      - LOG_LEVEL=warn
    # Usar secrets para variables sensibles
    secrets:
      - api_token
      - db_password
```

### **⚡ Optimizaciones de Performance**
```dockerfile
# Multi-stage build para imagen más pequeña
FROM python:3.11-slim as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
# ... resto de la configuración
```

### **📊 Monitoreo**
```bash
# Healthcheck automático
HEALTHCHECK --interval=30s --timeout=30s \
    CMD curl -f http://localhost:8000/health || exit 1

# Logs estructurados
LOG_FORMAT=json
```

## 📞 **Soporte**

### **🆘 Si Tienes Problemas:**
1. 📋 Verifica logs: `docker-compose logs madein-api`
2. 🔄 Reinicia servicios: `docker-start.sh restart`
3. 🧹 Limpia y reconstruye: `docker-start.sh cleanup` → `docker-start.sh build`
4. 📖 Revisa documentación: http://localhost:8000/docs

### **📈 Estadísticas de Performance:**
- ⚡ **Tiempo de inicio**: ~30-60 segundos
- 💾 **Memoria promedio**: 500MB-1GB
- 🔄 **Requests/seg**: 10-50 (dependiendo de complejidad)

---

## 🎯 **Resumen de Comandos Rápidos**

```bash
# 🏗️ Setup inicial
docker-start.sh build
docker-start.sh start

# 📊 Verificar
docker-start.sh status
curl http://localhost:8000/health

# 🔧 Mantener
docker-start.sh logs    # Ver actividad
docker-start.sh restart # Si hay problemas

# 🧹 Limpiar
docker-start.sh cleanup # Eliminar todo
```

**🎉 ¡Tu API está lista para procesar imágenes en Docker!** 🐳 

¡Perfecto! 🎉 Ya estás conectado al servidor. Vamos paso a paso:

## 🔧 **Paso 1: Configurar Firewall**

```bash
# Abrir puertos para HTTP y HTTPS
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload

# Verificar estado del firewall
ufw status
```

## 📁 **Paso 2: Crear Estructura de Directorios**

```bash
<code_block_to_apply_changes_from>
# Crear directorio principal
mkdir -p /opt/madein-api
cd /opt/madein-api

# Crear subdirectorios (ESTE era el problema)
mkdir -p data/uploads
mkdir -p data/outputs  
mkdir -p data/logs
mkdir -p nginx/conf.d
mkdir -p nginx/ssl

# Verificar que se crearon
ls -la
ls -la nginx/
```

## ⚙️ **Paso 3: Crear Archivos de Configuración**

### **3.1 docker-compose.prod.yml**

```bash
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  madein-api:
    image: AQUI_VA_TU_IMAGEN  # Lo cambiaremos después
    container_name: madein-api-prod
    restart: always
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=info
      - DEBUG=false
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - WORKERS=2
      - MIN_AREA=50000
      - PDF_DPI=300
      - OCR_LANGUAGES=es,en
      - MAX_FILE_SIZE=50
      - CORS_ORIGINS=*
      - UPLOAD_DIR=/app/uploads
      - OUTPUT_DIR=/app/outputs
    
    volumes:
      - uploads_prod:/app/uploads
      - outputs_prod:/app/outputs
      - logs_prod:/app/logs
    
    networks:
      - madein-network
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    
    expose:
      - "8000"

  nginx:
    image: nginx:alpine
    container_name: madein-nginx-prod
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - logs_nginx:/var/log/nginx
    depends_on:
      - madein-api
    networks:
      - madein-network

volumes:
  uploads_prod:
  outputs_prod:
  logs_prod:
  logs_nginx:

networks:
  madein-network:
    driver: bridge
EOF
```

### **3.2 Configuración de Nginx**

```bash
cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 100M;

    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    include /etc/nginx/conf.d/*.conf;
}
EOF
```

### **3.3 Configuración del servidor API**

```bash
cat > nginx/conf.d/api.conf << 'EOF'
upstream madein_api {
    server madein-api:8000;
}

server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://madein_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 30s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location ~ ^/(extract-|process-|run-) {
        proxy_pass http://madein_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        proxy_buffering off;
    }

    location /health {
        proxy_pass http://madein_api;
        access_log off;
    }
}
EOF
```

## 🔍 **Paso 4: Verificar tu Imagen Docker**

Antes de continuar, necesito saber cuál es tu imagen Docker. Ejecuta estos comandos:

```bash
# Ver imágenes disponibles
docker images

# Ver si hay contenedores corriendo
docker ps -a
```

**📝 Copia aquí el resultado** para que pueda ayudarte a configurar correctamente el docker-compose.

También dime:
- ¿Cómo se llama tu imagen?
- ¿Es una imagen que subiste a Docker Hub?
- ¿O la construiste localmente en el servidor?

¡Ejecuta esos comandos y comparte el resultado! 🚀 

¡Ah! El error es porque el directorio `nginx` no existe aún. Vamos paso a paso:

## 🔧 **Paso 1: Configurar Firewall Primero**

```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload
ufw status
```

## 📁 **Paso 2: Crear Directorios CORRECTAMENTE**

```bash
# Crear directorio principal
mkdir -p /opt/madein-api
cd /opt/madein-api

# Crear subdirectorios (ESTE era el problema)
mkdir -p data/uploads
mkdir -p data/outputs  
mkdir -p data/logs
mkdir -p nginx/conf.d
mkdir -p nginx/ssl

# Verificar que se crearon
ls -la
ls -la nginx/
```

## ⚙️ **Paso 3: Ahora SÍ crear los archivos**

### **3.1 docker-compose.prod.yml**
```bash
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  madein-api:
    image: AQUI_VA_TU_IMAGEN
    container_name: madein-api-prod
    restart: always
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=info
      - DEBUG=false
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - WORKERS=2
      - MIN_AREA=50000
      - PDF_DPI=300
      - OCR_LANGUAGES=es,en
      - MAX_FILE_SIZE=50
      - CORS_ORIGINS=*
      - UPLOAD_DIR=/app/uploads
      - OUTPUT_DIR=/app/outputs
    
    volumes:
      - uploads_prod:/app/uploads
      - outputs_prod:/app/outputs
      - logs_prod:/app/logs
    
    networks:
      - madein-network
    
    expose:
      - "8000"

  nginx:
    image: nginx:alpine
    container_name: madein-nginx-prod
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - logs_nginx:/var/log/nginx
    depends_on:
      - madein-api
    networks:
      - madein-network

volumes:
  uploads_prod:
  outputs_prod:
  logs_prod:
  logs_nginx:

networks:
  madein-network:
    driver: bridge
EOF
```

### **3.2 Configuración de Nginx**
```bash
cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent"';

    access_log /var/log/nginx/access.log main;
    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 100M;
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;
    include /etc/nginx/conf.d/*.conf;
}
EOF
```

### **3.3 Configuración del servidor API**
```bash
cat > nginx/conf.d/api.conf << 'EOF'
upstream madein_api {
    server madein-api:8000;
}

server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://madein_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://madein_api;
        access_log off;
    }
}
EOF
```

## 🔍 **Paso 4: Verificar archivos creados**
```bash
<code_block_to_apply_changes_from>
```

## 📦 **Paso 5: Ahora verificar tu imagen Docker**
```bash
docker images
docker ps -a
```

**¡Ejecuta estos comandos en orden y comparte el resultado!** 🚀

Necesito saber el nombre de tu imagen Docker para actualizar el docker-compose.prod.yml correctamente. 