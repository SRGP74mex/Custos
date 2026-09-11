#!/usr/bin/env python3
"""Custos: Generador local de contraseñas, frases de paso y lotes seguros.

Copyright (C) 2026 Custos
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

import argparse
import math
import os
import secrets
import string
import sys

# Si falta PySide6 en el intérprete actual (ej. se ejecutó con python3 del sistema),
# relanzar automáticamente usando el entorno virtual local o instalado.
try:
    import PySide6
except ModuleNotFoundError:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, ".venv", "bin", "custos"),
        os.path.join(script_dir, ".venv", "bin", "python"),
        os.path.expanduser("~/.local/share/custos/.venv/bin/custos"),
        os.path.expanduser("~/.local/share/custos/.venv/bin/python"),
        os.path.expanduser("~/.local/share/password-studio/.venv/bin/custos"),
    ]
    for exe in candidates:
        if os.path.isfile(exe) and os.access(exe, os.X_OK):
            os.execv(exe, [exe, __file__] + sys.argv[1:])
    raise

# Asignar nombre del proceso en Linux para que /proc/self/comm sea 'custos'
if sys.platform.startswith("linux"):
    try:
        import ctypes
        libc = ctypes.CDLL(None)
        libc.prctl(15, b"custos", 0, 0, 0)
    except Exception:
        pass

# Importar lista de palabras Diceware
try:
    from wordlist import UNIQUE_WORDS, WORDLIST_SIZE
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from wordlist import UNIQUE_WORDS, WORDLIST_SIZE

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QProgressBar, QPushButton, QScrollArea,
    QSizeGrip, QSlider, QStackedWidget, QVBoxLayout, QWidget,
)

MIN_LENGTH, MAX_LENGTH, DEFAULT_LENGTH = 8, 128, 20
MIN_WORDS, MAX_WORDS, DEFAULT_WORDS = 3, 10, 5
CLIPBOARD_CLEAR_MS = 30_000

UPPER, LOWER, DIGITS = string.ascii_uppercase, string.ascii_lowercase, string.digits
SYMBOLS_FULL = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
SYMBOLS_SAFE = "!@#$%^&*()-_=+[]{}<>?,.:~"
AMBIGUOUS = frozenset("O0oIl1|`")

ENTROPY_LEVELS = (
    (100, "Excelente", "#64e6a6"),
    (80, "Muy fuerte", "#70d7ff"),
    (60, "Fuerte", "#8da2ff"),
    (40, "Mejorable", "#ffc96b"),
    (0, "Débil", "#ff7a91"),
)


def entropy_label(bits: float) -> tuple[str, str]:
    for threshold, label, color in ENTROPY_LEVELS:
        if bits >= threshold:
            return label, color
    return ENTROPY_LEVELS[-1][1], ENTROPY_LEVELS[-1][2]


def generate_password(length: int, categories: list[str]) -> str:
    """Genera una contraseña y garantiza un carácter de cada categoría."""
    if not categories:
        raise ValueError("Selecciona al menos un tipo de carácter.")
    if length < len(categories):
        raise ValueError("La longitud no cubre todas las categorías elegidas.")
    pool = "".join(categories)
    result = [secrets.choice(category) for category in categories]
    result.extend(secrets.choice(pool) for _ in range(length - len(result)))
    secrets.SystemRandom().shuffle(result)
    return "".join(result)


def generate_passphrase(
    words_count: int = 5,
    separator: str = "-",
    capitalize: bool = True,
    include_number: bool = True,
) -> tuple[str, float]:
    """Genera una frase de paso Diceware y calcula su entropía matemática."""
    selected = [secrets.choice(UNIQUE_WORDS) for _ in range(words_count)]
    if capitalize:
        selected = [w.capitalize() for w in selected]
    if include_number:
        num = secrets.randbelow(90) + 10  # 10..99
        pos = secrets.randbelow(len(selected) + 1)
        selected.insert(pos, str(num))

    passphrase = separator.join(selected)

    bits = words_count * math.log2(WORDLIST_SIZE)
    if capitalize:
        bits += words_count * 1.0
    if include_number:
        bits += math.log2(90 * (words_count + 1))

    return passphrase, bits


# ----------------------------------------------------------------------
# CLI (Línea de comandos)
# ----------------------------------------------------------------------

def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="custos",
        description="Custos: Generador local de contraseñas y frases de paso seguras.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  custos                               Abre la interfaz gráfica
  custos -l 24                         Genera una contraseña de 24 caracteres
  custos --safe                        Genera contraseña segura para bases de datos
  custos -p -w 6 -s .                  Genera frase de paso de 6 palabras con separador '.'
  custos -c 5 -l 16                    Genera un lote de 5 contraseñas
  custos -p -c 5 --no-caps             Genera lote de 5 frases sin mayúsculas
  custos -l 32 -e -C                   Genera, muestra entropía y copia al portapapeles
        """,
    )
    parser.add_argument("--gui", action="store_true", help="Fuerza el inicio de la interfaz gráfica.")
    parser.add_argument("--cli", action="store_true", help="Fuerza el modo de línea de comandos.")
    parser.add_argument("-l", "--length", type=int, default=DEFAULT_LENGTH, help=f"Longitud de la contraseña ({MIN_LENGTH}-{MAX_LENGTH}, por defecto: {DEFAULT_LENGTH}).")
    parser.add_argument("-c", "--count", type=int, default=1, help="Cantidad a generar (modo lote).")
    parser.add_argument("-p", "--passphrase", action="store_true", help="Genera frase de paso (Diceware) en vez de contraseña.")
    parser.add_argument("-w", "--words", type=int, default=DEFAULT_WORDS, help=f"Cantidad de palabras ({MIN_WORDS}-{MAX_WORDS}, por defecto: {DEFAULT_WORDS}).")
    parser.add_argument("-s", "--separator", type=str, default="-", help="Separador entre palabras (por defecto: '-').")
    parser.add_argument("--no-caps", action="store_true", help="No capitalizar las palabras de la frase de paso.")
    parser.add_argument("--no-num", action="store_true", help="No insertar número en la frase de paso.")
    parser.add_argument("--no-upper", action="store_true", help="Excluir mayúsculas (A-Z).")
    parser.add_argument("--no-lower", action="store_true", help="Excluir minúsculas (a-z).")
    parser.add_argument("--no-digits", action="store_true", help="Excluir dígitos (0-9).")
    parser.add_argument("--no-symbols", action="store_true", help="Excluir símbolos.")
    parser.add_argument("--safe", action="store_true", help="Solo símbolos seguros para bases de datos (sin comillas, barras ni punto y coma).")
    parser.add_argument("--exclude-ambiguous", action="store_true", help="Excluir caracteres ambiguos (0, O, 1, l, I, etc.).")
    parser.add_argument("-e", "--entropy", action="store_true", help="Muestra los bits de entropía y clasificación.")
    parser.add_argument("-C", "--copy", action="store_true", help="Copia el resultado generado al portapapeles.")
    return parser


