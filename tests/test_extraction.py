#!/usr/bin/env python3
"""Tests for text detection, encoding fallbacks and output-path safety."""

import codecs
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import extract_text  # noqa: E402
import extract_text_gui  # noqa: E402


def _both_readers(path: Path):
    """Return the CLI and GUI readings of the same file."""
    return (
        extract_text.leer_archivo_texto(str(path)),
        extract_text_gui.read_text_file(str(path)),
    )


def test_utf8_bom_is_removed(tmp_path: Path) -> None:
    path = tmp_path / "page.html"
    path.write_bytes(codecs.BOM_UTF8 + "<p>café</p>".encode("utf-8"))

    cli_text, gui_text = _both_readers(path)
    assert cli_text == "<p>café</p>"
    assert gui_text == "<p>café</p>"


def test_windows_1252_fallback(tmp_path: Path) -> None:
    path = tmp_path / "notas.txt"
    path.write_bytes("Informe: café, niño, acción".encode("cp1252"))

    cli_text, gui_text = _both_readers(path)
    assert cli_text == "Informe: café, niño, acción"
    assert gui_text == "Informe: café, niño, acción"


def test_utf16_bom_is_supported(tmp_path: Path) -> None:
    path = tmp_path / "unicode.txt"
    path.write_bytes("Hola, ñandú".encode("utf-16"))

    cli_text, gui_text = _both_readers(path)
    assert cli_text == "Hola, ñandú"
    assert gui_text == "Hola, ñandú"


def test_binary_with_nul_is_skipped(tmp_path: Path) -> None:
    path = tmp_path / "image.bin"
    path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    assert _both_readers(path) == (None, None)


def test_binary_control_bytes_are_skipped(tmp_path: Path) -> None:
    path = tmp_path / "data.bin"
    path.write_bytes(b"\x01\x02\x03\x04\x05" * 100)

    assert _both_readers(path) == (None, None)


def test_plain_text_with_tabs_and_newlines_is_readable(tmp_path: Path) -> None:
    path = tmp_path / "code.py"
    path.write_bytes(b"def main():\n\treturn 1\n")

    cli_text, gui_text = _both_readers(path)
    assert cli_text == "def main():\n\treturn 1\n"
    assert gui_text == "def main():\n\treturn 1\n"


def test_output_inside_input_is_rejected(tmp_path: Path) -> None:
    input_dir = tmp_path / "page"
    input_dir.mkdir()
    (input_dir / "index.html").write_text("<html>Hello</html>", encoding="utf-8")
    output = input_dir / "report.txt"

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "extract_text.py"),
            str(input_dir),
            "-o",
            str(output),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 1
    assert "no puede estar dentro" in result.stderr
    assert not output.exists()


def test_output_cannot_overwrite_a_source_file(tmp_path: Path) -> None:
    input_dir = tmp_path / "page"
    input_dir.mkdir()
    source = input_dir / "index.html"
    original = "<html>Do not overwrite me</html>"
    source.write_text(original, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "extract_text.py"),
            str(input_dir),
            "-o",
            str(source),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 1
    assert source.read_text(encoding="utf-8") == original


def test_cli_extracts_ansi_file_outside_input(tmp_path: Path) -> None:
    input_dir = tmp_path / "page"
    input_dir.mkdir()
    (input_dir / "index.html").write_text(
        "<html>Hola</html>", encoding="utf-8"
    )
    (input_dir / "notas.txt").write_bytes("café".encode("cp1252"))
    output = tmp_path / "report.txt"

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "extract_text.py"),
            str(input_dir),
            "-o",
            str(output),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0, result.stderr
    report = output.read_text(encoding="utf-8")
    assert "Hola" in report
    assert "café" in report
    assert "\ufeff" not in report


def test_gui_path_containment_helper(tmp_path: Path) -> None:
    input_dir = tmp_path / "page"
    input_dir.mkdir()
    nested = input_dir / "sub" / "report.txt"
    sibling = tmp_path / "report.txt"

    assert extract_text_gui.is_path_within(str(nested), str(input_dir))
    assert not extract_text_gui.is_path_within(str(sibling), str(input_dir))
    assert extract_text.esta_dentro_de(str(nested), str(input_dir))
    assert not extract_text.esta_dentro_de(str(sibling), str(input_dir))


