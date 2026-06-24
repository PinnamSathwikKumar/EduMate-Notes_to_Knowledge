#!/bin/bash
# Build script for Edumate Docker image

set -e

echo "🐳 Building Edumate Docker Image..."
echo ""

# Check if models directory exists
if [ ! -d "models" ]; then
    echo "❌ Error: models/ directory not found!"
    echo "   Please run download_models.py first to download all required models."
    exit 1
fi

# Check if required model directories exist
REQUIRED_MODELS=("summarizer" "qa_model" "sentence_embedder" "en-hi" "en-te" "vosk-model-small-en-us-0.15")
MISSING_MODELS=()

for model in "${REQUIRED_MODELS[@]}"; do
    if [ ! -d "models/$model" ]; then
        MISSING_MODELS+=("$model")
    fi
done

if [ ${#MISSING_MODELS[@]} -ne 0 ]; then
    echo "⚠️  Warning: Missing model directories:"
    for model in "${MISSING_MODELS[@]}"; do
        echo "   - models/$model"
    done
    echo ""
    echo "   Some features may not work. Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Build cancelled."
        exit 1
    fi
fi

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t sathwikkumar/edumate:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Docker image built successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Test locally:"
    echo "      docker run -d --name edumate-test -p 5000:5000 sathwikkumar/edumate:latest"
    echo ""
    echo "   2. Push to Docker Hub:"
    echo "      docker login"
    echo "      docker push sathwikkumar/edumate:latest"
    echo ""
    echo "   3. Or use docker-compose:"
    echo "      docker-compose up -d"
else
    echo "❌ Build failed!"
    exit 1
fi

