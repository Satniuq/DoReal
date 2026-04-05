#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gerar_run_containers_nao_resegmentados_v4.py

Colocar em: 00_bruto/gerar_run_containers_nao_resegmentados_v4.py

Objetivo
--------
Gerar uma run formalizada dos fragmentos ainda não resegmentados, com limpeza
mais agressiva de ruído operacional/transcricional, respeitando a arquitetura
já existente em 00_bruto:

1) lê `fragmentos_nao_processados.md`;
2) limpa e filtra blocos de controlo evidentes;
3) corta sujidade embutida (prompt, linhas de controlo, meta de Whisper, etc.);
4) colapsa repetições internas evidentes e remove duplicados exatos;
5) remove superblocos redundantes que apenas recombinam blocos já mantidos;
6) continua a numeração canónica F####;
7) escreve um `.md` de run com headers formais `## F#### — AAAA-MM-DD`;
8) gera o respetivo `containers_segmentacao__run_*.json` no formato compatível
   com `containers_segmentacao.json`;
9) valida cobertura/ordem/ids dessa run, produzindo
   `relatorio_validacao_containers__run_*.json`.

Notas metodológicas
-------------------
- Não escreve em `fragmentos.md`, nem em `containers_segmentacao.json`.
- Não tenta gerar `fragmentos_resegmentados.json`.
- A run fica isolada no bruto, mas já no paradigma canónico de containers.
- Esta v4 tenta tratar automaticamente: prompt embutido, eco de transcrição,
  duplicado exato, superbloco redundante e prefixo meta com referência a IA.

Uso
---
python gerar_run_containers_nao_resegmentados_v4.py
python gerar_run_containers_nao_resegmentados_v4.py --start-from 242
python gerar_run_containers_nao_resegmentados_v4.py --input fragmentos_nao_processados.md
python gerar_run_containers_nao_resegmentados_v4.py --output-prefix run_nao_resegmentados
python gerar_run_containers_nao_resegmentados_v4.py --keep-control-blocks
python gerar_run_containers_nao_resegmentados_v4.py --keep-duplicates
python gerar_run_containers_nao_resegmentados_v4.py --keep-superblocks

Saídas
------
- <prefix>__YYYYMMDD_HHMMSS.md
- containers_segmentacao__<prefix>__YYYYMMDD_HHMMSS.json
- relatorio_validacao_containers__<prefix>__YYYYMMDD_HHMMSS.json
- <prefix>__YYYYMMDD_HHMMSS__relatorio.txt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# -----------------------------------------------------------------------------
# Padrões de limpeza / deteção
# -----------------------------------------------------------------------------

CONTROL_BLOCK_PATTERNS = [
    re.compile(r"^\s*(?:Certo\.\s*)?Continua\.\s*$", re.I),
    re.compile(r"^\s*Sim\.\s*Continua\.\s*$", re.I),
    re.compile(r"^\s*Pensado\s+para\s+\d+s\s*$", re.I),
    re.compile(r"^\s*Pensei\s+durante.*$", re.I),
]

INLINE_LINE_NOISE_PATTERNS = [
    (re.compile(r"^\s*Pensado\s+para\s+\d+s\s*$", re.I | re.M), "removeu_linha_pensado_para"),
    (re.compile(r"^\s*Pensei\s+durante.*$", re.I | re.M), "removeu_linha_pensei_durante"),
    (re.compile(r"^\s*(?:Certo\.\s*)?Continua\.\s*$", re.I | re.M), "removeu_linha_continua"),
    (re.compile(r"^\s*Sim\.\s*Continua\.\s*$", re.I | re.M), "removeu_linha_sim_continua"),
]

SENTENCE_NOISE_PATTERNS = [
    (re.compile(r"\bEu vou continuar,?\s*n[aã]o digas nada\.?", re.I), "removeu_instrucao_nao_digas_nada"),
    (re.compile(r"\bn[aã]o s[oó]\s+parar\s+para\s+o\s+whisper\s+n[aã]o\s+falhar\.?", re.I), "removeu_meta_whisper"),
    (re.compile(r"\bn[aã]o s[oó]\s+parar\s+para\s+o\s+bicep\s+n[aã]o\s+falhar\.?", re.I), "removeu_meta_bicep"),
]

PROMPT_CUT_RE = re.compile(r"(?:----\s*)?\bprompt\s*:\s*", re.I)

HEADER_RE = re.compile(r"^##\s+(F\d{4})(?:\s+—\s+(.*?))?\s*$", re.MULTILINE)
DATA_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
F_ID_RE = re.compile(r"\bF(\d{4})\b")
MULTISPACE_RE = re.compile(r"[ \t]+")
MULTIBREAK_RE = re.compile(r"\n{3,}")
CHATGPT_PREFIX_SPLIT_RE = re.compile(r"\s[-—]\s+")

MAX_PARAGRAFOS_POR_CONTAINER = 8
MAX_CHARS_POR_CONTAINER = 4000

# -----------------------------------------------------------------------------
# Dataclasses auxiliares
# -----------------------------------------------------------------------------

@dataclass
class RunBlock:
    object_id: str
    raw_block: str
    cleaned_block: str
    normalized_block: str
    line_count: int
    char_count: int
    suspicion_flags: List[str]
    removed_control_only: bool = False


# -----------------------------------------------------------------------------
# Utilitários gerais
# -----------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = MULTISPACE_RE.sub(" ", text)
    text = MULTIBREAK_RE.sub("\n\n", text)
    return text.strip()


def split_blocks(text: str) -> List[str]:
    parts = re.split(r"\n\s*\n+", text)
    return [part.strip() for part in parts if part.strip()]


def split_sentences(text: str) -> List[str]:
    text = text.replace("\n", " ")
    chunks = re.split(r"(?<=[.!?])\s+", text)
    return [c.strip() for c in chunks if c.strip()]


def sha1_texto(texto: str) -> str:
    return hashlib.sha1(texto.encode("utf-8")).hexdigest()


def is_control_block(block: str) -> bool:
    return any(pat.match(block) for pat in CONTROL_BLOCK_PATTERNS)


def normalize_for_match(text: str) -> str:
    text = normalize_text(text).casefold()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def estimate_sentence_count(text: str) -> int:
    chunks = [c for c in re.split(r"[.!?;]+", text) if c.strip()]
    return max(1, len(chunks)) if text.strip() else 0


# -----------------------------------------------------------------------------
# Deteção do próximo F####
# -----------------------------------------------------------------------------


def extract_max_f_from_obj(obj: Any) -> int:
    max_id = 0
    if isinstance(obj, dict):
        for value in obj.values():
            max_id = max(max_id, extract_max_f_from_obj(value))
    elif isinstance(obj, list):
        for item in obj:
            max_id = max(max_id, extract_max_f_from_obj(item))
    elif isinstance(obj, str):
        for m in F_ID_RE.finditer(obj):
            max_id = max(max_id, int(m.group(1)))
    return max_id


def candidate_reference_paths(script_dir: Path) -> List[Path]:
    out: List[Path] = []
    parent = script_dir.parent

    direct_candidates = [
        script_dir / "fragmentos_resegmentados.json",
        script_dir / "containers_segmentacao.json",
        parent / "01_segmentar_fragmentos" / "fragmentos_resegmentados.json",
        parent / "01_segmentar_fragmentos" / "containers_segmentacao.json",
        parent / "13_Meta_Indice" / "cadência" / "01_segmentar_fragmentos" / "fragmentos_resegmentados.json",
        parent / "13_Meta_Indice" / "cadência" / "01_segmentar_fragmentos" / "containers_segmentacao.json",
    ]
    for p in direct_candidates:
        if p.exists() and p not in out:
            out.append(p)

    for p in sorted(script_dir.glob("*.json")):
        if p.name.startswith(("run_nao_resegmentados__", "containers_segmentacao__run_nao_resegmentados__")):
            out.append(p)

    patterns = ["fragmentos_resegmentados.json", "containers_segmentacao.json"]
    for pattern in patterns:
        for p in parent.glob(f"**/{pattern}"):
            try:
                rel = p.relative_to(parent)
            except ValueError:
                continue
            if len(rel.parts) <= 5 and p not in out:
                out.append(p)

    return out


def detect_start_index(script_dir: Path, reference_jsons: List[Path], start_from: Optional[int]) -> Tuple[int, List[str]]:
    notes: List[str] = []
    if start_from is not None:
        notes.append(f"start_forcado={start_from}")
        return start_from, notes

    max_found = 0
    refs = reference_jsons or candidate_reference_paths(script_dir)

    for ref in refs:
        try:
            if ref.suffix.lower() == ".json":
                data = json.loads(ref.read_text(encoding="utf-8"))
                local_max = extract_max_f_from_obj(data)
            else:
                local_max = 0
                for m in F_ID_RE.finditer(ref.read_text(encoding="utf-8", errors="ignore")):
                    local_max = max(local_max, int(m.group(1)))
            if local_max > 0:
                notes.append(f"referencia={ref.name}:max_F={local_max:04d}")
            max_found = max(max_found, local_max)
        except Exception as exc:  # pragma: no cover
            notes.append(f"falha_referencia={ref.name}:{exc.__class__.__name__}")

    if max_found <= 0:
        notes.append("sem_referencia_util:start=1")
        return 1, notes

    notes.append(f"start_detectado={max_found + 1}")
    return max_found + 1, notes


# -----------------------------------------------------------------------------
# Limpeza avançada dos blocos
# -----------------------------------------------------------------------------


