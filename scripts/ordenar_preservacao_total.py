#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from dataclasses import dataclass
from typing import List

ROMAN = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
    "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12
}

@dataclass
class Block:
    raw: str
    part: int
    chapter: int
    suffix: int
    sub: int
    order: int


def roman_to_int(r: str) -> int:
    return ROMAN.get(r.upper(), 10_000)


def parse_header(block_text: str):
    part = chapter = suffix = sub = 10_000
    lines = block_text.splitlines()

    for ln in lines[:20]:
        if "PARTE" in ln:
            m = re.search(r"PARTE\s+([IVXLCDM]+)", ln)
            if m:
                part = roman_to_int(m.group(1))

        if "Capítulo" in ln:
            m = re.search(r"Cap[ií]tulo\s+(\d+)", ln)
            if m:
                chapter = int(m.group(1))

        m = re.match(r"\s*(\d+)(?:-([A-Z]))?\.(\d+)", ln)
        if m:
            sub = int(m.group(3))
            suffix = ord(m.group(2)) - ord("A") + 1 if m.group(2) else 0

    return part, chapter, suffix, sub


def cortar_blocos_exatos(text: str) -> List[str]:
    """
    Corta o ficheiro em blocos usando POSIÇÕES EXACTAS.
    O delimitador '---' é incluído no bloco seguinte, tal como no original.
    """
    indices = [m.start() for m in re.finditer(r"(?m)^---", text)]

    if not indices:
        return [text]

    blocks = []

    for i, start in enumerate(indices):
        end = indices[i + 1] if i + 1 < len(indices) else len(text)
        blocks.append(text[start:end])

    return blocks


def main(inp: str, outp: str):
    with open(inp, "r", encoding="utf-8") as f:
        text = f.read()

    blocks_raw = cortar_blocos_exatos(text)

    blocks: List[Block] = []

    for i, raw in enumerate(blocks_raw):
        part, chap, suf, sub = parse_header(raw)
        blocks.append(Block(
            raw=raw,
            part=part,
            chapter=chap,
            suffix=suf,
            sub=sub,
            order=i
        ))

    blocks.sort(key=lambda b: (
        b.part,
        b.chapter,
        b.suffix,
        b.sub,
        b.order
    ))

    with open(outp, "w", encoding="utf-8") as f:
        for b in blocks:
            f.write(b.raw)

    print(f"OK — {len(blocks)} blocos reordenados com preservação TOTAL.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Uso: python ordenar_preservacao_total.py entrada.md saida.md")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
