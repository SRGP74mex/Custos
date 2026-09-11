# Custos

Generador de contraseñas, frases de paso (Diceware) y lotes seguros para Linux.
100% local: no hace peticiones de red ni depende de servicios externos. GUI
(PySide6) y modo de línea de comandos en el mismo programa.

🌐 [Read in English](README.en.md)

## Capturas de pantalla

<p align="center">
  <img src="screenshots/contrasena.png" alt="Generador de contraseñas: longitud, composición y entropía" width="360">
  <img src="screenshots/frase-de-paso.png" alt="Frase de paso Diceware con separador y opciones" width="360">
  <img src="screenshots/lote.png" alt="Generación por lotes de contraseñas o frases" width="360">
</p>

## Funciones

- **Contraseñas**: longitud configurable (8–128, por defecto 20), con control
  independiente de mayúsculas, minúsculas, dígitos y símbolos. Garantiza al
  menos un carácter de cada categoría elegida.
- **Frases de paso (Diceware)**: lista curada de 1024 palabras en español
  (`wordlist.py`), de 3 a 10 palabras (por defecto 5), separador
  configurable, capitalización y número insertado opcionales.
- **Modo seguro**: excluye símbolos problemáticos para bases de datos
  (comillas, barras, punto y coma) y, aparte, un modo para excluir
  caracteres ambiguos (`0`, `O`, `1`, `l`, `I`, etc.).
- **Entropía**: cálculo de bits de entropía y clasificación de fortaleza
  para cada resultado generado.
- **Lotes**: genera varias contraseñas o frases de paso de una sola vez.
- **Portapapeles**: copia directa al portapapeles (Wayland vía `wl-copy`,
  X11 vía `xclip`).
- **CLI y GUI**: el mismo binario decide automáticamente, o se fuerza con
  `--gui` / `--cli`.

Generación con el módulo `secrets` de Python (aleatoriedad criptográfica),
sin llamadas de red en ningún punto del código.

## Uso por línea de comandos

```bash
custos --cli -l 24 -e                    # contraseña de 24 caracteres + entropía
custos --cli -p -w 6 -C                  # frase de paso de 6 palabras, copiada al portapapeles
custos --cli -c 5 --safe                 # lote de 5 contraseñas, símbolos seguros para BD
custos --cli --help                      # ver todas las opciones
```

## Instalación

Requisitos: Linux de escritorio, Python 3, `python3-venv`. Bibliotecas Qt
para PySide6 (ver [requisitos de Qt para Linux](https://doc.qt.io/qt-6/linux-requirements.html)).

```bash
git clone https://github.com/SRGP74mex/Custos.git
cd Custos
./install.sh
```

El instalador crea un entorno virtual propio en
`~/.local/share/custos/.venv`, instala `PySide6`, y agrega el acceso al
menú de aplicaciones. No lo ejecutes con `sudo`.

Para desinstalar:

```bash
./uninstall.sh
```

## Licencia

Código bajo [GPL-3.0](LICENSE).
