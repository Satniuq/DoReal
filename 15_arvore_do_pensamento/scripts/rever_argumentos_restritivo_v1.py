# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

INPUT_TREE_FILENAME = "arvore_do_pensamento_v1_pos_percursos.json"
INPUT_TRIAGEM_JSON_FILENAME = "triagem_fecho_superior_v1.json"
INPUT_TRIAGEM_REPORT_FILENAME = "relatorio_triagem_fecho_superior_v1.txt"
INPUT_REPORT_GERACAO_ARGUMENTOS = "relatorio_geracao_argumentos_v1.txt"
INPUT_REPORT_VALIDACAO_ARGUMENTOS = "relatorio_validacao_argumentos_v1.txt"
INPUT_REPORT_REVISAO_PERCURSOS = "relatorio_revisao_percursos_superiores_v1.txt"

OUTPUT_TREE_FILENAME = "arvore_do_pensamento_v1_fecho_superior.json"
OUTPUT_REPORT_FILENAME = "relatorio_revisao_argumentos_restritiva_v1.txt"

RAMO_ID_RE = re.compile(r"\b(RA_\d{4})\b")
PERCURSO_ID_RE = re.compile(r"\b(P_[A-Z0-9_]+)\b")
ARGUMENTO_ID_RE = re.compile(r"\b(ARG_[A-Z0-9_]+)\b")
WARNING_LINE_RE = re.compile(
    r"^-\s*(RA_\d{4})\s*->\s*(.*?)\s*\[([A-Za-z_]+)\]:\s*(.*)$"
)
GENERATION_LOG_RE = re.compile(
    r"^(RA_\d{4})\s*->\s*(ARG_[A-Z0-9_]+)\s*\|\s*score=(\d+)\s*\|\s*(.*)$"
)
GENERATION_EMPTY_RE = re.compile(r"^(RA_\d{4})\s*->\s*sem associação suficiente\s*$", re.IGNORECASE)

ARGUMENTO_FIELD_CANDIDATES = (
    "argumento_ids_associados",
    "argumento_ids",
    "argumentos_associados",
    "argumentos_ids",
)
PERCURSO_FIELD_CANDIDATES = (
    "percurso_ids_associados",
    "percurso_ids",
    "percursos_associados",
    "percursos_ids",
)
ARGUMENTO_RAMO_IDS_FIELD_CANDIDATES = (
    "ramo_ids",
    "ramo_ids_associados",
)

NEGATIVE_PERCURSO_REVIEW_KEYWORDS = (
    "revisão manual",
    "revisao manual",
    "não decidido",
    "nao decidido",
    "sem percurso final",
    "removido",
)

STRONG_REASON_MARKERS = (
    "passo-alvo fortemente compatível",
    "problema/trabalho dominante compatível",
    "problema dominante compatível",
    "trabalho dominante compatível",
    "conceito-alvo/operação compatível",
    "conceito-alvo compatível",
    "operação compatível",
)
WEAK_ONLY_REASON_MARKERS = (
    "passo-alvo adjacente ao capítulo do argumento",
    "percurso compatível",
    "evidência textual acumulada",
)


class RevisaoArgumentosRestritivaError(RuntimeError):
    """Erro fatal na revisão restritiva de argumentos."""


def build_paths(script_dir: Path) -> Dict[str, Path]:
    arvore_root = script_dir.parent
    dados_dir = arvore_root / "01_dados"
    return {
        "script_dir": script_dir,
        "arvore_root": arvore_root,
        "dados_dir": dados_dir,
        "input_tree": dados_dir / INPUT_TREE_FILENAME,
        "triagem_json": dados_dir / INPUT_TRIAGEM_JSON_FILENAME,
        "triagem_report": dados_dir / INPUT_TRIAGEM_REPORT_FILENAME,
        "report_geracao_argumentos": dados_dir / INPUT_REPORT_GERACAO_ARGUMENTOS,
        "report_validacao_argumentos": dados_dir / INPUT_REPORT_VALIDACAO_ARGUMENTOS,
        "report_revisao_percursos": dados_dir / INPUT_REPORT_REVISAO_PERCURSOS,
        "output_tree": dados_dir / OUTPUT_TREE_FILENAME,
        "output_report": dados_dir / OUTPUT_REPORT_FILENAME,
    }


