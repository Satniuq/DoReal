#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merge_transicao_para_proxima_fase.py

Corre na pasta:
    16_validacao_integral\\08_descida_expositiva_controlada\\90_transicao_para_proxima_fase

Objetivo:
- fazer merge dos ficheiros .md existentes na própria pasta;
- ignorar ficheiros já gerados com prefixo MERGED__;
- manter um formato semelhante ao script-base de merge das faixas.

O script:
1. lê os ficheiros .md da pasta atual (sem subpastas);
2. ordena-os por ordem natural;
3. remove duplicação do primeiro título interno quando coincide com o nome do ficheiro;
4. desce um nível os headings internos;
5. gera um único ficheiro MERGED na própria pasta.

Uso:
    python merge_transicao_para_proxima_fase.py
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parent
MERGED_PREFIX = "MERGED__"
TRANSICAO_RE = re.compile(r"^(\d+)_para_(\d+)_", re.IGNORECASE)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def natural_key(text: str):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", text)]


def normalize_for_compare(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"\.md$", "", text)
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def md_files_in_root(root: Path) -> List[Path]:
    return sorted(
        [
            p for p in root.iterdir()
            if p.is_file()
            and p.suffix.lower() == ".md"
            and not p.name.startswith(MERGED_PREFIX)
        ],
        key=lambda p: natural_key(p.name)
    )


def strip_first_title_if_matches_filename(text: str, filename_stem: str) -> str:
    """
    Remove o primeiro heading do ficheiro se ele for apenas o título principal
    duplicado do nome do ficheiro.
    """
    lines = text.splitlines()
    i = 0

    while i < len(lines) and not lines[i].strip():
        i += 1

    if i >= len(lines):
        return text

    m = re.match(r"^(#{1,6})\s+(.*)$", lines[i].strip())
    if not m:
        return text

    heading_title = m.group(2).strip()

    if normalize_for_compare(heading_title) == normalize_for_compare(filename_stem):
        return "\n".join(lines[:i] + lines[i + 1:]).lstrip("\n")

    return text


def demote_headings(text: str, levels: int = 1) -> str:
    out_lines = []
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            hashes, title = m.groups()
            new_level = min(len(hashes) + levels, 6)
            out_lines.append("#" * new_level + " " + title)
        else:
            out_lines.append(line)
    return "\n".join(out_lines).strip()


def build_output_name(files: List[Path], root: Path) -> str:
    folder_name = root.name
    numeros = []

    for path in files:
        m = TRANSICAO_RE.match(path.stem)
        if m:
            numeros.append(m.group(1))

    if numeros:
        sufixo = "_".join(numeros)
        return f"{MERGED_PREFIX}{folder_name}_{sufixo}.md"

    return f"{MERGED_PREFIX}{folder_name}.md"


def make_anchor(text: str) -> str:
    anchor = text.lower()
    anchor = unicodedata.normalize("NFKD", anchor)
    anchor = "".join(ch for ch in anchor if not unicodedata.combining(ch))
    anchor = re.sub(r"[^a-z0-9_]+", "-", anchor)
    anchor = anchor.strip("-")
    return anchor


def render_file_block(path: Path, base_dir: Path, heading_level: int = 2) -> str:
    rel = path.relative_to(base_dir)
    title = path.stem
    text = path.read_text(encoding="utf-8")

    text = strip_first_title_if_matches_filename(text, path.stem)
    text = demote_headings(text, levels=1)

    return (
        f'{"#" * heading_level} {title}\n\n'
        f"**Ficheiro de origem:** `{rel}`\n\n"
        f"{text}\n"
    )


def render_merged(files: List[Path], root: Path, output_name: str) -> str:
    lines = []
    lines.append(f"# MERGED — {root.name}")
    lines.append("")
    lines.append(f"- Gerado em: `{now_str()}`")
    lines.append(f"- Pasta: `{root}`")
    lines.append(f"- Ficheiros incluídos: `{len(files)}`")
    lines.append(f"- Ficheiro gerado: `{output_name}`")
    lines.append("")

    lines.append("## Índice interno")
    lines.append("")
    for p in files:
        rel = p.relative_to(root)
        lines.append(f"- [{p.stem}](#{make_anchor(p.stem)}) — `{rel}`")
    lines.append("")

    lines.append("## Estatuto desta agregação")
    lines.append("")
    lines.append("- Esta agregação substitui a leitura dispersa dos ficheiros desta pasta por um único ficheiro local.")
    lines.append("- Só são incluídos ficheiros `.md` existentes na própria pasta.")
    lines.append(f"- Ficheiros já gerados com prefixo `{MERGED_PREFIX}` são ignorados para evitar recursão no merge.")
    lines.append("")

    for p in files:
        lines.append(render_file_block(p, root, heading_level=2).strip())
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    files = md_files_in_root(ROOT)

    if not files:
        raise SystemExit("Nenhum ficheiro .md encontrado na pasta atual.")

    output_name = build_output_name(files, ROOT)
    output_path = ROOT / output_name
    content = render_merged(files, ROOT, output_name)
    output_path.write_text(content, encoding="utf-8")

    print("OK")
    print(f"Ficheiros processados: {len(files)}")
    for p in files:
        print(f" - {p.name}")
    print(f"Merged: {output_path.name}")


if __name__ == "__main__":
    main()
