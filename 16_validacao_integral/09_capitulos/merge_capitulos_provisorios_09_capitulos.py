#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merge_capitulos_provisorios_09_capitulos.py

Gera merges rerunáveis para tudo o que estiver dentro de:
- 02_capitulos_provisorios/<cada_subpasta_local>

Saídas:
- um MERGED__<nome_da_pasta>.md dentro de cada pasta local de capítulo
- um ficheiro mestre em 02_capitulos_provisorios/

Regras:
- só agrega ficheiros .md
- ignora ficheiros cujo nome começa por "MERGED__"
- pode ser corrido várias vezes; reescreve os outputs
- usa ordem editorial:
    1) PROLOGO_*
    2) CAP_01, CAP_02, CAP_03...
    3) L1, L2...
    4) R1, R2...
    5) resto
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path
from typing import Iterable, List, Tuple

CHAPTERS_ROOT_NAME = "02_capitulos_provisorios"
MASTER_OUTPUT_NAME = "MERGED__02_capitulos_provisorios.md"
INCLUDE_EXTENSIONS = {".md"}


# ---------------------------------------------------------------------------
# utilitários gerais
# ---------------------------------------------------------------------------

def natural_key(value: str):
    parts = re.split(r"(\d+)", value.lower())
    key = []
    for part in parts:
        key.append(int(part) if part.isdigit() else part)
    return key


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "secao"


def now_str() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").rstrip() + "\n"


# ---------------------------------------------------------------------------
# ordenação editorial das pastas locais
# ---------------------------------------------------------------------------

def chapter_folder_sort_key(folder: Path):
    """
    Ordem editorial:
    0) PROLOGO_*
    1) CAP_XX_*
    2) L1_*, L2_* ...
    3) R1_*, R2_* ...
    4) resto
    """
    name = folder.name
    upper = name.upper()

    if upper.startswith("PROLOGO"):
        return (0, 0, natural_key(name))

    m_cap = re.match(r"^CAP_(\d+)(?:_|$)", upper)
    if m_cap:
        return (1, int(m_cap.group(1)), natural_key(name))

    m_l = re.match(r"^L(\d+)(?:_|$)", upper)
    if m_l:
        return (2, int(m_l.group(1)), natural_key(name))

    m_r = re.match(r"^R(\d+)(?:_|$)", upper)
    if m_r:
        return (3, int(m_r.group(1)), natural_key(name))

    return (4, 999999, natural_key(name))


# ---------------------------------------------------------------------------
# ordenação dos ficheiros dentro de cada pasta local
# ---------------------------------------------------------------------------

def file_name_sort_key(name: str):
    """
    Dá prioridade a prefixos do tipo:
    00_, 01_, 02_, ...
    e depois usa natural sort.
    """
    stem = Path(name).stem
    m = re.match(r"^(\d+)_", stem)
    if m:
        return (0, int(m.group(1)), natural_key(stem))
    return (1, 999999, natural_key(stem))


def relative_path_sort_key(rel_path: Path):
    """
    Ordena um caminho relativo respeitando ordem natural em cada componente,
    dando prioridade a prefixos numéricos do tipo 00_, 01_, ...
    """
    parts = []
    for part in rel_path.parts[:-1]:
        parts.append(file_name_sort_key(part))
    parts.append(file_name_sort_key(rel_path.name))
    return parts


# ---------------------------------------------------------------------------
# recolha de ficheiros
# ---------------------------------------------------------------------------

def is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def collect_markdown_files(folder: Path) -> List[Path]:
    files: List[Path] = []

    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in INCLUDE_EXTENSIONS:
            continue
        if path.name.startswith("MERGED__"):
            continue
        if is_hidden_path(path.relative_to(folder)):
            continue
        files.append(path)

    return sorted(files, key=lambda p: relative_path_sort_key(p.relative_to(folder)))


# ---------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------

def build_local_merge(chapter_folder: Path, files: List[Path], base_dir: Path) -> str:
    output_name = f"MERGED__{chapter_folder.name}.md"
    folder_rel = chapter_folder.relative_to(base_dir).as_posix()

    lines: List[str] = []
    lines.append(f"# MERGED — {chapter_folder.name}")
    lines.append("")
    lines.append(f"- Gerado em: `{now_str()}`")
    lines.append(f"- Pasta local: `{folder_rel}`")
    lines.append(f"- Ficheiros incluídos: `{len(files)}`")
    lines.append(f"- Ficheiro gerado: `{(chapter_folder / output_name).relative_to(base_dir).as_posix()}`")
    lines.append("")
    lines.append("## Índice interno")
    lines.append("")

    if not files:
        lines.append("- *(sem ficheiros elegíveis para merge)*")
    else:
        for path in files:
            rel = path.relative_to(base_dir).as_posix()
            local_rel = path.relative_to(chapter_folder).as_posix()
            anchor = slugify(f"{chapter_folder.name}-{local_rel}")
            lines.append(f"- [{path.stem}](#{anchor}) — `{rel}`")

    lines.append("")
    lines.append("## Estatuto desta agregação")
    lines.append("")
    lines.append("- Esta agregação reúne tudo o que já existe nesta pasta local de capítulo.")
    lines.append("- O merge é rerunável e refeito integralmente em cada execução.")
    lines.append("- Ficheiros `MERGED__*.md` são ignorados para evitar recursão.")
    lines.append("")

    for path in files:
        rel = path.relative_to(base_dir).as_posix()
        local_rel = path.relative_to(chapter_folder).as_posix()
        anchor = slugify(f"{chapter_folder.name}-{local_rel}")

        lines.append(f'<a id="{anchor}"></a>')
        lines.append(f"## {path.stem}")
        lines.append("")
        lines.append(f"**Ficheiro de origem:** `{rel}`")
        lines.append("")
        lines.append(read_text(path))

    return "\n".join(lines).rstrip() + "\n"


