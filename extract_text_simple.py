#!/usr/bin/env python3
"""
extract_text_simple.py — Versión original y mínima del script.

Versión simple, sin argumentos de línea de comandos: cambia las variables
al final del archivo y ejecuta con `python extract_text_simple.py`.
"""

import os


def es_archivo_texto(ruta_archivo):
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            f.read()
        return True
    except:
        return False


def analizar_directorio(directorio, archivo_salida):
    with open(archivo_salida, 'w', encoding='utf-8') as salida:
        for ruta_directorio, subdirectorios, archivos in os.walk(directorio):
            for archivo in archivos:
                ruta_completa = os.path.join(ruta_directorio, archivo)
                if es_archivo_texto(ruta_completa):
                    try:
                        salida.write(f"\n--- Contenido del archivo de texto: {ruta_completa} ---\n")
                        with open(ruta_completa, 'r', encoding='utf-8') as f:
                            salida.write(f.read())
                        salida.write("\n")  # Agrega una nueva línea al final del contenido
                    except Exception as e:
                        salida.write(f"\n[Error al leer {ruta_completa}: {str(e)}]\n")
                else:
                    # Para archivos no de texto, solo listamos el nombre
                    salida.write(f"\n--- Archivo no de texto: {ruta_completa} ---\n")


# Define el directorio a analizar y el archivo de salida
directorio_a_analizar = "Promts"
archivo_de_salida = "Promts_src.txt"

# Ejecuta el análisis
analizar_directorio(directorio_a_analizar, archivo_de_salida)

print(f"Análisis completado. El informe se ha guardado en {archivo_de_salida}.")
