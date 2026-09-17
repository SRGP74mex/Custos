# Soporte para Windows — registro de cambios

Custos se creó originalmente solo para Linux. Este documento describe los
cambios que se hicieron para que corra también en Windows: qué se tocó en el
código, qué archivos nuevos se agregaron, y qué se probó antes de darlo por
funcional.

## Resumen

Custos ahora se puede usar en Windows de tres formas:

1. **Instalador MSI** (`Custos-Setup.msi`) — para usuarios finales, no
   requiere Python instalado.
2. **Instalación por script** (`install.ps1`) — equivalente Windows de
   `install.sh`, crea un entorno virtual de Python propio.
3. **Ejecutable standalone** (`Custos.exe`) — generado con PyInstaller, para
   distribuir sin instalador.

## Cambios en el código existente

### [`generador_contrasenas.py`](../generador_contrasenas.py)

El modo `--cli --copy` detectaba herramientas de portapapeles de Linux así:

```python
subprocess.run(["which", tool], capture_output=True).returncode == 0
```

El binario `which` no existe en Windows, así que esa llamada lanzaba
`FileNotFoundError` sin capturar y el programa terminaba con error. Se
corrigió para que la detección de `wl-copy`/`xclip` solo se intente en
Linux (`sys.platform.startswith("linux")`) y use `shutil.which()` en vez de
invocar un binario externo. Fuera de Linux, Custos usa directamente el
portapapeles nativo de Qt (`QApplication.clipboard()`), que ya existía como
mecanismo de respaldo.

Ningún otro cambio fue necesario: el resto del script (generación de
contraseñas, GUI con PySide6, rutas de relanzamiento del intérprete) ya era
portable, porque PySide6 soporta Windows de forma nativa y las rutas
específicas de Linux (`~/.local/share/...`, `prctl`) están protegidas por
comprobaciones de plataforma o son solo candidatos opcionales que se
descartan si no existen.

## Archivos nuevos

| Archivo | Para qué sirve |
|---|---|
| [`install.ps1`](../install.ps1) | Instalador Windows equivalente a `install.sh`: crea un venv en `%LOCALAPPDATA%\Custos\.venv`, instala `PySide6`, agrega acceso directo al menú Inicio y expone el comando `custos` en el PATH del usuario. |
| [`uninstall.ps1`](../uninstall.ps1) | Revierte todo lo anterior. |
| [`build_windows.ps1`](../build_windows.ps1) | Compila `generador_contrasenas.py` en un `.exe` standalone con PyInstaller (`dist\Custos.exe`, modo `--windowed`, sin consola). Usa `custos.ico` como icono si existe. |
| [`custos.ico`](../custos.ico) | Icono generado a partir de `custos.svg` (renderizado con `QSvgRenderer` a varias resoluciones y empaquetado con Pillow). Se usa en el `.exe` y en el MSI. |
| [`build_msi.ps1`](../build_msi.ps1) | Empaqueta `dist\Custos.exe` en un instalador MSI (`dist\Custos-Setup.msi`) usando WiX Toolset v3 (`candle.exe`/`light.exe`). Acepta `-Version` para fijar la versión del paquete. |
| [`wix/Product.wxs`](../wix/Product.wxs) | Definición WiX del instalador: instala en `Program Files\Custos`, crea el acceso directo del menú Inicio, registra la entrada en «Agregar o quitar programas», soporta actualizaciones (`MajorUpgrade`) y muestra la licencia GPL-3.0 en el asistente. |
| [`wix/License.rtf`](../wix/License.rtf) | Texto de licencia (GPL-3.0, resumido) que se muestra en el asistente del MSI. |
| [`.github/workflows/windows-build.yml`](../.github/workflows/windows-build.yml) | Compila `.exe`/`.msi` en un runner `windows-latest` y publica ambos en un GitHub Release cuando se empuja un tag `v*`. |

También se actualizó [`.gitignore`](../.gitignore) para ignorar los
artefactos de build (`.venv-build/`, `*.spec`, `*.wixobj`, `*.wixpdb`,
además de los ya existentes `.venv/`, `build/`, `dist/`), y se ampliaron
[`README.md`](../README.md) y [`README.en.md`](../README.en.md) con una
sección "Windows" que cubre las tres formas de instalación.

## Qué se probó

Todo se probó en una máquina Windows 10 real (no headless), instalando las
herramientas necesarias sobre la marcha con `winget` (Python 3.12, WiX
Toolset v3, Git):

- **CLI**: `custos --cli -l 24 -e` y `custos --cli -l 12 -C` (con el fix del
  portapapeles) — sin errores, copiado al portapapeles confirmado.
- **GUI**: arranque vía `install.ps1` y vía `dist\Custos.exe` — la ventana
  se mantiene abierta sin errores.
- **MSI**: instalación con elevación (`msiexec /i ... /qn`, UAC aceptado) →
  se verificó que `Custos.exe` y `LICENSE` quedan en
  `C:\Program Files\Custos`, que aparece el acceso directo en el menú
  Inicio, y que la entrada en «Agregar o quitar programas» tiene el nombre,
  versión y publicador correctos. Luego se lanzó el `.exe` instalado y se
  confirmó que corre. Por último se desinstaló (`msiexec /x`) y se verificó
  que los tres rastros (exe, shortcut, entrada ARP) se eliminan por
  completo.