def run_cli(args: argparse.Namespace) -> int:
    count = max(1, args.count)
    results: list[tuple[str, float]] = []

    if args.passphrase:
        sep = " " if args.separator in ("espacio", "space") else args.separator
        for _ in range(count):
            pwd, bits = generate_passphrase(
                words_count=max(MIN_WORDS, min(args.words, MAX_WORDS)),
                separator=sep,
                capitalize=not args.no_caps,
                include_number=not args.no_num,
            )
            results.append((pwd, bits))
    else:
        categories = []
        if not args.no_upper:
            categories.append(UPPER)
        if not args.no_lower:
            categories.append(LOWER)
        if not args.no_digits:
            categories.append(DIGITS)
        if not args.no_symbols:
            categories.append(SYMBOLS_SAFE if args.safe else SYMBOLS_FULL)
        if args.exclude_ambiguous:
            categories = ["".join(c for c in cat if c not in AMBIGUOUS) for cat in categories]
        categories = [cat for cat in categories if cat]
        if not categories:
            print("Error: Selecciona al menos una categoría de caracteres.", file=sys.stderr)
            return 1

        length = max(MIN_LENGTH, min(args.length, MAX_LENGTH))
        for _ in range(count):
            try:
                pwd = generate_password(length, categories)
                pool_size = len(set("".join(categories)))
                bits = length * math.log2(pool_size) if pool_size > 0 else 0
                results.append((pwd, bits))
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1

    for pwd, bits in results:
        if args.entropy:
            label, _ = entropy_label(bits)
            print(f"{pwd}\t({bits:.1f} bits, {label})")
        else:
            print(pwd)

    if args.copy:
        full_text = "\n".join(p for p, _ in results)
        copied = False
        import subprocess
        for tool, cmd in (("wl-copy", ["wl-copy"]), ("xclip", ["xclip", "-selection", "clipboard"])):
            if subprocess.run(["which", tool], capture_output=True).returncode == 0:
                try:
                    subprocess.run(cmd, input=full_text.encode(), check=True)
                    copied = True
                    break
                except Exception:
                    pass
        if not copied:
            try:
                app = QApplication.instance() or QApplication(["password-studio"])
                app.clipboard().setText(full_text)
                copied = True
            except Exception:
                pass
        if copied:
            print("✓ Copiado al portapapeles", file=sys.stderr)

    return 0


# ----------------------------------------------------------------------
# Interfaz Gráfica (PySide6)
# ----------------------------------------------------------------------

