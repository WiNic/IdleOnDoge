#!/bin/bash

# Define the target directory
TARGET_DIR="src"

echo "🚀 Running Ruff (Linting)..."
uv run ruff check "$TARGET_DIR"
if [ $? -ne 0 ]; then
    echo "❌ Ruff found issues!"
fi

echo "🛠 Running isort (Sorting imports)..."
uv run isort "$TARGET_DIR"

echo "🔍 Running mypy (Type Checking)..."
uv run mypy "$TARGET_DIR"
if [ $? -ne 0 ]; then
    echo "❌ mypy found issues!"
fi

echo "✅ All checks passed!"
exit 0