## Ajustes posteriores a la revisión

Tras revisar `wix/Product.wxs` y `build_msi.ps1` antes de integrarlos a este
repositorio, se hicieron dos correcciones y se agregó CI:

### Auto-reparación al abrir el acceso directo con otro usuario

El componente `ApplicationShortcut` usaba una clave de registro en `HKCU`
como `KeyPath` (patrón estándar de WiX para asociar un acceso directo a un
componente), pero el paquete se instala en modo `perMachine`. Eso significa
que Windows Installer marca ese componente como "instalado" solo para el
usuario que ejecutó el instalador; si un usuario *distinto* en la misma
máquina abre el acceso directo del menú Inicio, Windows Installer no
encuentra esa clave en su propio `HKCU` y dispara un ciclo de
autoreparación (vuelve a copiar archivos, puede pedir el MSI original o
UAC) antes de lanzar el programa. Se corrigió cambiando esa clave a `HKLM`
en `wix/Product.wxs`, coherente con el resto del paquete, que de por sí
requiere privilegios de administrador para instalarse.

### Versionado del paquete

Por ahora el proyecto sigue en beta y la versión del MSI se mantiene fija
en `1.0.0.0` (valor por defecto de `-Version` en `build_msi.ps1`). Cuando
haga falta publicar una actualización, hay un detalle no obvio de Windows
Installer a tener en cuenta: el `ProductVersion` de un MSI tiene 4 campos
(`Major.Minor.Build.Revision`), pero **Windows Installer solo compara los
primeros tres** (`Major.Minor.Build`) para decidir si una instalación nueva
reemplaza a la anterior (tabla `Upgrade`, la que usa `<MajorUpgrade>`). El
cuarto campo se ignora por completo para ese propósito, así que pasar de
`1.0.0.0` a `1.0.0.1` (o `1.0.0.10`) no dispararía la actualización: para
Windows Installer ambas versiones son "`1.0.0`".

Recomendación para incrementos de beta: subir el **tercer campo** (Build),
por ejemplo `1.0.1.0`, `1.0.2.0`, `1.0.3.0`… Eso deja margen para muchas
iteraciones (el campo Build admite valores de 0 a 65534) sin tocar Minor o
Major, que conviene reservar para hitos más grandes (Minor) o para la
primera versión estable (`1.0` → `2.0`, etc.).

### Integración con CI (GitHub Actions)

Se agregó [`.github/workflows/windows-build.yml`](../.github/workflows/windows-build.yml),
que compila `Custos.exe` y `Custos-Setup.msi` en un runner `windows-latest`:

- Se puede disparar manualmente (`workflow_dispatch`) para generar los
  artefactos de build sin publicar nada (quedan como artifact del run).
- Al empujar un tag `v*` (por ejemplo `v1.0.0-beta1`), además publica
  `Custos.exe` y `Custos-Setup.msi` como archivos adjuntos de un GitHub
  Release (se crea automáticamente si no existe).

No hace falta ningún registro con Microsoft para esto: WiX Toolset y la
distribución vía GitHub Releases no dependen de una cuenta de Microsoft ni
de la Microsoft Store. Lo único que una cuenta/certificado habilitaría es
la **firma de código (Authenticode)**, que evita la advertencia de
SmartScreen en la primera ejecución (ver "Limitaciones conocidas" abajo).
Firmar el instalador requeriría comprar un certificado de firma de código a
una autoridad certificadora (DigiCert, SSL.com, etc.) o usar Microsoft
Trusted Signing, que sí exige verificar una cuenta/organización; publicar
en la Microsoft Store es un trámite aparte (cuenta de Partner Center de
pago) y no hace falta para distribuir el MSI directamente desde Releases.

## Requisitos para compilar en Windows

- Python 3.9+ (para correr el script, `install.ps1` o `build_windows.ps1`).
- [WiX Toolset v3](https://wixtoolset.org/) (`winget install
  WiXToolset.WiXToolset`) — solo si se quiere generar el `.msi` con
  `build_msi.ps1`.

## Limitaciones conocidas

- `dist\Custos.exe` se compila con `--windowed` (sin consola), por lo que
  solo sirve para el modo GUI. Para usar `--cli` desde una terminal hay que
  instalar con `install.ps1` (que sí deja un `python.exe` con consola).
- El MSI no está firmado digitalmente (code signing), así que Windows
  SmartScreen puede advertir la primera vez que alguien lo ejecute.

## Posibles siguientes pasos

- Firmar el instalador para evitar la advertencia de SmartScreen (requiere
  comprar un certificado de firma de código o usar Microsoft Trusted
  Signing; no es necesario para publicar en Releases, solo para quitar la
  advertencia).
- Cuando el proyecto salga de beta, empezar a versionar de verdad: bumpear
  `-Version` en cada tag y considerar derivar el número automáticamente del
  tag de git en el workflow de CI.
