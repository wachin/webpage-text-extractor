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
import codecs
import locale
import os
import sys

# Extensiones que suelen ser binarias y no vale la pena intentar leer como texto.
EXTENSIONES_BINARIAS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".bmp",
    ".mp4", ".webm", ".mp3", ".wav", ".ogg", ".m4a",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".zip", ".gz", ".br", ".rar", ".7z", ".pdf", ".exe", ".dll", ".so",
}

# Caracteres de control que sí aparecen en archivos de texto normales.
CONTROLES_PERMITIDOS = "\t\n\r\f\b"


def _parece_texto(texto):
    """Descarta contenido binario que haya podido decodificarse por error."""
    if "\x00" in texto:
        return False
    muestra = texto[:8192]
    if not muestra:
        return True
    controles = sum(
        1
        for caracter in muestra
        if (ord(caracter) < 32 or ord(caracter) == 127)
        and caracter not in CONTROLES_PERMITIDOS
    )
    return controles / len(muestra) <= 0.02


def _decodificar_texto(datos):
    """Devuelve el texto de `datos` o None si parecen datos binarios.

    Se respeta el BOM de UTF-8, UTF-16 y UTF-32. Sin BOM se intenta UTF-8,
    la codificación preferida del sistema (ANSI en Windows) y cp1252, de
    modo que los archivos guardados con el Bloc de notas no se pierdan.
    """
    if not datos:
        return ""

    if datos.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        candidatas = ("utf-32",)
    elif datos.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        candidatas = ("utf-16",)
    elif datos.startswith(codecs.BOM_UTF8):
        candidatas = ("utf-8-sig",)
    else:
        # Un NUL en un archivo sin BOM es una señal fiable de contenido binario.
        if b"\x00" in datos[:8192]:
            return None
        candidatas = []
        preferida = locale.getpreferredencoding(False)
        for codificacion in ("utf-8", preferida, "cp1252"):
            if codificacion and codificacion.lower() not in (
                candidata.lower() for candidata in candidatas
            ):
                candidatas.append(codificacion)

    for codificacion in candidatas:
        try:
            texto = datos.decode(codificacion)
        except (UnicodeDecodeError, LookupError):
            continue
        return texto if _parece_texto(texto) else None
    return None


def leer_archivo_texto(ruta_archivo):
    """Lee el archivo una sola vez y devuelve su texto, o None si es binario."""
    extension = os.path.splitext(ruta_archivo)[1].lower()
    if extension in EXTENSIONES_BINARIAS:
        return None
    try:
        with open(ruta_archivo, "rb") as f:
            datos = f.read()
    except OSError:
        return None
    return _decodificar_texto(datos)


def es_archivo_texto(ruta_archivo, verbose=False):
    """Devuelve True si el archivo se puede leer como texto."""
    if leer_archivo_texto(ruta_archivo) is not None:
        return True
    if verbose:
        print(f"  [omitido, no es texto] {ruta_archivo}", file=sys.stderr)
    return False


def esta_dentro_de(ruta, directorio):
    """Devuelve True si `ruta` está dentro de `directorio`."""
    try:
        ruta_normal = os.path.normcase(os.path.realpath(os.path.abspath(ruta)))
        directorio_normal = os.path.normcase(
            os.path.realpath(os.path.abspath(directorio))
        )
        return os.path.commonpath([ruta_normal, directorio_normal]) == directorio_normal
    except ValueError:  # Rutas en unidades distintas (por ejemplo C: y D:).
        return False


def analizar_directorio(directorio, archivo_salida, verbose=False):
    """Recorre el directorio y concatena los archivos de texto en archivo_salida."""
    contador_texto = 0
    contador_binario = 0

    with open(archivo_salida, "w", encoding="utf-8") as salida:
        for ruta_directorio, _subdirectorios, archivos in os.walk(directorio):
            for archivo in archivos:
                ruta_completa = os.path.join(ruta_directorio, archivo)
                contenido = leer_archivo_texto(ruta_completa)
                if contenido is not None:
                    try:
                        salida.write(f"\n--- Contenido del archivo de texto: {ruta_completa} ---\n")
                        salida.write(contenido)
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
                    if verbose:
                        print(f"  [omitido, no es texto] {ruta_completa}", file=sys.stderr)

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

    if esta_dentro_de(archivo_salida, args.directorio):
        print(
            "Error: el archivo de salida no puede estar dentro del "
            f"directorio a analizar: '{archivo_salida}'",
            file=sys.stderr,
        )
        print(
            "Elija una ubicación fuera de esa carpeta para no sobrescribir "
            "los archivos que se van a analizar.",
            file=sys.stderr,
        )
        sys.exit(1)

    texto, binarios = analizar_directorio(args.directorio, archivo_salida, args.verbose)

    print(f"Análisis completado: {texto} archivos de texto, {binarios} binarios/omitidos.")
    print(f"El informe se ha guardado en {archivo_salida}.")


if __name__ == "__main__":
    main()
