@echo off
setlocal enabledelayedexpansion

REM Script de inicio para MADEIN Image Processing API con Docker (Windows)
REM Uso: docker-start.bat [build|start|stop|restart|logs|status]

title MADEIN API Docker Manager

REM Configuración
set CONTAINER_NAME=madein-image-processing-api
set IMAGE_NAME=madein-api
set SERVICE_NAME=madein-api

echo.
echo ================================================
echo  MADEIN Image Processing API - Docker Manager
echo ================================================
echo.

REM Verificar si Docker está corriendo
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker no está corriendo. Por favor inicia Docker Desktop.
    pause
    exit /b 1
)

REM Procesar argumentos
set ACTION=%1
if "%ACTION%"=="" set ACTION=help

if "%ACTION%"=="build" goto :build
if "%ACTION%"=="start" goto :start
if "%ACTION%"=="stop" goto :stop
if "%ACTION%"=="restart" goto :restart
if "%ACTION%"=="logs" goto :logs
if "%ACTION%"=="status" goto :status
if "%ACTION%"=="cleanup" goto :cleanup
goto :help

:build
echo ℹ️  Construyendo imagen Docker...
docker-compose build --no-cache
if errorlevel 1 (
    echo ❌ Error construyendo imagen
    pause
    exit /b 1
)
echo ✅ Imagen construida exitosamente
goto :end

:start
echo ℹ️  Iniciando servicios...
docker-compose up -d
if errorlevel 1 (
    echo ❌ Error iniciando servicios
    pause
    exit /b 1
)

echo ℹ️  Esperando a que la API esté lista...
timeout /t 10 /nobreak >nul

REM Verificar que la API esté respondiendo
for /l %%i in (1,1,30) do (
    curl -f http://localhost:8000/health >nul 2>&1
    if not errorlevel 1 (
        echo ✅ API está corriendo y respondiendo
        echo 🌐 Documentación API: http://localhost:8000/docs
        echo 🔧 Health Check: http://localhost:8000/health
        goto :end
    )
    timeout /t 2 /nobreak >nul
)

echo ⚠️  La API puede estar iniciando todavía. Verifica los logs con: docker-start.bat logs
goto :end

:stop
echo ℹ️  Deteniendo servicios...
docker-compose down
echo ✅ Servicios detenidos
goto :end

:restart
echo ℹ️  Reiniciando servicios...
call :stop
call :start
goto :end

:logs
echo ℹ️  Mostrando logs de la API...
docker-compose logs -f %SERVICE_NAME%
goto :end

:status
echo ℹ️  Estado de los servicios:
docker-compose ps
echo.

REM Verificar si hay servicios corriendo
docker-compose ps | findstr "Up" >nul
if not errorlevel 1 (
    echo ℹ️  URLs disponibles:
    echo   🌐 API Docs: http://localhost:8000/docs
    echo   🔧 Health: http://localhost:8000/health
    echo   📊 Redoc: http://localhost:8000/redoc
)
goto :end

:cleanup
echo ℹ️  Limpiando contenedores e imágenes...
docker-compose down --rmi all --volumes --remove-orphans
echo ✅ Cleanup completado
goto :end

:help
echo Uso: %0 [comando]
echo.
echo Comandos disponibles:
echo   build     - Construir imagen Docker
echo   start     - Iniciar servicios
echo   stop      - Detener servicios
echo   restart   - Reiniciar servicios
echo   logs      - Mostrar logs de la API
echo   status    - Mostrar estado de servicios
echo   cleanup   - Limpiar contenedores e imágenes
echo   help      - Mostrar esta ayuda
echo.
echo Ejemplos:
echo   %0 build    # Construir imagen
echo   %0 start    # Iniciar API
echo   %0 logs     # Ver logs en tiempo real
echo.

:end
if "%ACTION%"=="logs" goto :skip_pause
pause
:skip_pause
endlocal 