# ---------------------------------------------------------------------------
# Extension filter
# ---------------------------------------------------------------------------


def _action(path: str, rules) -> str:
    return extract_text_gui.extension_action(path, list(rules))


def test_extension_filter_normalizes_tokens() -> None:
    normalize = extract_text_gui.normalize_filter_token

    assert normalize("  .SVG  ") == ".svg"
    assert normalize("*.Min.JS") == ".min.js"
    assert normalize("PACKAGE-LOCK.JSON") == "package-lock.json"


def test_default_rules_mention_svg_and_lock_files() -> None:
    rules = extract_text_gui.DEFAULT_EXTENSION_RULES

    assert _action("site/assets/diseno.svg", rules) == (
        extract_text_gui.FILTER_MENTION
    )
    assert _action("package-lock.json", rules) == extract_text_gui.FILTER_MENTION
    assert _action("assets/app.min.js", rules) == extract_text_gui.FILTER_MENTION
    assert _action("page.html", rules) == extract_text_gui.FILTER_EXTRACT


def test_exact_file_name_beats_suffix_rule() -> None:
    rules = [
        (".json", extract_text_gui.FILTER_IGNORE),
        ("package-lock.json", extract_text_gui.FILTER_MENTION),
    ]

    assert _action("package-lock.json", rules) == extract_text_gui.FILTER_MENTION
    assert _action("data.json", rules) == extract_text_gui.FILTER_IGNORE


def test_longest_suffix_wins() -> None:
    rules = [
        (".js", extract_text_gui.FILTER_IGNORE),
        (".min.js", extract_text_gui.FILTER_MENTION),
    ]

    assert _action("app.min.js", rules) == extract_text_gui.FILTER_MENTION
    assert _action("app.js", rules) == extract_text_gui.FILTER_IGNORE


def test_later_duplicate_rule_overrides_earlier_one() -> None:
    rules = [
        (".map", extract_text_gui.FILTER_MENTION),
        (".map", extract_text_gui.FILTER_IGNORE),
    ]

    assert _action("app.js.map", rules) == extract_text_gui.FILTER_IGNORE


def test_binary_extension_defaults_to_mention_only() -> None:
    assert _action("photo.png", []) == extract_text_gui.FILTER_MENTION


def test_explicit_extract_rule_overrides_binary_default(tmp_path: Path) -> None:
    path = tmp_path / "icon.svg"
    path.write_text("<svg><path d='M0 0'/></svg>", encoding="utf-8")
    rules = [(".svg", extract_text_gui.FILTER_EXTRACT)]

    assert _action(str(path), rules) == extract_text_gui.FILTER_EXTRACT
    assert extract_text_gui.read_text_file(str(path), force=True) == (
        "<svg><path d='M0 0'/></svg>"
    )


def test_worker_mentions_and_ignores_filtered_files(tmp_path: Path) -> None:
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])

    input_dir = tmp_path / "page"
    input_dir.mkdir()
    (input_dir / "index.html").write_text("<html>Hola</html>", encoding="utf-8")
    (input_dir / "icon.svg").write_text(
        "<svg><path d='M0 0'/></svg>", encoding="utf-8"
    )
    (input_dir / "app.js.map").write_text('{"version": 3}', encoding="utf-8")
    (input_dir / "app.min.js").write_text("minified()", encoding="utf-8")
    output = tmp_path / "report.txt"

    rules = list(extract_text_gui.DEFAULT_EXTENSION_RULES) + [
        (".map", extract_text_gui.FILTER_IGNORE)
    ]
    worker = extract_text_gui.ExtractionWorker(
        str(input_dir), str(output), [], [], rules
    )
    logs = []
    results = {}
    worker.log_message.connect(logs.append)
    worker.result_ready.connect(
        lambda ok, message: results.update(ok=ok, message=message)
    )
    worker.run()

    report = output.read_text(encoding="utf-8")
    assert results["ok"] is True
    assert "<html>Hola</html>" in report
    assert "icon.svg" in report
    assert "<path d=" not in report
    assert "app.js.map" not in report
    assert "minified()" not in report
    assert any("[ignored by extension filter]" in line for line in logs)
    assert any("[mentioned only]" in line for line in logs)
    assert app is not None
