# ============================================
# Script para configurar Ollama en Docker
# ============================================

Write-Host "🚀 Configurando Ollama con Docker..." -ForegroundColor Cyan
Write-Host ""

# Verificar si Docker está corriendo
Write-Host "📋 Verificando Docker..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker no está corriendo. Por favor inicia Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker está corriendo" -ForegroundColor Green
Write-Host ""

# Iniciar servicios con docker-compose
Write-Host "🐳 Iniciando servicios (PostgreSQL, Redis, Ollama)..." -ForegroundColor Yellow
Set-Location -Path (Split-Path -Parent $PSScriptRoot)
docker-compose -f docker/docker-compose.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al iniciar servicios" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Servicios iniciados" -ForegroundColor Green
Write-Host ""

# Esperar a que Ollama esté listo
Write-Host "⏳ Esperando a que Ollama esté listo..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$ollamaReady = $false

while ($attempt -lt $maxAttempts -and -not $ollamaReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $ollamaReady = $true
        }
    } catch {
        Start-Sleep -Seconds 2
        $attempt++
        Write-Host "." -NoNewline
    }
}

Write-Host ""

if (-not $ollamaReady) {
    Write-Host "❌ Timeout esperando a Ollama. Verifica los logs con: docker logs rim-ollama" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Ollama está listo" -ForegroundColor Green
Write-Host ""

# Descargar modelo Llama 3.1 8B
Write-Host "📥 Descargando modelo Llama 3.1 8B (esto puede tardar varios minutos)..." -ForegroundColor Yellow
Write-Host "    Tamaño aproximado: 4.7 GB" -ForegroundColor Gray
Write-Host ""

docker exec rim-ollama ollama pull llama3.1:8b

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al descargar el modelo" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Modelo descargado exitosamente" -ForegroundColor Green
Write-Host ""

# Probar el modelo
Write-Host "🧪 Probando el modelo..." -ForegroundColor Yellow
$testPrompt = "Responde brevemente: ¿Qué eres?"
$testResponse = docker exec rim-ollama ollama run llama3.1:8b "$testPrompt"

Write-Host ""
Write-Host "📝 Respuesta del modelo:" -ForegroundColor Cyan
Write-Host $testResponse -ForegroundColor White
Write-Host ""

# Resumen final
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✨ CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Servicios disponibles:" -ForegroundColor Cyan
Write-Host "  • PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "  • Redis:      localhost:6379" -ForegroundColor White
Write-Host "  • Ollama:     localhost:11434" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Modelo Ollama:" -ForegroundColor Cyan
Write-Host "  • llama3.1:8b (listo para usar)" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Comandos útiles:" -ForegroundColor Cyan
Write-Host "  • Ver logs:        docker logs rim-ollama -f" -ForegroundColor Gray
Write-Host "  • Detener:         docker-compose -f docker/docker-compose.yml down" -ForegroundColor Gray
Write-Host "  • Reiniciar:       docker-compose -f docker/docker-compose.yml restart" -ForegroundColor Gray
Write-Host "  • Lista modelos:   docker exec rim-ollama ollama list" -ForegroundColor Gray
Write-Host ""
Write-Host "🚀 Siguiente paso: Ejecuta tu aplicación FastAPI" -ForegroundColor Yellow
Write-Host "   uvicorn src.main:app --reload" -ForegroundColor White
Write-Host ""