def build_master_merge(
    chapters_root: Path,
    chapter_groups: List[Tuple[str, Path, List[Path]]],
) -> str:
    lines: List[str] = []
    lines.append("# MERGED — 02_capitulos_provisorios")
    lines.append("")
    lines.append(f"- Gerado em: `{now_str()}`")
    lines.append(f"- Pasta: `{chapters_root}`")
    lines.append(f"- Pastas locais incluídas: `{len(chapter_groups)}`")
    lines.append(f"- Ficheiro gerado: `{chapters_root / MASTER_OUTPUT_NAME}`")
    lines.append("")
    lines.append("## Índice das pastas locais")
    lines.append("")

    if not chapter_groups:
        lines.append("- *(sem pastas locais com ficheiros elegíveis)*")
    else:
        for name, folder, files in chapter_groups:
            anchor = slugify(f"capitulo-{name}")
            merged_name = f"MERGED__{folder.name}.md"
            rel_merged = (folder / merged_name).relative_to(chapters_root).as_posix()
            lines.append(
                f"- [{name}](#{anchor}) — `{len(files)}` ficheiro(s) — `{rel_merged}`"
            )

    lines.append("")
    lines.append("## Estatuto desta agregação")
    lines.append("")
    lines.append("- Este merge mestre reúne as pastas locais de 02_capitulos_provisorios.")
    lines.append("- Mantém cada pasta separada e indexada, para leitura e auditoria locais.")
    lines.append("- É rerunável e ignora automaticamente merges antigos.")
    lines.append("")

    for name, folder, files in chapter_groups:
        group_anchor = slugify(f"capitulo-{name}")
        lines.append(f'<a id="{group_anchor}"></a>')
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"- Pasta: `{folder.relative_to(chapters_root).as_posix()}`")
        lines.append(f"- Ficheiros incluídos: `{len(files)}`")
        lines.append("")
        lines.append("### Índice interno da pasta")
        lines.append("")

        for path in files:
            anchor = slugify(f"{name}-{path.relative_to(folder).as_posix()}")
            rel = path.relative_to(chapters_root).as_posix()
            lines.append(f"- [{path.stem}](#{anchor}) — `{rel}`")

        lines.append("")

        for path in files:
            anchor = slugify(f"{name}-{path.relative_to(folder).as_posix()}")
            rel = path.relative_to(chapters_root).as_posix()
            lines.append(f'<a id="{anchor}"></a>')
            lines.append(f"### {path.stem}")
            lines.append("")
            lines.append(f"**Ficheiro de origem:** `{rel}`")
            lines.append("")
            lines.append(read_text(path))

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge rerunável das pastas locais em 02_capitulos_provisorios."
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Pasta base 09_capitulos. Por omissão usa a pasta do script.",
    )
    args = parser.parse_args()

    base_dir = args.base_dir.resolve()
    chapters_root = base_dir / CHAPTERS_ROOT_NAME
    chapters_root.mkdir(parents=True, exist_ok=True)

    chapter_folders = [p for p in chapters_root.iterdir() if p.is_dir()]
    chapter_folders = sorted(chapter_folders, key=chapter_folder_sort_key)

    chapter_groups: List[Tuple[str, Path, List[Path]]] = []

    for folder in chapter_folders:
        files = collect_markdown_files(folder)

        if not files:
            print(f"[SKIP] {folder.relative_to(base_dir).as_posix()} (sem ficheiros .md elegíveis)")
            continue

        chapter_groups.append((folder.name, folder, files))

        local_output = folder / f"MERGED__{folder.name}.md"
        local_output.write_text(
            build_local_merge(folder, files, base_dir),
            encoding="utf-8",
        )
        print(f"[OK] {local_output.relative_to(base_dir).as_posix()} ({len(files)} ficheiro(s))")

    master_output = chapters_root / MASTER_OUTPUT_NAME
    master_output.write_text(
        build_master_merge(chapters_root, chapter_groups),
        encoding="utf-8",
    )
    print(f"[OK] {master_output.relative_to(base_dir).as_posix()} (merge mestre)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())