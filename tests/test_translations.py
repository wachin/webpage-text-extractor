#!/usr/bin/env python3
"""Tests for the GUI translations (Qt .qm files in translations/).

For every supported locale the test loads the compiled translation and
checks that the translated strings are really present in the .qm, i.e.
that switching the locale makes translated UI strings appear.
"""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtCore import QTranslator  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TRANSLATIONS_DIR = REPO_ROOT / "translations"

APP_ID = "webpage-text-extractor"

LOCALES = [
    "es_ES", "de_DE", "fr_FR", "fr_CA",
    "id_ID", "ja_JP", "ko",
    "pt_BR", "pt_PT",
    "th_TH", "tr_TR", "ru_RU",
    "zh_CN", "zh_TW", "zh_HK",
]

# (locale, context, source, expected translation) spot-checks.
LOCALE_STRINGS = [
    ("es_ES", "MainWindow", "Ready", "Listo"),
    ("es_ES", "MainWindow", "Extraction", "Extracción"),
    ("es_ES", "MainWindow", "Extract text", "Extraer texto"),
    ("de_DE", "MainWindow", "Ready", "Bereit"),
    ("de_DE", "MainWindow", "Extraction", "Extraktion"),
    ("de_DE", "MainWindow", "Extract text", "Text extrahieren"),
    ("fr_FR", "MainWindow", "Ready", "Prêt"),
    ("fr_FR", "MainWindow", "Extraction", "Extraction"),
    ("fr_FR", "MainWindow", "Extract text", "Extraire le texte"),
    ("id_ID", "MainWindow", "Ready", "Siap"),
    ("id_ID", "MainWindow", "Extraction", "Ekstraksi"),
    ("ja_JP", "MainWindow", "Ready", "\u6e96\u5099\u5b8c\u4e86"),
    ("ja_JP", "MainWindow", "Extraction", "\u62bd\u51fa"),
]


def _load_translator(locale: str) -> QTranslator:
    translator = QTranslator()
    assert translator.load(
        f"{APP_ID}_{locale}", str(TRANSLATIONS_DIR)
    ), f"missing translations/{APP_ID}_{locale}.qm"
    return translator


@pytest.mark.parametrize("locale", LOCALES)
def test_qm_file_exists_and_loads(locale: str) -> None:
    translator = _load_translator(locale)
    # With no translation the source string comes back unchanged; a real
    # translation proves the .qm contains translated UI strings for this locale.
    ready = translator.translate("MainWindow", "Ready")
    assert ready and ready != "Ready", f"{locale}: 'Ready' not translated"


@pytest.mark.parametrize("locale,context,source,expected", LOCALE_STRINGS)
def test_translated_strings_match(
    locale: str, context: str, source: str, expected: str
) -> None:
    translator = _load_translator(locale)
    got = translator.translate(context, source)
    assert got == expected, (
        f"{locale}: {context}/{source!r} -> {got!r} (expected {expected!r})"
    )