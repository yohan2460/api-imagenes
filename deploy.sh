#!/bin/bash

# Script de Deployment para MADEIN API en DigitalOcean
# Uso: ./deploy.sh [local|staging|production] [opciones]

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Configuración por defecto
ENVIRONMENT=${1:-local}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-}
PROJECT_NAME="madein-api"
VERSION=${VERSION:-latest}
DEPLOY_PATH="/opt/madein-api"

# Función de ayuda
show_help() {
    echo "Uso: $0 [ENVIRONMENT] [OPCIONES]"
    echo ""
    echo "AMBIENTES:"
    echo "  local       - Deployment local para desarrollo"
    echo "  staging     - Deployment en servidor de staging"
    echo "  production  - Deployment en producción"
    echo ""
    echo "OPCIONES:"
    echo "  --build-only    Solo construir, no desplegar"
    echo "  --no-cache      Construir sin cache"
    echo "  --pull          Actualizar imágenes base"
    echo "  --clean         Limpiar contenedores y volúmenes anteriores"
    echo "  --ssl           Configurar SSL automáticamente (solo producción)"
    echo "  --help          Mostrar esta ayuda"
    echo ""
    echo "VARIABLES DE ENTORNO:"
    echo "  DOCKER_REGISTRY - Registry de Docker (opcional)"
    echo "  VERSION         - Versión a desplegar (default: latest)"
    echo "  DOMAIN          - Dominio para SSL (solo producción)"
    echo "  EMAIL           - Email para Let's Encrypt (solo producción)"
}

# Validar ambiente
validate_environment() {
    case $ENVIRONMENT in
        local|staging|production)
            log "Desplegando en ambiente: $ENVIRONMENT"
            ;;
        *)
            error "Ambiente no válido: $ENVIRONMENT"
            show_help
            exit 1
            ;;
    esac
}

# Verificar prerequisitos
check_prerequisites() {
    log "Verificando prerequisitos..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado"
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está instalado"
        exit 1
    fi
    
    # Verificar que Docker está corriendo
    if ! docker info &> /dev/null; then
        error "Docker no está corriendo"
        exit 1
    fi
    
    info "Prerequisitos OK"
}

# Crear directorios necesarios
setup_directories() {
    log "Configurando directorios..."
    
    case $ENVIRONMENT in
        production|staging)
            sudo mkdir -p $DEPLOY_PATH/{data/{uploads,outputs,logs},nginx/{ssl,conf.d}}
            sudo chown -R $USER:$USER $DEPLOY_PATH
            ;;
        local)
            mkdir -p ./data/{uploads,outputs,logs}
            mkdir -p ./nginx/{ssl,conf.d}
            ;;
    esac
    
    info "Directorios configurados"
}

# Configurar variables de entorno
setup_environment() {
    log "Configurando variables de entorno para $ENVIRONMENT..."
    
    case $ENVIRONMENT in
        production)
            cat > .env.prod << EOF
# Configuración de Producción
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
WORKERS=4

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://${DOMAIN:-api.madein.com}

# Procesamiento
MIN_AREA=50000
PDF_DPI=300
OCR_LANGUAGES=es,en
MAX_FILE_SIZE=100

# Paths
DATA_PATH=$DEPLOY_PATH/data
UPLOAD_DIR=/app/uploads
OUTPUT_DIR=/app/outputs

# Security
API_TOKEN=${API_TOKEN:-$(openssl rand -hex 32)}

# SSL
DOMAIN=${DOMAIN:-}
EMAIL=${EMAIL:-}
EOF
            ;;
        staging)
            cat > .env.staging << EOF
# Configuración de Staging
ENVIRONMENT=staging
DEBUG=true
LOG_LEVEL=debug
WORKERS=2

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://staging.madein.com,http://localhost:3000

# Procesamiento
MIN_AREA=50000
PDF_DPI=300
OCR_LANGUAGES=es,en
MAX_FILE_SIZE=50

# Paths
DATA_PATH=$DEPLOY_PATH/data
UPLOAD_DIR=/app/uploads
OUTPUT_DIR=/app/outputs

# Security
API_TOKEN=${API_TOKEN:-staging-token-123}
EOF
            ;;
        local)
            cp env.example .env.local 2>/dev/null || true
            ;;
    esac
    
    info "Variables de entorno configuradas"
}

# Construir imágenes
build_images() {
    log "Construyendo imágenes Docker..."
    
    BUILD_ARGS=""
    if [[ "$*" == *"--no-cache"* ]]; then
        BUILD_ARGS="$BUILD_ARGS --no-cache"
    fi
    
    if [[ "$*" == *"--pull"* ]]; then
        BUILD_ARGS="$BUILD_ARGS --pull"
    fi
    
    case $ENVIRONMENT in
        production|staging)
            docker-compose -f docker-compose.prod.yml build $BUILD_ARGS
            ;;
        local)
            docker-compose build $BUILD_ARGS
            ;;
    esac
    
    info "Imágenes construidas exitosamente"
}

