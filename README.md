> **🇪🇸 Spanish version available:** [README_ES.md](README_ES.md) — Versión en español para público de habla hispana.

# webpage-text-extractor

**Extract all text from a folder — like a web page saved with `Ctrl + S` in Chrome — and concatenate it into a single `.txt` file ready to send to an AI agent.**

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![No dependencies](https://img.shields.io/badge/dependencies-none-orange.svg)](#requirements)

---

## Why this script exists?

When you ask an AI agent (ChatGPT, Claude, a local assistant, etc.) to analyze a web page, the most practical approach is often not to pass the URL but **the actual content of the page**: its HTML, styles, and structure.

The workflow is:

1. Open the page in Google Chrome.
2. Press `Ctrl + S` (on macOS `⌘ + S`) and choose **"Webpage, Complete"**.
3. Chrome creates a folder with the page's HTML **and** all its resources (CSS, JS, images).
4. Run this script on that folder.
5. Get **a single `.txt` file** with the readable content of all text files, clearly separated by headers.

That `.txt` file is much easier to handle: you attach it to your AI agent, paste it in a chat, or process it as you wish, without having to send dozens of loose files.

## Features

- **Recursive**: traverses all subdirectories with `os.walk`.
- **Text detection**: attempts to read each file as UTF-8; binary files (images, fonts, videos) are listed by name without cluttering output.
- **Clear separators**: each text file is preceded by a header with its full path:
  ```
  --- Text file content: Blog-example/page.html ---
  ```
- **Zero dependencies**: only Python standard library. No `pip install` needed.
- **Two versions + a GUI**:
  - `extract_text.py` — version with command-line arguments (recommended).
  - `extract_text_simple.py` — original minimal version, edit two variables and run.
  - `extract_text_gui.py` — graphical interface with PyQt6 (see [Graphical user interface](#graphical-user-interface-pyqt6)).

## Requirements

- Python **3.6 or higher** (works on Windows, macOS, and Linux).
- No external dependencies.

Check your version with:

```bash
python3 --version
```

## Installation

```bash
git clone https://github.com/YOUR_USER/webpage-text-extractor.git
cd webpage-text-extractor
```

Nothing else to install.

## Graphical user interface (PyQt6)

The project also includes a multi-platform GUI (Windows, Linux and macOS): [`extract_text_gui.py`](extract_text_gui.py).

### Requirements

- Python **3.8 or higher**.
- PyQt6:

  ```bash
  pip install PyQt6
  ```

- On **Linux**, install Qt's translations so that the standard dialogs (*Open file / Save file*, etc.) automatically appear in your system language:

  ```bash
  sudo apt install qt6-translations-l10n
  ```

### Run the GUI

```bash
python extract_text_gui.py
```

### Features

- **Extraction tab**: selectors for the input folder, the output folder and the output file, with a progress bar and an execution log.
- **Exclusions tab**: 18 selectors to exclude directories or files from the extraction (each one can point to a directory or to a file). **Add multiple folders…** selects several folders at once and fills the selectors automatically, and ticking **Show hidden files and folders** reveals entries such as `.git` that the system hides by default (they are extracted too, so you will usually want to exclude them).
- **Help → About**: developer information dialog — program icon on the left, text on the right — with a clickable email link (opens your default email client) and website link (opens your default browser).
- **Light and dark themes**: _View → Theme_.
- **Multiplatform**: runs on Windows, Linux and macOS; the `Fusion` style guarantees the same look and working themes everywhere.
- **Internationalization**: the interface is written in English and every string uses `tr()`, ready to be translated with [Qt Linguist](https://doc.qt.io/qt-6/linguist-index.html).

The program icon is [`icons/webpage-text-extractor.svg`](icons/webpage-text-extractor.svg), a plain SVG (no filters or raster effects) that you can edit with [Inkscape](https://inkscape.org/).

### Translating the interface

```bash
pylupdate6 extract_text_gui.py -ts translations/webpage-text-extractor.ts   # extract the strings
lrelease translations/webpage-text-extractor.ts                            # compile the .qm
```

Place the resulting `webpage-text-extractor_<locale>.qm` file (for example `webpage-text-extractor_es.qm`) in the `translations/` folder and the program will load it automatically at startup.

## Usage

### Command-line arguments version (recommended)

```bash
python extract_text.py <DIRECTORY> [-o OUTPUT_FILE] [-v]
```

| Argument | Description | Default |
|---|---|---|
| `directory` | Folder containing files to analyze | `Promts` |
| `-o`, `--output` | Output file name | `<directory>_src.txt` |
| `-v`, `--verbose` | Show each processed file in console | disabled |

### Simple version

Edit the two variables at the end of `extract_text_simple.py`:

```python
directory_to_analyze = "Promts"
output_file = "Promts_src.txt"
```

And run:

```bash
python extract_text_simple.py
```

## Usage Examples

### Example 1 — Analyze a web page saved with `Ctrl + S`

You saved `https://www.digitalocean.com/resources/articles/ai-blogs` with `Ctrl + S`. Chrome created this:

```
Downloads/
└── 12 AI Blogs for Keeping Up With AI Trends in 2026 _ DigitalOcean.html
└── 12 AI Blogs for Keeping Up With AI Trends in 2026 _ DigitalOcean_files/
    ├── 6994b812b10824a2.css
    ├── main-app-9d77c18dd5f52d72.js
    ├── images(6)
    └── ...
```

Run:

```bash
python extract_text.py "Downloads/12 AI Blogs for Keeping Up With AI Trends in 2026 _ DigitalOcean" -o blog_ai.txt -v
```

Console output:

```
  [text]   Downloads/.../12 AI Blogs ....html
  [text]   Downloads/..._files/6994b812b10824a2.css
  [skipped, not text] Downloads/..._files/images(6)
  ...
Analysis completed: 22 text files, 3 binary/skipped.
Report saved to blog_ai.txt.
```

And `blog_ai.txt` will have this format:

```
--- Text file content: Downloads/.../12 AI Blogs ....html ---
<!DOCTYPE html>
<html lang="en" ...>
...

--- Text file content: Downloads/..._files/6994b812b10824a2.css ---
...

--- Non-text file: Downloads/..._files/images(6) ---
```

Now you attach **a single file** to your AI agent and ask what you need:

> "This .txt contains the complete page of a tech blog (HTML + CSS). Create a prompt to build a page with this same style."

### Example 2 — Use default folder name

If your folder is named `Promts` (like in the original script), no arguments needed:

```bash
python extract_text.py
```

Generates `Promts_src.txt`.

### Example 3 — Extract text from local documentation

You have a folder with documentation in Markdown, HTML, or source code and want to summarize it with AI:

```bash
python extract_text.py ./my-project/docs -o documentation.txt
python extract_text.py ./my-project/src  -o source_code.txt -v
```

### Example 4 — Automate full workflow for multiple pages

```bash
#!/bin/bash
for folder in saved_pages/*/; do
  name=$(basename "$folder")
  python extract_text.py "$folder" -o "outputs/${name}_src.txt"
done
```

## Which files are recognized as text?

The script attempts to read **everything** as UTF-8. Additionally, it directly skips typically binary extensions to save time:

```
.png .jpg .jpeg .gif .webp .ico .svg .bmp
.mp4 .webm .mp3 .wav .ogg .m4a
.woff .woff2 .ttf .otf .eot
.zip .gz .br .rar .7z .pdf .exe .dll .so
```

Any other file that cannot be decoded as UTF-8 is marked as `--- Non-text file: ... ---` in the output, only with its name.

## Tips

- **`.js` and `.css` files are also extracted**: this is intentional. To replicate a page's design (colors, typography, layout), CSS is exactly what your AI agent needs.
- **Large outputs**: a complete site saved with `Ctrl + S` can generate several MB of text. If your agent has context limits, process the main `.html` first or split the output.
- **Encoding**: everything is processed as UTF-8. If you have files in another encoding (e.g., Latin-1), convert them first or modify `open(..., encoding="utf-8")`.
- **File order**: `os.walk` traverses in filesystem order. If you need a specific order, sort the `files` list inside the script.

## Limitations

- Does not interpret HTML: extracts the **source code as-is**, not the rendered visible text. This is an advantage for analysis and design replication tasks, but if you only want visible text, you'll need something like `BeautifulSoup` or `html2text`.
- Very large files are loaded entirely into memory (normal for this use case).

## Contributing

Contributions are welcome:

1. Fork the repository.
2. Create a branch for your improvement: `git checkout -b my-improvement`.
3. Commit: `git commit -m "Description of improvement"`.
4. Push to the branch: `git push origin my-improvement`.
5. Open a Pull Request.

Improvement ideas: extension filters, visible HTML text extraction only, multiple encoding support, per-file output mode.

## License

This project is under the GPL 3 License — see the [LICENSE](LICENSE) file for details.

---

**If you find this useful, give the repository a star. Thanks!**