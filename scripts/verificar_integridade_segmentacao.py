import json
import re
from pathlib import Path
from collections import Counter


def normalizar(texto: str) -> list[str]:
    """
    Normaliza o texto apenas para efeitos de comparação:
    - lowercase
    - separação por palavras
    NÃO remove palavras
    NÃO remove números
    NÃO remove acentos
    """
    texto = texto.lower()
    return re.findall(r"\b\w+\b", texto, flags=re.UNICODE)


def carregar_texto_extraido(caminho: Path) -> list[str]:
    data = json.loads(caminho.read_text(encoding="utf-8"))
    palavras = []
    for frag in data.values():
        palavras.extend(normalizar(frag["text"]))
    return palavras


def carregar_texto_segmentado(caminho: Path) -> list[str]:
    data = json.loads(caminho.read_text(encoding="utf-8"))
    palavras = []
    for seg in data.values():
        palavras.extend(normalizar(seg["texto"]))
    return palavras


def comparar(extraido: list[str], segmentado: list[str]):
    c_ext = Counter(extraido)
    c_seg = Counter(segmentado)

    faltam = c_ext - c_seg
    sobram = c_seg - c_ext

    if not faltam and not sobram:
        print("✔ INTEGRIDADE TOTAL — nenhuma palavra perdida ou adicionada")
        print(f"Total extraído : {sum(c_ext.values())}")
        print(f"Total segmentado: {sum(c_seg.values())}")
        return

    print("✘ DIFERENÇAS DETETADAS\n")

    if faltam:
        print("Palavras em falta (exemplos):")
        for palavra, n in faltam.most_common(20):
            print(f"  - {palavra}: {n}")

    if sobram:
        print("\nPalavras a mais (exemplos):")
        for palavra, n in sobram.most_common(20):
            print(f"  + {palavra}: {n}")

    print("\nResumo:")
    print(f"Total extraído : {sum(c_ext.values())}")
    print(f"Total segmentado: {sum(c_seg.values())}")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent

    caminho_extraido = base_dir / "01_extraido" / "fragmentos_extraidos.json"
    caminho_segmentado = base_dir / "02_segmentado" / "fragmentos_segmentados.json"

    extraido = carregar_texto_extraido(caminho_extraido)
    segmentado = carregar_texto_segmentado(caminho_segmentado)

    comparar(extraido, segmentado)
