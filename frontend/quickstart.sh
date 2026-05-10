#!/bin/bash

# AutoML Frontend Setup Script
# Run this script to install dependencies and start the development server

echo "🚀 AutoML Frontend Setup"
echo "========================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "✓ Node.js version: $(node --version)"
echo "✓ npm version: $(npm --version)"
echo ""

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "⚠️  Backend is not running. Make sure to start it first:"
    echo "   cd ../automl-backend"
    echo "   uvicorn main:app --reload"
    echo ""
fi

echo "📦 Installing dependencies..."
npm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "Starting development server..."
echo "🌐 Frontend will be available at: http://localhost:3000"
echo ""

npm run dev
