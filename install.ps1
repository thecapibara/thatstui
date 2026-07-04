Write-Host "=== Installing thatstui ===" -ForegroundColor Cyan

# Check Python
$pythonCmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
}

if (-not $pythonCmd) {
    Write-Host "Error: Python is required but not installed." -ForegroundColor Red
    exit 1
}

# Detect source
$INSTALL_SRC = "git+https://github.com/thecapibara/thatstui.git"
if (Test-Path "pyproject.toml") {
    $content = Get-Content "pyproject.toml" -Raw
    if ($content -match 'name = "thatstui"') {
        Write-Host "Found local source. Installing from local directory..."
        $INSTALL_SRC = "."
    }
}

# Install
if (Get-Command pipx -ErrorAction SilentlyContinue) {
    Write-Host "Installing via pipx..."
    pipx install "$INSTALL_SRC" --force
} else {
    Write-Host "pipx not found. Installing via pip..."
    & $pythonCmd -m pip install --user "$INSTALL_SRC"
}

Write-Host "=== Installation complete! ===" -ForegroundColor Green
Write-Host "You can now run the game using the command: thatstui"
