#!/bin/sh
set -eu

data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
bin_home="${XDG_BIN_HOME:-$HOME/.local/bin}"

rm -f -- "$bin_home/custos" "$bin_home/password-studio"
rm -f -- "$data_home/applications/custos.desktop" "$data_home/applications/password-studio.desktop"
rm -f -- "$data_home/icons/hicolor/scalable/apps/custos.svg" "$data_home/icons/hicolor/scalable/apps/password-studio.svg"
rm -rf -- "$data_home/custos" "$data_home/password-studio"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$data_home/applications" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$data_home/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Custos se desinstaló correctamente."