def ensure_required_files(paths: Dict[str, Path]) -> None:
    required = [
        paths["input_tree"],
        paths["triagem_json"],
        paths["triagem_report"],
        paths["report_geracao_argumentos"],
        paths["report_validacao_argumentos"],
        paths["report_revisao_percursos"],
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RevisaoArgumentosRestritivaError(
            "Faltam ficheiros obrigatórios para a revisão restritiva de argumentos:\n- "
            + "\n- ".join(missing)
        )


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise RevisaoArgumentosRestritivaError(f"Ficheiro não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RevisaoArgumentosRestritivaError(f"JSON inválido em {path}: {exc}") from exc
    except OSError as exc:
        raise RevisaoArgumentosRestritivaError(f"Não foi possível ler {path}: {exc}") from exc


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RevisaoArgumentosRestritivaError(f"Ficheiro não encontrado: {path}") from exc
    except OSError as exc:
        raise RevisaoArgumentosRestritivaError(f"Não foi possível ler {path}: {exc}") from exc


def save_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        temp_path.replace(path)
    except OSError as exc:
        raise RevisaoArgumentosRestritivaError(f"Não foi possível escrever {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as exc:
        raise RevisaoArgumentosRestritivaError(f"Não foi possível escrever o relatório {path}: {exc}") from exc


def unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        value = value.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def safe_list_of_strings(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, list):
        return unique_preserve_order(
            item.strip() for item in value if isinstance(item, str) and item.strip()
        )
    return []


def first_nonempty_string(mapping: Dict[str, Any], keys: Sequence[str]) -> Optional[str]:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def get_first_list_of_strings(mapping: Dict[str, Any], keys: Sequence[str]) -> List[str]:
    for key in keys:
        if key in mapping:
            value = mapping.get(key)
            values = safe_list_of_strings(value)
            if values:
                return values
            if isinstance(value, list):
                return []
    return []


def ramo_sort_key(ramo_id: str) -> Tuple[int, str]:
    match = re.fullmatch(r"RA_(\d+)", ramo_id or "")
    if match:
        return (int(match.group(1)), ramo_id)
    return (10**9, ramo_id or "")


def argumento_sort_key(argumento_id: str) -> Tuple[str, str]:
    return (argumento_id or "", argumento_id or "")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iter_object_graph(obj: Any, trail: str = "raiz") -> Iterable[Tuple[str, Any]]:
    yield trail, obj
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from iter_object_graph(value, f"{trail}.{key}")
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            yield from iter_object_graph(value, f"{trail}[{idx}]")


def looks_like_ramos_list(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    dict_items = [item for item in value if isinstance(item, dict)]
    if len(dict_items) < max(1, len(value) // 2):
        return False
    score = 0
    for item in dict_items[:5]:
        ramo_id = first_nonempty_string(item, ("id", "ramo_id"))
        if ramo_id and RAMO_ID_RE.fullmatch(ramo_id):
            score += 2
        if any(key in item for key in ARGUMENTO_FIELD_CANDIDATES):
            score += 1
        if any(key in item for key in PERCURSO_FIELD_CANDIDATES):
            score += 1
    return score >= 3


def looks_like_argumentos_list(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    dict_items = [item for item in value if isinstance(item, dict)]
    if len(dict_items) < max(1, len(value) // 2):
        return False
    checked = 0
    matched = 0
    for item in dict_items[:10]:
        checked += 1
        item_id = first_nonempty_string(item, ("id",))
        if item_id and item_id.startswith("ARG_"):
            matched += 1
    return checked > 0 and matched >= max(1, checked // 2)


def locate_ramos(tree: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    for key in ("ramos", "nos_ramo", "bloco_ramos"):
        value = tree.get(key)
        if looks_like_ramos_list(value):
            return value, f"raiz.{key}"
    for trail, value in iter_object_graph(tree):
        if trail == "raiz":
            continue
        if looks_like_ramos_list(value):
            return value, trail
    raise RevisaoArgumentosRestritivaError(
        "Não foi possível localizar o bloco de ramos utilizável na árvore."
    )


def locate_argumentos(tree: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    for key in ("argumentos",):
        value = tree.get(key)
        if looks_like_argumentos_list(value):
            return value, f"raiz.{key}"
    for trail, value in iter_object_graph(tree):
        if trail == "raiz":
            continue
        if looks_like_argumentos_list(value):
            return value, trail
    raise RevisaoArgumentosRestritivaError(
        "Não foi possível localizar um bloco de argumentos utilizável na árvore pós-percursos. "
        "Este script exige uma árvore com a camada de argumentos já gerada."
    )


def detect_ramo_argumento_field(ramo: Dict[str, Any]) -> str:
    for key in ARGUMENTO_FIELD_CANDIDATES:
        if key in ramo:
            return key
    return "argumento_ids_associados"


def detect_argumento_ramo_ids_field(argumento: Dict[str, Any]) -> str:
    for key in ARGUMENTO_RAMO_IDS_FIELD_CANDIDATES:
        if key in argumento:
            return key
    return "ramo_ids"


def extract_group_items(triagem_payload: Dict[str, Any], group_key: str) -> Dict[str, Dict[str, Any]]:
    grupos = triagem_payload.get("grupos")
    if not isinstance(grupos, dict):
        raise RevisaoArgumentosRestritivaError(
            "O ficheiro de triagem não contém um bloco 'grupos' utilizável."
        )

    raw_items = grupos.get(group_key)
    if raw_items is None:
        return {}
    if not isinstance(raw_items, list):
        raise RevisaoArgumentosRestritivaError(
            f"O grupo '{group_key}' na triagem não é uma lista."
        )

    result: Dict[str, Dict[str, Any]] = {}
    for idx, item in enumerate(raw_items, start=1):
        if isinstance(item, str):
            ramo_id = item.strip()
            payload = {"ramo_id": ramo_id, "motivos": []}
        elif isinstance(item, dict):
            ramo_id = first_nonempty_string(item, ("ramo_id", "id"))
            payload = item
        else:
            raise RevisaoArgumentosRestritivaError(
                f"Entrada inválida em triagem.{group_key}[{idx}]: esperado dict ou str, obtido {type(item).__name__}."
            )
        if not ramo_id:
            raise RevisaoArgumentosRestritivaError(
                f"Entrada sem ramo_id em triagem.{group_key}[{idx}]."
            )
        result[ramo_id] = payload
    return result


def index_text_mentions_by_ramo(text: str) -> Dict[str, List[str]]:
    mentions: Dict[str, List[str]] = {}
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        ramo_ids = unique_preserve_order(RAMO_ID_RE.findall(line))
        for ramo_id in ramo_ids:
            mentions.setdefault(ramo_id, []).append(line.strip())
    return mentions


def contains_keyword_substrings(lines: Sequence[str], keywords: Sequence[str]) -> bool:
    for line in lines:
        lower = line.lower()
        if any(keyword in lower for keyword in keywords):
            return True
    return False


def collect_triagem_signals(triagem_item: Dict[str, Any]) -> Dict[str, Any]:
    motives = unique_preserve_order(safe_list_of_strings(triagem_item.get("motivos")))
    evidencias = triagem_item.get("evidencias")
    if not isinstance(evidencias, dict):
        evidencias = {}
    return {
        "motivos": motives,
        "factos_estrutura": unique_preserve_order(
            safe_list_of_strings(evidencias.get("factos_estrutura"))
        ),
        "factos_relatorios": unique_preserve_order(
            safe_list_of_strings(evidencias.get("factos_relatorios"))
        ),
        "inferencias_prudentes": unique_preserve_order(
            safe_list_of_strings(evidencias.get("inferencias_prudentes"))
        ),
    }


def parse_generation_argumentos_report(text: str) -> Dict[str, Any]:
    entries_by_ramo: Dict[str, List[Dict[str, Any]]] = {}
    empty_ramos: Set[str] = set()
    in_log = False
    linhas_ra = 0

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Log de associações"):
            in_log = True
            continue
        if in_log and line.startswith("Conclusão final"):
            break
        if not in_log:
            continue

        empty_match = GENERATION_EMPTY_RE.match(line)
        if empty_match:
            ramo_id = empty_match.group(1)
            empty_ramos.add(ramo_id)
            entries_by_ramo.setdefault(ramo_id, [])
            linhas_ra += 1
            continue

        match = GENERATION_LOG_RE.match(line)
        if not match:
            continue
        ramo_id, argumento_id, score_raw, reasons_raw = match.groups()
        reasons = [part.strip() for part in reasons_raw.split(";") if part.strip()]
        entries_by_ramo.setdefault(ramo_id, []).append(
            {
                "argumento_id": argumento_id,
                "score": int(score_raw),
                "reasons": reasons,
                "raw_line": line,
            }
        )
        linhas_ra += 1

    for ramo_id, entries in entries_by_ramo.items():
        deduped: List[Dict[str, Any]] = []
        seen: Set[Tuple[str, int, Tuple[str, ...]]] = set()
        for entry in entries:
            signature = (
                entry["argumento_id"],
                entry["score"],
                tuple(entry["reasons"]),
            )
            if signature in seen:
                continue
            seen.add(signature)
            deduped.append(entry)
        entries_by_ramo[ramo_id] = deduped

    return {
        "entries_by_ramo": entries_by_ramo,
        "empty_ramos": sorted(empty_ramos, key=ramo_sort_key),
        "linhas_ramo_detectadas": linhas_ra,
    }


def parse_validation_argumentos_report(text: str) -> Dict[str, Any]:
    warnings_by_ramo: Dict[str, List[Dict[str, Any]]] = {}
    total_warning_lines = 0
    warning_types_counter: Dict[str, int] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = WARNING_LINE_RE.match(line)
        if not match:
            continue

        ramo_id, target_block, warning_type, description = match.groups()
        warning_type_norm = warning_type.strip().lower()
        total_warning_lines += 1
        warning_types_counter[warning_type_norm] = warning_types_counter.get(warning_type_norm, 0) + 1

        warnings_by_ramo.setdefault(ramo_id, []).append(
            {
                "tipo": warning_type_norm,
                "descricao": description.strip(),
                "argumento_ids": unique_preserve_order(ARGUMENTO_ID_RE.findall(target_block)),
                "texto_bruto": line,
            }
        )

    return {
        "warnings_por_ramo": warnings_by_ramo,
        "total_warning_lines": total_warning_lines,
        "warning_types_counter": warning_types_counter,
    }


def build_argumento_profile(argumento: Dict[str, Any]) -> Dict[str, Any]:
    fundamento = argumento.get("fundamenta")
    if not isinstance(fundamento, dict):
        fundamento = {}

    perfis_percursos = safe_list_of_strings(fundamento.get("percursos"))
    regimes = safe_list_of_strings(fundamento.get("regimes"))

    return {
        "id": first_nonempty_string(argumento, ("id",)) or "",
        "capitulo": first_nonempty_string(argumento, ("capitulo",)) or "",
        "parte": first_nonempty_string(argumento, ("parte",)) or "",
        "conceito_alvo": first_nonempty_string(argumento, ("conceito_alvo",)) or "",
        "tipo_de_necessidade": first_nonempty_string(argumento, ("tipo_de_necessidade",)) or "",
        "nivel_de_operacao": first_nonempty_string(argumento, ("nivel_de_operacao",)) or "",
        "natureza": first_nonempty_string(argumento, ("natureza",)) or "",
        "nivel": argumento.get("nivel") if isinstance(argumento.get("nivel"), int) else None,
        "fundamenta_percursos": perfis_percursos,
        "regimes": regimes,
    }


def best_generation_entries_by_argumento(entries: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    by_arg: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        argumento_id = entry.get("argumento_id")
        if not isinstance(argumento_id, str) or not argumento_id:
            continue
        previous = by_arg.get(argumento_id)
        if previous is None:
            by_arg[argumento_id] = entry
            continue
        prev_score = int(previous.get("score", 0))
        score = int(entry.get("score", 0))
        if score > prev_score:
            by_arg[argumento_id] = entry
            continue
        if score == prev_score and len(entry.get("reasons", [])) > len(previous.get("reasons", [])):
            by_arg[argumento_id] = entry
    return by_arg


def parse_reason_categories(reasons: Sequence[str]) -> Set[str]:
    categories: Set[str] = set()
    for reason in reasons:
        if not isinstance(reason, str):
            continue
        lowered = reason.lower()
        if "passo-alvo fortemente compatível" in lowered:
            categories.add("passo_forte")
        elif "passo-alvo adjacente" in lowered:
            categories.add("passo_adjacente")
        if "percurso compatível" in lowered:
            categories.add("percurso")
        if (
            "problema/trabalho dominante compatível" in lowered
            or "problema dominante compatível" in lowered
            or "trabalho dominante compatível" in lowered
        ):
            categories.add("problema_trabalho")
        if (
            "conceito-alvo/operação compatível" in lowered
            or "conceito-alvo compatível" in lowered
            or "operação compatível" in lowered
        ):
            categories.add("conceito_operacao")
        if "evidência textual acumulada" in lowered:
            categories.add("evidencia_textual")
    return categories


def evaluate_candidate(
    ramo_id: str,
    argumento_id: str,
    ramo_percurso_ids: List[str],
    current_argumento_ids: List[str],
    argumento_profile: Optional[Dict[str, Any]],
    generation_entry: Optional[Dict[str, Any]],
    warnings_for_ramo: List[Dict[str, Any]],
) -> Dict[str, Any]:
    reasons = list(generation_entry.get("reasons", [])) if isinstance(generation_entry, dict) else []
    score = int(generation_entry.get("score", 0)) if isinstance(generation_entry, dict) else 0
    categories = parse_reason_categories(reasons)
    strong_signal_count = sum(
        1 for item in categories if item in {"passo_forte", "problema_trabalho", "conceito_operacao"}
    )
    total_signal_count = len(categories)

    profile = argumento_profile or {
        "id": argumento_id,
        "capitulo": "",
        "parte": "",
        "conceito_alvo": "",
        "tipo_de_necessidade": "",
        "nivel_de_operacao": "",
        "natureza": "",
        "nivel": None,
        "fundamenta_percursos": [],
        "regimes": [],
    }

    percurso_overlap = sorted(
        set(ramo_percurso_ids).intersection(set(profile.get("fundamenta_percursos", [])))
    )
    current_associated = argumento_id in current_argumento_ids

    relevant_warnings: List[Dict[str, Any]] = []
    warning_types: List[str] = []
    explicit_associacao_fraca = False
    heterogeneidade = False
    for warning in warnings_for_ramo:
        warning_ids = safe_list_of_strings(warning.get("argumento_ids"))
        if warning_ids and argumento_id not in warning_ids:
            continue
        relevant_warnings.append(warning)
        warning_type = first_nonempty_string(warning, ("tipo",)) or ""
        if warning_type:
            warning_types.append(warning_type)
        if warning_type == "associacao_fraca":
            explicit_associacao_fraca = True
        if warning_type == "heterogeneidade_excessiva":
            heterogeneidade = True

    depends_only_on_weak_signals = (
        bool(categories)
        and strong_signal_count == 0
        and categories.issubset({"passo_adjacente", "percurso", "evidencia_textual"})
    )

    has_generation_entry = generation_entry is not None
    has_min_structural_base = strong_signal_count >= 1 or bool(percurso_overlap)

    sufficient_for_single = False
    if not explicit_associacao_fraca and not depends_only_on_weak_signals:
        if score >= 4 and has_min_structural_base:
            sufficient_for_single = True
        elif score >= 3 and strong_signal_count >= 1 and total_signal_count >= 3 and bool(percurso_overlap):
            sufficient_for_single = True

    if not has_generation_entry and current_associated:
        # Em caso de associação atual sem rastreio no relatório de geração, não há base automática forte.
        sufficient_for_single = False

    rank = 0
    rank += score * 100
    rank += strong_signal_count * 25
    rank += total_signal_count * 4
    rank += 15 if percurso_overlap else 0
    rank += 8 if current_associated else 0
    rank += 4 if has_generation_entry else 0
    rank -= 120 if explicit_associacao_fraca else 0
    rank -= 20 if heterogeneidade else 0
    rank -= 25 if depends_only_on_weak_signals else 0
    rank -= 10 if not argumento_profile else 0

    factos: List[str] = []
    if has_generation_entry:
        factos.append(f"score_relatorio={score}")
        if reasons:
            factos.append(f"reasons_relatorio={len(reasons)}")
    else:
        factos.append("sem_entrada_no_relatorio_de_geracao")
    if percurso_overlap:
        factos.append(f"percurso_overlap={','.join(percurso_overlap)}")
    if current_associated:
        factos.append("argumento_existia_no_ramo")
    if warning_types:
        factos.append(f"avisos={','.join(unique_preserve_order(warning_types))}")

    inferencias: List[str] = []
    if depends_only_on_weak_signals:
        inferencias.append(
            "A associação depende apenas de sinais fracos (adjacência de capítulo/percurso/evidência textual genérica)."
        )
    if explicit_associacao_fraca:
        inferencias.append(
            "O relatório de validação assinala associação fraca com poucos sinais independentes."
        )
    if not has_generation_entry and current_associated:
        inferencias.append(
            "A associação atual não foi reencontrada com segurança no relatório de geração; não há base prudente para manutenção automática."
        )

    return {
        "argumento_id": argumento_id,
        "score": score,
        "reasons": reasons,
        "reason_categories": sorted(categories),
        "strong_signal_count": strong_signal_count,
        "total_signal_count": total_signal_count,
        "percurso_overlap": percurso_overlap,
        "warning_types": unique_preserve_order(warning_types),
        "explicit_associacao_fraca": explicit_associacao_fraca,
        "heterogeneidade_excessiva": heterogeneidade,
        "depends_only_on_weak_signals": depends_only_on_weak_signals,
        "sufficient_for_single": sufficient_for_single,
        "current_associated": current_associated,
        "has_generation_entry": has_generation_entry,
        "rank": rank,
        "argumento_profile": profile,
        "factos": unique_preserve_order(factos),
        "inferencias": unique_preserve_order(inferencias),
        "warning_descriptions": [w.get("descricao", "") for w in relevant_warnings if isinstance(w.get("descricao"), str)],
    }


def are_pair_compatible(
    first: Dict[str, Any],
    second: Dict[str, Any],
) -> Tuple[bool, List[str], List[str]]:
    profile_a = first["argumento_profile"]
    profile_b = second["argumento_profile"]

    blocking_reasons: List[str] = []
    support_reasons: List[str] = []

    part_a = profile_a.get("parte", "")
    part_b = profile_b.get("parte", "")
    if not part_a or not part_b or part_a != part_b:
        blocking_reasons.append("parte_incompativel")
    else:
        support_reasons.append("mesma_parte")

    nivel_a = profile_a.get("nivel_de_operacao", "")
    nivel_b = profile_b.get("nivel_de_operacao", "")
    if not nivel_a or not nivel_b or nivel_a != nivel_b:
        blocking_reasons.append("nivel_de_operacao_incompativel")
    else:
        support_reasons.append("mesmo_nivel_de_operacao")

    necessidade_a = profile_a.get("tipo_de_necessidade", "")
    necessidade_b = profile_b.get("tipo_de_necessidade", "")
    if not necessidade_a or not necessidade_b or necessidade_a != necessidade_b:
        blocking_reasons.append("tipo_de_necessidade_incompativel")
    else:
        support_reasons.append("mesmo_tipo_de_necessidade")

    percursos_a = set(safe_list_of_strings(profile_a.get("fundamenta_percursos", [])))
    percursos_b = set(safe_list_of_strings(profile_b.get("fundamenta_percursos", [])))
    regimes_a = set(safe_list_of_strings(profile_a.get("regimes", [])))
    regimes_b = set(safe_list_of_strings(profile_b.get("regimes", [])))
    capitulo_a = profile_a.get("capitulo", "")
    capitulo_b = profile_b.get("capitulo", "")

    shared_anchor = False
    if percursos_a and percursos_b and percursos_a.intersection(percursos_b):
        shared_anchor = True
        support_reasons.append("partilham_percurso_fundante")
    elif regimes_a and regimes_b and regimes_a.intersection(regimes_b):
        shared_anchor = True
        support_reasons.append("partilham_regime_fundante")
    elif capitulo_a and capitulo_b and capitulo_a == capitulo_b:
        shared_anchor = True
        support_reasons.append("mesmo_capitulo")
    else:
        blocking_reasons.append("sem_ancoragem_estrutural_partilhada")

    if first.get("explicit_associacao_fraca") or second.get("explicit_associacao_fraca"):
        blocking_reasons.append("um_dos_argumentos_tem_associacao_fraca")

    compatible = not blocking_reasons and shared_anchor
    return compatible, unique_preserve_order(support_reasons), unique_preserve_order(blocking_reasons)


def select_final_argumentos(
    candidate_evaluations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    sorted_candidates = sorted(
        candidate_evaluations,
        key=lambda item: (-item["rank"], -item["score"], item["argumento_id"]),
    )
    viable = [item for item in sorted_candidates if item["sufficient_for_single"]]

    if not viable:
        return {
            "final_ids": [],
            "decision": "removido_totalmente",
            "automatic": True,
            "manual": False,
            "motivos": ["nenhum_argumento_com_suporte_suficiente"],
            "pair_support_reasons": [],
            "pair_blocking_reasons": [],
        }

    if len(viable) == 1:
        return {
            "final_ids": [viable[0]["argumento_id"]],
            "decision": "mantido_1",
            "automatic": True,
            "manual": False,
            "motivos": ["argumento_dominante_unico_com_suporte_suficiente"],
            "pair_support_reasons": [],
            "pair_blocking_reasons": [],
        }

    first = viable[0]
    second = viable[1]
    third = viable[2] if len(viable) >= 3 else None

    compatible, pair_support, pair_blocking = are_pair_compatible(first, second)
    top_gap = first["rank"] - second["rank"]
    second_to_third_gap = second["rank"] - third["rank"] if third is not None else 999
    clear_single_dominance = (
        top_gap >= 20
        or first["score"] > second["score"]
        or (first["strong_signal_count"] > second["strong_signal_count"] and top_gap >= 8)
    )
    overcrowded = third is not None and third["rank"] >= second["rank"] - 5

    if compatible and not overcrowded and second["score"] >= 4:
        return {
            "final_ids": [first["argumento_id"], second["argumento_id"]],
            "decision": "mantido_2_excecional",
            "automatic": True,
            "manual": False,
            "motivos": ["dois_argumentos_estruturalmente_compativeis_com_suporte_forte"],
            "pair_support_reasons": pair_support,
            "pair_blocking_reasons": [],
        }

    if clear_single_dominance:
        return {
            "final_ids": [first["argumento_id"]],
            "decision": "mantido_1",
            "automatic": True,
            "manual": False,
            "motivos": ["argumento_dominante_supera_alternativas"],
            "pair_support_reasons": pair_support if compatible else [],
            "pair_blocking_reasons": pair_blocking if not compatible else [],
        }

    if compatible and overcrowded:
        return {
            "final_ids": [],
            "decision": "revisao_manual_recomendada",
            "automatic": False,
            "manual": True,
            "motivos": ["sobreoferta_de_argumentos_viaveis_sem_reducao_prudente_automatica"],
            "pair_support_reasons": pair_support,
            "pair_blocking_reasons": ["terceiro_argumento_competitivo_impede_excecao_binaria_prudente"],
        }

    return {
        "final_ids": [],
        "decision": "revisao_manual_recomendada",
        "automatic": False,
        "manual": True,
        "motivos": ["empate_ou_concorrencia_sem_dominancia_clara"],
        "pair_support_reasons": pair_support if compatible else [],
        "pair_blocking_reasons": pair_blocking,
    }


def decide_ramo_argumentativo(
    ramo_id: str,
    ramo: Dict[str, Any],
    universe_kind: str,
    triagem_item: Optional[Dict[str, Any]],
    generation_entries: List[Dict[str, Any]],
    generation_empty_ramos: Set[str],
    warnings_for_ramo: List[Dict[str, Any]],
    argumento_profiles: Dict[str, Dict[str, Any]],
    triagem_report_mentions: List[str],
    percursos_review_mentions: List[str],
) -> Dict[str, Any]:
    argumento_field = detect_ramo_argumento_field(ramo)
    current_argumento_ids = get_first_list_of_strings(ramo, ARGUMENTO_FIELD_CANDIDATES)
    current_percurso_ids = get_first_list_of_strings(ramo, PERCURSO_FIELD_CANDIDATES)

    triagem_signals = collect_triagem_signals(triagem_item or {})
    generation_by_arg = best_generation_entries_by_argumento(generation_entries)

    factos: List[str] = [
        f"n_percursos_atuais={len(current_percurso_ids)}",
        f"n_argumentos_anteriores={len(current_argumento_ids)}",
        f"universo={universe_kind}",
    ]
    if current_percurso_ids:
        factos.append(f"percursos_atuais={','.join(current_percurso_ids)}")
    if current_argumento_ids:
        factos.append(f"argumentos_anteriores={','.join(current_argumento_ids)}")

    inferencias_prudentes: List[str] = []
    if triagem_signals["inferencias_prudentes"]:
        inferencias_prudentes.extend(triagem_signals["inferencias_prudentes"])

    if universe_kind == "B_secundario" and not current_percurso_ids:
        return {
            "ramo_id": ramo_id,
            "universo": universe_kind,
            "argumento_field": argumento_field,
            "percurso_ids_atuais": current_percurso_ids,
            "argumento_ids_anteriores": current_argumento_ids,
            "argumento_ids_finais": [],
            "decisao": "removido_totalmente",
            "automatico": True,
            "revisao_manual_recomendada": False,
            "motivos": ["sem_percurso_estabilizado_para_subida_argumentativa"],
            "factos": unique_preserve_order(factos),
            "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
            "candidatos": [],
            "pair_support_reasons": [],
            "pair_blocking_reasons": [],
            "triagem_motivos": triagem_signals["motivos"],
        }

    if universe_kind == "B_secundario" and contains_keyword_substrings(
        percursos_review_mentions, NEGATIVE_PERCURSO_REVIEW_KEYWORDS
    ):
        inferencias_prudentes.append(
            "O relatório de revisão de percursos contém sinais de instabilidade ou revisão manual; a subida argumentativa secundária não foi forçada."
        )
        return {
            "ramo_id": ramo_id,
            "universo": universe_kind,
            "argumento_field": argumento_field,
            "percurso_ids_atuais": current_percurso_ids,
            "argumento_ids_anteriores": current_argumento_ids,
            "argumento_ids_finais": [],
            "decisao": "revisao_manual_recomendada",
            "automatico": False,
            "revisao_manual_recomendada": True,
            "motivos": ["percursos_superiores_ainda_com_sinal_de_instabilidade_local"],
            "factos": unique_preserve_order(factos),
            "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
            "candidatos": [],
            "pair_support_reasons": [],
            "pair_blocking_reasons": [],
            "triagem_motivos": triagem_signals["motivos"],
        }

    candidate_ids = unique_preserve_order(
        list(current_argumento_ids) + list(generation_by_arg.keys())
    )

    if not candidate_ids:
        if ramo_id in generation_empty_ramos:
            factos.append("relatorio_geracao_indica_sem_associacao_suficiente")
        inferencias_prudentes.append(
            "Sem candidatos argumentativos extraíveis com segurança, o ramo fica explicitamente sem argumento."
        )
        return {
            "ramo_id": ramo_id,
            "universo": universe_kind,
            "argumento_field": argumento_field,
            "percurso_ids_atuais": current_percurso_ids,
            "argumento_ids_anteriores": current_argumento_ids,
            "argumento_ids_finais": [],
            "decisao": "removido_totalmente",
            "automatico": True,
            "revisao_manual_recomendada": False,
            "motivos": ["sem_candidatos_argumentativos_suficientes"],
            "factos": unique_preserve_order(factos),
            "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
            "candidatos": [],
            "pair_support_reasons": [],
            "pair_blocking_reasons": [],
            "triagem_motivos": triagem_signals["motivos"],
        }

    candidate_evaluations: List[Dict[str, Any]] = []
    missing_profiles: List[str] = []
    for argumento_id in candidate_ids:
        profile = argumento_profiles.get(argumento_id)
        if profile is None:
            missing_profiles.append(argumento_id)
        evaluation = evaluate_candidate(
            ramo_id=ramo_id,
            argumento_id=argumento_id,
            ramo_percurso_ids=current_percurso_ids,
            current_argumento_ids=current_argumento_ids,
            argumento_profile=profile,
            generation_entry=generation_by_arg.get(argumento_id),
            warnings_for_ramo=warnings_for_ramo,
        )
        candidate_evaluations.append(evaluation)

    if missing_profiles:
        factos.append(f"argumentos_sem_metadado={','.join(sorted(missing_profiles, key=argumento_sort_key))}")

    selection = select_final_argumentos(candidate_evaluations)
    final_ids = selection["final_ids"]
    decision = selection["decision"]

    if decision == "mantido_1" and len(current_argumento_ids) >= 2:
        decision = "reduzido"
    if decision == "mantido_2_excecional" and len(current_argumento_ids) >= 3:
        decision = "reduzido"

    factos.extend(
        unique_preserve_order(
            triagem_signals["factos_estrutura"]
            + [f"triagem_relatorio:{item}" for item in triagem_signals["factos_relatorios"]]
        )
    )
    if triagem_report_mentions:
        factos.append(f"mencoes_no_relatorio_de_triagem={len(triagem_report_mentions)}")
    if percursos_review_mentions:
        factos.append(f"mencoes_no_relatorio_de_percursos={len(percursos_review_mentions)}")

    for candidate in candidate_evaluations:
        inferencias_prudentes.extend(candidate["inferencias"])

    if selection["manual"] and not final_ids:
        inferencias_prudentes.append(
            "Na dúvida, o ramo foi deixado sem argumento e assinalado para revisão manual, em vez de manter associações frouxas."
        )
    elif not final_ids:
        inferencias_prudentes.append(
            "Nenhum argumento passou o crivo restritivo suficiente; o ramo fica explicitamente sem argumento."
        )

    detail_candidates: List[Dict[str, Any]] = []
    for candidate in sorted(candidate_evaluations, key=lambda item: (-item["rank"], -item["score"], item["argumento_id"])):
        detail_candidates.append(
            {
                "argumento_id": candidate["argumento_id"],
                "score": candidate["score"],
                "rank": candidate["rank"],
                "reason_categories": candidate["reason_categories"],
                "reasons": candidate["reasons"],
                "warning_types": candidate["warning_types"],
                "sufficient_for_single": candidate["sufficient_for_single"],
                "current_associated": candidate["current_associated"],
                "percurso_overlap": candidate["percurso_overlap"],
                "factos": candidate["factos"],
            }
        )

    return {
        "ramo_id": ramo_id,
        "universo": universe_kind,
        "argumento_field": argumento_field,
        "percurso_ids_atuais": current_percurso_ids,
        "argumento_ids_anteriores": current_argumento_ids,
        "argumento_ids_finais": final_ids,
        "decisao": decision,
        "automatico": selection["automatic"],
        "revisao_manual_recomendada": selection["manual"],
        "motivos": unique_preserve_order(selection["motivos"]),
        "factos": unique_preserve_order(factos),
        "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
        "candidatos": detail_candidates,
        "pair_support_reasons": selection["pair_support_reasons"],
        "pair_blocking_reasons": selection["pair_blocking_reasons"],
        "triagem_motivos": triagem_signals["motivos"],
    }


def sync_argumento_reverse_links(
    argumentos: List[Dict[str, Any]],
    decisions_by_ramo: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    touched: Set[str] = set()

    for argumento in argumentos:
        if not isinstance(argumento, dict):
            continue
        argumento_id = first_nonempty_string(argumento, ("id",))
        if not argumento_id:
            continue

        field = detect_argumento_ramo_ids_field(argumento)
        ramo_ids = get_first_list_of_strings(argumento, ARGUMENTO_RAMO_IDS_FIELD_CANDIDATES)
        new_ramo_ids = list(ramo_ids)
        changed = False

        for ramo_id, decision in decisions_by_ramo.items():
            should_have = argumento_id in decision["argumento_ids_finais"]
            currently_has = ramo_id in new_ramo_ids
            if should_have and not currently_has:
                new_ramo_ids.append(ramo_id)
                changed = True
            elif not should_have and currently_has:
                new_ramo_ids = [item for item in new_ramo_ids if item != ramo_id]
                changed = True

        if changed:
            ordered = unique_preserve_order(new_ramo_ids)
            argumento[field] = ordered
            if field != "ramo_ids":
                argumento["ramo_ids"] = list(ordered)
            if "ramo_ids_associados" in argumento:
                argumento["ramo_ids_associados"] = list(ordered)
            touched.add(argumento_id)

    return {
        "reverse_links_updated": True,
        "argumentos_tocados": sorted(touched, key=argumento_sort_key),
        "nota": "Sincronização local argumento->ramo aplicada apenas para os ramos revistos nesta fase.",
    }


def build_report_text(
    payload: Dict[str, Any],
    ramos_location: str,
    argumentos_location: str,
) -> str:
    metadata = payload["metadata"]
    resumo = payload["resumo"]
    details = payload["detalhe_ramos"]
    criteria = payload["criterios_aplicados"]

    lines: List[str] = []
    lines.append("RELATÓRIO DE REVISÃO RESTRITIVA DE ARGUMENTOS V1")
    lines.append("=" * 72)
    lines.append(f"Data/hora UTC: {metadata['timestamp_utc']}")
    lines.append(f"Script: {metadata['script']}")
    lines.append(f"Bloco de ramos localizado em: {ramos_location}")
    lines.append(f"Bloco de argumentos localizado em: {argumentos_location}")
    lines.append("")

    lines.append("Ficheiros lidos")
    lines.append("-" * 72)
    for key, value in metadata["ficheiros_lidos"].items():
        lines.append(f"{key}: {value}")
    lines.append("")

    lines.append("Ficheiros escritos")
    lines.append("-" * 72)
    for key, value in metadata["ficheiros_escritos"].items():
        lines.append(f"{key}: {value}")
    lines.append("")

    lines.append("Resumo quantitativo")
    lines.append("-" * 72)
    lines.append(f"Total de ramos revistos: {resumo['ramos_revistos']}")
    lines.append(f"Ramos finais com 1 argumento: {resumo['com_1_argumento']}")
    lines.append(f"Ramos finais com 2 argumentos: {resumo['com_2_argumentos']}")
    lines.append(f"Ramos finais sem argumento: {resumo['sem_argumento']}")
    lines.append(f"Reduções de 3+ para 1 ou 2: {resumo['reduzidos_de_3_ou_mais']}")
    lines.append(f"Revisão manual recomendada: {resumo['revisao_manual_recomendada']}")
    lines.append(f"Não decididos automaticamente: {resumo['nao_decididos_automaticamente']}")
    lines.append(f"Universo primário A revisto: {resumo['universo_A_revistos']}")
    lines.append(f"Universo secundário B revisto: {resumo['universo_B_secundario_revistos']}")
    lines.append("")

    lines.append("Critérios aplicados")
    lines.append("-" * 72)
    lines.append(f"Regra dominante: {criteria['regra_dominante']}")
    lines.append(f"Regra restritiva: {criteria['regra_restritiva']}")
    lines.append(f"Limite da decisão automática: {criteria['limite_decisao_automatica']}")
    lines.append("Heurística transparente usada:")
    for item in criteria["heuristicas"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("Listagem detalhada por ramo")
    lines.append("-" * 72)
    if not details:
        lines.append("Nenhum ramo foi revisto nesta execução.")
    for item in details:
        lines.append(
            f"{item['ramo_id']} | universo={item['universo']} | "
            f"percursos={','.join(item['percurso_ids_atuais']) if item['percurso_ids_atuais'] else '∅'} | "
            f"anteriores={','.join(item['argumento_ids_anteriores']) if item['argumento_ids_anteriores'] else '∅'} | "
            f"finais={','.join(item['argumento_ids_finais']) if item['argumento_ids_finais'] else '∅'} | "
            f"decisão={item['decisao']}"
        )
        if item["motivos"]:
            lines.append(f"  motivos: {', '.join(item['motivos'])}")
        triagem_motivos = item.get("triagem_motivos", [])
        if triagem_motivos:
            lines.append(f"  triagem_motivos: {', '.join(triagem_motivos)}")
        if item["pair_support_reasons"]:
            lines.append(f"  fundamentos_do_par_excecional: {', '.join(item['pair_support_reasons'])}")
        if item["pair_blocking_reasons"]:
            lines.append(f"  bloqueios_da_decisao_binaria: {', '.join(item['pair_blocking_reasons'])}")
        if item["factos"]:
            lines.append(f"  factos: {' | '.join(item['factos'])}")
        if item["inferencias_prudentes"]:
            lines.append(f"  inferências_prudentes: {' | '.join(item['inferencias_prudentes'])}")
        if item["revisao_manual_recomendada"]:
            lines.append("  revisão_manual_recomendada: sim")
        if item["candidatos"]:
            lines.append("  candidatos_avaliados:")
            for candidate in item["candidatos"]:
                lines.append(
                    f"    - {candidate['argumento_id']} | score={candidate['score']} | rank={candidate['rank']} | "
                    f"suficiente={candidate['sufficient_for_single']} | aviso={','.join(candidate['warning_types']) if candidate['warning_types'] else '∅'}"
                )
                if candidate["reason_categories"]:
                    lines.append(f"      categorias: {', '.join(candidate['reason_categories'])}")
                if candidate["percurso_overlap"]:
                    lines.append(f"      percurso_overlap: {', '.join(candidate['percurso_overlap'])}")
                if candidate["reasons"]:
                    lines.append(f"      reasons: {'; '.join(candidate['reasons'])}")
        lines.append("")

    lines.append("Observações finais")
    lines.append("-" * 72)
    lines.append(
        "Zona superior suficientemente fechada após a revisão restritiva de argumentos: "
        + ("sim" if payload["observacoes_finais"]["zona_superior_suficientemente_fechada"] else "não")
    )
    lines.append(
        "Ramos que ainda exigem atenção manual antes da fase seguinte: "
        + (
            ", ".join(payload["observacoes_finais"]["ramos_com_atencao_manual"])
            if payload["observacoes_finais"]["ramos_com_atencao_manual"]
            else "nenhum"
        )
    )
    lines.append(payload["observacoes_finais"]["nota"])
    lines.append(payload["observacoes_finais"]["nota_reverse_links"])
    lines.append(
        "Limitação de escopo: este script estabiliza a zona superior ramo→argumento e sincroniza argumento→ramo; não recalcula propagação descendente para microlinhas/fragmentos."
    )
    lines.append("")

    return "\n".join(lines)


def terminal_summary(payload: Dict[str, Any], output_tree: Path, output_report: Path) -> str:
    resumo = payload["resumo"]
    return "\n".join(
        [
            f"Ramos revistos: {resumo['ramos_revistos']}",
            f"Com 1 argumento: {resumo['com_1_argumento']}",
            f"Com 2 argumentos: {resumo['com_2_argumentos']}",
            f"Sem argumento: {resumo['sem_argumento']}",
            f"Revisão manual: {resumo['revisao_manual_recomendada']}",
            f"Árvore escrita em: {output_tree}",
            f"Relatório escrito em: {output_report}",
        ]
    )


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    paths = build_paths(script_dir)
    ensure_required_files(paths)

    tree = load_json(paths["input_tree"])
    if not isinstance(tree, dict):
        raise RevisaoArgumentosRestritivaError(
            "O ficheiro da árvore pós-percursos tem de ser um objeto JSON no topo."
        )
    triagem = load_json(paths["triagem_json"])
    if not isinstance(triagem, dict):
        raise RevisaoArgumentosRestritivaError(
            "O ficheiro de triagem tem de ser um objeto JSON no topo."
        )

    triagem_report_text = load_text(paths["triagem_report"])
    geracao_argumentos_text = load_text(paths["report_geracao_argumentos"])
    validacao_argumentos_text = load_text(paths["report_validacao_argumentos"])
    revisao_percursos_text = load_text(paths["report_revisao_percursos"])

    ramos, ramos_location = locate_ramos(tree)
    argumentos, argumentos_location = locate_argumentos(tree)
    if not ramos:
        raise RevisaoArgumentosRestritivaError("O bloco de ramos foi localizado, mas está vazio.")
    if not argumentos:
        raise RevisaoArgumentosRestritivaError("O bloco de argumentos foi localizado, mas está vazio.")

    ramo_map: Dict[str, Dict[str, Any]] = {}
    for idx, ramo in enumerate(ramos, start=1):
        if not isinstance(ramo, dict):
            raise RevisaoArgumentosRestritivaError(
                f"Elemento inválido em ramos[{idx}]: esperado dict, obtido {type(ramo).__name__}."
            )
        ramo_id = first_nonempty_string(ramo, ("id", "ramo_id"))
        if not ramo_id:
            raise RevisaoArgumentosRestritivaError(f"Falta 'id' utilizável em ramos[{idx}].")
        ramo_map[ramo_id] = ramo

    argumento_profiles: Dict[str, Dict[str, Any]] = {}
    for idx, argumento in enumerate(argumentos, start=1):
        if not isinstance(argumento, dict):
            raise RevisaoArgumentosRestritivaError(
                f"Elemento inválido em argumentos[{idx}]: esperado dict, obtido {type(argumento).__name__}."
            )
        argumento_id = first_nonempty_string(argumento, ("id",))
        if not argumento_id:
            raise RevisaoArgumentosRestritivaError(f"Falta 'id' utilizável em argumentos[{idx}].")
        argumento_profiles[argumento_id] = build_argumento_profile(argumento)

    group_a = extract_group_items(triagem, "A_rever_argumento")
    group_b = extract_group_items(triagem, "B_rever_percurso_e_depois_argumento")
    _group_c = extract_group_items(triagem, "C_sem_subida_nesta_ronda")
    _group_d = extract_group_items(triagem, "D_fora_do_ambito_desta_ronda")

    missing_in_tree = [ramo_id for ramo_id in list(group_a.keys()) + list(group_b.keys()) if ramo_id not in ramo_map]
    if missing_in_tree:
        raise RevisaoArgumentosRestritivaError(
            "A triagem refere ramos inexistentes na árvore pós-percursos:\n- "
            + "\n- ".join(sorted(unique_preserve_order(missing_in_tree), key=ramo_sort_key))
        )

    parsed_generation = parse_generation_argumentos_report(geracao_argumentos_text)
    parsed_validation = parse_validation_argumentos_report(validacao_argumentos_text)
    triagem_mentions = index_text_mentions_by_ramo(triagem_report_text)
    percursos_review_mentions = index_text_mentions_by_ramo(revisao_percursos_text)

    universe_order: List[Tuple[str, str]] = []
    for ramo_id in sorted(group_a.keys(), key=ramo_sort_key):
        universe_order.append((ramo_id, "A_principal"))

    secondary_b_excluded: List[str] = []
    for ramo_id in sorted(group_b.keys(), key=ramo_sort_key):
        ramo = ramo_map[ramo_id]
        percurso_ids = get_first_list_of_strings(ramo, PERCURSO_FIELD_CANDIDATES)
        argumento_ids = get_first_list_of_strings(ramo, ARGUMENTO_FIELD_CANDIDATES)
        mentions = percursos_review_mentions.get(ramo_id, [])
        if percurso_ids and not argumento_ids and not contains_keyword_substrings(mentions, NEGATIVE_PERCURSO_REVIEW_KEYWORDS):
            universe_order.append((ramo_id, "B_secundario"))
        else:
            secondary_b_excluded.append(ramo_id)

    seen_ramos: Set[str] = set()
    decisions: List[Dict[str, Any]] = []
    decisions_by_ramo: Dict[str, Dict[str, Any]] = {}

    for ramo_id, universe_kind in universe_order:
        if ramo_id in seen_ramos:
            continue
        seen_ramos.add(ramo_id)
        triagem_item = group_a.get(ramo_id) or group_b.get(ramo_id)
        decision = decide_ramo_argumentativo(
            ramo_id=ramo_id,
            ramo=ramo_map[ramo_id],
            universe_kind=universe_kind,
            triagem_item=triagem_item,
            generation_entries=parsed_generation["entries_by_ramo"].get(ramo_id, []),
            generation_empty_ramos=set(parsed_generation["empty_ramos"]),
            warnings_for_ramo=parsed_validation["warnings_por_ramo"].get(ramo_id, []),
            argumento_profiles=argumento_profiles,
            triagem_report_mentions=triagem_mentions.get(ramo_id, []),
            percursos_review_mentions=percursos_review_mentions.get(ramo_id, []),
        )
        decisions.append(decision)
        decisions_by_ramo[ramo_id] = decision

    for decision in decisions:
        ramo = ramo_map[decision["ramo_id"]]
        field = decision["argumento_field"]
        ramo[field] = list(decision["argumento_ids_finais"])
        if field != "argumento_ids_associados":
            ramo["argumento_ids_associados"] = list(decision["argumento_ids_finais"])

    reverse_sync = sync_argumento_reverse_links(argumentos, decisions_by_ramo)

    com_1 = sum(1 for item in decisions if len(item["argumento_ids_finais"]) == 1)
    com_2 = sum(1 for item in decisions if len(item["argumento_ids_finais"]) == 2)
    sem_argumento = sum(1 for item in decisions if len(item["argumento_ids_finais"]) == 0)
    revisao_manual = sum(1 for item in decisions if item["revisao_manual_recomendada"])
    nao_automaticos = sum(1 for item in decisions if not item["automatico"])
    reduzidos_de_3 = sum(
        1
        for item in decisions
        if len(item["argumento_ids_anteriores"]) >= 3 and len(item["argumento_ids_finais"]) in {1, 2}
    )
    universo_a_revistos = sum(1 for item in decisions if item["universo"] == "A_principal")
    universo_b_revistos = sum(1 for item in decisions if item["universo"] == "B_secundario")

    observacoes_finais = {
        "zona_superior_suficientemente_fechada": revisao_manual == 0 and nao_automaticos == 0,
        "ramos_com_atencao_manual": sorted(
            [item["ramo_id"] for item in decisions if item["revisao_manual_recomendada"]],
            key=ramo_sort_key,
        ),
        "nota": (
            "A zona superior só é considerada suficientemente fechada quando nenhum ramo revisto permanece dependente de revisão manual e nenhum ramo fica com mais de dois argumentos."
        ),
        "nota_reverse_links": reverse_sync["nota"],
    }

    payload = {
        "metadata": {
            "script": "rever_argumentos_restritivo_v1.py",
            "timestamp_utc": utc_now_iso(),
            "ficheiros_lidos": {
                "arvore_pos_percursos": str(paths["input_tree"]),
                "triagem_json": str(paths["triagem_json"]),
                "triagem_report": str(paths["triagem_report"]),
                "relatorio_geracao_argumentos": str(paths["report_geracao_argumentos"]),
                "relatorio_validacao_argumentos": str(paths["report_validacao_argumentos"]),
                "relatorio_revisao_percursos": str(paths["report_revisao_percursos"]),
            },
            "ficheiros_escritos": {
                "arvore_fecho_superior": str(paths["output_tree"]),
                "relatorio_revisao_argumentos": str(paths["output_report"]),
            },
            "universo_alvo": {
                "grupo_A": sorted(group_a.keys(), key=ramo_sort_key),
                "grupo_B_secundario_incluido": sorted(
                    [ramo_id for ramo_id, kind in universe_order if kind == "B_secundario"],
                    key=ramo_sort_key,
                ),
                "grupo_B_secundario_excluido": sorted(unique_preserve_order(secondary_b_excluded), key=ramo_sort_key),
            },
            "validacao_warning_types": parsed_validation["warning_types_counter"],
        },
        "criterios_aplicados": {
            "regra_dominante": "Função estrutural dominante do ramo, lida de modo prudente pela compatibilidade entre percurso estabilizado, suporte do relatório de geração e metadados estruturais do argumento.",
            "regra_restritiva": "Por defeito, manter no máximo 1 argumento; admitir 2 apenas em caso excecional, com forte suporte e compatibilidade estrutural explícita. Na dúvida, não subir.",
            "limite_decisao_automatica": "Associação automática apenas quando o argumento tem score e sinais independentes suficientes, sem depender apenas de percurso/capítulo/evidência textual genérica e sem aviso de associação fraca.",
            "heuristicas": [
                "Grupo A é o universo principal da revisão restritiva.",
                "Grupo B só entra secundariamente quando ficou com percurso estabilizado e ainda sem argumento.",
                "Candidatos com aviso explícito de associação fraca são excluídos da manutenção automática.",
                "Candidatos assentes apenas em adjacência de capítulo, percurso compatível e evidência textual genérica são removidos por insuficiência semântica.",
                "Dois argumentos só sobrevivem juntos quando partilham parte, nível de operação, tipo de necessidade e uma âncora estrutural comum (capítulo, percurso fundante ou regime).",
                "Quando há empate ou sobreoferta sem dominância clara, o ramo fica sem argumento e é assinalado para revisão manual.",
            ],
        },
        "resumo": {
            "ramos_revistos": len(decisions),
            "com_1_argumento": com_1,
            "com_2_argumentos": com_2,
            "sem_argumento": sem_argumento,
            "reduzidos_de_3_ou_mais": reduzidos_de_3,
            "revisao_manual_recomendada": revisao_manual,
            "nao_decididos_automaticamente": nao_automaticos,
            "universo_A_revistos": universo_a_revistos,
            "universo_B_secundario_revistos": universo_b_revistos,
        },
        "detalhe_ramos": decisions,
        "observacoes_finais": observacoes_finais,
        "reverse_sync": reverse_sync,
    }

    report_text = build_report_text(payload, ramos_location, argumentos_location)
    save_json_atomic(paths["output_tree"], tree)
    write_text(paths["output_report"], report_text)

    print(terminal_summary(payload, paths["output_tree"], paths["output_report"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RevisaoArgumentosRestritivaError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)
