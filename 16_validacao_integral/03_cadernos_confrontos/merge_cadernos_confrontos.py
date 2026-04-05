#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Une todos os CF##_dossier_confronto.md num único Markdown com índice,
mas substitui CF03 / CF04 / CF05 pelas versões finas reformuladas, se existirem.

Uso:
    python merge_cadernos_confrontos_com_reformulados.py

Opcional:
    python merge_cadernos_confrontos_com_reformulados.py --output DOSSIERS_CONFRONTO__MERGED_COM_REFORMULADOS.md
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

PATTERN = re.compile(r"^(CF\d{2})_dossier_confronto\.md$", re.IGNORECASE)

# Caminho esperado das versões finas
# A pasta 03_cadernos_confrontos está ao lado de 05_dossiers_reformulados\validacao_fina
FINE_DIR_RELATIVE = Path("..") / "05_dossiers_reformulados" / "validacao_fina"

# Para cada CF, lista de ficheiros candidatos por ordem de preferência
FINE_CANDIDATES = {
    "CF03": [
        "CF03_dossier_confronto_fino_v3.md",
    ],
    "CF04": [
        "CF04_dossier_confronto_fino_dirigido.md",
    ],
    "CF05": [
        "CF05_dossier_confronto_fino_dirigido.md",
        "CF05_dossier_confronto_fino.md",
    ],
}


def natural_cf_key(path: Path):
    m = PATTERN.match(path.name)
    if not m:
        return (9999, path.name.lower())
    cf = m.group(1).upper()
    num = int(cf[2:])
    return (num, path.name.lower())


def first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def build_anchor(cf_id: str) -> str:
    return f"{cf_id.lower()}_dossier_confronto"


def clean_title_from_content(text: str, fallback: str) -> str:
    first = first_nonempty_line(text)
    if first.startswith("#"):
        return first.lstrip("#").strip()
    return fallback


def find_fine_version(base_folder: Path, cf_id: str) -> Path | None:
    fine_dir = (base_folder / FINE_DIR_RELATIVE).resolve()
    if cf_id not in FINE_CANDIDATES:
        return None
    for filename in FINE_CANDIDATES[cf_id]:
        candidate = fine_dir / filename
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def load_section_source(base_folder: Path, original_file: Path):
    cf_id = PATTERN.match(original_file.name).group(1).upper()
    fine_file = find_fine_version(base_folder, cf_id)

    if fine_file is not None:
        text = fine_file.read_text(encoding="utf-8", errors="replace").strip()
        return {
            "cf_id": cf_id,
            "text": text,
            "source_path": fine_file,
            "display_source": fine_file.name,
            "is_reformulated": True,
            "original_source": original_file.name,
        }

    text = original_file.read_text(encoding="utf-8", errors="replace").strip()
    return {
        "cf_id": cf_id,
        "text": text,
        "source_path": original_file,
        "display_source": original_file.name,
        "is_reformulated": False,
        "original_source": original_file.name,
    }


def merge_markdown(folder: Path, output_name: str) -> Path:
    files = sorted(
        [p for p in folder.iterdir() if p.is_file() and PATTERN.match(p.name)],
        key=natural_cf_key
    )

    if not files:
        raise FileNotFoundError("Não foram encontrados ficheiros CF##_dossier_confronto.md na pasta indicada.")

    output_path = folder / output_name
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    resolved_sections = [load_section_source(folder, p) for p in files]

    parts: list[str] = []
    parts.append("# DOSSIERS DE CONFRONTO — MERGED")
    parts.append("")
    parts.append(f"- Gerado em: `{now}`")
    parts.append(f"- Pasta origem: `{folder}`")
    parts.append(f"- Total de ficheiros agregados: `{len(files)}`")
    parts.append("")
    parts.append("## Nota metodológica")
    parts.append("")
    parts.append("Este ficheiro agrega os cadernos de confronto da pasta `03_cadernos_confrontos`.")
    parts.append("Quando existirem versões finas reformuladas de `CF03`, `CF04` ou `CF05`, essas versões substituem o caderno original nesta compilação, com indicação explícita na respetiva secção.")
    parts.append("")
    parts.append("## Índice")
    parts.append("")

    body_parts: list[str] = []

    for item in resolved_sections:
        cf_id = item["cf_id"]
        anchor = build_anchor(cf_id)
        if item["is_reformulated"]:
            parts.append(f"- [{cf_id}](#{anchor}) — versão reformulada/fina ativa")
        else:
            parts.append(f"- [{cf_id}](#{anchor})")

    parts.append("")

    for item in resolved_sections:
        cf_id = item["cf_id"]
        text = item["text"]
        anchor = build_anchor(cf_id)
        fallback_title = f"{cf_id} — dossier de confronto"
        title = clean_title_from_content(text, fallback_title)

        body_parts.append("---")
        body_parts.append("")
        body_parts.append(f'<a id="{anchor}"></a>')
        body_parts.append(f"## {cf_id}")
        body_parts.append("")
        body_parts.append(f"**Ficheiro de origem nesta compilação:** `{item['display_source']}`")

        if item["is_reformulated"]:
            body_parts.append(f"**Estado nesta compilação:** versão reformulada/fina ativa")
            body_parts.append(f"**Caderno original substituído:** `{item['original_source']}`")
        else:
            body_parts.append("**Estado nesta compilação:** caderno original")

        body_parts.append("")

        lines = text.splitlines()
        if lines and lines[0].strip().startswith("# "):
            body_parts.extend(lines)
        else:
            body_parts.append(f"# {title}")
            body_parts.append("")
            body_parts.extend(lines)

        body_parts.append("")
        body_parts.append("[Voltar ao índice](#índice)")
        body_parts.append("")

    parts.extend(body_parts)

    output_path.write_text("\n".join(parts), encoding="utf-8")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Une todos os CF##_dossier_confronto.md num único ficheiro Markdown, substituindo CF03/CF04/CF05 por versões finas quando existirem."
    )
    parser.add_argument(
        "--output",
        default="DOSSIERS_CONFRONTO__MERGED_COM_REFORMULADOS.md",
        help="Nome do ficheiro de saída"
    )
    args = parser.parse_args()

    folder = Path.cwd()
    output_path = merge_markdown(folder, args.output)
    print(f"[ok] Ficheiro gerado: {output_path}")


if __name__ == "__main__":
    main()