class TitleBar(QWidget):
    """Barra de título compacta inspirada en macOS con movimiento nativo en Wayland."""

    def __init__(self, window: QMainWindow) -> None:
        super().__init__()
        self.window = window
        self.drag_origin: QPoint | None = None
        self.setObjectName("titleBar")
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 16, 6)
        layout.setSpacing(9)
        for name, color, callback in (
            ("Cerrar", "#ff5f57", window.close),
            ("Minimizar", "#febc2e", window.showMinimized),
            ("Maximizar", "#28c840", self._toggle_maximized),
        ):
            button = QPushButton()
            button.setToolTip(name)
            button.setFixedSize(13, 13)
            button.setStyleSheet(
                f"QPushButton {{background:{color};border:none;border-radius:6px;}}"
                "QPushButton:hover {border:2px solid rgba(255,255,255,0.48);}"
            )
            button.clicked.connect(callback)
            layout.addWidget(button)
        layout.addStretch()
        title = QLabel("◈  Custos")
        title.setObjectName("windowTitle")
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(title)
        layout.addStretch()
        spacer = QWidget()
        spacer.setFixedWidth(56)
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(spacer)

    def _toggle_maximized(self) -> None:
        self.window.showNormal() if self.window.isMaximized() else self.window.showMaximized()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window.windowHandle()
            if handle is not None and handle.startSystemMove():
                self.drag_origin = None
                event.accept()
                return
            self.drag_origin = event.globalPosition().toPoint() - self.window.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self.drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if self.window.isMaximized():
                self.window.showNormal()
            self.window.move(event.globalPosition().toPoint() - self.drag_origin)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self.drag_origin = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximized()
        super().mouseDoubleClickEvent(event)


