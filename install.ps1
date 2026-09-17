<#
.SYNOPSIS
    Instalador de Custos para Windows.
.DESCRIPTION
    Crea un entorno virtual propio en %LOCALAPPDATA%\Custos\.venv, instala
    PySide6, agrega un acceso directo al menu Inicio y expone el comando
    'custos' en una nueva terminal. Equivalente Windows de install.sh.
#>

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appDir = Join-Path $env:LOCALAPPDATA "Custos"
$binDir = Join-Path $appDir "bin"
$venvDir = Join-Path $appDir ".venv"

$python = $null
foreach ($candidate in @("py", "python")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $python = $candidate
        break
    }
}
if (-not $python) {
    Write-Error "No se encontro Python 3. Instalalo desde https://www.python.org/downloads/ o con 'winget install Python.Python.3.12', y vuelve a ejecutar este script."
    exit 1
}

$requiredFiles = @("generador_contrasenas.py", "wordlist.py", "requirements.txt", "custos.svg")
foreach ($f in $requiredFiles) {
    if (-not (Test-Path (Join-Path $scriptDir $f))) {
        Write-Error "Falta el archivo requerido: $f"
        exit 1
    }
}

Write-Host "Instalando Custos en $appDir"
New-Item -ItemType Directory -Force -Path $appDir, $binDir | Out-Null

foreach ($f in $requiredFiles) {
    Copy-Item (Join-Path $scriptDir $f) (Join-Path $appDir $f) -Force
}
if (Test-Path (Join-Path $scriptDir "LICENSE")) {
    Copy-Item (Join-Path $scriptDir "LICENSE") (Join-Path $appDir "LICENSE") -Force
}

$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    & $python -m venv $venvDir
}

& $venvPython -m pip install --disable-pip-version-check --upgrade pip | Out-Null
& $venvPython -m pip install --disable-pip-version-check -r (Join-Path $appDir "requirements.txt")
& $venvPython -m pip check

# Lanzador de linea de comandos ('custos' en una terminal)
$launcherPath = Join-Path $binDir "custos.cmd"
$launcherContent = "@echo off`r`n`"$venvPython`" `"$appDir\generador_contrasenas.py`" %*`r`n"
[System.IO.File]::WriteAllText($launcherPath, $launcherContent, [System.Text.Encoding]::ASCII)

# Acceso directo del menu Inicio (modo GUI, sin consola)
$venvPythonw = Join-Path $venvDir "Scripts\pythonw.exe"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$shortcutPath = Join-Path $startMenuDir "Custos.lnk"
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $venvPythonw
$shortcut.Arguments = "`"$appDir\generador_contrasenas.py`" --gui"
$shortcut.WorkingDirectory = $appDir
$shortcut.Description = "Generador de contrasenas, frases de paso y lotes seguros"
$shortcut.Save()

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$binDir*") {
    $newPath = if ([string]::IsNullOrEmpty($userPath)) { $binDir } else { "$userPath;$binDir" }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Se agrego $binDir al PATH del usuario. Abre una nueva terminal para usar 'custos'."
}

Write-Host "Custos se instalo correctamente."
Write-Host "Puedes abrirlo desde el menu Inicio (Custos) o ejecutar 'custos' en una nueva terminal."
