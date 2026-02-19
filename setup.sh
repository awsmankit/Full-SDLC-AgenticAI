#!/bin/bash

echo "🚀 Starting setup for Multi-Agent QA System..."

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ 'uv' is not installed. Please install it first: pip install uv"
    exit 1
else
    echo "✅ 'uv' is installed."
fi

# Check for ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ 'ollama' is not installed. Please install it from https://ollama.com/"
    exit 1
else
    echo "✅ 'ollama' is installed."
fi

# Pull Qwen model
echo "⬇️ Pulling qwen2.5:7b model..."
ollama pull qwen2.5:7b

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

echo "🎉 Setup complete! You can now run the system with:"
echo "uv run python -m src.main \"Your product idea\""