class App(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Custos")
        self.setMinimumSize(580, 560)
        self.resize(740, 700)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

        self._clipboard_token: str | None = None
        self._password_visible = True
        self._passphrase_visible = True

        self._build_ui()

        QShortcut(QKeySequence("Ctrl+G"), self, activated=self._on_regenerate_shortcut)
        QShortcut(QKeySequence("Ctrl+C"), self, activated=self._on_copy_shortcut)

        self._generate_password()
        self._generate_passphrase()
        self._generate_batch()

    def _build_ui(self) -> None:
        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(12, 12, 12, 12)

        glass = QFrame(objectName="glass")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 150))
        glass.setGraphicsEffect(shadow)
        outer.addWidget(glass)

        main = QVBoxLayout(glass)
        main.setContentsMargins(0, 0, 0, 8)
        main.setSpacing(0)
        main.addWidget(TitleBar(self))

        # Selector de Modo (Pills)
        mode_container = QHBoxLayout()
        mode_container.setContentsMargins(36, 6, 36, 12)
        mode_box = QFrame(objectName="modeSwitcher")
        mode_layout = QHBoxLayout(mode_box)
        mode_layout.setContentsMargins(4, 4, 4, 4)
        mode_layout.setSpacing(6)

        self.tab_buttons = []
        for index, label in enumerate(("🔒  Contraseña", "📝  Frase de paso", "📋  Lote")):
            btn = QPushButton(label)
            btn.setProperty("class", "modeTab")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, i=index: self._switch_tab(i))
            mode_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        mode_container.addWidget(mode_box)
        main.addLayout(mode_container)

        # Scroll Area principal
        scroll = QScrollArea(objectName="mainScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget(objectName="scrollContent")
        self.stack = QStackedWidget()

        # Tab 0: Contraseña
        self.tab_password = self._build_password_tab()
        self.stack.addWidget(self.tab_password)

        # Tab 1: Frase de paso
        self.tab_passphrase = self._build_passphrase_tab()
        self.stack.addWidget(self.tab_passphrase)

        # Tab 2: Lote
        self.tab_batch = self._build_batch_tab()
        self.stack.addWidget(self.tab_batch)

        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(36, 0, 36, 10)
        content_layout.addWidget(self.stack)

        scroll.setWidget(scroll_content)
        main.addWidget(scroll, 1)

        # Barra de estado común
        self.status_label = QLabel("", objectName="status")
        self.status_label.setWordWrap(True)
        self.status_label.setContentsMargins(36, 2, 36, 2)
        main.addWidget(self.status_label)

        # Pie de página
        footer = QHBoxLayout()
        footer.setContentsMargins(24, 0, 14, 4)
        footer.addWidget(QLabel("Generación local · Tus contraseñas nunca salen de este equipo", objectName="footer"))
        footer.addStretch()
        footer.addWidget(QSizeGrip(self))
        main.addLayout(footer)

        self._switch_tab(0)
        self.setStyleSheet(STYLESHEET)

    def _switch_tab(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ------------------------------------------------------------------
    # TAB 0: CONTRASEÑA INDIVIDUAL
    # ------------------------------------------------------------------
    def _build_password_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        layout.addWidget(QLabel("CONTRASEÑA GENERADA", objectName="eyebrow"))

        card = QFrame(objectName="passwordCard")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 6, 8, 6)
        card_layout.setSpacing(6)

        self.password_edit = QLineEdit(objectName="passwordEdit")
        self.password_edit.setReadOnly(True)
        self.password_edit.setMinimumHeight(44)
        card_layout.addWidget(self.password_edit, 1)

        self.eye_button = QPushButton("◉", objectName="iconButton")
        self.eye_button.setToolTip("Mostrar u ocultar contraseña")
        self.eye_button.clicked.connect(self._toggle_password)
        card_layout.addWidget(self.eye_button)

        copy_btn = QPushButton("⎘", objectName="iconButton")
        copy_btn.setToolTip("Copiar contraseña (Ctrl+C)")
        copy_btn.clicked.connect(self._copy_password)
        card_layout.addWidget(copy_btn)
        layout.addWidget(card)

        # Entropía
        strength_row = QHBoxLayout()
        self.strength_label = QLabel(objectName="strengthLabel")
        self.entropy_widget = QLabel(objectName="secondary")
        strength_row.addWidget(self.strength_label)
        strength_row.addStretch()
        strength_row.addWidget(self.entropy_widget)
        layout.addLayout(strength_row)

        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 128)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setFixedHeight(7)
        layout.addWidget(self.strength_bar)

        # Longitud
        len_row = QHBoxLayout()
        len_row.addWidget(QLabel("Longitud", objectName="sectionTitle"))
        len_row.addStretch()
        self.length_value = QLabel(str(DEFAULT_LENGTH), objectName="lengthBadge")
        len_row.addWidget(self.length_value)
        layout.addLayout(len_row)

        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setRange(MIN_LENGTH, MAX_LENGTH)
        self.length_slider.setValue(DEFAULT_LENGTH)
        self.length_slider.valueChanged.connect(self._on_length_changed)
        layout.addWidget(self.length_slider)

        # Composición
        layout.addWidget(QLabel("Composición", objectName="sectionTitle"))
        options = QFrame(objectName="optionsCard")
        opt_layout = QVBoxLayout(options)
        opt_layout.setContentsMargins(18, 10, 18, 10)
        opt_layout.setSpacing(2)
        self.upper_check = self._option("Mayúsculas", "A–Z", True, opt_layout)
        self.lower_check = self._option("Minúsculas", "a–z", True, opt_layout)
        self.digits_check = self._option("Números", "0–9", True, opt_layout)
        self.symbols_check = self._option("Símbolos", "!  @  #  $", True, opt_layout)
        self.safe_check = self._option("Compatibles con bases de datos", "sin  '  \"  \\  `  ;", False, opt_layout)
        self.ambiguous_check = self._option("Excluir caracteres ambiguos", "O  0  l  1", False, opt_layout)
        layout.addWidget(options)

        gen_btn = QPushButton("✦  Generar nueva contraseña", objectName="primaryButton")
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gen_btn.clicked.connect(self._generate_password)
        layout.addWidget(gen_btn)
        return widget

    # ------------------------------------------------------------------
    # TAB 1: FRASE DE PASO (PASSPHRASE / DICEWARE)
    # ------------------------------------------------------------------
    def _build_passphrase_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        layout.addWidget(QLabel("FRASE DE PASO SEGURA (DICEWARE)", objectName="eyebrow"))

        card = QFrame(objectName="passwordCard")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 6, 8, 6)
        card_layout.setSpacing(6)

        self.passphrase_edit = QLineEdit(objectName="passwordEdit")
        self.passphrase_edit.setReadOnly(True)
        self.passphrase_edit.setMinimumHeight(44)
        card_layout.addWidget(self.passphrase_edit, 1)

        self.passphrase_eye = QPushButton("◉", objectName="iconButton")
        self.passphrase_eye.setToolTip("Mostrar u ocultar frase de paso")
        self.passphrase_eye.clicked.connect(self._toggle_passphrase)
        card_layout.addWidget(self.passphrase_eye)

        copy_btn = QPushButton("⎘", objectName="iconButton")
        copy_btn.setToolTip("Copiar frase de paso (Ctrl+C)")
        copy_btn.clicked.connect(self._copy_passphrase)
        card_layout.addWidget(copy_btn)
        layout.addWidget(card)

        # Entropía frase
        strength_row = QHBoxLayout()
        self.passphrase_strength_label = QLabel(objectName="strengthLabel")
        self.passphrase_entropy_widget = QLabel(objectName="secondary")
        strength_row.addWidget(self.passphrase_strength_label)
        strength_row.addStretch()
        strength_row.addWidget(self.passphrase_entropy_widget)
        layout.addLayout(strength_row)

        self.passphrase_strength_bar = QProgressBar()
        self.passphrase_strength_bar.setRange(0, 128)
        self.passphrase_strength_bar.setTextVisible(False)
        self.passphrase_strength_bar.setFixedHeight(7)
        layout.addWidget(self.passphrase_strength_bar)

        # Cantidad de palabras
        words_row = QHBoxLayout()
        words_row.addWidget(QLabel("Cantidad de palabras", objectName="sectionTitle"))
        words_row.addStretch()
        self.words_value = QLabel(str(DEFAULT_WORDS), objectName="lengthBadge")
        words_row.addWidget(self.words_value)
        layout.addLayout(words_row)

        self.words_slider = QSlider(Qt.Orientation.Horizontal)
        self.words_slider.setRange(MIN_WORDS, MAX_WORDS)
        self.words_slider.setValue(DEFAULT_WORDS)
        self.words_slider.valueChanged.connect(self._on_words_changed)
        layout.addWidget(self.words_slider)

        # Opciones de Frase
        layout.addWidget(QLabel("Configuración de frase", objectName="sectionTitle"))
        options = QFrame(objectName="optionsCard")
        opt_layout = QVBoxLayout(options)
        opt_layout.setContentsMargins(18, 12, 18, 12)
        opt_layout.setSpacing(8)

        # Separador selector
        sep_row = QHBoxLayout()
        sep_row.addWidget(QLabel("Separador entre palabras:", objectName="subSectionTitle"))
        sep_row.addStretch()
        self.sep_buttons: list[QPushButton] = []
        for sep_char, sep_label in (("-", "Guión (-)"), ("_", "Bajo (_)"), (".", "Punto (.)"), (" ", "Espacio")):
            s_btn = QPushButton(sep_label)
            s_btn.setProperty("class", "segmentedBtn")
            s_btn.setProperty("sepValue", sep_char)
            s_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            s_btn.clicked.connect(lambda _, val=sep_char: self._on_separator_selected(val))
            sep_row.addWidget(s_btn)
            self.sep_buttons.append(s_btn)
        self.current_separator = "-"
        opt_layout.addLayout(sep_row)
        self._update_sep_buttons_ui()

        self.caps_check = self._option("Mayúscula inicial", "Capitalizar cada palabra (ej. Gato-Nieve)", True, opt_layout)
        self.num_check = self._option("Incluir número aleatorio", "Inserta un número para mayor entropía", True, opt_layout)
        layout.addWidget(options)

        gen_btn = QPushButton("✦  Generar nueva frase de paso", objectName="primaryButton")
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gen_btn.clicked.connect(self._generate_passphrase)
        layout.addWidget(gen_btn)
        return widget

    # ------------------------------------------------------------------
    # TAB 2: GENERACIÓN POR LOTES (BATCH)
    # ------------------------------------------------------------------
    def _build_batch_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(QLabel("GENERACIÓN POR LOTES (MÚLTIPLES)", objectName="eyebrow"))

        # Controles superiores
        cfg_card = QFrame(objectName="optionsCard")
        cfg_layout = QHBoxLayout(cfg_card)
        cfg_layout.setContentsMargins(16, 10, 16, 10)
        cfg_layout.setSpacing(14)

        cfg_layout.addWidget(QLabel("Tipo:", objectName="subSectionTitle"))
        self.batch_type_password = QPushButton("Contraseñas")
        self.batch_type_password.setProperty("class", "segmentedBtn")
        self.batch_type_password.setCursor(Qt.CursorShape.PointingHandCursor)
        self.batch_type_password.clicked.connect(lambda: self._set_batch_type("password"))
        cfg_layout.addWidget(self.batch_type_password)

        self.batch_type_passphrase = QPushButton("Frases")
        self.batch_type_passphrase.setProperty("class", "segmentedBtn")
        self.batch_type_passphrase.setCursor(Qt.CursorShape.PointingHandCursor)
        self.batch_type_passphrase.clicked.connect(lambda: self._set_batch_type("passphrase"))
        cfg_layout.addWidget(self.batch_type_passphrase)

        cfg_layout.addSpacing(14)
        cfg_layout.addWidget(QLabel("Cantidad:", objectName="subSectionTitle"))
        self.batch_count_buttons: list[QPushButton] = []
        for count in (5, 10, 20):
            c_btn = QPushButton(str(count))
            c_btn.setProperty("class", "segmentedBtn")
            c_btn.setProperty("countValue", count)
            c_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            c_btn.clicked.connect(lambda _, c=count: self._set_batch_count(c))
            cfg_layout.addWidget(c_btn)
            self.batch_count_buttons.append(c_btn)

        self.batch_mode = "password"
        self.batch_count = 5
        self._update_batch_controls_ui()
        layout.addWidget(cfg_card)

        # Contenedor de lista de resultados
        self.batch_list_container = QVBoxLayout()
        self.batch_list_container.setSpacing(6)
        layout.addLayout(self.batch_list_container)

        # Botones de acción del lote
        action_row = QHBoxLayout()
        gen_batch_btn = QPushButton("✦  Generar nuevo lote", objectName="primaryButton")
        gen_batch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gen_batch_btn.clicked.connect(self._generate_batch)
        action_row.addWidget(gen_batch_btn, 2)

        copy_all_btn = QPushButton("⎘  Copiar todas", objectName="secondaryButton")
        copy_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_all_btn.clicked.connect(self._copy_all_batch)
        action_row.addWidget(copy_all_btn, 1)

        layout.addLayout(action_row)
        return widget

    def _set_batch_type(self, b_type: str) -> None:
        self.batch_mode = b_type
        self._update_batch_controls_ui()
        self._generate_batch()

    def _set_batch_count(self, count: int) -> None:
        self.batch_count = count
        self._update_batch_controls_ui()
        self._generate_batch()

    def _update_batch_controls_ui(self) -> None:
        self.batch_type_password.setProperty("active", self.batch_mode == "password")
        self.batch_type_password.style().unpolish(self.batch_type_password)
        self.batch_type_password.style().polish(self.batch_type_password)

        self.batch_type_passphrase.setProperty("active", self.batch_mode == "passphrase")
        self.batch_type_passphrase.style().unpolish(self.batch_type_passphrase)
        self.batch_type_passphrase.style().polish(self.batch_type_passphrase)

        for btn in self.batch_count_buttons:
            active = btn.property("countValue") == self.batch_count
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_separator_selected(self, val: str) -> None:
        self.current_separator = val
        self._update_sep_buttons_ui()
        self._generate_passphrase()

    def _update_sep_buttons_ui(self) -> None:
        for btn in self.sep_buttons:
            active = btn.property("sepValue") == self.current_separator
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _option(self, title: str, hint: str, checked: bool, layout: QVBoxLayout) -> QCheckBox:
        check = QCheckBox(f"{title}     {hint}")
        check.setChecked(checked)
        check.setCursor(Qt.CursorShape.PointingHandCursor)
        check.toggled.connect(self._on_option_changed)
        layout.addWidget(check)
        return check

    def _on_option_changed(self) -> None:
        self.safe_check.setEnabled(self.symbols_check.isChecked())
        if self.stack.currentIndex() == 0:
            self._generate_password()
        elif self.stack.currentIndex() == 1:
            self._generate_passphrase()

    def _on_length_changed(self, value: int) -> None:
        self.length_value.setText(str(value))
        self._generate_password()

    def _on_words_changed(self, value: int) -> None:
        self.words_value.setText(str(value))
        self._generate_passphrase()

    def _selected_categories(self) -> list[str]:
        categories = []
        for check, characters in (
            (self.upper_check, UPPER), (self.lower_check, LOWER), (self.digits_check, DIGITS)
        ):
            if check.isChecked():
                categories.append(characters)
        if self.symbols_check.isChecked():
            categories.append(SYMBOLS_SAFE if self.safe_check.isChecked() else SYMBOLS_FULL)
        if self.ambiguous_check.isChecked():
            categories = ["".join(c for c in category if c not in AMBIGUOUS) for category in categories]
        return [category for category in categories if category]

    def _generate_password(self) -> None:
        categories = self._selected_categories()
        if not categories:
            self.password_edit.clear()
            self.strength_bar.setValue(0)
            self.strength_label.clear()
            self.entropy_widget.clear()
            self._show_status("Selecciona al menos un tipo de carácter.", error=True)
            return
        password = generate_password(self.length_slider.value(), categories)
        self.password_edit.setText(password)
        self.status_label.clear()

        pool_size = len(set("".join(categories)))
        bits = self.length_slider.value() * math.log2(pool_size)
        label, color = entropy_label(bits)

        self.strength_label.setText(f"●  {label}")
        self.strength_label.setStyleSheet(f"color:{color};")
        self.entropy_widget.setText(f"{bits:.1f} bits")
        self.strength_bar.setValue(min(round(bits), 128))
        self.strength_bar.setStyleSheet(
            "QProgressBar{background:rgba(255,255,255,0.08);border:none;border-radius:3px;}"
            f"QProgressBar::chunk{{background:{color};border-radius:3px;}}"
        )

    def _generate_passphrase(self) -> None:
        passphrase, bits = generate_passphrase(
            words_count=self.words_slider.value(),
            separator=self.current_separator,
            capitalize=self.caps_check.isChecked(),
            include_number=self.num_check.isChecked(),
        )
        self.passphrase_edit.setText(passphrase)
        self.status_label.clear()

        label, color = entropy_label(bits)
        self.passphrase_strength_label.setText(f"●  {label}")
        self.passphrase_strength_label.setStyleSheet(f"color:{color};")
        self.passphrase_entropy_widget.setText(f"{bits:.1f} bits")
        self.passphrase_strength_bar.setValue(min(round(bits), 128))
        self.passphrase_strength_bar.setStyleSheet(
            "QProgressBar{background:rgba(255,255,255,0.08);border:none;border-radius:3px;}"
            f"QProgressBar::chunk{{background:{color};border-radius:3px;}}"
        )

    def _generate_batch(self) -> None:
        # Limpiar elementos previos
        while self.batch_list_container.count():
            child = self.batch_list_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.current_batch_results: list[str] = []

        if self.batch_mode == "passphrase":
            for _ in range(self.batch_count):
                pwd, bits = generate_passphrase(
                    words_count=self.words_slider.value(),
                    separator=self.current_separator,
                    capitalize=self.caps_check.isChecked(),
                    include_number=self.num_check.isChecked(),
                )
                self.current_batch_results.append(pwd)
                self._add_batch_item(pwd, bits)
        else:
            categories = self._selected_categories()
            if not categories:
                categories = [UPPER, LOWER, DIGITS, SYMBOLS_FULL]
            length = self.length_slider.value()
            pool_size = len(set("".join(categories)))
            bits = length * math.log2(pool_size) if pool_size > 0 else 0
            for _ in range(self.batch_count):
                pwd = generate_password(length, categories)
                self.current_batch_results.append(pwd)
                self._add_batch_item(pwd, bits)

    def _add_batch_item(self, text: str, bits: float) -> None:
        item = QFrame()
        item.setProperty("class", "batchItem")
        layout = QHBoxLayout(item)
        layout.setContentsMargins(12, 6, 8, 6)
        layout.setSpacing(10)

        line = QLineEdit(text)
        line.setReadOnly(True)
        line.setStyleSheet("QLineEdit{background:transparent;border:none;color:white;font-family:'JetBrains Mono','SF Mono',monospace;font-size:14px;}")
        layout.addWidget(line, 1)

        label, color = entropy_label(bits)
        badge = QLabel(f"{bits:.0f}b")
        badge.setStyleSheet(f"color:{color};font-size:11px;font-weight:700;padding:2px 6px;border-radius:6px;background:rgba(255,255,255,0.06);")
        layout.addWidget(badge)

        copy_btn = QPushButton("⎘")
        copy_btn.setToolTip("Copiar esta credencial")
        copy_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.08);border:none;border-radius:6px;color:#c0cae8;font-size:14px;width:32px;height:30px;} QPushButton:hover{background:rgba(125,116,255,0.4);color:white;}")
        copy_btn.clicked.connect(lambda _, t=text: self._copy_text(t, "Contraseña copiada"))
        layout.addWidget(copy_btn)

        self.batch_list_container.addWidget(item)

    def _copy_all_batch(self) -> None:
        if not hasattr(self, "current_batch_results") or not self.current_batch_results:
            return
        all_text = "\n".join(self.current_batch_results)
        self._copy_text(all_text, f"{len(self.current_batch_results)} credenciales copiadas en bloque")

    def _on_regenerate_shortcut(self) -> None:
        idx = self.stack.currentIndex()
        if idx == 0:
            self._generate_password()
        elif idx == 1:
            self._generate_passphrase()
        else:
            self._generate_batch()

    def _on_copy_shortcut(self) -> None:
        idx = self.stack.currentIndex()
        if idx == 0:
            self._copy_password()
        elif idx == 1:
            self._copy_passphrase()
        else:
            self._copy_all_batch()

    def _toggle_password(self) -> None:
        self._password_visible = not self._password_visible
        self.password_edit.setEchoMode(
            QLineEdit.EchoMode.Normal if self._password_visible else QLineEdit.EchoMode.Password
        )
        self.eye_button.setText("◉" if self._password_visible else "◎")

    def _toggle_passphrase(self) -> None:
        self._passphrase_visible = not self._passphrase_visible
        self.passphrase_edit.setEchoMode(
            QLineEdit.EchoMode.Normal if self._passphrase_visible else QLineEdit.EchoMode.Password
        )
        self.passphrase_eye.setText("◉" if self._passphrase_visible else "◎")

    def _copy_password(self) -> None:
        self._copy_text(self.password_edit.text(), "Contraseña copiada")

    def _copy_passphrase(self) -> None:
        self._copy_text(self.passphrase_edit.text(), "Frase de paso copiada")

    def _copy_text(self, text: str, msg_prefix: str) -> None:
        if not text:
            return
        QApplication.clipboard().setText(text)
        self._clipboard_token = text
        self._show_status(f"{msg_prefix} · Se limpiará del portapapeles en 30 segundos")
        QTimer.singleShot(CLIPBOARD_CLEAR_MS, lambda: self._clear_clipboard(text))

    def _clear_clipboard(self, expected: str) -> None:
        clipboard = QApplication.clipboard()
        if clipboard.text() == expected:
            clipboard.clear()
            if self._clipboard_token == expected:
                self._show_status("El portapapeles se limpió por seguridad")
        if self._clipboard_token == expected:
            self._clipboard_token = None

    def _show_status(self, message: str, error: bool = False) -> None:
        self.status_label.setText(message)
        self.status_label.setProperty("error", error)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)


