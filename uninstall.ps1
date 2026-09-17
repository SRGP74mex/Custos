<#
.SYNOPSIS
    Desinstalador de Custos para Windows.
.DESCRIPTION
    Elimina el entorno instalado por install.ps1: carpeta de la app,
    acceso directo del menu Inicio y entrada en el PATH del usuario.
#>

$ErrorActionPreference = "Stop"

$appDir = Join-Path $env:LOCALAPPDATA "Custos"
$binDir = Join-Path $appDir "bin"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$shortcutPath = Join-Path $startMenuDir "Custos.lnk"

if (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath -Force
}

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -and ($userPath -like "*$binDir*")) {
    $newPath = ($userPath -split ";" | Where-Object { $_ -and ($_ -ne $binDir) }) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
}

if (Test-Path $appDir) {
    Remove-Item $appDir -Recurse -Force
}

Write-Host "Custos se desinstalo correctamente."
