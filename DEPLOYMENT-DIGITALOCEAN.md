# 🚀 Deployment en DigitalOcean - MADEIN API

Guía completa para desplegar la API de procesamiento de imágenes MADEIN en DigitalOcean usando Docker.

## 📋 Prerequisitos

### 🖥️ **Servidor DigitalOcean**
- **Droplet**: Ubuntu 22.04 LTS o superior
- **RAM**: Mínimo 4GB (recomendado 8GB)
- **CPU**: Mínimo 2 vCPUs
- **Disco**: Mínimo 50GB SSD
- **Firewall**: Puertos 80, 443, 22 abiertos

### 🛠️ **Software Requerido**
- Docker CE 24.0+
- Docker Compose v2.0+
- Git
- Nginx (se instala automáticamente via Docker)

## 🏗️ **Setup Inicial del Servidor**

### **1. 📥 Preparar el Servidor**

```bash
# Conectar al servidor
ssh root@your-server-ip

# Actualizar sistema
apt update && apt upgrade -y

# Instalar dependencias básicas
apt install -y curl wget git ufw

# Configurar firewall
ufw allow ssh
ufw allow http
ufw allow https
ufw enable
```

### **2. 🐳 Instalar Docker**

```bash
# Instalar Docker usando el script oficial
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Agregar usuario al grupo docker
usermod -aG docker $USER
newgrp docker

# Verificar instalación
docker --version
docker-compose --version
```

### **3. 👤 Crear Usuario de Aplicación**

```bash
# Crear usuario dedicado (opcional pero recomendado)
adduser madein-api
usermod -aG docker madein-api
usermod -aG sudo madein-api

# Cambiar a usuario de aplicación
su - madein-api
```

## 🚀 **Deployment Automático**

### **Opción A: Script de Deployment (Recomendado)**

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/madein-api.git
cd madein-api/APIMadein

# Hacer script ejecutable
chmod +x deploy.sh

# Configurar variables de entorno
cp env.production.example .env.production
nano .env.production  # Editar con tus valores

# Desplegar en producción
./deploy.sh production

# Con SSL automático (Let's Encrypt)
DOMAIN=tu-dominio.com EMAIL=admin@tu-dominio.com ./deploy.sh production --ssl
```

### **Opción B: Deployment Manual**

```bash
# 1. Clonar y configurar
git clone https://github.com/tu-usuario/madein-api.git
cd madein-api/APIMadein

# 2. Configurar variables de entorno
cp env.production.example .env.production
# Editar .env.production con tus valores reales

# 3. Crear directorios
sudo mkdir -p /opt/madein-api/data/{uploads,outputs,logs}
sudo chown -R $USER:$USER /opt/madein-api

# 4. Construir y desplegar
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# 5. Verificar
docker-compose -f docker-compose.prod.yml ps
curl http://localhost/health
```

## ⚙️ **Configuración Detallada**

### **🔐 Variables de Entorno Críticas**

```bash
# Editar .env.production
nano .env.production
```

**Variables obligatorias a cambiar:**
- `DOMAIN`: Tu dominio real (ej: api.tuempresa.com)
- `API_TOKEN`: Token seguro generado con `openssl rand -hex 32`
- `EMAIL`: Tu email para Let's Encrypt
- `CORS_ORIGINS`: Dominios permitidos para CORS

### **🌐 Configuración de Dominio**

```bash
# En tu proveedor de DNS, configurar:
# Tipo A: api.tuempresa.com -> IP-DE-TU-SERVIDOR
# Tipo A: *.api.tuempresa.com -> IP-DE-TU-SERVIDOR (opcional)
```

### **🔒 SSL Automático con Let's Encrypt**

```bash
# Desplegar con SSL automático
DOMAIN=api.tuempresa.com EMAIL=admin@tuempresa.com ./deploy.sh production --ssl

# O configurar SSL manualmente después
docker run --rm -v /opt/madein-api/nginx/ssl:/etc/letsencrypt \
  certbot/certbot certonly --standalone \
  --email admin@tuempresa.com --agree-tos \
  -d api.tuempresa.com
```

## 📊 **Monitoreo y Mantenimiento**

### **🔍 Comandos de Verificación**

```bash
# Estado de contenedores
docker-compose -f docker-compose.prod.yml ps

# Logs en tiempo real
docker-compose -f docker-compose.prod.yml logs -f

# Logs específicos
docker-compose -f docker-compose.prod.yml logs madein-api
docker-compose -f docker-compose.prod.yml logs nginx

# Uso de recursos
docker stats

# Health check
curl -f http://tu-dominio.com/health
curl -f https://tu-dominio.com/health  # Con SSL
```

### **🔄 Comandos de Mantenimiento**

```bash
# Reiniciar servicios
docker-compose -f docker-compose.prod.yml restart

# Actualizar aplicación
git pull origin main
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Limpieza de sistema
docker system prune -f
docker volume prune -f
```

### **📋 Logs y Debugging**

```bash
# Ver logs detallados
docker-compose -f docker-compose.prod.yml logs --tail=100 madein-api