# ----------------------------------------------------------------------
# Estilos CSS (Dark Glassmorphism)
# ----------------------------------------------------------------------

STYLESHEET = """
QWidget#root {
    background: transparent;
    color: #f5f7ff;
    font-family: Inter, "SF Pro Display", "Segoe UI", sans-serif;
    font-size: 14px;
}
QFrame#glass {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(24,29,49,247), stop:0.52 rgba(15,20,38,247), stop:1 rgba(30,20,48,247));
    border: 1px solid rgba(255,255,255,35);
    border-radius: 24px;
}
QWidget#titleBar {background: transparent;}
QLabel#windowTitle {color: rgba(242,245,255,185); font-weight: 600;}
QLabel#eyebrow {color: #8e9ab8; font-size: 11px; font-weight: 700; letter-spacing: 2px;}

QFrame#modeSwitcher {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
}
QPushButton.modeTab {
    background: transparent;
    border: none;
    border-radius: 9px;
    color: #9aa8c7;
    font-size: 13px;
    font-weight: 600;
    padding: 7px 16px;
}
QPushButton.modeTab:hover {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.07);
}
QPushButton.modeTab[active="true"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3954db, stop:1 #674ee8);
    color: #ffffff;
    font-weight: 700;
}

QFrame#passwordCard, QFrame#optionsCard {
    background: rgba(255,255,255,13);
    border: 1px solid rgba(255,255,255,25);
    border-radius: 15px;
}
QLineEdit#passwordEdit {
    background: transparent;
    border: none;
    color: white;
    font-family: "JetBrains Mono", "SF Mono", Consolas, monospace;
    font-size: 19px;
    selection-background-color: #675ee8;
}
QPushButton#iconButton {
    background: rgba(255,255,255,12);
    border: 1px solid rgba(255,255,255,18);
    border-radius: 10px;
    color: #bfc8e8;
    font-size: 19px;
    min-width: 40px;
    min-height: 40px;
}
QPushButton#iconButton:hover {
    background: rgba(125,116,255,45);
    color: white;
}

QLabel#strengthLabel {font-weight: 650;}
QLabel#secondary {color: #8e9ab8;}
QLabel#sectionTitle {color: #edf0ff; font-size: 15px; font-weight: 650;}
QLabel#subSectionTitle {color: #c9d2f0; font-size: 13px; font-weight: 600;}

QLabel#lengthBadge {
    color: #d9dcff;
    background: rgba(112,100,255,42);
    border: 1px solid rgba(145,135,255,60);
    border-radius: 9px;
    min-width: 36px;
    padding: 3px 8px;
    font-weight: 700;
    text-align: center;
}

QPushButton.segmentedBtn {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    color: #a6b2d4;
    font-size: 12px;
    font-weight: 600;
    padding: 5px 12px;
}
QPushButton.segmentedBtn:hover {
    color: white;
    background: rgba(255,255,255,0.12);
}
QPushButton.segmentedBtn[active="true"] {
    background: #5d52e0;
    border-color: #7b71ff;
    color: white;
    font-weight: 700;
}

QFrame.batchItem {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
}
QFrame.batchItem:hover {
    background: rgba(255,255,255,0.09);
    border-color: rgba(120,110,255,0.35);
}

QSlider::groove:horizontal {
    height: 6px;
    background: rgba(255,255,255,18);
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #52bfff,stop:1 #806cff);
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: white;
    border: 4px solid #7468f0;
    width: 15px;
    height: 15px;
    margin: -7px 0;
    border-radius: 11px;
}

QCheckBox {
    color: #dce1f5;
    spacing: 12px;
    min-height: 32px;
}
QCheckBox:disabled {color: #59617a;}
QCheckBox::indicator {
    width: 19px;
    height: 19px;
    border-radius: 6px;
    border: 1px solid #56607d;
    background: rgba(255,255,255,6);
}
QCheckBox::indicator:hover {border-color: #8b83ff;}
QCheckBox::indicator:checked {background: #756bea; border-color: #948cff; image: none;}

QLabel#status {color: #92a1c3; min-height: 20px;}
QLabel#status[error="true"] {color: #ff7a91;}

QPushButton#primaryButton {
    color: white;
    font-size: 14px;
    font-weight: 700;
    min-height: 46px;
    border: 1px solid rgba(255,255,255,42);
    border-radius: 13px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #347fdb,stop:.48 #665ee8,stop:1 #8b4fc5);
}
QPushButton#primaryButton:hover {border-color: rgba(255,255,255,100);}
QPushButton#primaryButton:pressed {background: #5148c7;}

QPushButton#secondaryButton {
    color: #d8dff7;
    font-size: 13px;
    font-weight: 650;
    min-height: 46px;
    border: 1px solid rgba(255,255,255,22);
    border-radius: 13px;
    background: rgba(255,255,255,0.08);
}
QPushButton#secondaryButton:hover {
    background: rgba(255,255,255,0.14);
    color: white;
}

QLabel#footer {color: rgba(174,184,214,125); font-size: 11px; padding-left: 20px;}
QSizeGrip {width: 18px; height: 18px;}
QToolTip {color: white; background: #242940; border: 1px solid #454c6b; padding: 5px;}

QScrollArea#mainScroll {background: transparent; border: none;}
QWidget#scrollContent {background: transparent;}
QScrollBar:vertical {background: transparent; width: 6px; margin: 4px 2px 4px 0;}
QScrollBar::handle:vertical {background: rgba(255,255,255,0.22); min-height: 20px; border-radius: 3px;}
QScrollBar::handle:vertical:hover {background: rgba(255,255,255,0.4);}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height: 0; background: none;}
"""


