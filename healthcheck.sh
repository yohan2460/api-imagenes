#!/bin/bash

# Script de Health Check para MADEIN API
# Uso: ./healthcheck.sh [URL] [opciones]

set -e

# Configuración por defecto
API_URL=${1:-"http://localhost:8000"}
TIMEOUT=${TIMEOUT:-10}
MAX_RETRIES=${MAX_RETRIES:-3}
NOTIFICATION_WEBHOOK=${NOTIFICATION_WEBHOOK:-}

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Función para enviar notificaciones
send_notification() {
    local status=$1
    local message=$2
    
    if [[ -n "$NOTIFICATION_WEBHOOK" ]]; then
        local emoji="🚨"
        [[ "$status" == "OK" ]] && emoji="✅"
        
        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$emoji MADEIN API: $message\"}" \
            "$NOTIFICATION_WEBHOOK" >/dev/null 2>&1 || true
    fi
}

# Health check de la API
check_api_health() {
    local url="$API_URL/health"
    local attempt=1
    
    log "Verificando health de API en: $url"
    
    while [ $attempt -le $MAX_RETRIES ]; do
        info "Intento $attempt/$MAX_RETRIES"
        
        # Realizar request con timeout
        if response=$(curl -s -f --max-time $TIMEOUT "$url" 2>/dev/null); then
            # Verificar que la respuesta contenga status: ok
            if echo "$response" | grep -q '"status":"ok"' || echo "$response" | grep -q '"status": "ok"'; then
                log "✅ API Health Check OK"
                echo "$response"
                return 0
            else
                warning "API responde pero status no es 'ok': $response"
            fi
        else
            warning "No se pudo conectar a la API (intento $attempt/$MAX_RETRIES)"
        fi
        
        ((attempt++))
        [[ $attempt -le $MAX_RETRIES ]] && sleep 5
    done
    
    error "❌ API Health Check FAILED después de $MAX_RETRIES intentos"
    return 1
}

# Health check de documentación
check_docs() {
    local url="$API_URL/docs"
    
    info "Verificando documentación en: $url"
    
    if curl -s -f --max-time $TIMEOUT "$url" >/dev/null 2>&1; then
        log "✅ Documentación accesible"
        return 0
    else
        warning "⚠️ Documentación no accesible"
        return 1
    fi
}

# Health check de contenedores Docker
check_docker_containers() {
    info "Verificando contenedores Docker..."
    
    # Verificar si Docker está disponible
    if ! command -v docker &> /dev/null; then
        warning "Docker no está disponible"
        return 1
    fi
    
    # Verificar contenedores de la aplicación
    local containers=$(docker ps --filter "name=madein" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null)
    
    if [[ -n "$containers" ]]; then
        log "Contenedores MADEIN:"
        echo "$containers"
        
        # Verificar que todos estén healthy
        local unhealthy=$(docker ps --filter "name=madein" --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null)
        if [[ -n "$unhealthy" ]]; then
            error "Contenedores no saludables: $unhealthy"
            return 1
        else
            log "✅ Todos los contenedores están saludables"
            return 0
        fi
    else
        warning "No se encontraron contenedores MADEIN"
        return 1
    fi
}

# Verificar uso de recursos
check_resources() {
    info "Verificando uso de recursos..."
    
    if command -v docker &> /dev/null; then
        # Obtener estadísticas de contenedores
        local stats=$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep madein || true)
        
        if [[ -n "$stats" ]]; then
            log "Uso de recursos:"
            echo "$stats"
        fi
    fi
    
    # Verificar espacio en disco
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        warning "⚠️ Uso de disco alto: ${disk_usage}%"
        return 1
    else
        info "Uso de disco: ${disk_usage}%"
    fi
    
    return 0
}

# Función principal
main() {
    local exit_code=0
    local checks_passed=0
    local total_checks=0
    
    log "🏥 Iniciando Health Check de MADEIN API"
    
    # Health check de API
    ((total_checks++))
    if check_api_health; then
        ((checks_passed++))
    else
        exit_code=1
        send_notification "FAIL" "API Health Check falló"
    fi
    
    # Health check de documentación
    ((total_checks++))
    if check_docs; then
        ((checks_passed++))
    else
        # Documentación no es crítica
        warning "Documentación no accesible (no crítico)"
    fi
    
    # Health check de contenedores
    ((total_checks++))
    if check_docker_containers; then
        ((checks_passed++))
    else
        exit_code=1
        send_notification "FAIL" "Contenedores Docker no están saludables"
    fi
    
    # Verificar recursos
    ((total_checks++))
    if check_resources; then
        ((checks_passed++))
    else
        # Recursos no es crítico pero es importante
        warning "Recursos del sistema bajo estrés"
    fi
    
    # Resumen final
    echo ""
    if [[ $exit_code -eq 0 ]]; then
        log "🎉 Health Check PASSED ($checks_passed/$total_checks checks OK)"
        send_notification "OK" "Todos los checks pasaron ($checks_passed/$total_checks)"
    else
        error "❌ Health Check FAILED ($checks_passed/$total_checks checks OK)"
        send_notification "FAIL" "Health check falló ($checks_passed/$total_checks checks OK)"
    fi
    
    exit $exit_code
}

# Mostrar ayuda
show_help() {
    echo "Uso: $0 [URL] [opciones]"
    echo ""
    echo "PARÁMETROS:"
    echo "  URL                  URL base de la API (default: http://localhost:8000)"
    echo ""
    echo "VARIABLES DE ENTORNO:"
    echo "  TIMEOUT              Timeout en segundos (default: 10)"
    echo "  MAX_RETRIES          Número máximo de reintentos (default: 3)"
    echo "  NOTIFICATION_WEBHOOK Webhook para notificaciones (Slack/Discord)"
    echo ""
    echo "EJEMPLOS:"
    echo "  $0                                    # Local"
    echo "  $0 https://api.tudominio.com         # Producción"
    echo "  TIMEOUT=30 $0 https://api.tudominio.com # Con timeout personalizado"
}

# Procesar argumentos
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac 