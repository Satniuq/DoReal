#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime
import re

# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILENAME = "DOSSIERS_FINAIS_ESTABILIZADOS__MERGED.md"

EXCLUDED_FILENAMES = {
    OUTPUT_FILENAME,
}

TARGET_SUFFIX = ".md"

# Tipos canónicos permitidos no merged final
DOC_TYPE_PRIORITY = {
    "dossier_confronto_fino_dirigido": 10,
    "dossier_confronto_fino_v3": 10,
    "dossier_confronto_fino_v2": 10,
    "dossier_confronto_fino_v1": 10,
    "dossier_confronto_fino": 10,

    "complemento_FECHO_LOCAL": 20,
    "complemento_fecho_local": 20,

    "ficha_gesto_estrutural": 30,

    "mapa_minimo_pre_exposicao": 40,
}

DEFAULT_TYPE_PRIORITY = 999

# Regex estrita:
# só aceita ficheiros do tipo CF03_...md, CF04_...md, etc.
CF_FILENAME_PATTERN = re.compile(r"^(CF\d{2})_(.+)\.md$", flags=re.IGNORECASE)


# ============================================================
# UTILITÁRIOS
# ============================================================

def natural_sort_key(text: str):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", text)
    ]


def parse_cf_and_type(filename_stem: str):
    m = re.match(r"^(CF\d{2})_(.+)$", filename_stem, flags=re.IGNORECASE)
    if m:
        return m.group(1).upper(), m.group(2)
    return None, None


def get_doc_type_priority(doc_type: str):
    lowered = doc_type.lower()
    for known_type, priority in DOC_TYPE_PRIORITY.items():
        if lowered.startswith(known_type.lower()):
            return priority
    return DEFAULT_TYPE_PRIORITY


def is_allowed_markdown(path: Path) -> bool:
    if not path.is_file():
        return False

    if path.suffix.lower() != TARGET_SUFFIX:
        return False

    if path.name in EXCLUDED_FILENAMES:
        return False

    m = CF_FILENAME_PATTERN.match(path.name)
    if not m:
        return False

    _, doc_type = parse_cf_and_type(path.stem)
    if not doc_type:
        return False

    # Só entra se o tipo documental for um dos canónicos permitidos
    return get_doc_type_priority(doc_type) != DEFAULT_TYPE_PRIORITY


def file_sort_key(path: Path):
    cf_id, doc_type = parse_cf_and_type(path.stem)
    cf_num_match = re.match(r"^CF(\d{2})$", cf_id or "")
    cf_num = int(cf_num_match.group(1)) if cf_num_match else 999
    type_priority = get_doc_type_priority(doc_type or "")
    return (cf_num, type_priority, natural_sort_key(path.name))


def list_markdown_files(base_dir: Path):
    files = [path for path in base_dir.iterdir() if is_allowed_markdown(path)]
    files.sort(key=file_sort_key)
    return files


def read_text_safe(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def make_anchor(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text)
    return text


def build_index(files):
    lines = []
    lines.append("## Índice\n")
    current_cf = None

    for path in files:
        cf_id, _ = parse_cf_and_type(path.stem)

        if cf_id != current_cf:
            if current_cf is not None:
                lines.append("\n")
            lines.append(f"### {cf_id}\n")
            current_cf = cf_id

        anchor = make_anchor(path.stem)
        lines.append(f"- [{path.stem}](#{anchor})\n")

    return "".join(lines)


def build_merged_content(files):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    parts = []
    parts.append("# DOSSIERS FINAIS ESTABILIZADOS — MERGED\n\n")
    parts.append(f"- Gerado em: `{now}`\n")
    parts.append(f"- Pasta origem: `{BASE_DIR}`\n")
    parts.append(f"- Total de ficheiros agregados: `{len(files)}`\n\n")

    if not files:
        parts.append("**Nenhum ficheiro canónico `.md` encontrado para agregar.**\n")
        return "".join(parts)

    parts.append(build_index(files))
    parts.append("\n---\n")

    current_cf = None

    for path in files:
        cf_id, _ = parse_cf_and_type(path.stem)

        if cf_id != current_cf:
            parts.append(f"\n# {cf_id}\n")
            parts.append("\n---\n")
            current_cf = cf_id

        try:
            content = read_text_safe(path).strip()
        except Exception as e:
            content = f"**[ERRO AO LER FICHEIRO: {e}]**"

        parts.append(f"\n## {path.stem}\n\n")
        parts.append(f"**Ficheiro de origem:** `{path.name}`\n\n")
        parts.append(content)
        parts.append("\n\n---\n")

    return "".join(parts)


def write_output(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


# ============================================================
# EXECUÇÃO
# ============================================================

def main():
    files = list_markdown_files(BASE_DIR)
    output_path = BASE_DIR / OUTPUT_FILENAME
    merged_content = build_merged_content(files)
    write_output(output_path, merged_content)

    print(f"[ok] Ficheiro gerado: {output_path}")
    print(f"[ok] Nº de ficheiros agregados: {len(files)}")

    if files:
        print("[ok] Ordem final:")
        for f in files:
            print(f"   - {f.name}")
    else:
        print("[aviso] Não foram encontrados ficheiros canónicos para agregar.")


if __name__ == "__main__":
    main()