# ----------------------------------------------------------------------
# Punto de entrada principal
# ----------------------------------------------------------------------

def main() -> int:
    parser = build_cli_parser()

    # Si se pasaron banderas de CLI o se pide explícitamente ayuda o modo CLI
    cli_flags = {"-l", "--length", "-c", "--count", "-p", "--passphrase", "-w", "--words",
                 "-s", "--separator", "--no-caps", "--no-num", "--no-upper", "--no-lower",
                 "--no-digits", "--no-symbols", "--safe", "--exclude-ambiguous", "-e",
                 "--entropy", "-C", "--copy", "--cli", "-h", "--help"}

    has_cli_intent = any(arg in cli_flags for arg in sys.argv[1:])

    if has_cli_intent and "--gui" not in sys.argv:
        args = parser.parse_args(sys.argv[1:])
        return run_cli(args)

    # Modo GUI: Identidad explícita para el compositor y el entorno de escritorio
    sys.argv[0] = "custos"
    app = QApplication(sys.argv)
    app.setApplicationName("custos")
    app.setApplicationDisplayName("Custos")
    app.setDesktopFileName("custos")
    app.setStyle("Fusion")

    # Icono oficial
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_paths = [
        os.path.join(base_dir, "custos.svg"),
        os.path.expanduser("~/.local/share/custos/custos.svg"),
        os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps/custos.svg"),
        os.path.join(base_dir, "password-studio.svg"),
    ]
    for p in icon_paths:
        if os.path.isfile(p):
            app.setWindowIcon(QIcon(p))
            break
    else:
        app.setWindowIcon(QIcon.fromTheme("custos", QIcon.fromTheme("security-high")))

    window = App()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
