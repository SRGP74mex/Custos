<#
.SYNOPSIS
    Genera un instalador MSI para Custos con WiX Toolset v3.
.DESCRIPTION
    Empaqueta dist\Custos.exe (generado por build_windows.ps1) en un MSI que
    instala en Program Files, crea el acceso directo del menu Inicio y
    registra la entrada en Agregar o quitar programas, con desinstalacion
    y actualizacion (MajorUpgrade) manejadas por Windows Installer.

    Requiere WiX Toolset v3 (candle.exe / light.exe):
    winget install WiXToolset.WiXToolset
.PARAMETER Version
    Version del producto en formato MSI (major.minor.build.revision).
#>

param(
    [string]$Version = "1.0.0.0"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$distDir = Join-Path $scriptDir "dist"
$distExe = Join-Path $distDir "Custos.exe"
$iconPath = Join-Path $scriptDir "custos.ico"
$wixDir = Join-Path $scriptDir "wix"
$licenseRtf = Join-Path $wixDir "License.rtf"

if (-not (Test-Path $distExe)) {
    Write-Error "No se encontro $distExe. Ejecuta primero .\build_windows.ps1."
    exit 1
}
if (-not (Test-Path $iconPath)) {
    Write-Error "No se encontro $iconPath (custos.ico)."
    exit 1
}

$wixBinCandidates = @(
    "C:\Program Files (x86)\WiX Toolset v3.14\bin",
    "C:\Program Files (x86)\WiX Toolset v3.11\bin",
    "C:\Program Files\WiX Toolset v3.14\bin"
)
$wixBin = $wixBinCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $wixBin) {
    Write-Error "No se encontro WiX Toolset v3 (candle.exe/light.exe). Instalalo con 'winget install WiXToolset.WiXToolset'."
    exit 1
}

$candle = Join-Path $wixBin "candle.exe"
$light = Join-Path $wixBin "light.exe"

& $candle -nologo `
    -arch x64 `
    -dSourceDir="$distDir" `
    -dProductVersion="$Version" `
    -dLicenseRtf="$licenseRtf" `
    -out "$wixDir\Product.wixobj" `
    "$wixDir\Product.wxs"
if ($LASTEXITCODE -ne 0) { Write-Error "candle.exe fallo (exit $LASTEXITCODE)"; exit $LASTEXITCODE }

& $light -nologo `
    -ext WixUIExtension `
    -cultures:en-us `
    -sice:ICE61 `
    -out "$distDir\Custos-Setup.msi" `
    "$wixDir\Product.wixobj"
if ($LASTEXITCODE -ne 0) { Write-Error "light.exe fallo (exit $LASTEXITCODE)"; exit $LASTEXITCODE }

Write-Host "Listo. MSI generado en $distDir\Custos-Setup.msi"
