<#
.SYNOPSIS
    Compila Custos como un ejecutable Windows independiente (.exe).
.DESCRIPTION
    Crea un entorno virtual de build, instala PySide6 y PyInstaller, y
    empaqueta generador_contrasenas.py en un unico .exe que no requiere
    tener Python instalado para ejecutarse. El resultado queda en dist\Custos.exe.
#>

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildVenv = Join-Path $scriptDir ".venv-build"

$python = $null
foreach ($candidate in @("py", "python")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $python = $candidate
        break
    }
}
if (-not $python) {
    Write-Error "No se encontro Python 3. Instalalo desde https://www.python.org/downloads/ o con 'winget install Python.Python.3.12'."
    exit 1
}

$venvPython = Join-Path $buildVenv "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    & $python -m venv $buildVenv
}

& $venvPython -m pip install --disable-pip-version-check --upgrade pip | Out-Null
& $venvPython -m pip install --disable-pip-version-check -r (Join-Path $scriptDir "requirements.txt") pyinstaller

$iconArgs = @()
$iconPath = Join-Path $scriptDir "custos.ico"
if (Test-Path $iconPath) {
    $iconArgs = @("--icon", $iconPath)
}

Push-Location $scriptDir
try {
    & $venvPython -m PyInstaller `
        --noconfirm `
        --onefile `
        --windowed `
        --name Custos `
        --add-data "custos.svg;." `
        @iconArgs `
        generador_contrasenas.py
}
finally {
    Pop-Location
}

Write-Host "Listo. Ejecutable generado en $scriptDir\dist\Custos.exe"
Write-Host "Nota: --windowed oculta la consola, por lo que dist\Custos.exe abre siempre en modo GUI."
Write-Host "Para el modo CLI desde una terminal, usa install.ps1 (usa python.exe del venv con consola) en vez de este .exe."
