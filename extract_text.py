#!/usr/bin/env python3
"""
extract_text.py — Extrae el contenido de todos los archivos de texto de un
directorio (por ejemplo, una página web guardada con Ctrl+S en Chrome) y lo
concatena en un único archivo .txt listo para enviar a un agente de IA.

Uso:
    python extract_text.py [DIRECTORIO] [-o ARCHIVO_SALIDA] [-v]

Sin dependencias externas: solo biblioteca estándar de Python 3.
"""

import argparse
import os
import sys

# Extensiones que suelen ser binarias y no vale la pena intentar leer como texto.
EXTENSIONES_BINARIAS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".bmp",
    ".mp4", ".webm", ".mp3", ".wav", ".ogg", ".m4a",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".zip", ".gz", ".br", ".rar", ".7z", ".pdf", ".exe", ".dll", ".so",
}


def es_archivo_texto(ruta_archivo, verbose=False):
    """Devuelve True si el archivo se puede leer como texto UTF-8."""
    extension = os.path.splitext(ruta_archivo)[1].lower()
    if extension in EXTENSIONES_BINARIAS:
        return False
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            f.read()
        return True
    except (UnicodeDecodeError, OSError):
        if verbose:
            print(f"  [omitido, no es texto] {ruta_archivo}", file=sys.stderr)
        return False


def analizar_directorio(directorio, archivo_salida, verbose=False):
    """Recorre el directorio y concatena los archivos de texto en archivo_salida."""
    contador_texto = 0
    contador_binario = 0

    with open(archivo_salida, "w", encoding="utf-8") as salida:
        for ruta_directorio, _subdirectorios, archivos in os.walk(directorio):
            for archivo in archivos:
                ruta_completa = os.path.join(ruta_directorio, archivo)
                if es_archivo_texto(ruta_completa, verbose):
                    try:
                        salida.write(f"\n--- Contenido del archivo de texto: {ruta_completa} ---\n")
                        with open(ruta_completa, "r", encoding="utf-8") as f:
                            salida.write(f.read())
                        salida.write("\n")  # Nueva línea al final del contenido
                        contador_texto += 1
                        if verbose:
                            print(f"  [texto]   {ruta_completa}", file=sys.stderr)
                    except Exception as e:
                        salida.write(f"\n[Error al leer {ruta_completa}: {str(e)}]\n")
                else:
                    # Para archivos binarios, solo listamos el nombre
                    salida.write(f"\n--- Archivo no de texto: {ruta_completa} ---\n")
                    contador_binario += 1

    return contador_texto, contador_binario


def main():
    parser = argparse.ArgumentParser(
        description="Extrae el contenido de los archivos de texto de un directorio "
                    "a un único archivo .txt (útil para enviar páginas web guardadas a agentes de IA)."
    )
    parser.add_argument(
        "directorio",
        nargs="?",
        default="Promts",
        help="Directorio que contiene los archivos a analizar (por defecto: %(default)s)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Archivo de salida (por defecto: <directorio>_src.txt)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Muestra en consola cada archivo procesado",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.directorio):
        print(f"Error: no existe el directorio '{args.directorio}'", file=sys.stderr)
        sys.exit(1)

    archivo_salida = args.output or f"{os.path.basename(os.path.normpath(args.directorio))}_src.txt"

    texto, binarios = analizar_directorio(args.directorio, archivo_salida, args.verbose)

    print(f"Análisis completado: {texto} archivos de texto, {binarios} binarios/omitidos.")
    print(f"El informe se ha guardado en {archivo_salida}.")


if __name__ == "__main__":
    main()
