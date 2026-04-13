#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merge_camadas_09_capitulos.py

Gera merges rerunáveis para as camadas estruturais de 09_capitulos:
- 01_arquitetura_total
- 03_mapeamento_fragmentario
- 05_revisoes_macro
- 90_decisoes_de_transicao

Saídas:
- um MERGED__<pasta>.md dentro de cada uma das pastas acima
- um ficheiro mestre na raiz de 09_capitulos

Regras:
- só agrega ficheiros .md
- ignora ficheiros cujo nome começa por "MERGED__"
- pode ser corrido várias vezes; reescreve os outputs
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path
from typing import List, Tuple

TARGET_DIRS = [
    "01_arquitetura_total",
    "03_mapeamento_fragmentario",
    "05_revisoes_macro",
    "90_decisoes_de_transicao",
]
MASTER_OUTPUT_NAME = "MERGED__09_capitulos__CAMADAS_ESTRUTURAIS.md"
INCLUDE_EXTENSIONS = {".md"}


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


def collect_markdown_files(folder: Path) -> List[Path]:
    files = []
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in INCLUDE_EXTENSIONS:
            continue
        if path.name.startswith("MERGED__"):
            continue
        files.append(path)
    return sorted(files, key=lambda p: natural_key(str(p.relative_to(folder))))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").rstrip() + "\n"


def build_local_merge(folder: Path, files: List[Path], project_root: Path) -> str:
    output_name = f"MERGED__{folder.name}.md"
    lines: List[str] = []
    lines.append(f"# MERGED — {folder.name}")
    lines.append("")
    lines.append(f"- Gerado em: `{now_str()}`")
    lines.append(f"- Pasta: `{folder}`")
    lines.append(f"- Ficheiros incluídos: `{len(files)}`")
    lines.append(f"- Ficheiro gerado: `{folder / output_name}`")
    lines.append("")
    lines.append("## Índice interno")
    lines.append("")
    if not files:
        lines.append("- *(sem ficheiros elegíveis para merge)*")
    else:
        for path in files:
            rel = path.relative_to(project_root).as_posix()
            anchor = slugify(f"{folder.name}-{path.relative_to(folder).as_posix()}")
            lines.append(f"- [{path.stem}](#{anchor}) — `{rel}`")
    lines.append("")
    lines.append("## Estatuto desta agregação")
    lines.append("")
    lines.append("- Esta agregação substitui a leitura dispersa desta camada por um único ficheiro local.")
    lines.append("- O merge é rerunável: ao correr novamente o script, o ficheiro é refeito e atualizado.")
    lines.append("- Ficheiros `MERGED__*.md` são ignorados para evitar recursão.")
    lines.append("")
    if files:
        for path in files:
            rel = path.relative_to(project_root).as_posix()
            anchor = slugify(f"{folder.name}-{path.relative_to(folder).as_posix()}")
            lines.append(f'<a id="{anchor}"></a>')
            lines.append(f"## {path.stem}")
            lines.append("")
            lines.append(f"**Ficheiro de origem:** `{rel}`")
            lines.append("")
            lines.append(read_text(path))
    return "\n".join(lines).rstrip() + "\n"


def build_master_merge(base_dir: Path, grouped_files: List[Tuple[str, Path, List[Path]]]) -> str:
    lines: List[str] = []
    lines.append("# MERGED — 09_capitulos / camadas estruturais")
    lines.append("")
    lines.append(f"- Gerado em: `{now_str()}`")
    lines.append(f"- Pasta raiz: `{base_dir}`")
    lines.append(f"- Camadas incluídas: `{', '.join(name for name, _, _ in grouped_files)}`")
    lines.append(f"- Ficheiro gerado: `{base_dir / MASTER_OUTPUT_NAME}`")
    lines.append("")
    lines.append("## Índice das camadas")
    lines.append("")
    for name, folder, files in grouped_files:
        anchor = slugify(f"camada-{name}")
        merged_name = f"MERGED__{folder.name}.md"
        lines.append(
            f"- [{name}](#{anchor}) — `{len(files)}` ficheiro(s) elegível(eis) — "
            f"`{(folder / merged_name).relative_to(base_dir).as_posix()}`"
        )
    lines.append("")
    lines.append("## Estatuto desta agregação")
    lines.append("")
    lines.append("- Este merge mestre reúne as quatro camadas estruturais indicadas no pedido.")
    lines.append("- Mantém cada camada separada, com índice próprio, para facilitar releitura e auditoria.")
    lines.append("- É rerunável e reescreve o output a cada execução.")
    lines.append("")
    for name, folder, files in grouped_files:
        group_anchor = slugify(f"camada-{name}")
        lines.append(f'<a id="{group_anchor}"></a>')
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"- Pasta: `{folder.relative_to(base_dir).as_posix()}`")
        lines.append(f"- Ficheiros incluídos: `{len(files)}`")
        lines.append("")
        lines.append("### Índice interno da camada")
        lines.append("")
        if not files:
            lines.append("- *(sem ficheiros elegíveis para merge)*")
        else:
            for path in files:
                anchor = slugify(f"{name}-{path.relative_to(folder).as_posix()}")
                rel = path.relative_to(base_dir).as_posix()
                lines.append(f"- [{path.stem}](#{anchor}) — `{rel}`")
        lines.append("")
        for path in files:
            anchor = slugify(f"{name}-{path.relative_to(folder).as_posix()}")
            rel = path.relative_to(base_dir).as_posix()
            lines.append(f'<a id="{anchor}"></a>')
            lines.append(f"### {path.stem}")
            lines.append("")
            lines.append(f"**Ficheiro de origem:** `{rel}`")
            lines.append("")
            lines.append(read_text(path))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge rerunável das camadas estruturais de 09_capitulos.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Pasta base 09_capitulos. Por omissão usa a pasta do script.",
    )
    args = parser.parse_args()

    base_dir = args.base_dir.resolve()
    if not base_dir.exists():
        print(f"[ERRO] Pasta base não existe: {base_dir}", file=sys.stderr)
        return 1

    grouped_files: List[Tuple[str, Path, List[Path]]] = []

    for rel_dir in TARGET_DIRS:
        folder = base_dir / rel_dir
        folder.mkdir(parents=True, exist_ok=True)
        files = collect_markdown_files(folder)
        grouped_files.append((rel_dir, folder, files))
        local_output = folder / f"MERGED__{folder.name}.md"
        local_output.write_text(build_local_merge(folder, files, base_dir), encoding="utf-8")
        print(f"[OK] {local_output.relative_to(base_dir).as_posix()} ({len(files)} ficheiro(s))")

    master_output = base_dir / MASTER_OUTPUT_NAME
    master_output.write_text(build_master_merge(base_dir, grouped_files), encoding="utf-8")
    print(f"[OK] {master_output.relative_to(base_dir).as_posix()} (merge mestre)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
