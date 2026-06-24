# PowerShell build script for Edumate Docker image

Write-Host "🐳 Building Edumate Docker Image..." -ForegroundColor Cyan
Write-Host ""

# Check if models directory exists
if (-Not (Test-Path "models")) {
    Write-Host "❌ Error: models/ directory not found!" -ForegroundColor Red
    Write-Host "   Please run download_models.py first to download all required models." -ForegroundColor Yellow
    exit 1
}

# Check if required model directories exist
$requiredModels = @("summarizer", "qa_model", "sentence_embedder", "en-hi", "en-te", "vosk-model-small-en-us-0.15")
$missingModels = @()

foreach ($model in $requiredModels) {
    if (-Not (Test-Path "models\$model")) {
        $missingModels += $model
    }
}

if ($missingModels.Count -gt 0) {
    Write-Host "⚠️  Warning: Missing model directories:" -ForegroundColor Yellow
    foreach ($model in $missingModels) {
        Write-Host "   - models\$model" -ForegroundColor Yellow
    }
    Write-Host ""
    $response = Read-Host "   Some features may not work. Continue anyway? (y/n)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Build cancelled." -ForegroundColor Red
        exit 1
    }
}

# Build the Docker image
Write-Host "📦 Building Docker image..." -ForegroundColor Cyan
docker build -t sathwikkumar/edumate:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Docker image built successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Test locally:"
    Write-Host "      docker run -d --name edumate-test -p 5000:5000 sathwikkumar/edumate:latest"
    Write-Host ""
    Write-Host "   2. Push to Docker Hub:"
    Write-Host "      docker login"
    Write-Host "      docker push sathwikkumar/edumate:latest"
    Write-Host ""
    Write-Host "   3. Or use docker-compose:"
    Write-Host "      docker-compose up -d"
} else {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

