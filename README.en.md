# Custos

A password, passphrase (Diceware) and secure-batch generator for Linux and
Windows. 100% local: no network requests, no external services. GUI
(PySide6) and command-line mode in the same program.

🌐 [Leer en español](README.md)

## Screenshots

<p align="center">
  <img src="screenshots/contrasena.png" alt="Password generator: length, composition and entropy" width="360">
  <img src="screenshots/frase-de-paso.png" alt="Diceware passphrase with separator and options" width="360">
  <img src="screenshots/lote.png" alt="Batch generation of passwords or passphrases" width="360">
</p>

## Features

- **Passwords**: configurable length (8–128, default 20), with independent
  toggles for uppercase, lowercase, digits and symbols. Guarantees at least
  one character from each selected category.
- **Passphrases (Diceware)**: curated 1024-word Spanish wordlist
  (`wordlist.py`), 3 to 10 words (default 5), configurable separator,
  optional capitalization and inserted number.
- **Safe mode**: excludes symbols that are problematic for databases
  (quotes, slashes, semicolons), plus a separate mode to exclude ambiguous
  characters (`0`, `O`, `1`, `l`, `I`, etc.).
- **Entropy**: computes entropy bits and a strength classification for
  every generated result.
- **Batch generation**: generate several passwords or passphrases at once.
- **Clipboard**: direct copy to clipboard (Wayland via `wl-copy`, X11 via
  `xclip`; on Windows it uses Qt's native clipboard).
- **CLI and GUI**: the same binary picks automatically, or force it with
  `--gui` / `--cli`.

Generation uses Python's `secrets` module (cryptographic randomness), with
no network calls anywhere in the code.

## Command-line usage

```bash
custos --cli -l 24 -e                    # 24-character password + entropy
custos --cli -p -w 6 -C                  # 6-word passphrase, copied to clipboard
custos --cli -c 5 --safe                 # batch of 5 passwords, DB-safe symbols
custos --cli --help                      # see all options
```

## Installing

Requirements: Linux desktop, Python 3, `python3-venv`. Qt libraries for
PySide6 (see [Qt for Linux requirements](https://doc.qt.io/qt-6/linux-requirements.html)).

```bash
git clone https://github.com/SRGP74mex/Custos.git
cd Custos
./install.sh
```

The installer creates its own virtual environment at
`~/.local/share/custos/.venv`, installs `PySide6`, and adds the app menu
entry. Do not run it with `sudo`.

To uninstall:

```bash
./uninstall.sh
```

### Windows

See [docs/CAMBIOS-WINDOWS.md](docs/CAMBIOS-WINDOWS.md) (Spanish) for the
technical detail of the changes behind this support.

The simplest option for end users is the MSI installer (see
[Downloads](#downloads-windows) or build it yourself below). There is also a
Python-based install, equivalent to `install.sh`:

Requirements: Python 3.9+ (`winget install Python.Python.3.12` if you don't
have it).

```powershell
git clone https://github.com/SRGP74mex/Custos.git
cd Custos
.\install.ps1
```

Creates a virtual environment at `%LOCALAPPDATA%\Custos\.venv`, installs
`PySide6`, adds a Start Menu shortcut, and exposes the `custos` command in a
new terminal. To uninstall: `.\uninstall.ps1`.

#### Downloads (Windows)

`Custos-Setup.msi` is published under
[Releases](https://github.com/SRGP74mex/Custos/releases): it installs to
`Program Files`, adds the Start Menu shortcut, and shows up in "Add or
remove programs" (requires administrator rights). No Python install needed.

#### Building the .exe / .msi yourself

Requires Python 3.9+ and, for the MSI, [WiX Toolset
v3](https://wixtoolset.org/) (`winget install WiXToolset.WiXToolset`):

```powershell
.\build_windows.ps1   # builds dist\Custos.exe (standalone, via PyInstaller)
.\build_msi.ps1        # packages dist\Custos.exe into dist\Custos-Setup.msi
```

`build_windows.ps1` creates a build environment in `.venv-build`, installs
`PySide6` and `pyinstaller`, and packages `generador_contrasenas.py` into a
single `--windowed` `.exe` (no console, GUI-only; use `install.ps1` for
`--cli`). If `custos.ico` exists at the project root (generated from
`custos.svg`), it's used as the `.exe` icon.

`build_msi.ps1` takes that `.exe` and produces an MSI installer
(`dist\Custos-Setup.msi`) from [`wix/Product.wxs`](wix/Product.wxs): install
to `Program Files`, Start Menu shortcut, "Add or remove programs" entry,
GPL-3.0 license in the wizard, and upgrade support (`MajorUpgrade`) for
future versions. Accepts `-Version` to set the package version, e.g.
`.\build_msi.ps1 -Version 1.1.0.0`.

## License

Code under [GPL-3.0](LICENSE).