# Entrar al contenedor para debugging
docker-compose -f docker-compose.prod.yml exec madein-api bash

# Ver métricas de Nginx
docker-compose -f docker-compose.prod.yml exec nginx cat /var/log/nginx/access.log
```

## 🔧 **Configuración Avanzada**

### **⚡ Optimización de Performance**

```yaml
# En docker-compose.prod.yml, ajustar recursos:
deploy:
  resources:
    limits:
      memory: 8G      # Aumentar para más memoria
      cpus: '4.0'     # Aumentar para más CPUs
    reservations:
      memory: 2G
      cpus: '1.0'
```

### **📈 Scaling Horizontal**

```bash
# Escalar API a múltiples instancias
docker-compose -f docker-compose.prod.yml up -d --scale madein-api=3

# Load balancing automático via Nginx
```

### **💾 Backup Automático**

```bash
# Crear script de backup
cat > /opt/madein-api/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/madein-api/backups"
mkdir -p $BACKUP_DIR

# Backup de volúmenes
tar -czf $BACKUP_DIR/data_$DATE.tar.gz -C /opt/madein-api data/

# Backup de configuración
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C /opt/madein-api *.yml *.env

# Limpiar backups antiguos (más de 30 días)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

chmod +x /opt/madein-api/backup.sh

# Programar backup automático
crontab -e
# Agregar: 0 2 * * * /opt/madein-api/backup.sh
```

## 🚨 **Troubleshooting**

### **❌ Problemas Comunes**

#### **1. Contenedor no inicia**
```bash
# Verificar logs
docker-compose -f docker-compose.prod.yml logs madein-api

# Verificar configuración
docker-compose -f docker-compose.prod.yml config

# Reconstruir imagen
docker-compose -f docker-compose.prod.yml build --no-cache madein-api
```

#### **2. Nginx no responde**
```bash
# Verificar configuración de Nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Recargar configuración
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Verificar puertos
netstat -tlnp | grep :80
```

#### **3. SSL no funciona**
```bash
# Verificar certificados
docker-compose -f docker-compose.prod.yml exec nginx ls -la /etc/nginx/ssl/

# Renovar certificados
docker run --rm -v /opt/madein-api/nginx/ssl:/etc/letsencrypt \
  certbot/certbot renew --quiet
```

#### **4. Performance lenta**
```bash
# Verificar recursos
docker stats

# Verificar logs de API
docker-compose -f docker-compose.prod.yml logs --tail=100 madein-api | grep ERROR

# Ajustar workers en .env.production
WORKERS=4  # Aumentar según CPU disponible
```

### **🔍 Monitoreo de Salud**

```bash
# Script de monitoreo automático
cat > /opt/madein-api/healthcheck.sh << 'EOF'
#!/bin/bash
HEALTH_URL="https://tu-dominio.com/health"
SLACK_WEBHOOK="tu-webhook-slack"

if ! curl -f $HEALTH_URL &>/dev/null; then
    # Enviar alerta
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚨 MADEIN API está DOWN!"}' \
        $SLACK_WEBHOOK
    
    # Intentar reiniciar
    cd /opt/madein-api && docker-compose -f docker-compose.prod.yml restart
fi
EOF

# Ejecutar cada 5 minutos
# */5 * * * * /opt/madein-api/healthcheck.sh
```

## 📈 **Métricas y Análisis**

### **📊 URLs de Monitoreo**
- **API Health**: `https://tu-dominio.com/health`
- **API Docs**: `https://tu-dominio.com/docs`
- **Logs**: `docker-compose logs -f`

### **🎯 KPIs Importantes**
- **Tiempo de respuesta**: < 2 segundos para /health
- **Uso de memoria**: < 80% del límite configurado
- **Uso de CPU**: < 70% promedio
- **Requests exitosos**: > 95%

## 🎉 **Post-Deployment**

### **✅ Checklist Final**
- [ ] API responde en `https://tu-dominio.com/health`
- [ ] Documentación accesible en `https://tu-dominio.com/docs`
- [ ] SSL certificado válido
- [ ] Logs funcionando correctamente
- [ ] Backup automático configurado
- [ ] Monitoreo activo
- [ ] Variables de entorno seguras configuradas

### **📞 Soporte**
Si tienes problemas:
1. Revisa logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verifica configuración: `docker-compose -f docker-compose.prod.yml config`
3. Reinicia servicios: `docker-compose -f docker-compose.prod.yml restart`
4. Contacta soporte técnico con logs específicos

---

## 🎯 **Comandos de Referencia Rápida**

```bash
# Deployment inicial
./deploy.sh production --ssl

# Ver estado
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Actualizar
git pull && ./deploy.sh production --no-cache

# Backup manual
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# Monitoreo
curl -f https://tu-dominio.com/health && echo "✅ OK" || echo "❌ FAIL"
```

**🎉 ¡Tu API MADEIN está lista para producción en DigitalOcean!** 🚀 