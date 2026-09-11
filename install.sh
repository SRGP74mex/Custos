#!/bin/sh
set -eu
umask 077

if [ "$(id -u)" -eq 0 ]; then
    echo "No ejecutes este instalador con sudo. La instalación es para el usuario actual." >&2
    exit 1
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
bin_home="${XDG_BIN_HOME:-$HOME/.local/bin}"
app_dir="$data_home/custos"
desktop_dir="$data_home/applications"
icon_dir="$data_home/icons/hicolor/scalable/apps"

for required in python3 "$script_dir/generador_contrasenas.py" "$script_dir/wordlist.py" "$script_dir/requirements.txt"; do
    if ! command -v "$required" >/dev/null 2>&1 && [ ! -f "$required" ]; then
        echo "Falta el requisito: $required" >&2
        exit 1
    fi
done

if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "Falta el módulo venv. En Debian: sudo apt install python3-venv" >&2
    exit 1
fi

echo "Instalando Custos en $app_dir"
install -d -m 700 "$app_dir" "$bin_home" "$desktop_dir" "$icon_dir"
install -m 600 "$script_dir/generador_contrasenas.py" "$app_dir/generador_contrasenas.py"
install -m 600 "$script_dir/wordlist.py" "$app_dir/wordlist.py"
install -m 600 "$script_dir/requirements.txt" "$app_dir/requirements.txt"
install -m 644 "$script_dir/custos.svg" "$app_dir/custos.svg"
if [ -f "$script_dir/LICENSE" ]; then
    install -m 644 "$script_dir/LICENSE" "$app_dir/LICENSE"
fi

if [ ! -x "$app_dir/.venv/bin/python" ]; then
    python3 -m venv "$app_dir/.venv"
fi
"$app_dir/.venv/bin/python" -m pip install --disable-pip-version-check -r "$app_dir/requirements.txt"
"$app_dir/.venv/bin/python" -m pip check

# Enlaces simbólicos para que el proceso no sea genéricamente 'python3'
ln -sf python "$app_dir/.venv/bin/custos"
ln -sf python "$app_dir/.venv/bin/password-studio"
if [ -d "$script_dir/.venv/bin" ]; then
    ln -sf python "$script_dir/.venv/bin/custos"
    ln -sf python "$script_dir/.venv/bin/password-studio"
fi

install -m 755 "$script_dir/custos" "$bin_home/custos"
ln -sf custos "$bin_home/password-studio"

install -m 644 "$script_dir/custos.desktop" "$desktop_dir/custos.desktop"
install -m 644 "$script_dir/custos.svg" "$icon_dir/custos.svg"

# Limpieza de versión anterior si existe
rm -f -- "$desktop_dir/password-studio.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$desktop_dir" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$data_home/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Custos se instaló correctamente."
echo "Puedes abrirlo desde el menú de aplicaciones o ejecutar: $bin_home/custos"
