#!/usr/bin/env bash
# Quick start script for AutoML Backend

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     AutoML Pipeline Backend - Quick Start Guide              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "⚠  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✓ Created .env"
    echo ""
    echo "📝 IMPORTANT: Edit .env and add your GROQ_API_KEY"
    echo "   Get it from: https://console.groq.com"
    echo ""
fi

# Check Python
if ! command -v python &> /dev/null; then
    echo "✗ Python not found. Please install Python 3.9+"
    exit 1
fi

echo "✓ Python found: $(python --version)"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
python -m pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Ready to Start!                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

echo ""
echo "🚀 To start the server, run:"
echo ""
echo "    uvicorn main:app --reload"
echo ""
echo "The server will start at: http://localhost:8000"
echo ""
echo "📖 API Documentation (Swagger UI):"
echo "    http://localhost:8000/docs"
echo ""
echo "🧪 Run test suite (in another terminal):"
echo "    python test_api.py"
echo ""
echo "📚 Full documentation:"
echo "    cat BACKEND_README.md"
echo ""
