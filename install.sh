#!/bin/bash
set -e

echo "=== Installing thatstui ==="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Detect source
if [ -f "pyproject.toml" ] && grep -q "name = \"thatstui\"" pyproject.toml; then
    echo "Found local source. Installing from local directory..."
    INSTALL_SRC="."
else
    INSTALL_SRC="git+https://github.com/thecapibara/thatstui.git"
fi

# Install
if command -v pipx &> /dev/null; then
    echo "Installing via pipx..."
    pipx install "$INSTALL_SRC" --force
elif command -v pip3 &> /dev/null; then
    echo "pipx not found. Installing via pip3..."
    python3 -m pip install --user "$INSTALL_SRC" --break-system-packages 2>/dev/null || python3 -m pip install --user "$INSTALL_SRC"
else
    echo "Error: Neither pipx nor pip was found. Please install pip or pipx."
    exit 1
fi

echo "=== Installation complete! ==="
echo "You can now run the game using the command: thatstui"
