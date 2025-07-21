#!/bin/bash

# Script de inicio para MADEIN Image Processing API con Docker
# Uso: ./docker-start.sh [build|start|stop|restart|logs|status]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
CONTAINER_NAME="madein-image-processing-api"
IMAGE_NAME="madein-api"
SERVICE_NAME="madein-api"

# Funciones de utilidad
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE} MADEIN Image Processing API - Docker Manager${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Verificar si Docker está corriendo
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker no está corriendo. Por favor inicia Docker Desktop."
        exit 1
    fi
}

# Construir imagen
build_image() {
    print_info "Construyendo imagen Docker..."
    docker-compose build --no-cache
    print_success "Imagen construida exitosamente"
}

# Iniciar servicios
start_services() {
    print_info "Iniciando servicios..."
    docker-compose up -d
    
    # Esperar a que el servicio esté listo
    print_info "Esperando a que la API esté lista..."
    sleep 10
    
    # Verificar health check
    for i in {1..30}; do
        if docker-compose exec $SERVICE_NAME curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_success "API está corriendo y respondiendo"
            print_info "🌐 Documentación API: http://localhost:8000/docs"
            print_info "🔧 Health Check: http://localhost:8000/health"
            return 0
        fi
        sleep 2
    done
    
    print_warning "La API puede estar iniciando todavía. Verifica los logs con: ./docker-start.sh logs"
}

# Detener servicios
stop_services() {
    print_info "Deteniendo servicios..."
    docker-compose down
    print_success "Servicios detenidos"
}

# Reiniciar servicios
restart_services() {
    print_info "Reiniciando servicios..."
    stop_services
    start_services
}

# Mostrar logs
show_logs() {
    print_info "Mostrando logs de la API..."
    docker-compose logs -f $SERVICE_NAME
}

# Mostrar estado
show_status() {
    print_info "Estado de los servicios:"
    docker-compose ps
    echo ""
    
    if docker-compose ps | grep -q "Up"; then
        print_info "URLs disponibles:"
        echo "  🌐 API Docs: http://localhost:8000/docs"
        echo "  🔧 Health: http://localhost:8000/health"
        echo "  📊 Redoc: http://localhost:8000/redoc"
    fi
}

# Limpiar contenedores e imágenes
cleanup() {
    print_info "Limpiando contenedores e imágenes..."
    docker-compose down --rmi all --volumes --remove-orphans
    print_success "Cleanup completado"
}

# Función principal
main() {
    print_header
    check_docker
    
    case "${1:-help}" in
        build)
            build_image
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        cleanup)
            cleanup
            ;;
        help|*)
            echo "Uso: $0 [comando]"
            echo ""
            echo "Comandos disponibles:"
            echo "  build     - Construir imagen Docker"
            echo "  start     - Iniciar servicios"
            echo "  stop      - Detener servicios"
            echo "  restart   - Reiniciar servicios"
            echo "  logs      - Mostrar logs de la API"
            echo "  status    - Mostrar estado de servicios"
            echo "  cleanup   - Limpiar contenedores e imágenes"
            echo "  help      - Mostrar esta ayuda"
            echo ""
            echo "Ejemplos:"
            echo "  $0 build    # Construir imagen"
            echo "  $0 start    # Iniciar API"
            echo "  $0 logs     # Ver logs en tiempo real"
            ;;
    esac
}

# Ejecutar función principal
main "$@" 