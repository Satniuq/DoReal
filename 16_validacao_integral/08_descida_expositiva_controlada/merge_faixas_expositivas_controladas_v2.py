#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merge_faixas_expositivas_controladas_v2.py

Corre na pasta:
    16_validacao_integral\08_descida_expositiva_controlada

V2:
- remove duplicação do primeiro título interno quando ele coincide com o nome do ficheiro;
- gera o merged global com nome que já contém as faixas presentes:
    MERGED__DESCIDA_EXPOSITIVA_CONTROLADA_FAIXAS_01_02_03.md

O script:
1. deteta subpastas de faixa (ex.: 01_faixa_..., 02_faixa_...);
2. gera um ficheiro MERGED por cada faixa;
3. gera um ficheiro MERGED global com todas as faixas;
4. ignora, por defeito, histórico de testes;
5. se a faixa já tiver consolidado, usa o consolidado como peça ativa e não inclui ensaios;
6. se a faixa ainda não tiver consolidado, inclui abertura + decisões/limites + último ensaio disponível.

Uso:
    python merge_faixas_expositivas_controladas_v2.py
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


ROOT = Path(__file__).resolve().parent
FAIXA_RE = re.compile(r"^(\d+)_faixa_")
MERGED_PREFIX = "MERGED__"

# Configuração
INCLUIR_ENSAIOS_QUANDO_HA_CONSOLIDADO = False
INCLUIR_HISTORICO_TESTES = False

DIR_ABERTURA = {"00_abertura"}
DIR_ENSAIOS = {"01_ensaios"}
DIR_DECISOES = {"01_decisoes_e_limites", "02_decisoes_e_limites"}
DIR_CONSOLIDADO = {"00_consolidado", "03_consolidado"}
DIR_HISTORICO = {"02_historico_testes"}


@dataclass
class FaixaBundle:
    pasta: Path
    abertura: List[Path]
    decisoes: List[Path]
    ensaios: List[Path]
    consolidado: List[Path]
    ativo: Optional[Path]
    incluidos: List[Path]
    output_merged: Path
    numero_faixa: str


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


def md_files_in_dir(dir_path: Path) -> List[Path]:
    if not dir_path.exists():
        return []
    return sorted(
        [
            p for p in dir_path.rglob("*.md")
            if p.is_file() and not p.name.startswith(MERGED_PREFIX)
        ],
        key=lambda p: natural_key(str(p.relative_to(dir_path)))
    )


def extract_version(path: Path) -> int:
    m = re.search(r"_v(\d+)\.md$", path.name, re.IGNORECASE)
    return int(m.group(1)) if m else -1


def latest_version(files: Iterable[Path]) -> List[Path]:
    files = list(files)
    if not files:
        return []
    return [max(files, key=lambda p: (extract_version(p), p.name.lower()))]


def strip_first_title_if_matches_filename(text: str, filename_stem: str) -> str:
    """
    Remove o primeiro heading do ficheiro se ele for apenas o título principal
    duplicado do nome do ficheiro.
    """
    lines = text.splitlines()
    i = 0

    # saltar linhas em branco iniciais
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


def pick_active_file(
    consolidado: List[Path],
    decisoes: List[Path],
    abertura: List[Path],
    ensaios: List[Path],
) -> Optional[Path]:
    if consolidado:
        return consolidado[0]
    if decisoes:
        return sorted(decisoes, key=lambda p: natural_key(p.name))[-1]
    if abertura:
        return abertura[0]
    if ensaios:
        return latest_version(ensaios)[0]
    return None


def gather_faixa_bundle(faixa_dir: Path) -> FaixaBundle:
    abertura = []
    decisoes = []
    ensaios = []
    consolidado = []
    historico = []

    for child in faixa_dir.iterdir():
        if not child.is_dir():
            continue

        name = child.name

        if name in DIR_ABERTURA:
            abertura.extend(md_files_in_dir(child))
        elif name in DIR_DECISOES:
            decisoes.extend(md_files_in_dir(child))
        elif name in DIR_ENSAIOS:
            ensaios.extend(md_files_in_dir(child))
        elif name in DIR_CONSOLIDADO:
            consolidado.extend(md_files_in_dir(child))
        elif name in DIR_HISTORICO:
            historico.extend(md_files_in_dir(child))

    abertura = sorted(abertura, key=lambda p: natural_key(p.name))
    decisoes = sorted(decisoes, key=lambda p: natural_key(p.name))
    ensaios = sorted(ensaios, key=lambda p: natural_key(p.name))
    consolidado = sorted(consolidado, key=lambda p: natural_key(p.name))
    historico = sorted(historico, key=lambda p: natural_key(p.name))

    incluidos: List[Path] = []

    if consolidado:
        incluidos.extend(consolidado)
        incluidos.extend(abertura)
        incluidos.extend(decisoes)
        if INCLUIR_ENSAIOS_QUANDO_HA_CONSOLIDADO:
            incluidos.extend(ensaios)
        if INCLUIR_HISTORICO_TESTES:
            incluidos.extend(historico)
    else:
        incluidos.extend(abertura)
        incluidos.extend(decisoes)
        incluidos.extend(latest_version(ensaios))
        if INCLUIR_HISTORICO_TESTES:
            incluidos.extend(historico)

    seen = set()
    incluidos_dedup = []
    for p in incluidos:
        if p not in seen:
            seen.add(p)
            incluidos_dedup.append(p)

    ativo = pick_active_file(consolidado, decisoes, abertura, ensaios)
    output_merged = faixa_dir / f"{MERGED_PREFIX}{faixa_dir.name}.md"

    m = FAIXA_RE.match(faixa_dir.name)
    numero_faixa = m.group(1) if m else "??"

    return FaixaBundle(
        pasta=faixa_dir,
        abertura=abertura,
        decisoes=decisoes,
        ensaios=ensaios,
        consolidado=consolidado,
        ativo=ativo,
        incluidos=incluidos_dedup,
        output_merged=output_merged,
        numero_faixa=numero_faixa,
    )


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