def clean_inline_lines(block: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
    cleaned = block
    for pattern, label in INLINE_LINE_NOISE_PATTERNS:
        if pattern.search(cleaned):
            cleaned = pattern.sub("", cleaned)
            notes.append(label)
    return cleaned, notes


def cut_prompt_suffix(block: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
    match = PROMPT_CUT_RE.search(block)
    if not match:
        return block, notes
    cleaned = block[: match.start()].rstrip(" -—_\n\t")
    notes.append("cortou_sufixo_prompt")
    return cleaned, notes


def clean_sentence_noise(block: str) -> Tuple[str, List[str]]:
    cleaned = block
    notes: List[str] = []
    for pattern, label in SENTENCE_NOISE_PATTERNS:
        if pattern.search(cleaned):
            cleaned = pattern.sub("", cleaned)
            notes.append(label)
    return cleaned, notes


def strip_chatgpt_meta_prefix(block: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
    lower = block.casefold()
    if "chatgpt" not in lower:
        return block, notes

    parts = CHATGPT_PREFIX_SPLIT_RE.split(block, maxsplit=1)
    if len(parts) == 2:
        prefix, suffix = parts[0].strip(), parts[1].strip()
        if "chatgpt" in prefix.casefold() and len(suffix) >= 120 and any(tok in suffix.casefold() for tok in ["real", "apreens", "represent", "consci", "adequa"]):
            notes.append("cortou_prefixo_meta_ia")
            return suffix, notes
    return block, notes


def dedupe_immediate_sentences(sentences: List[str]) -> Tuple[List[str], int]:
    if not sentences:
        return sentences, 0
    out = [sentences[0]]
    removed = 0
    for s in sentences[1:]:
        if normalize_for_match(s) == normalize_for_match(out[-1]):
            removed += 1
            continue
        out.append(s)
    return out, removed


def collapse_repeated_prefix_window(sentences: List[str]) -> Tuple[List[str], int]:
    """Remove repetição longa de um prefixo do bloco quando o mesmo reaparece logo depois.

    Ex.: A+B+C+A+B+C+D  -> A+B+C+D
    """
    n = len(sentences)
    if n < 4:
        return sentences, 0

    norm = [normalize_for_match(s) for s in sentences]
    best: Optional[Tuple[int, int]] = None  # (j, k)

    for j in range(1, n - 1):
        max_k = min(j, n - j)
        for k in range(max_k, 1, -1):
            if norm[:k] == norm[j : j + k]:
                chars = sum(len(sentences[idx]) for idx in range(j, j + k))
                if chars >= 160:
                    best = (j, k)
                    break
        if best:
            break

    if not best:
        return sentences, 0

    j, k = best
    collapsed = sentences[:j] + sentences[j + k :]
    return collapsed, k


def collapse_internal_repetition(block: str) -> Tuple[str, List[str]]:
    sentences = split_sentences(block)
    notes: List[str] = []
    if len(sentences) < 2:
        return block, notes

    sentences, removed_exact = dedupe_immediate_sentences(sentences)
    if removed_exact:
        notes.append(f"removeu_frases_duplicadas_imediatas={removed_exact}")

    sentences, removed_prefix = collapse_repeated_prefix_window(sentences)
    if removed_prefix:
        notes.append(f"removeu_repeticao_interna_prefixo={removed_prefix}")

    cleaned = " ".join(s.strip() for s in sentences if s.strip())
    cleaned = normalize_text(cleaned)
    return cleaned, notes


def detect_suspicions(raw_block: str, cleaned_block: str) -> List[str]:
    out: List[str] = []
    lower_raw = raw_block.casefold()

    if "prompt:" in lower_raw:
        out.append("contaminacao_prompt")
    if "whisper" in lower_raw or "bicep" in lower_raw:
        out.append("possivel_artefacto_transcricao")
    if "chatgpt" in lower_raw:
        out.append("dialogo_ou_meta_ia")
    if "\n" in raw_block:
        out.append("bloco_multilinha")
    if len(cleaned_block) < 120:
        out.append("bloco_curto")
    if re.search(r"\bqq\b|\bpq\b|\btmb\b|\bnao\b|\bqnd\b", lower_raw):
        out.append("oralidade_ou_abreviacao")
    return out


def clean_block(raw_block: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
    cleaned = raw_block

    for fn in (clean_inline_lines, cut_prompt_suffix, clean_sentence_noise, strip_chatgpt_meta_prefix, collapse_internal_repetition):
        cleaned, fn_notes = fn(cleaned)
        notes.extend(fn_notes)

    cleaned = normalize_text(cleaned)
    return cleaned, sorted(set(notes))


def is_redundant_superblock(current_norm: str, kept_norms: List[str]) -> Tuple[bool, List[str]]:
    if len(current_norm) < 800:
        return False, []

    matching_lengths: List[int] = []
    match_count = 0
    for prev in kept_norms:
        if len(prev) < 250:
            continue
        if prev in current_norm:
            match_count += 1
            matching_lengths.append(len(prev))

    if match_count < 2:
        return False, []

    total_matched = sum(matching_lengths)
    covered = total_matched / max(1, len(current_norm))
    if covered >= 0.75:
        return True, [f"superbloco_redundante_matchs={match_count}", f"superbloco_redundante_cobertura={covered:.2f}"]
    return False, []


# -----------------------------------------------------------------------------
# Geração dos blocos da run
# -----------------------------------------------------------------------------


def parse_run_blocks(
    input_path: Path,
    start_index: int,
    keep_control_blocks: bool,
    keep_duplicates: bool,
    keep_superblocks: bool,
) -> Tuple[List[RunBlock], List[str], List[str]]:
    raw = input_path.read_text(encoding="utf-8")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    blocks = split_blocks(raw)

    run_blocks: List[RunBlock] = []
    notes: List[str] = []
    dropped: List[str] = []
    next_idx = start_index
    removed_control = 0
    removed_duplicates = 0
    removed_superblocks = 0

    kept_hashes: set[str] = set()
    kept_norms: List[str] = []

    for raw_idx, block in enumerate(blocks, start=1):
        control_only = is_control_block(block)
        if control_only and not keep_control_blocks:
            removed_control += 1
            dropped.append(f"bloco_raw_{raw_idx}: removido_controlo_puro")
            continue

        cleaned, cleaning_notes = clean_block(block)
        if not cleaned:
            removed_control += 1
            dropped.append(f"bloco_raw_{raw_idx}: removido_vazio_pos_limpeza")
            continue

        normalized = normalize_for_match(cleaned)
        block_hash = sha1_texto(normalized)

        if not keep_duplicates and block_hash in kept_hashes:
            removed_duplicates += 1
            dropped.append(f"bloco_raw_{raw_idx}: removido_duplicado_exato")
            continue

        if not keep_superblocks:
            is_superblock, super_notes = is_redundant_superblock(normalized, kept_norms)
            if is_superblock:
                removed_superblocks += 1
                dropped.append(f"bloco_raw_{raw_idx}: removido_" + ",".join(super_notes))
                continue

        container_id = f"F{next_idx:04d}"
        next_idx += 1
        flags = cleaning_notes + detect_suspicions(block, cleaned)

        rb = RunBlock(
            object_id=container_id,
            raw_block=block,
            cleaned_block=cleaned,
            normalized_block=normalize_text(cleaned),
            line_count=max(1, cleaned.count("\n") + 1),
            char_count=len(cleaned),
            suspicion_flags=sorted(set(flags)),
            removed_control_only=False,
        )
        run_blocks.append(rb)
        kept_hashes.add(block_hash)
        kept_norms.append(normalized)

    notes.append(f"blocos_brutos={len(blocks)}")
    notes.append(f"blocos_ignorados_controlo={removed_control}")
    notes.append(f"blocos_removidos_duplicado_exato={removed_duplicates}")
    notes.append(f"blocos_removidos_superbloco={removed_superblocks}")
    notes.append(f"blocos_run={len(run_blocks)}")
    return run_blocks, notes, dropped


def write_run_markdown(run_blocks: List[RunBlock], output_md: Path, run_date: str) -> None:
    parts: List[str] = []
    for rb in run_blocks:
        parts.append(f"## {rb.object_id} — {run_date}\n")
        parts.append(rb.cleaned_block.strip() + "\n")
    output_md.write_text("\n".join(parts).strip() + "\n", encoding="utf-8")


# -----------------------------------------------------------------------------
# Lógica compatível com preparar_containers_segmentacao.py
# -----------------------------------------------------------------------------


def normalizar_espacos(texto: str) -> str:
    texto = texto.replace("\u00A0", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def separar_paragrafos(texto: str) -> List[str]:
    texto = texto.replace("\r\n", "\n").replace("\r", "\n").strip()
    blocos = re.split(r"\n\s*\n+", texto)
    return [b.strip() for b in blocos if b.strip()]


def inferir_tipo_material(container_texto: str) -> str:
    t = container_texto.lower()
    if "[proposta gpt]" in t or "[resposta do autor]" in t or "chatgpt" in t:
        return "dialogo_com_ia"
    if "—" in container_texto and len(container_texto.split()) > 120:
        return "fragmento_reflexivo"
    if len(container_texto.split()) > 180:
        return "fragmento_editorial"
    return "misto"


def extrair_titulo_e_data(resto_header: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not resto_header:
        return None, None
    resto = resto_header.strip()
    data_match = DATA_RE.search(resto)
    data = data_match.group(1) if data_match else None
    titulo = resto
    if data:
        titulo = titulo.replace(data, "").strip(" —-–")
    titulo = titulo.strip()
    if not titulo:
        titulo = None
    return titulo, data


def construir_paragrafos(container_id: str, paragrafos_raw: List[str]) -> List[Dict[str, Any]]:
    paragrafos: List[Dict[str, Any]] = []
    for i, p in enumerate(paragrafos_raw, start=1):
        texto_norm = normalizar_espacos(p)
        paragrafos.append(
            {
                "paragrafo_id": f"{container_id}_P{i:02d}",
                "ordem_no_container": i,
                "texto": p.strip(),
                "texto_normalizado": texto_norm,
                "n_chars": len(texto_norm),
                "n_linhas_aprox": max(1, p.count("\n") + 1),
            }
        )
    return paragrafos


def criar_container(
    container_id: str,
    header_original: Optional[str],
    titulo_container: Optional[str],
    data: Optional[str],
    paragrafos_raw: List[str],
    ordem_no_ficheiro: int,
    tem_header_formal: bool,
    origem_ficheiro: str,
    observacoes_extra: Optional[List[str]] = None,
) -> Dict[str, Any]:
    corpo = "\n\n".join(paragrafos_raw)
    tipo_material = inferir_tipo_material(corpo)
    paragrafos = construir_paragrafos(container_id, paragrafos_raw)

    observacoes: List[str] = []
    if not tem_header_formal:
        observacoes.append("container sem header formal")
    if titulo_container:
        observacoes.append("título presente no cabeçalho")
    if tipo_material == "dialogo_com_ia":
        observacoes.append("contém marcas de diálogo com IA")
    if observacoes_extra:
        observacoes.extend(observacoes_extra)

    return {
        "container_id": container_id,
        "titulo_container": titulo_container,
        "data": data,
        "origem_ficheiro": origem_ficheiro,
        "tipo_material_fonte": tipo_material,
        "ordem_no_ficheiro": ordem_no_ficheiro,
        "tem_header_formal": tem_header_formal,
        "header_original": header_original,
        "paragrafos": paragrafos,
        "n_paragrafos": len(paragrafos),
        "observacoes_container": observacoes,
    }


def dividir_em_subcontainers(
    base_container_id: str,
    header_original: Optional[str],
    titulo_container: Optional[str],
    data: Optional[str],
    paragrafos_raw: List[str],
    ordem_inicial: int,
    tem_header_formal: bool,
    origem_ficheiro: str,
) -> List[Dict[str, Any]]:
    containers: List[Dict[str, Any]] = []
    chunk: List[str] = []
    chunk_chars = 0
    ordem = ordem_inicial
    sub_idx = 1

    for p in paragrafos_raw:
        p_norm = normalizar_espacos(p)
        p_chars = len(p_norm)
        precisa_fechar = False

        if chunk:
            if len(chunk) >= MAX_PARAGRAFOS_POR_CONTAINER:
                precisa_fechar = True
            elif chunk_chars + p_chars > MAX_CHARS_POR_CONTAINER:
                precisa_fechar = True

        if precisa_fechar:
            sub_id = f"{base_container_id}_A{sub_idx:02d}"
            containers.append(
                criar_container(
                    container_id=sub_id,
                    header_original=header_original,
                    titulo_container=titulo_container,
                    data=data,
                    paragrafos_raw=chunk,
                    ordem_no_ficheiro=ordem,
                    tem_header_formal=tem_header_formal,
                    origem_ficheiro=origem_ficheiro,
                    observacoes_extra=[
                        f"subcontainer automático derivado de {base_container_id}",
                        f"chunk {sub_idx}",
                    ],
                )
            )
            ordem += 1
            sub_idx += 1
            chunk = []
            chunk_chars = 0

        chunk.append(p)
        chunk_chars += p_chars

    if chunk:
        sub_id = f"{base_container_id}_A{sub_idx:02d}"
        containers.append(
            criar_container(
                container_id=sub_id,
                header_original=header_original,
                titulo_container=titulo_container,
                data=data,
                paragrafos_raw=chunk,
                ordem_no_ficheiro=ordem,
                tem_header_formal=tem_header_formal,
                origem_ficheiro=origem_ficheiro,
                observacoes_extra=[
                    f"subcontainer automático derivado de {base_container_id}",
                    f"chunk {sub_idx}",
                ],
            )
        )
    return containers


def processar_bloco(
    container_id: str,
    header_original: Optional[str],
    titulo_container: Optional[str],
    data: Optional[str],
    corpo: str,
    ordem_no_ficheiro: int,
    tem_header_formal: bool,
    origem_ficheiro: str,
) -> List[Dict[str, Any]]:
    paragrafos_raw = separar_paragrafos(corpo)
    total_chars = sum(len(normalizar_espacos(p)) for p in paragrafos_raw)

    if len(paragrafos_raw) > MAX_PARAGRAFOS_POR_CONTAINER or total_chars > MAX_CHARS_POR_CONTAINER:
        return dividir_em_subcontainers(
            base_container_id=container_id,
            header_original=header_original,
            titulo_container=titulo_container,
            data=data,
            paragrafos_raw=paragrafos_raw,
            ordem_inicial=ordem_no_ficheiro,
            tem_header_formal=tem_header_formal,
            origem_ficheiro=origem_ficheiro,
        )

    return [
        criar_container(
            container_id=container_id,
            header_original=header_original,
            titulo_container=titulo_container,
            data=data,
            paragrafos_raw=paragrafos_raw,
            ordem_no_ficheiro=ordem_no_ficheiro,
            tem_header_formal=tem_header_formal,
            origem_ficheiro=origem_ficheiro,
        )
    ]


def processar_ficheiro_markdown(caminho: Path) -> List[Dict[str, Any]]:
    conteudo = caminho.read_text(encoding="utf-8")
    conteudo = conteudo.replace("\r\n", "\n").replace("\r", "\n")
    matches = list(HEADER_RE.finditer(conteudo))
    containers: List[Dict[str, Any]] = []
    ordem = 1
    auto_count = 1

    if not matches:
        container_id = f"AUTO_{auto_count:04d}"
        containers.extend(
            processar_bloco(
                container_id=container_id,
                header_original=None,
                titulo_container=None,
                data=None,
                corpo=conteudo,
                ordem_no_ficheiro=ordem,
                tem_header_formal=False,
                origem_ficheiro=caminho.name,
            )
        )
        return containers

    inicio_primeiro = matches[0].start()
    prefixo = conteudo[:inicio_primeiro].strip()
    if prefixo:
        container_id = f"AUTO_{auto_count:04d}"
        novos = processar_bloco(
            container_id=container_id,
            header_original=None,
            titulo_container=None,
            data=None,
            corpo=prefixo,
            ordem_no_ficheiro=ordem,
            tem_header_formal=False,
            origem_ficheiro=caminho.name,
        )
        containers.extend(novos)
        ordem += len(novos)
        auto_count += 1

    for idx, m in enumerate(matches):
        container_id = m.group(1).strip()
        resto_header = m.group(2).strip() if m.group(2) else None
        header_original = m.group(0).strip()
        titulo_container, data = extrair_titulo_e_data(resto_header)
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(conteudo)
        corpo = conteudo[start:end].strip()

        novos = processar_bloco(
            container_id=container_id,
            header_original=header_original,
            titulo_container=titulo_container,
            data=data,
            corpo=corpo,
            ordem_no_ficheiro=ordem,
            tem_header_formal=True,
            origem_ficheiro=caminho.name,
        )
        containers.extend(novos)
        ordem += len(novos)

    return containers


# -----------------------------------------------------------------------------
# Validação compatível com validar_containers_segmentacao.py
# -----------------------------------------------------------------------------


def extrair_paragrafos_do_md(caminho: Path) -> Tuple[List[Dict[str, Any]], int]:
    conteudo = caminho.read_text(encoding="utf-8")
    conteudo = conteudo.replace("\r\n", "\n").replace("\r", "\n")
    headers = list(HEADER_RE.finditer(conteudo))
    n_headers = len(headers)
    paragrafos_extraidos: List[Dict[str, Any]] = []

    if not headers:
        for i, p in enumerate(separar_paragrafos(conteudo), start=1):
            p_norm = normalizar_espacos(p)
            paragrafos_extraidos.append(
                {
                    "ordem_global": i,
                    "texto": p,
                    "texto_normalizado": p_norm,
                    "hash": sha1_texto(p_norm),
                }
            )
        return paragrafos_extraidos, n_headers

    ordem_global = 1
    inicio_primeiro = headers[0].start()
    prefixo = conteudo[:inicio_primeiro].strip()
    if prefixo:
        for p in separar_paragrafos(prefixo):
            p_norm = normalizar_espacos(p)
            paragrafos_extraidos.append(
                {
                    "ordem_global": ordem_global,
                    "texto": p,
                    "texto_normalizado": p_norm,
                    "hash": sha1_texto(p_norm),
                }
            )
            ordem_global += 1

    for idx, h in enumerate(headers):
        start = h.end()
        end = headers[idx + 1].start() if idx + 1 < len(headers) else len(conteudo)
        corpo = conteudo[start:end].strip()
        for p in separar_paragrafos(corpo):
            p_norm = normalizar_espacos(p)
            paragrafos_extraidos.append(
                {
                    "ordem_global": ordem_global,
                    "texto": p,
                    "texto_normalizado": p_norm,
                    "hash": sha1_texto(p_norm),
                }
            )
            ordem_global += 1

    return paragrafos_extraidos, n_headers


def extrair_paragrafos_do_json(containers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    paragrafos: List[Dict[str, Any]] = []
    ordem_global = 1
    for c in containers:
        cid = c.get("container_id")
        for p in c.get("paragrafos", []):
            txt = p.get("texto_normalizado") or normalizar_espacos(p.get("texto", ""))
            paragrafos.append(
                {
                    "ordem_global": ordem_global,
                    "container_id": cid,
                    "paragrafo_id": p.get("paragrafo_id"),
                    "texto_normalizado": txt,
                    "hash": sha1_texto(txt),
                }
            )
            ordem_global += 1
    return paragrafos


def validar(md_path: Path, containers: List[Dict[str, Any]]) -> Dict[str, Any]:
    paragrafos_md, n_headers_md = extrair_paragrafos_do_md(md_path)
    paragrafos_json = extrair_paragrafos_do_json(containers)

    erros: List[Dict[str, Any]] = []
    avisos: List[Dict[str, Any]] = []

    containers_vazios: List[str] = []
    container_ids: List[str] = []
    header_formais_json = 0

    for c in containers:
        cid = c.get("container_id")
        container_ids.append(cid)
        if c.get("tem_header_formal") is True:
            header_formais_json += 1
        ps = c.get("paragrafos", [])
        if not isinstance(ps, list) or len(ps) == 0:
            containers_vazios.append(cid)

    if containers_vazios:
        erros.append({"tipo": "containers_vazios", "containers": containers_vazios})

    dup_container_ids = sorted({x for x in container_ids if container_ids.count(x) > 1})
    if dup_container_ids:
        erros.append({"tipo": "container_ids_duplicados", "container_ids": dup_container_ids})

    paragrafo_ids = [p.get("paragrafo_id") for c in containers for p in c.get("paragrafos", [])]
    dup_par_ids = sorted({x for x in paragrafo_ids if paragrafo_ids.count(x) > 1})
    if dup_par_ids:
        erros.append({"tipo": "paragrafo_ids_duplicados", "paragrafo_ids": dup_par_ids})

    if n_headers_md != header_formais_json:
        avisos.append(
            {
                "tipo": "diferenca_numero_headers",
                "headers_md": n_headers_md,
                "containers_com_header_formal": header_formais_json,
            }
        )

    hashes_md = [p["hash"] for p in paragrafos_md]
    hashes_json = [p["hash"] for p in paragrafos_json]
    set_md = set(hashes_md)
    set_json = set(hashes_json)

    faltam_no_json = list(set_md - set_json)
    extras_no_json = list(set_json - set_md)

    if faltam_no_json:
        faltantes = [p for p in paragrafos_md if p["hash"] in set(faltam_no_json)]
        erros.append({"tipo": "paragrafos_em_falta_no_json", "total": len(faltantes), "exemplos": faltantes[:20]})

    if extras_no_json:
        extras = [p for p in paragrafos_json if p["hash"] in set(extras_no_json)]
        erros.append({"tipo": "paragrafos_a_mais_no_json", "total": len(extras), "exemplos": extras[:20]})

    freq_md: Dict[str, int] = {}
    for h in hashes_md:
        freq_md[h] = freq_md.get(h, 0) + 1
    freq_json: Dict[str, int] = {}
    for h in hashes_json:
        freq_json[h] = freq_json.get(h, 0) + 1

    duplicacoes_indevidas: List[Dict[str, Any]] = []
    perdas_de_ocorrencia: List[Dict[str, Any]] = []
    for h in set(freq_md.keys()) | set(freq_json.keys()):
        n_md = freq_md.get(h, 0)
        n_json = freq_json.get(h, 0)
        if n_json > n_md:
            duplicacoes_indevidas.append({"hash": h, "ocorrencias_md": n_md, "ocorrencias_json": n_json})
        elif n_json < n_md:
            perdas_de_ocorrencia.append({"hash": h, "ocorrencias_md": n_md, "ocorrencias_json": n_json})

    if duplicacoes_indevidas:
        erros.append({"tipo": "duplicacoes_indevidas_no_json", "total": len(duplicacoes_indevidas), "exemplos": duplicacoes_indevidas[:20]})
    if perdas_de_ocorrencia:
        erros.append({"tipo": "perdas_de_ocorrencia_no_json", "total": len(perdas_de_ocorrencia), "exemplos": perdas_de_ocorrencia[:20]})

    ordem_ok = True
    primeira_divergencia = None
    min_len = min(len(paragrafos_md), len(paragrafos_json))
    for i in range(min_len):
        if paragrafos_md[i]["hash"] != paragrafos_json[i]["hash"]:
            ordem_ok = False
            primeira_divergencia = {"indice": i + 1, "md": paragrafos_md[i], "json": paragrafos_json[i]}
            break

    if not ordem_ok:
        erros.append({"tipo": "ordem_divergente", "primeira_divergencia": primeira_divergencia})

    resumo = {
        "ficheiro_md": md_path.name,
        "n_headers_md": n_headers_md,
        "n_containers_json": len(containers),
        "n_paragrafos_md": len(paragrafos_md),
        "n_paragrafos_json": len(paragrafos_json),
        "cobertura_total_ok": len(faltam_no_json) == 0 and len(extras_no_json) == 0,
        "ordem_total_ok": ordem_ok,
        "ids_ok": len(dup_container_ids) == 0 and len(dup_par_ids) == 0,
        "containers_vazios_ok": len(containers_vazios) == 0,
    }

    estado_final = "ok" if not erros else "com_erros"
    return {"estado_final": estado_final, "resumo": resumo, "erros": erros, "avisos": avisos}


# -----------------------------------------------------------------------------
# Escrita dos relatórios
# -----------------------------------------------------------------------------


def write_relatorio_txt(
    out_path: Path,
    input_path: Path,
    output_md: Path,
    output_json: Path,
    output_validation: Path,
    run_blocks: List[RunBlock],
    validation: Dict[str, Any],
    detection_notes: List[str],
    parsing_notes: List[str],
    dropped_notes: List[str],
) -> None:
    lines: List[str] = []
    lines.append("RUN DE CONTAINERS — NÃO RESEGMENTADOS")
    lines.append("=" * 72)
    lines.append(f"Input: {input_path.name}")
    lines.append(f"Markdown run: {output_md.name}")
    lines.append(f"Containers JSON: {output_json.name}")
    lines.append(f"Validação JSON: {output_validation.name}")
    lines.append("")
    lines.append("Deteção de numeração")
    lines.append("-" * 72)
    lines.extend(f"- {n}" for n in detection_notes)
    lines.append("")
    lines.append("Parsing / limpeza")
    lines.append("-" * 72)
    lines.extend(f"- {n}" for n in parsing_notes)
    lines.append("")
    lines.append("Resumo")
    lines.append("-" * 72)
    lines.append(f"- blocos_run: {len(run_blocks)}")
    lines.append(f"- primeiro_id: {run_blocks[0].object_id if run_blocks else '∅'}")
    lines.append(f"- ultimo_id: {run_blocks[-1].object_id if run_blocks else '∅'}")
    lines.append(f"- validacao_estado: {validation['estado_final']}")
    lines.append(f"- cobertura_total_ok: {validation['resumo']['cobertura_total_ok']}")
    lines.append(f"- ordem_total_ok: {validation['resumo']['ordem_total_ok']}")
    lines.append(f"- ids_ok: {validation['resumo']['ids_ok']}")
    lines.append(f"- containers_vazios_ok: {validation['resumo']['containers_vazios_ok']}")
    lines.append("")
    lines.append("Sinais por bloco")
    lines.append("-" * 72)
    for rb in run_blocks:
        flags = ", ".join(rb.suspicion_flags) if rb.suspicion_flags else "sem_sinais"
        lines.append(f"- {rb.object_id}: {flags}")
    lines.append("")
    if dropped_notes:
        lines.append("Blocos removidos automaticamente")
        lines.append("-" * 72)
        lines.extend(f"- {d}" for d in dropped_notes)
        lines.append("")
    if validation["erros"]:
        lines.append("Erros de validação")
        lines.append("-" * 72)
        for err in validation["erros"]:
            lines.append(f"- {err['tipo']}")
        lines.append("")
    if validation["avisos"]:
        lines.append("Avisos de validação")
        lines.append("-" * 72)
        for av in validation["avisos"]:
            lines.append(f"- {av['tipo']}")
        lines.append("")

    out_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gerar run de containers para não resegmentados.")
    parser.add_argument("--input", default="fragmentos_nao_processados.md", help="Ficheiro markdown de entrada.")
    parser.add_argument("--output-prefix", default="run_nao_resegmentados", help="Prefixo dos outputs.")
    parser.add_argument("--start-from", type=int, default=None, help="Forçar primeiro F#### (número sem F).")
    parser.add_argument("--reference-json", action="append", default=[], help="Ficheiro(s) JSON de referência para detetar o maior F####.")
    parser.add_argument("--keep-control-blocks", action="store_true", help="Não ignora blocos de controlo como 'Continua.'.")
    parser.add_argument("--keep-duplicates", action="store_true", help="Mantém duplicados exatos de blocos.")
    parser.add_argument("--keep-superblocks", action="store_true", help="Mantém blocos redundantes que apenas recombinam outros já mantidos.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    script_path = Path(__file__).resolve()
    script_dir = script_path.parent
    input_path = (script_dir / args.input).resolve()

    if not input_path.exists():
        raise SystemExit(f"[erro] Ficheiro de entrada não existe: {input_path}")

    ref_paths: List[Path] = []
    for ref in args.reference_json:
        rp = (script_dir / ref).resolve()
        if rp.exists():
            ref_paths.append(rp)

    start_index, detection_notes = detect_start_index(script_dir, ref_paths, args.start_from)
    run_blocks, parsing_notes, dropped_notes = parse_run_blocks(
        input_path,
        start_index,
        args.keep_control_blocks,
        args.keep_duplicates,
        args.keep_superblocks,
    )

    if not run_blocks:
        raise SystemExit("[erro] Não sobraram blocos após limpeza/filtragem.")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_date = datetime.now().strftime("%Y-%m-%d")

    output_md = script_dir / f"{args.output_prefix}__{ts}.md"
    output_json = script_dir / f"containers_segmentacao__{args.output_prefix}__{ts}.json"
    output_validation = script_dir / f"relatorio_validacao_containers__{args.output_prefix}__{ts}.json"
    output_txt = script_dir / f"{args.output_prefix}__{ts}__relatorio.txt"

    write_run_markdown(run_blocks, output_md, run_date)
    containers = processar_ficheiro_markdown(output_md)
    validation = validar(output_md, containers)

    output_json.write_text(json.dumps(containers, ensure_ascii=False, indent=2), encoding="utf-8")
    output_validation.write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")
    write_relatorio_txt(
        output_txt,
        input_path,
        output_md,
        output_json,
        output_validation,
        run_blocks,
        validation,
        detection_notes,
        parsing_notes,
        dropped_notes,
    )

    print("=" * 72)
    print("RUN DE CONTAINERS — NÃO RESEGMENTADOS (v4)")
    print("=" * 72)
    print(f"Input:               {input_path.name}")
    print(f"Markdown run:        {output_md.name}")
    print(f"Containers JSON:     {output_json.name}")
    print(f"Validação JSON:      {output_validation.name}")
    print(f"Relatório TXT:       {output_txt.name}")
    print("-" * 72)
    print(f"Blocos run:          {len(run_blocks)}")
    print(f"Primeiro ID:         {run_blocks[0].object_id}")
    print(f"Último ID:           {run_blocks[-1].object_id}")
    print(f"Estado validação:    {validation['estado_final']}")
    print(f"Cobertura total ok:  {validation['resumo']['cobertura_total_ok']}")
    print(f"Ordem total ok:      {validation['resumo']['ordem_total_ok']}")
    print(f"IDs ok:              {validation['resumo']['ids_ok']}")
    print(f"Containers vazios:   {validation['resumo']['containers_vazios_ok']}")
    print("=" * 72)


if __name__ == "__main__":
    main()