# Limpiar contenedores anteriores
cleanup_containers() {
    if [[ "$*" == *"--clean"* ]]; then
        log "Limpiando contenedores anteriores..."
        
        case $ENVIRONMENT in
            production|staging)
                docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
                ;;
            local)
                docker-compose down --remove-orphans 2>/dev/null || true
                ;;
        esac
        
        # Limpiar imágenes no utilizadas
        docker image prune -f
        
        info "Limpieza completada"
    fi
}

# Configurar SSL con Let's Encrypt
setup_ssl() {
    if [[ "$*" == *"--ssl"* ]] && [[ "$ENVIRONMENT" == "production" ]]; then
        log "Configurando SSL con Let's Encrypt..."
        
        if [[ -z "$DOMAIN" ]] || [[ -z "$EMAIL" ]]; then
            error "Variables DOMAIN y EMAIL son requeridas para SSL"
            exit 1
        fi
        
        # Crear configuración temporal para obtener certificados
        docker run --rm -v "${DEPLOY_PATH}/nginx/ssl:/etc/letsencrypt" \
            certbot/certbot certonly --standalone \
            --email $EMAIL --agree-tos --no-eff-email \
            -d $DOMAIN
        
        # Configurar renovación automática
        echo "0 12 * * * docker run --rm -v ${DEPLOY_PATH}/nginx/ssl:/etc/letsencrypt certbot/certbot renew --quiet" | sudo crontab -
        
        info "SSL configurado para $DOMAIN"
    fi
}

# Desplegar aplicación
deploy_application() {
    log "Desplegando aplicación..."
    
    case $ENVIRONMENT in
        production)
            docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
            ;;
        staging)
            docker-compose -f docker-compose.prod.yml --env-file .env.staging up -d
            ;;
        local)
            docker-compose --env-file .env.local up -d
            ;;
    esac
    
    info "Aplicación desplegada"
}

# Verificar deployment
verify_deployment() {
    log "Verificando deployment..."
    
    # Esperar que los servicios estén listos
    sleep 30
    
    # Verificar health check
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost/health &>/dev/null; then
            log "✅ Health check OK"
            break
        fi
        
        warning "Intento $attempt/$max_attempts - Esperando que la API esté lista..."
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        error "❌ Health check falló después de $max_attempts intentos"
        return 1
    fi
    
    # Mostrar estado de contenedores
    case $ENVIRONMENT in
        production|staging)
            docker-compose -f docker-compose.prod.yml ps
            ;;
        local)
            docker-compose ps
            ;;
    esac
    
    info "Deployment verificado exitosamente"
}

# Mostrar información post-deployment
show_deployment_info() {
    log "🎉 Deployment completado exitosamente!"
    echo ""
    info "URLs disponibles:"
    
    case $ENVIRONMENT in
        production)
            echo "  🌐 API: https://${DOMAIN:-your-domain.com}"
            echo "  📚 Docs: https://${DOMAIN:-your-domain.com}/docs"
            echo "  ❤️ Health: https://${DOMAIN:-your-domain.com}/health"
            ;;
        staging)
            echo "  🌐 API: http://staging.madein.com"
            echo "  📚 Docs: http://staging.madein.com/docs"
            echo "  ❤️ Health: http://staging.madein.com/health"
            ;;
        local)
            echo "  🌐 API: http://localhost:8000"
            echo "  📚 Docs: http://localhost:8000/docs"
            echo "  ❤️ Health: http://localhost:8000/health"
            ;;
    esac
    
    echo ""
    info "Comandos útiles:"
    echo "  📊 Ver logs: docker-compose logs -f"
    echo "  🔄 Restart: docker-compose restart"
    echo "  🛑 Stop: docker-compose down"
    echo "  🧹 Clean: ./deploy.sh $ENVIRONMENT --clean"
}

# Función principal
main() {
    # Procesar argumentos
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
    esac
    
    if [[ "$*" == *"--build-only"* ]]; then
        log "🏗️ Modo solo construcción activado"
        validate_environment
        check_prerequisites
        build_images "$@"
        log "✅ Construcción completada"
        exit 0
    fi
    
    # Ejecutar deployment completo
    log "🚀 Iniciando deployment de MADEIN API"
    
    validate_environment
    check_prerequisites
    setup_directories
    setup_environment
    cleanup_containers "$@"
    build_images "$@"
    setup_ssl "$@"
    deploy_application
    verify_deployment
    show_deployment_info
    
    log "🎉 ¡Deployment completado exitosamente!"
}

# Ejecutar función principal con todos los argumentos
main "$@" 