def render_faixa_merged(bundle: FaixaBundle, root: Path) -> str:
    rel_faixa = bundle.pasta.relative_to(root)
    ativo_rel = bundle.ativo.relative_to(root) if bundle.ativo else None

    lines = []
    lines.append(f"# MERGED — {bundle.pasta.name}")
    lines.append("")
    lines.append(f"- Gerado em: `{now_str()}`")
    lines.append(f"- Pasta da faixa: `{rel_faixa}`")
    lines.append(f"- Número da faixa: `{bundle.numero_faixa}`")
    if ativo_rel:
        lines.append(f"- Ficheiro ativo atual: `{ativo_rel}`")
    lines.append("")

    lines.append("## Índice interno")
    lines.append("")
    for p in bundle.incluidos:
        rel = p.relative_to(root)
        anchor = p.stem.lower()
        anchor = re.sub(r"[^a-z0-9_]+", "-", anchor)
        lines.append(f"- [{p.stem}](#{anchor}) — `{rel}`")
    lines.append("")

    lines.append("## Estatuto desta agregação")
    lines.append("")
    lines.append("- Esta agregação substitui leitura dispersa da faixa por um único ficheiro local.")
    lines.append("- O ficheiro ativo da faixa continua a ser o consolidado, se existir; caso não exista, vale a última decisão válida.")
    lines.append("- Ensaios e histórico só entram quando a faixa ainda não está consolidada, ou se a configuração os mandar incluir.")
    lines.append("")

    for p in bundle.incluidos:
        lines.append(render_file_block(p, root, heading_level=2).strip())
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_global_output_name(bundles: List[FaixaBundle]) -> str:
    nums = "_".join(b.numero_faixa for b in bundles)
    return f"{MERGED_PREFIX}DESCIDA_EXPOSITIVA_CONTROLADA_FAIXAS_{nums}.md"


def render_global_merged(bundles: List[FaixaBundle], root: Path) -> str:
    lines = []
    lines.append("# MERGED — descida expositiva controlada")
    lines.append("")
    lines.append(f"- Gerado em: `{now_str()}`")
    lines.append(f"- Pasta raiz: `{root}`")
    lines.append(f"- Faixas presentes: `{', '.join(b.numero_faixa for b in bundles)}`")
    lines.append("")

    lines.append("## Índice das faixas")
    lines.append("")
    for b in bundles:
        rel = b.output_merged.relative_to(root)
        ativo_rel = b.ativo.relative_to(root) if b.ativo else None
        lines.append(f"### {b.pasta.name}")
        lines.append(f"- Número da faixa: `{b.numero_faixa}`")
        lines.append(f"- Merged local: `{rel}`")
        if ativo_rel:
            lines.append(f"- Ficheiro ativo atual: `{ativo_rel}`")
        lines.append("")

    lines.append("## Conteúdo agregado das faixas")
    lines.append("")

    for b in bundles:
        lines.append(f"## {b.pasta.name}")
        lines.append("")
        lines.append(render_faixa_merged(b, root).strip())
        lines.append("")
        lines.append("================================================================")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    faixa_dirs = sorted(
        [p for p in ROOT.iterdir() if p.is_dir() and FAIXA_RE.match(p.name)],
        key=lambda p: natural_key(p.name)
    )

    if not faixa_dirs:
        raise SystemExit("Nenhuma pasta de faixa encontrada.")

    bundles = [gather_faixa_bundle(fd) for fd in faixa_dirs]

    for b in bundles:
        content = render_faixa_merged(b, ROOT)
        b.output_merged.write_text(content, encoding="utf-8")

    global_output = ROOT / build_global_output_name(bundles)
    global_content = render_global_merged(bundles, ROOT)
    global_output.write_text(global_content, encoding="utf-8")

    print("OK")
    print(f"Faixas processadas: {len(bundles)}")
    for b in bundles:
        print(f" - {b.output_merged.name}")
    print(f"Global: {global_output.name}")


if __name__ == "__main__":
    main()
