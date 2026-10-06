#!/usr/bin/env python3
"""
extract_text_gui.py — Graphical user interface (PyQt6) for
webpage-text-extractor.

Extracts the content of every text file inside a folder (for example a web
page saved with "Ctrl + S" in Chrome) and concatenates it into a single .txt
report ready to send to an AI agent.

Features
--------
* Tab "Extraction": selectors for the input folder, the output folder and the
  output file name, plus a progress bar and the execution log.
* Tab "Exclusions": 18 selectors to exclude directories or files; they can
  be filled in bulk with "Add multiple folders..." and hidden entries
  (.git, .venv, ...) can be revealed with "Show hidden files and folders".
* Help > About: developer information dialog; program icon on the left,
  text on the right, with clickable e-mail and website links.
* Light and dark themes (menu View > Theme).
* The interface is written in English and every user-visible string uses
  tr(), so the program can be translated with Qt Linguist.
* Multi-platform: Windows, Linux and macOS.

Requirements
------------
* Python 3.8 or higher and PyQt6::

    pip install PyQt6

* On Linux, install Qt's translations so that the standard dialogs
  (Open file / Save file, ...) automatically appear in the system language::

    sudo apt install qt6-translations-l10n

Run
---
    python extract_text_gui.py

Copyright: (c) 2026 Washington Indacochea Delgado <linuxfrontier@proton.me>
License: GPL-3.0
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import (
    QDir,
    QLibraryInfo,
    QLocale,
    QSettings,
    QThread,
    QTranslator,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QCloseEvent,
    QColor,
    QIcon,
    QKeySequence,
    QPalette,
    QPixmap,
)
try:  # QFileSystemModel moved between Qt modules across Qt 6 versions.
    from PyQt6.QtGui import QFileSystemModel
except ImportError:  # pragma: no cover - fallback for older bindings
    from PyQt6.QtWidgets import QFileSystemModel
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QTabWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from extract_text import es_archivo_texto

APP_NAME = "Webpage Text Extractor"
APP_VERSION = "1.0.0"
ORG_NAME = "wachin"
APP_ID = "webpage-text-extractor"
NUM_EXCLUSION_SELECTORS = 18

BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "icons" / "webpage-text-extractor.svg"
TRANSLATIONS_DIR = BASE_DIR / "translations"

# ---------------------------------------------------------------------------
# Themes (light / dark)
# ---------------------------------------------------------------------------

def build_palette(dark: bool) -> QPalette:
    """Build the QPalette used by the whole application (Fusion style).

    The palette is applied at application level, so every widget — including
    the Qt dialogs (Open file / Save file, ...) — follows the chosen theme.
    """
    if dark:
        colors = {
            QPalette.ColorRole.Window: "#24272c",
            QPalette.ColorRole.WindowText: "#e8eaed",
            QPalette.ColorRole.Base: "#1b1d21",
            QPalette.ColorRole.AlternateBase: "#272a2f",
            QPalette.ColorRole.ToolTipBase: "#31353c",
            QPalette.ColorRole.ToolTipText: "#e8eaed",
            QPalette.ColorRole.Text: "#e8eaed",
            QPalette.ColorRole.Button: "#2e3238",
            QPalette.ColorRole.ButtonText: "#e8eaed",
            QPalette.ColorRole.BrightText: "#ff7b72",
            QPalette.ColorRole.Link: "#6aa8ff",
            QPalette.ColorRole.LinkVisited: "#b39dff",
            QPalette.ColorRole.Highlight: "#3b82f6",
            QPalette.ColorRole.HighlightedText: "#ffffff",
            QPalette.ColorRole.PlaceholderText: "#9aa1ab",
            QPalette.ColorRole.Light: "#3d424a",
            QPalette.ColorRole.Midlight: "#2b2f35",
            QPalette.ColorRole.Mid: "#4a4f57",
            QPalette.ColorRole.Dark: "#191b1f",
            QPalette.ColorRole.Shadow: "#0d0e10",
        }
        disabled = {
            QPalette.ColorRole.Window: "#1f2226",
            QPalette.ColorRole.WindowText: "#7d838c",
            QPalette.ColorRole.Base: "#16181b",
            QPalette.ColorRole.Text: "#7d838c",
            QPalette.ColorRole.Button: "#26292f",
            QPalette.ColorRole.ButtonText: "#7d838c",
            QPalette.ColorRole.PlaceholderText: "#6d737b",
            QPalette.ColorRole.Highlight: "#2b3d5c",
            QPalette.ColorRole.HighlightedText: "#9aa1ab",
        }
    else:
        colors = {
            QPalette.ColorRole.Window: "#eef1f5",
            QPalette.ColorRole.WindowText: "#1c1f23",
            QPalette.ColorRole.Base: "#ffffff",
            QPalette.ColorRole.AlternateBase: "#f4f6f9",
            QPalette.ColorRole.ToolTipBase: "#ffffdc",
            QPalette.ColorRole.ToolTipText: "#1c1f23",
            QPalette.ColorRole.Text: "#1c1f23",
            QPalette.ColorRole.Button: "#ffffff",
            QPalette.ColorRole.ButtonText: "#1c1f23",
            QPalette.ColorRole.BrightText: "#c62828",
            QPalette.ColorRole.Link: "#1558c0",
            QPalette.ColorRole.LinkVisited: "#7048a8",
            QPalette.ColorRole.Highlight: "#2f6fed",
            QPalette.ColorRole.HighlightedText: "#ffffff",
            QPalette.ColorRole.PlaceholderText: "#8b929c",
            QPalette.ColorRole.Light: "#ffffff",
            QPalette.ColorRole.Midlight: "#e9ecf1",
            QPalette.ColorRole.Mid: "#b9bec6",
            QPalette.ColorRole.Dark: "#8b919a",
            QPalette.ColorRole.Shadow: "#6f757e",
        }
        disabled = {
            QPalette.ColorRole.Window: "#e9ecf1",
            QPalette.ColorRole.WindowText: "#9aa0a8",
            QPalette.ColorRole.Base: "#eceff3",
            QPalette.ColorRole.Text: "#9aa0a8",
            QPalette.ColorRole.Button: "#e2e5ea",
            QPalette.ColorRole.ButtonText: "#9aa0a8",
            QPalette.ColorRole.PlaceholderText: "#a6abb4",
            QPalette.ColorRole.Highlight: "#c8d5ea",
            QPalette.ColorRole.HighlightedText: "#8b919a",
        }

    palette = QPalette()
    for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
        for role, value in colors.items():
            palette.setColor(group, role, QColor(value))
    for role, value in disabled.items():
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(value))
    return palette

# ---------------------------------------------------------------------------
# About / developer information
# ---------------------------------------------------------------------------

class AboutWidget(QWidget):
    """Developer information: program icon on the left, text on the right.

    The e-mail and website links are clickable and open with the operating
    system's default mail client / web browser.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(24)

        # Left: the program icon, centered and large.
        icon_label = QLabel()
        pixmap = QPixmap(str(ICON_PATH))
        if not pixmap.isNull():
            icon_label.setPixmap(
                pixmap.scaled(
                    192,
                    192,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        # Right: the text.
        info = QLabel()
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setOpenExternalLinks(True)
        info.setWordWrap(True)
        info.setContentsMargins(0, 8, 0, 0)
        info.setText(self._build_html())
        layout.addWidget(info, 1, Qt.AlignmentFlag.AlignTop)

    def _build_html(self) -> str:
        link = "#2f6fed"
        return (
            f"<h2>{APP_NAME} <span style='color:#8b929c;'>{APP_VERSION}</span></h2>"
            "<p>"
            + self.tr(
                "Extracts the content of every text file in a folder — for "
                "example a web page saved with Ctrl + S in Chrome — and "
                "concatenates it into a single .txt report ready to send to "
                "an AI agent."
            )
            + "</p>"
            "<table cellpadding='4'>"
            "<tr><td><b>" + self.tr("Copyright:") + "</b></td>"
            "<td>© 2026 Washington Indacochea Delgado</td></tr>"
            "<tr><td><b>" + self.tr("Email:") + "</b></td>"
            f"<td><a href='mailto:linuxfrontier@proton.me' style='color:{link};'>"
            "linuxfrontier@proton.me</a></td></tr>"
            "<tr><td><b>" + self.tr("License:") + "</b></td>"
            "<td>GPL3</td></tr>"
            "<tr><td><b>" + self.tr("Website:") + "</b></td>"
            "<td><a href='https://github.com/wachin/webpage-text-extractor' "
            f"style='color:{link};'>https://github.com/wachin/webpage-text-extractor</a></td></tr>"
            "<tr><td><b>" + self.tr("Technologies used:") + "</b></td>"
            "<td>Python 3 · PyQt6 · Qt 6</td></tr>"
            "</table>"
        )


# ---------------------------------------------------------------------------
# Background extraction worker
# ---------------------------------------------------------------------------

class ExtractionWorker(QThread):
    """Scans the input folder and writes the report in a background thread
    so that the graphical interface stays responsive.

    Signals
    -------
    log_message:      one line for the log pane.
    progress_changed: progress percentage (0-100).
    cancelled:        emitted when the user cancels the extraction.
    result_ready:     (success, message) when the extraction finishes.
    """

    log_message = pyqtSignal(str)
    progress_changed = pyqtSignal(int)
    cancelled = pyqtSignal(str)
    result_ready = pyqtSignal(bool, str)

    def __init__(
        self,
        input_dir: str,
        output_file: str,
        exclusions: list,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.input_dir = input_dir
        self.output_file = output_file
        # List of (path, is_directory).
        self.exclusions = exclusions

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _normalize(path: str) -> str:
        return os.path.normcase(os.path.normpath(os.path.abspath(path)))

    def _compile_exclusions(self) -> tuple:
        excluded_dirs = []
        excluded_files = set()
        for path, is_directory in self.exclusions:
            if is_directory:
                excluded_dirs.append(self._normalize(path))
            else:
                excluded_files.add(self._normalize(path))
        # The report itself must never be read back while we write it.
        excluded_files.add(self._normalize(self.output_file))
        return excluded_dirs, excluded_files

    @staticmethod
    def _is_excluded(path: str, excluded_dirs: list, excluded_files: set) -> bool:
        normalized = os.path.normcase(os.path.normpath(os.path.abspath(path)))
        if normalized in excluded_files:
            return True
        return any(
            normalized == directory or normalized.startswith(directory + os.sep)
            for directory in excluded_dirs
        )

    def _count_files(self, excluded_dirs: list, excluded_files: set) -> int:
        """Quick pre-scan used to report a meaningful progress percentage."""
        total = 0
        for root, subdirs, names in os.walk(self.input_dir):
            subdirs[:] = [
                name
                for name in subdirs
                if not self._is_excluded(
                    os.path.join(root, name), excluded_dirs, excluded_files
                )
            ]
            total += sum(
                1
                for name in names
                if not self._is_excluded(
                    os.path.join(root, name), excluded_dirs, excluded_files
                )
            )
        return total

    # -- main work ---------------------------------------------------------

    def run(self) -> None:
        try:
            self._extract()
        except Exception as error:  # Surface any error to the interface.
            self.result_ready.emit(
                False,
                self.tr("Extraction failed: {error}").format(error=error),
            )

    def _extract(self) -> None:
        if not os.path.isdir(self.input_dir):
            self.result_ready.emit(
                False,
                self.tr("The input folder does not exist: {path}").format(
                    path=self.input_dir
                ),
            )
            return

        output_dir = os.path.dirname(self.output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        excluded_dirs, excluded_files = self._compile_exclusions()
        total = self._count_files(excluded_dirs, excluded_files)

        processed = 0
        text_count = 0
        binary_count = 0
        excluded_count = 0
        cancelled = False

        with open(self.output_file, "w", encoding="utf-8") as report:
            for root, subdirs, names in os.walk(self.input_dir):
                if cancelled:
                    break

                # Prune excluded directories (keeping a stable order).
                kept_dirs = []
                for name in sorted(subdirs):
                    full_path = os.path.join(root, name)
                    if self._is_excluded(full_path, excluded_dirs, excluded_files):
                        excluded_count += 1
                        self.log_message.emit(
                            self.tr("[excluded directory] {path}").format(
                                path=full_path
                            )
                        )
                    else:
                        kept_dirs.append(name)
                subdirs[:] = kept_dirs

                for name in sorted(names):
                    if self.isInterruptionRequested():
                        cancelled = True
                        break

                    path = os.path.join(root, name)
                    processed += 1

                    if self._is_excluded(path, excluded_dirs, excluded_files):
                        excluded_count += 1
                        self.log_message.emit(
                            self.tr("[excluded] {path}").format(path=path)
                        )
                    elif es_archivo_texto(path):
                        try:
                            with open(path, "r", encoding="utf-8") as handle:
                                content = handle.read()
                            report.write(
                                "\n"
                                + self.tr("--- Text file content: {path} ---").format(
                                    path=path
                                )
                                + "\n"
                            )
                            report.write(content)
                            report.write("\n")
                            text_count += 1
                            self.log_message.emit(
                                self.tr("[text] {path}").format(path=path)
                            )
                        except Exception as error:  # Keep going with next file.
                            report.write(
                                "\n"
                                + self.tr("[error reading {path}: {error}]").format(
                                    path=path, error=error
                                )
                                + "\n"
                            )
                            self.log_message.emit(
                                self.tr("[error] {path}: {error}").format(
                                    path=path, error=error
                                )
                            )
                    else:
                        report.write(
                            "\n"
                            + self.tr("--- Non-text file: {path} ---").format(
                                path=path
                            )
                            + "\n"
                        )
                        binary_count += 1
                        self.log_message.emit(
                            self.tr("[skipped, not text] {path}").format(path=path)
                        )

                    if total > 0:
                        self.progress_changed.emit(
                            min(100, int(processed * 100 / total))
                        )

        if cancelled:
            self.cancelled.emit(
                self.tr(
                    "Extraction cancelled. The partial report was kept at {path}"
                ).format(path=self.output_file)
            )
            return

        self.progress_changed.emit(100)
        self.result_ready.emit(
            True,
            self.tr(
                "Extraction completed: {text} text files, {binary} "
                "non-text/skipped, {excluded} excluded. Report saved to {path}"
            ).format(
                text=text_count,
                binary=binary_count,
                excluded=excluded_count,
                path=self.output_file,
            ),
        )


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Main window with two tabs: Extraction and Exclusions."""

    def __init__(self) -> None:
        super().__init__()

        # Qt translations first, so that the standard dialogs (Open/Save
        # file, ...) appear in the system language.
        self.translator: Optional[QTranslator] = None
        self.app_translator: Optional[QTranslator] = None
        self._install_translators()

        self.settings = QSettings(ORG_NAME, APP_ID)
        self.worker: Optional[ExtractionWorker] = None
        self._restoring = False
        self._output_name_custom = False
        self._excl_kinds: list = [None] * NUM_EXCLUSION_SELECTORS

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(920, 720)

        # Apply the saved theme before building the widgets.
        self._apply_theme(self.settings.value("theme/dark", False, type=bool))

        self._build_ui()
        self._build_menus()
        self._restore_settings()

    # -- translations ------------------------------------------------------

    def _install_translators(self) -> None:
        """Load the Qt translations for the system language.

        This makes the standard Qt dialogs (Open file / Save file, ...) appear
        automatically in the system language.

        On Linux the package `qt6-translations-l10n` must be installed::

            sudo apt install qt6-translations-l10n
        """
        self.translator = QTranslator()
        translations_path = QLibraryInfo.path(
            QLibraryInfo.LibraryPath.TranslationsPath
        )
        locale_name = QLocale.system().name()
        locale_short = locale_name.split("_")[0]

        for name in [f"qtbase_{locale_name}", f"qtbase_{locale_short}"]:
            if self.translator.load(name, translations_path):
                QApplication.installTranslator(self.translator)
                break

        # Application's own translation (produced with Qt Linguist).
        self.app_translator = QTranslator()
        for name in [f"{APP_ID}_{locale_name}", f"{APP_ID}_{locale_short}"]:
            if self.app_translator.load(name, str(TRANSLATIONS_DIR)):
                QApplication.installTranslator(self.app_translator)
                break

    # -- user interface ----------------------------------------------------

    def _build_ui(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._build_extraction_tab(), self.tr("Extraction"))
        self.tabs.addTab(self._build_exclusions_tab(), self.tr("Exclusions"))
        self.setCentralWidget(self.tabs)
        self.statusBar().showMessage(self.tr("Ready"))

    def _build_extraction_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox(self.tr("Source and destination"))
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        # Input folder.
        self.input_edit = QLineEdit()
        self.input_edit.setReadOnly(True)
        self.input_edit.setPlaceholderText(self.tr("Folder to analyze"))
        label_input = QLabel(self.tr("&Input folder:"))
        label_input.setBuddy(self.input_edit)
        self.button_input = QPushButton(self.tr("Browse…"))
        self.button_input.clicked.connect(self._browse_input_folder)
        grid.addWidget(label_input, 0, 0)
        grid.addWidget(self.input_edit, 0, 1)
        grid.addWidget(self.button_input, 0, 2)

        # Output folder.
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText(self.tr("Folder for the report"))
        label_output = QLabel(self.tr("&Output folder:"))
        label_output.setBuddy(self.output_edit)
        self.button_output = QPushButton(self.tr("Browse…"))
        self.button_output.clicked.connect(self._browse_output_folder)
        grid.addWidget(label_output, 1, 0)
        grid.addWidget(self.output_edit, 1, 1)
        grid.addWidget(self.button_output, 1, 2)

        # Output file.
        self.output_name_edit = QLineEdit()
        self.output_name_edit.setPlaceholderText(
            self.tr("Report file name, e.g. page_src.txt")
        )
        label_name = QLabel(self.tr("Output &file:"))
        label_name.setBuddy(self.output_name_edit)
        self.button_name = QPushButton(self.tr("Browse…"))
        self.button_name.clicked.connect(self._browse_output_file)
        grid.addWidget(label_name, 2, 0)
        grid.addWidget(self.output_name_edit, 2, 1)
        grid.addWidget(self.button_name, 2, 2)

        group.setLayout(grid)
        layout.addWidget(group)

        # Run controls.
        run_row = QHBoxLayout()
        self.run_button = QPushButton(self.tr("Extract text"))
        self.run_button.clicked.connect(self._start_extraction)
        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._cancel_extraction)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        run_row.addWidget(self.run_button)
        run_row.addWidget(self.cancel_button)
        run_row.addWidget(self.progress, 1)
        layout.addLayout(run_row)

        # Log.
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel(self.tr("Log:")))
        log_header.addStretch(1)
        button_clear_log = QPushButton(self.tr("Clear log"))
        button_clear_log.clicked.connect(lambda: self.log_view.clear())
        log_header.addWidget(button_clear_log)
        layout.addLayout(log_header)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
        self.log_view.setPlaceholderText(
            self.tr("The execution log will be shown here.")
        )
        layout.addWidget(self.log_view, 1)

        # Keep the default report name in sync with the input folder.
        self.input_edit.textChanged.connect(self._on_input_changed)
        self.output_name_edit.textEdited.connect(
            lambda: setattr(self, "_output_name_custom", True)
        )
        return page

    def _build_exclusions_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)

        intro = QLabel(
            self.tr(
                "Select up to {count} files or directories to exclude from "
                "the extraction. When a directory is excluded, everything "
                "inside it is skipped. Empty selectors are ignored."
            ).format(count=NUM_EXCLUSION_SELECTORS)
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # Option: reveal hidden entries (.git, .cache, ...) in the dialogs.
        options_row = QHBoxLayout()
        self.show_hidden_check = QCheckBox(
            self.tr("Show hidden files and folders")
        )
        self.show_hidden_check.setToolTip(
            self.tr("Reveal entries such as .git so they can be excluded")
        )
        self.show_hidden_check.setChecked(
            self.settings.value("exclusions/show_hidden", False, type=bool)
        )
        self.show_hidden_check.toggled.connect(
            lambda checked: self.settings.setValue(
                "exclusions/show_hidden", checked
            )
        )
        options_row.addWidget(self.show_hidden_check)
        self.add_multi_button = QPushButton(self.tr("Add multiple folders…"))
        self.add_multi_button.setToolTip(
            self.tr(
                "Select several folders at once and fill the exclusion "
                "selectors automatically"
            )
        )
        self.add_multi_button.clicked.connect(self._add_multiple_folders)
        options_row.addWidget(self.add_multi_button)
        options_row.addStretch(1)
        layout.addLayout(options_row)

        group = QGroupBox(self.tr("Files and directories to exclude"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        self.excl_edits: list = []
        self.excl_clear_buttons: list = []
        for index in range(NUM_EXCLUSION_SELECTORS):
            number = QLabel(str(index + 1))
            number.setAlignment(Qt.AlignmentFlag.AlignCenter)

            edit = QLineEdit()
            edit.setReadOnly(True)
            edit.setPlaceholderText(self.tr("Not selected"))
            edit.setToolTip(self.tr("Path that will be skipped in the extraction"))

            button = QPushButton(self.tr("Browse…"))
            menu = QMenu(button)
            action_dir = menu.addAction(self.tr("Exclude a directory…"))
            action_file = menu.addAction(self.tr("Exclude a file…"))
            action_dir.triggered.connect(
                lambda checked=False, row=index: self._select_exclusion(row, True)
            )
            action_file.triggered.connect(
                lambda checked=False, row=index: self._select_exclusion(row, False)
            )
            button.setMenu(menu)

            clear = QPushButton(self.tr("Clear"))
            clear.setEnabled(False)
            clear.clicked.connect(
                lambda checked=False, row=index: self._clear_exclusion(row)
            )

            grid.addWidget(number, index, 0)
            grid.addWidget(edit, index, 1)
            grid.addWidget(button, index, 2)
            grid.addWidget(clear, index, 3)
            self.excl_edits.append(edit)
            self.excl_clear_buttons.append(clear)

        grid.setColumnStretch(1, 1)

        bottom = QHBoxLayout()
        button_clear_all = QPushButton(self.tr("Clear all"))
        button_clear_all.clicked.connect(self._clear_all_exclusions)
        bottom.addWidget(button_clear_all)
        bottom.addStretch(1)
        self.excl_status = QLabel()
        bottom.addWidget(self.excl_status)
        grid.addLayout(bottom, NUM_EXCLUSION_SELECTORS, 0, 1, 4)

        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch(1)

        scroll.setWidget(content)
        self._update_exclusion_status()
        return scroll

    # -- exclusions helpers ------------------------------------------------

    @staticmethod
    def _start_directory(path: str) -> str:
        """Return a directory usable as start path for the file dialogs."""
        if path and os.path.isdir(path):
            return path
        if path:
            parent = os.path.dirname(path)
            if parent and os.path.isdir(parent):
                return parent
        return str(Path.home())

    def _create_exclusion_dialog(self, is_directory: bool, start: str) -> QFileDialog:
        """Build the browse dialog used by the exclusion selectors.

        When "Show hidden files and folders" is enabled, the Qt widget dialog
        is forced (the native dialogs offer no public API to reveal hidden
        entries on every platform) and QDir.Hidden is added to its internal
        file system model, so entries like .git become selectable on
        Windows, Linux and macOS alike.
        """
        if is_directory:
            dialog = QFileDialog(self, self.tr("Select directory to exclude"), start)
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        else:
            dialog = QFileDialog(self, self.tr("Select file to exclude"), start)
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            dialog.setNameFilter(self.tr("All files (*)"))

        if self.show_hidden_check.isChecked():
            dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
            for model in dialog.findChildren(QFileSystemModel):
                model.setFilter(
                    model.filter() | QDir.Filter.Hidden | QDir.Filter.System
                )
        return dialog

    def _create_multi_folder_dialog(self, start: str) -> QFileDialog:
        """Build the picker used by "Add multiple folders…".

        The Qt widget dialog is always used (the native dialogs cannot
        select more than one directory), its list allows extended selection
        (Ctrl+Click / Shift+Click) and, when "Show hidden files and
        folders" is enabled, hidden folders like .git are visible too.
        """
        dialog = QFileDialog(self, self.tr("Select folders to exclude"), start)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        if self.show_hidden_check.isChecked():
            for model in dialog.findChildren(QFileSystemModel):
                model.setFilter(
                    model.filter() | QDir.Filter.Hidden | QDir.Filter.System
                )
        for view in dialog.findChildren(QTreeView):
            view.setSelectionMode(
                QAbstractItemView.SelectionMode.ExtendedSelection
            )
        return dialog

    def _select_exclusion(self, row: int, is_directory: bool) -> None:
        current = self.excl_edits[row].text()
        start = self._start_directory(current or self.input_edit.text())

        dialog = self._create_exclusion_dialog(is_directory, start)
        if not dialog.exec():
            return
        selected = dialog.selectedFiles()
        if not selected:
            return
        path = selected[0]
        kind = "dir" if is_directory else "file"

        self.excl_edits[row].setText(path)
        self._excl_kinds[row] = kind
        self.excl_clear_buttons[row].setEnabled(True)
        self._update_exclusion_status()

    def _add_multiple_folders(self) -> None:
        """Open the multi-folder picker and fill empty selectors with it."""
        start = self._start_directory(self.input_edit.text())
        dialog = self._create_multi_folder_dialog(start)
        if not dialog.exec():
            return
        paths = dialog.selectedFiles()
        if not paths:
            return
        self._add_exclusion_paths(paths, "dir")

    def _add_exclusion_paths(self, paths: list, kind: str) -> None:
        """Put `paths` into the first empty selectors (duplicates skipped)."""
        existing = {
            os.path.normpath(edit.text().strip())
            for edit in self.excl_edits
            if edit.text().strip()
        }
        missing = 0
        for path in paths:
            normalized = os.path.normpath(path)
            if normalized in existing:
                continue
            row = next(
                (
                    index
                    for index, edit in enumerate(self.excl_edits)
                    if not edit.text().strip()
                ),
                None,
            )
            if row is None:
                missing += 1
                continue
            self.excl_edits[row].setText(path)
            self._excl_kinds[row] = kind
            self.excl_clear_buttons[row].setEnabled(True)
            existing.add(normalized)
        self._update_exclusion_status()
        if missing:
            QMessageBox.information(
                self,
                self.tr("Selectors full"),
                self.tr(
                    "{missing} of the {selected} selected folders could not "
                    "be added: all {total} selectors are in use."
                ).format(
                    missing=missing,
                    selected=len(paths),
                    total=NUM_EXCLUSION_SELECTORS,
                ),
            )

    def _clear_exclusion(self, row: int) -> None:
        self.excl_edits[row].clear()
        self._excl_kinds[row] = None
        self.excl_clear_buttons[row].setEnabled(False)
        self._update_exclusion_status()

    def _clear_all_exclusions(self) -> None:
        for row in range(NUM_EXCLUSION_SELECTORS):
            self._clear_exclusion(row)

    def _update_exclusion_status(self) -> None:
        used = sum(1 for edit in self.excl_edits if edit.text().strip())
        self.excl_status.setText(
            self.tr("{used} of {total} selectors in use").format(
                used=used, total=NUM_EXCLUSION_SELECTORS
            )
        )

    def _collect_exclusions(self) -> list:
        entries = []
        for row, edit in enumerate(self.excl_edits):
            path = edit.text().strip()
            if not path:
                continue
            is_directory = self._excl_kinds[row] != "file"
            entries.append((path, is_directory))
        return entries

    # -- menus and themes --------------------------------------------------

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr("&File"))
        quit_action = QAction(self.tr("&Quit"), self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.setMenuRole(QAction.MenuRole.QuitRole)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = self.menuBar().addMenu(self.tr("&View"))
        theme_menu = view_menu.addMenu(self.tr("&Theme"))
        self.theme_group = QActionGroup(self)
        self.light_action = QAction(self.tr("&Light"), self)
        self.dark_action = QAction(self.tr("&Dark"), self)
        for action in (self.light_action, self.dark_action):
            action.setCheckable(True)
            self.theme_group.addAction(action)
            theme_menu.addAction(action)

        dark = self.settings.value("theme/dark", False, type=bool)
        (self.dark_action if dark else self.light_action).setChecked(True)
        self.light_action.triggered.connect(lambda: self._apply_theme(False))
        self.dark_action.triggered.connect(lambda: self._apply_theme(True))

        help_menu = self.menuBar().addMenu(self.tr("&Help"))
        about_action = QAction(
            self.tr("&About {name}…").format(name=APP_NAME), self
        )
        about_action.setMenuRole(QAction.MenuRole.AboutRole)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _apply_theme(self, dark: bool) -> None:
        """Switch between the light and dark themes."""
        app = QApplication.instance()
        if app is not None:
            app.setPalette(build_palette(dark))
        self.settings.setValue("theme/dark", dark)
        # The menu actions only exist after _build_menus() has run.
        if getattr(self, "dark_action", None) is not None:
            action = self.dark_action if dark else self.light_action
            if not action.isChecked():
                action.setChecked(True)

    def _show_about(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("About {name}").format(name=APP_NAME))
        layout = QVBoxLayout(dialog)
        layout.addWidget(AboutWidget(dialog))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.resize(760, 360)
        dialog.exec()

    # -- folder / file selectors -------------------------------------------

    def _browse_input_folder(self) -> None:
        start = self._start_directory(self.input_edit.text())
        path = QFileDialog.getExistingDirectory(
            self, self.tr("Select input folder"), start
        )
        if path:
            self.input_edit.setText(path)

    def _browse_output_folder(self) -> None:
        start = self._start_directory(self.output_edit.text())
        path = QFileDialog.getExistingDirectory(
            self, self.tr("Select output folder"), start
        )
        if path:
            self.output_edit.setText(path)

    def _browse_output_file(self) -> None:
        start_dir = self._start_directory(self.output_edit.text())
        suggested = self.output_name_edit.text().strip() or f"{APP_ID}_src.txt"
        path, _selected = QFileDialog.getSaveFileName(
            self,
            self.tr("Select output file"),
            os.path.join(start_dir, suggested),
            self.tr("Text files (*.txt);;All files (*)"),
        )
        if not path:
            return
        folder, name = os.path.split(path)
        self.output_name_edit.setText(name)
        self._output_name_custom = True
        if folder:
            self.output_edit.setText(folder)

    def _on_input_changed(self, text: str) -> None:
        """Suggest the output folder and the report name for a new input."""
        if self._restoring or not text.strip():
            return
        if not self.output_edit.text().strip():
            parent = os.path.dirname(os.path.normpath(text))
            if parent:
                self.output_edit.setText(parent)
        if not self._output_name_custom:
            base = os.path.basename(os.path.normpath(text))
            if base:
                self.output_name_edit.setText(f"{base}_src.txt")

    # -- extraction control ------------------------------------------------

    def _append_log(self, message: str) -> None:
        self.log_view.appendPlainText(f"[{time.strftime('%H:%M:%S')}] {message}")

    def _set_running(self, running: bool) -> None:
        self.run_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.button_input.setEnabled(not running)
        self.button_output.setEnabled(not running)
        self.button_name.setEnabled(not running)
        if running:
            self.progress.setValue(0)

    def _start_extraction(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return

        input_dir = self.input_edit.text().strip()
        if not input_dir or not os.path.isdir(input_dir):
            QMessageBox.warning(
                self,
                self.tr("Invalid input folder"),
                self.tr("The input folder does not exist:\n{path}").format(
                    path=input_dir or "—"
                ),
            )
            return

        output_dir = self.output_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(
                self,
                self.tr("Missing output folder"),
                self.tr("Please choose an output folder for the report."),
            )
            return

        file_name = self.output_name_edit.text().strip()
        if not file_name:
            QMessageBox.warning(
                self,
                self.tr("Missing output file"),
                self.tr("Please enter an output file name."),
            )
            return

        output_file = (
            file_name
            if os.path.isabs(file_name)
            else os.path.join(output_dir, file_name)
        )

        self._append_log(
            self.tr("Extraction started: {source} → {target}").format(
                source=input_dir, target=output_file
            )
        )
        self.statusBar().showMessage(self.tr("Extracting…"))
        self._set_running(True)

        self.worker = ExtractionWorker(
            input_dir, output_file, self._collect_exclusions()
        )
        self.worker.log_message.connect(self._append_log)
        self.worker.progress_changed.connect(self.progress.setValue)
        self.worker.cancelled.connect(self._on_worker_cancelled)
        self.worker.result_ready.connect(self._on_worker_result)
        self.worker.start()

    def _cancel_extraction(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.cancel_button.setEnabled(False)
            self.worker.requestInterruption()
            self.statusBar().showMessage(self.tr("Cancelling…"))

    def _on_worker_result(self, success: bool, message: str) -> None:
        self._append_log(message)
        self._set_running(False)
        self.statusBar().showMessage(message)
        if not success:
            QMessageBox.warning(self, APP_NAME, message)

    def _on_worker_cancelled(self, message: str) -> None:
        self._append_log(message)
        self._set_running(False)
        self.statusBar().showMessage(message)

    # -- settings ----------------------------------------------------------

    @staticmethod
    def _read_list(settings: QSettings, key: str) -> list:
        value = settings.value(key, [])
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    def _restore_settings(self) -> None:
        self._restoring = True
        try:
            geometry = self.settings.value("window/geometry")
            if geometry is not None:
                self.restoreGeometry(geometry)

            self.input_edit.setText(self.settings.value("paths/input", "", type=str))
            self.output_edit.setText(
                self.settings.value("paths/output", "", type=str)
            )
            self.output_name_edit.setText(
                self.settings.value("paths/output_name", "", type=str)
            )
            self._output_name_custom = self.settings.value(
                "paths/output_name_custom", False, type=bool
            )

            paths = self._read_list(self.settings, "exclusions/paths")
            kinds = self._read_list(self.settings, "exclusions/kinds")
            for row, path in enumerate(paths[:NUM_EXCLUSION_SELECTORS]):
                if not path:
                    continue
                self.excl_edits[row].setText(path)
                kind = kinds[row] if row < len(kinds) else None
                self._excl_kinds[row] = kind if kind in ("dir", "file") else "dir"
                self.excl_clear_buttons[row].setEnabled(True)
        finally:
            self._restoring = False
        self._update_exclusion_status()

    def _save_settings(self) -> None:
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("paths/input", self.input_edit.text())
        self.settings.setValue("paths/output", self.output_edit.text())
        self.settings.setValue("paths/output_name", self.output_name_edit.text())
        self.settings.setValue("paths/output_name_custom", self._output_name_custom)
        self.settings.setValue(
            "exclusions/paths",
            [edit.text().strip() for edit in self.excl_edits if edit.text().strip()],
        )
        self.settings.setValue(
            "exclusions/kinds",
            [
                self._excl_kinds[row]
                for row, edit in enumerate(self.excl_edits)
                if edit.text().strip()
            ],
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt naming)
        # Stop the background thread before closing.
        if self.worker is not None and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(5000)

        # Remove the translators before they are destroyed with the window.
        app = QApplication.instance()
        if app is not None:
            if self.translator is not None:
                app.removeTranslator(self.translator)
            if self.app_translator is not None:
                app.removeTranslator(self.app_translator)

        self._save_settings()
        event.accept()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORG_NAME)
    # Fusion gives the same look (and working themes) on Windows, Linux
    # and macOS.
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())


