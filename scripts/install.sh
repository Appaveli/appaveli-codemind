#!/bin/bash

echo "🔄 Reinstalling Appaveli CodeMind with pipx..."

# Uninstall if already installed
if pipx list | grep -q "appaveli-codemind"; then
  echo "🧹 Uninstalling existing version..."
  pipx uninstall appaveli-codemind
fi

# Reinstall in editable mode
echo "📦 Installing editable version..."
pipx install --editable .

echo "✅ appaveli-codemind is now globally available!"