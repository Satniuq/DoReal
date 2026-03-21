# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

INPUT_TREE_FILENAME = "arvore_do_pensamento_v1.json"
INPUT_TRIAGEM_JSON_FILENAME = "triagem_fecho_superior_v1.json"
INPUT_TRIAGEM_REPORT_FILENAME = "relatorio_triagem_fecho_superior_v1.txt"
INPUT_REPORT_GERACAO_PERCURSOS = "relatorio_geracao_percursos_v1.txt"
INPUT_REPORT_VALIDACAO_PERCURSOS = "relatorio_validacao_percursos_v1.txt"

OUTPUT_TREE_FILENAME = "arvore_do_pensamento_v1_pos_percursos.json"
OUTPUT_REPORT_FILENAME = "relatorio_revisao_percursos_superiores_v1.txt"

RAMO_ID_RE = re.compile(r"\b(RA_\d{4})\b")
PERCURSO_ID_RE = re.compile(r"\b(P_[A-Z0-9_]+)\b")
GENERATION_LOG_RE = re.compile(
    r"^(RA_\d{4})\s*->\s*(P_[A-Z0-9_]+)\s*\|\s*score=(\d+)\s*\|\s*(.*)$"
)
GENERATION_EMPTY_RE = re.compile(r"^(RA_\d{4})\s*->\s*sem associação suficiente\s*$", re.IGNORECASE)

NEGATIVE_TEXT_KEYWORDS = (
    "aviso",
    "fragil",
    "frágil",
    "insuficien",
    "incoer",
    "incompat",
    "anomalia",
    "manual",
    "divergen",
    "fraca",
    "fraco",
    "sem base",
    "na duvida",
    "na dúvida",
)

PERCURSO_FIELD_CANDIDATES = (
    "percurso_ids_associados",
    "percurso_ids",
    "percursos_associados",
    "percursos_ids",
)
RAMO_IDS_FIELD_CANDIDATES = (
    "ramo_ids",
    "ramo_ids_associados",
)

STRONG_STRUCTURAL_REASON_PREFIXES = (
    "zona dominante coincidente",
    "problema dominante compatível",
    "trabalho dominante compatível",
    "tipo de utilidade compatível",
    "efeito no mapa compatível",
)
ADDITIONAL_REASON_PREFIXES = (
    "passos-alvo compatíveis",
    "passos-alvo adjacentes à faixa do percurso",
)

BENIGN_B_MOTIVES = {
    "tem_percurso_sem_argumento",
}


class RevisaoPercursosSuperioresError(RuntimeError):
    """Erro fatal na revisão de percursos superiores."""


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
        "report_geracao_percursos": dados_dir / INPUT_REPORT_GERACAO_PERCURSOS,
        "report_validacao_percursos": dados_dir / INPUT_REPORT_VALIDACAO_PERCURSOS,
        "output_tree": dados_dir / OUTPUT_TREE_FILENAME,
        "output_report": dados_dir / OUTPUT_REPORT_FILENAME,
    }


def ensure_required_files(paths: Dict[str, Path]) -> None:
    required = [
        paths["input_tree"],
        paths["triagem_json"],
        paths["triagem_report"],
        paths["report_geracao_percursos"],
        paths["report_validacao_percursos"],
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RevisaoPercursosSuperioresError(
            "Faltam ficheiros obrigatórios para a revisão de percursos superiores:\n- "
            + "\n- ".join(missing)
        )


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise RevisaoPercursosSuperioresError(f"Ficheiro não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RevisaoPercursosSuperioresError(f"JSON inválido em {path}: {exc}") from exc
    except OSError as exc:
        raise RevisaoPercursosSuperioresError(f"Não foi possível ler {path}: {exc}") from exc


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RevisaoPercursosSuperioresError(f"Ficheiro não encontrado: {path}") from exc
    except OSError as exc:
        raise RevisaoPercursosSuperioresError(f"Não foi possível ler {path}: {exc}") from exc


def save_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        temp_path.replace(path)
    except OSError as exc:
        raise RevisaoPercursosSuperioresError(f"Não foi possível escrever {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as exc:
        raise RevisaoPercursosSuperioresError(f"Não foi possível escrever o relatório {path}: {exc}") from exc


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
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
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
        if "microlinha_ids" in item:
            score += 1
        if any(key in item for key in PERCURSO_FIELD_CANDIDATES):
            score += 1
    return score >= 3


def looks_like_section_list(value: Any, id_prefix: str) -> bool:
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
        if item_id and item_id.startswith(id_prefix):
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
    raise RevisaoPercursosSuperioresError(
        "Não foi possível localizar o bloco de ramos utilizável na árvore. "
        "Este script exige uma árvore com a camada de ramos já gerada."
    )


def locate_optional_section(tree: Dict[str, Any], preferred_keys: Sequence[str], id_prefix: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    for key in preferred_keys:
        value = tree.get(key)
        if looks_like_section_list(value, id_prefix=id_prefix):
            return value, f"raiz.{key}"
    for trail, value in iter_object_graph(tree):
        if trail == "raiz":
            continue
        if looks_like_section_list(value, id_prefix=id_prefix):
            return value, trail
    return [], None


def build_reverse_ramo_index(section_items: List[Dict[str, Any]], ramo_id_keys: Sequence[str]) -> Dict[str, List[str]]:
    reverse: Dict[str, List[str]] = {}
    for item in section_items:
        item_id = first_nonempty_string(item, ("id",))
        if not item_id:
            continue
        ramo_ids = get_first_list_of_strings(item, ramo_id_keys)
        for ramo_id in ramo_ids:
            reverse.setdefault(ramo_id, []).append(item_id)
    for ramo_id, values in reverse.items():
        reverse[ramo_id] = unique_preserve_order(values)
    return reverse


def detect_ramo_percurso_field(ramo: Dict[str, Any]) -> str:
    for key in PERCURSO_FIELD_CANDIDATES:
        if key in ramo:
            return key
    return "percurso_ids_associados"


def detect_percurso_ramo_ids_field(percurso: Dict[str, Any]) -> str:
    for key in RAMO_IDS_FIELD_CANDIDATES:
        if key in percurso:
            return key
    return "ramo_ids"


def extract_group_items(triagem_payload: Dict[str, Any], group_key: str) -> Dict[str, Dict[str, Any]]:
    grupos = triagem_payload.get("grupos")
    if not isinstance(grupos, dict):
        raise RevisaoPercursosSuperioresError("O ficheiro de triagem não contém um bloco 'grupos' utilizável.")

    raw_items = grupos.get(group_key)
    if raw_items is None:
        return {}
    if not isinstance(raw_items, list):
        raise RevisaoPercursosSuperioresError(
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
            raise RevisaoPercursosSuperioresError(
                f"Entrada inválida em triagem.{group_key}[{idx}]: esperado dict ou str, obtido {type(item).__name__}."
            )
        if not ramo_id:
            raise RevisaoPercursosSuperioresError(
                f"Entrada sem ramo_id em triagem.{group_key}[{idx}]."
            )
        result[ramo_id] = payload
    return result


def extract_triagem_queue(triagem_payload: Dict[str, Any], key: str) -> List[str]:
    fila = triagem_payload.get("fila_operacional")
    if not isinstance(fila, dict):
        return []
    return unique_preserve_order(safe_list_of_strings(fila.get(key)))


def parse_generation_percursos_report(text: str) -> Dict[str, Any]:
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
        ramo_id, percurso_id, score_raw, reasons_raw = match.groups()
        reasons = [part.strip() for part in reasons_raw.split(";") if part.strip()]
        entries_by_ramo.setdefault(ramo_id, []).append(
            {
                "percurso_id": percurso_id,
                "score": int(score_raw),
                "reasons": reasons,
                "raw_line": line,
            }
        )
        linhas_ra += 1

    for ramo_id, entries in entries_by_ramo.items():
        unique_entries: List[Dict[str, Any]] = []
        seen: Set[Tuple[str, int, Tuple[str, ...]]] = set()
        for entry in entries:
            signature = (
                entry["percurso_id"],
                entry["score"],
                tuple(entry["reasons"]),
            )
            if signature in seen:
                continue
            seen.add(signature)
            unique_entries.append(entry)
        entries_by_ramo[ramo_id] = unique_entries

    return {
        "entries_by_ramo": entries_by_ramo,
        "empty_ramos": sorted(empty_ramos, key=ramo_sort_key),
        "linhas_ramo_detectadas": linhas_ra,
    }


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


def contains_negative_keyword(lines: Sequence[str]) -> bool:
    for line in lines:
        lower = line.lower()
        if any(keyword in lower for keyword in NEGATIVE_TEXT_KEYWORDS):
            return True
    return False


def collect_triagem_signals(triagem_item: Dict[str, Any]) -> Dict[str, Any]:
    motives = unique_preserve_order(safe_list_of_strings(triagem_item.get("motivos")))
    evidencias = triagem_item.get("evidencias")
    if not isinstance(evidencias, dict):
        evidencias = {}

    factos_estrutura = unique_preserve_order(
        safe_list_of_strings(evidencias.get("factos_estrutura"))
    )
    factos_relatorios = unique_preserve_order(
        safe_list_of_strings(evidencias.get("factos_relatorios"))
    )
    inferencias_prudentes = unique_preserve_order(
        safe_list_of_strings(evidencias.get("inferencias_prudentes"))
    )

    return {
        "motivos": motives,
        "factos_estrutura": factos_estrutura,
        "factos_relatorios": factos_relatorios,
        "inferencias_prudentes": inferencias_prudentes,
    }


def evaluate_generation_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    reasons = entry.get("reasons", [])
    score = int(entry.get("score", 0))

    def has_prefix(prefixes: Sequence[str]) -> bool:
        for reason in reasons:
            if not isinstance(reason, str):
                continue
            for prefix in prefixes:
                if reason.startswith(prefix):
                    return True
        return False

    return {
        "score": score,
        "has_strong_structural_anchor": has_prefix(STRONG_STRUCTURAL_REASON_PREFIXES),
        "has_additional_anchor": has_prefix(ADDITIONAL_REASON_PREFIXES),
        "reasons": reasons,
    }


def decide_group_b_ramo(
    ramo_id: str,
    ramo: Dict[str, Any],
    triagem_item: Dict[str, Any],
    generation_entries: List[Dict[str, Any]],
    generation_empty_ramos: Set[str],
    triagem_report_mentions: List[str],
    validacao_report_mentions: List[str],
) -> Dict[str, Any]:
    percurso_field = detect_ramo_percurso_field(ramo)
    previous_percurso_ids = get_first_list_of_strings(ramo, PERCURSO_FIELD_CANDIDATES)
    triagem_signals = collect_triagem_signals(triagem_item)

    evidencias_facto: List[str] = [
        f"percurso_ids_anteriores={','.join(previous_percurso_ids) if previous_percurso_ids else '∅'}",
        f"n_percursos_anteriores={len(previous_percurso_ids)}",
    ]
    inferencias_prudentes: List[str] = []
    motivos: List[str] = []

    triagem_extra_motives = [
        motive for motive in triagem_signals["motivos"] if motive not in BENIGN_B_MOTIVES
    ]
    has_negative_text = contains_negative_keyword(triagem_report_mentions + validacao_report_mentions)

    if triagem_extra_motives:
        motivos.extend(triagem_extra_motives)
        evidencias_facto.append("triagem_com_motivos_adicionais_ao_grupo_B")
    if triagem_signals["factos_relatorios"]:
        evidencias_facto.extend(
            f"triagem_facto_relatorio:{item}" for item in triagem_signals["factos_relatorios"]
        )
    if triagem_signals["inferencias_prudentes"]:
        inferencias_prudentes.extend(triagem_signals["inferencias_prudentes"])
    if has_negative_text:
        motivos.append("sinais_textuais_negativos")
        evidencias_facto.append("menções_textuais_com_keywords_negativas")

    if ramo_id in generation_empty_ramos:
        motivos.append("relatorio_geracao_sem_associacao_suficiente")
        evidencias_facto.append("relatorio_geracao_indica_sem_associacao_suficiente")

    unique_generation_ids = unique_preserve_order(
        entry["percurso_id"] for entry in generation_entries if entry.get("percurso_id")
    )

    if not previous_percurso_ids:
        final_percurso_ids: List[str] = []
        decision = "sem percurso nesta fase"
        automatic = True
        manual = bool(triagem_extra_motives or triagem_signals["inferencias_prudentes"])
        motivos.insert(0, "grupo_B_sem_percurso_na_estrutura")
        inferencias_prudentes.append(
            "O ramo apareceu no Grupo B mas a estrutura atual já não expõe percurso associado; manteve-se vazio por prudência."
        )
        return {
            "ramo_id": ramo_id,
            "percurso_field": percurso_field,
            "percurso_ids_anteriores": previous_percurso_ids,
            "percurso_ids_finais": final_percurso_ids,
            "decisao": decision,
            "automatico": automatic,
            "revisao_manual_recomendada": manual,
            "motivos": unique_preserve_order(motivos or ["sem_percurso_nesta_fase"]),
            "evidencias_facto": unique_preserve_order(evidencias_facto),
            "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
            "score_relatorio": None,
            "reasons_relatorio": [],
            "triagem_motivos": triagem_signals["motivos"],
            "triagem_report_mentions": triagem_report_mentions,
            "validacao_report_mentions": validacao_report_mentions,
        }

    if len(previous_percurso_ids) > 1:
        if len(unique_generation_ids) == 1 and unique_generation_ids[0] in previous_percurso_ids:
            entry = next(
                (item for item in generation_entries if item.get("percurso_id") == unique_generation_ids[0]),
                None,
            )
            eval_entry = evaluate_generation_entry(entry) if entry else None
            if entry and not triagem_extra_motives and not has_negative_text and (
                eval_entry["score"] >= 4
                or (
                    eval_entry["score"] == 3
                    and eval_entry["has_strong_structural_anchor"]
                    and eval_entry["has_additional_anchor"]
                )
            ):
                final_percurso_ids = [unique_generation_ids[0]]
                decision = "confirmado"
                automatic = True
                manual = False
                motivos.insert(0, "anomalia_multiplos_percursos_reduzida_com_base_textual_clara")
                evidencias_facto.append(f"score_relatorio={eval_entry['score']}")
                return {
                    "ramo_id": ramo_id,
                    "percurso_field": percurso_field,
                    "percurso_ids_anteriores": previous_percurso_ids,
                    "percurso_ids_finais": final_percurso_ids,
                    "decisao": decision,
                    "automatico": automatic,
                    "revisao_manual_recomendada": manual,
                    "motivos": unique_preserve_order(motivos),
                    "evidencias_facto": unique_preserve_order(evidencias_facto),
                    "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
                    "score_relatorio": eval_entry["score"],
                    "reasons_relatorio": eval_entry["reasons"],
                    "triagem_motivos": triagem_signals["motivos"],
                    "triagem_report_mentions": triagem_report_mentions,
                    "validacao_report_mentions": validacao_report_mentions,
                }

        final_percurso_ids = []
        decision = "revisão manual recomendada"
        automatic = False
        manual = True
        motivos.insert(0, "anomalia_multiplos_percursos_no_grupo_B")
        inferencias_prudentes.append(
            "O ramo do Grupo B apresenta mais de um percurso associado. Não houve base textual prudente suficiente para reduzir a um único percurso sem forçar cobertura."
        )
        return {
            "ramo_id": ramo_id,
            "percurso_field": percurso_field,
            "percurso_ids_anteriores": previous_percurso_ids,
            "percurso_ids_finais": final_percurso_ids,
            "decisao": decision,
            "automatico": automatic,
            "revisao_manual_recomendada": manual,
            "motivos": unique_preserve_order(motivos),
            "evidencias_facto": unique_preserve_order(evidencias_facto),
            "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
            "score_relatorio": None,
            "reasons_relatorio": [],
            "triagem_motivos": triagem_signals["motivos"],
            "triagem_report_mentions": triagem_report_mentions,
            "validacao_report_mentions": validacao_report_mentions,
        }

    current_percurso_id = previous_percurso_ids[0]
    matching_entries = [
        entry for entry in generation_entries if entry.get("percurso_id") == current_percurso_id
    ]

    if len(unique_generation_ids) > 1:
        motivos.append("relatorio_geracao_com_multiplos_candidatos_para_o_ramo")
        inferencias_prudentes.append(
            "O relatório de geração apresenta mais de um candidato de percurso para o mesmo ramo; por prudência, o percurso atual não foi mantido automaticamente."
        )
        return {
            "ramo_id": ramo_id,
            "percurso_field": percurso_field,
            "percurso_ids_anteriores": previous_percurso_ids,
            "percurso_ids_finais": [],
            "decisao": "revisão manual recomendada",
            "automatico": False,
            "revisao_manual_recomendada": True,
            "motivos": unique_preserve_order(motivos),
            "evidencias_facto": unique_preserve_order(evidencias_facto),
            "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
            "score_relatorio": None,
            "reasons_relatorio": [],
            "triagem_motivos": triagem_signals["motivos"],
            "triagem_report_mentions": triagem_report_mentions,
            "validacao_report_mentions": validacao_report_mentions,
        }

    if current_percurso_id not in unique_generation_ids:
        motivos.append("percurso_atual_sem_suporte_no_relatorio_de_geracao")
        if unique_generation_ids:
            evidencias_facto.append(
                f"relatorio_geracao_sugere_outro_percurso={','.join(unique_generation_ids)}"
            )
            inferencias_prudentes.append(
                "O percurso atual não coincide com o suporte textual disponível no relatório de geração. O ramo foi esvaziado e assinalado para revisão manual."
            )
            decision = "revisão manual recomendada"
            automatic = False
            manual = True
        else:
            inferencias_prudentes.append(
                "O percurso atual não foi reencontrado no relatório de geração; sem base prudente para o manter, foi removido."
            )
            decision = "removido"
            automatic = True
            manual = False
        return {
            "ramo_id": ramo_id,
            "percurso_field": percurso_field,
            "percurso_ids_anteriores": previous_percurso_ids,
            "percurso_ids_finais": [],
            "decisao": decision,
            "automatico": automatic,
            "revisao_manual_recomendada": manual,
            "motivos": unique_preserve_order(motivos),
            "evidencias_facto": unique_preserve_order(evidencias_facto),
            "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
            "score_relatorio": None,
            "reasons_relatorio": [],
            "triagem_motivos": triagem_signals["motivos"],
            "triagem_report_mentions": triagem_report_mentions,
            "validacao_report_mentions": validacao_report_mentions,
        }

    entry = matching_entries[0] if matching_entries else None
    if entry is None:
        motivos.append("sem_entrada_correspondente_no_relatorio_de_geracao")
        inferencias_prudentes.append(
            "O percurso atual coincide com o id esperado, mas não foi possível recuperar a linha de suporte no relatório de geração. O ramo foi esvaziado por prudência."
        )
        return {
            "ramo_id": ramo_id,
            "percurso_field": percurso_field,
            "percurso_ids_anteriores": previous_percurso_ids,
            "percurso_ids_finais": [],
            "decisao": "revisão manual recomendada",
            "automatico": False,
            "revisao_manual_recomendada": True,
            "motivos": unique_preserve_order(motivos),
            "evidencias_facto": unique_preserve_order(evidencias_facto),
            "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
            "score_relatorio": None,
            "reasons_relatorio": [],
            "triagem_motivos": triagem_signals["motivos"],
            "triagem_report_mentions": triagem_report_mentions,
            "validacao_report_mentions": validacao_report_mentions,
        }

    entry_eval = evaluate_generation_entry(entry)
    evidencias_facto.append(f"score_relatorio={entry_eval['score']}")
    evidencias_facto.extend(f"razao_relatorio:{reason}" for reason in entry_eval["reasons"])

    has_negative_structural_signals = bool(
        triagem_extra_motives or triagem_signals["factos_relatorios"] or triagem_signals["inferencias_prudentes"]
    )

    confirmable = False
    if not has_negative_text and not has_negative_structural_signals and entry_eval["score"] >= 4:
        confirmable = True
    elif (
        not has_negative_text
        and not has_negative_structural_signals
        and entry_eval["score"] == 3
        and entry_eval["has_strong_structural_anchor"]
        and entry_eval["has_additional_anchor"]
    ):
        confirmable = True

    if confirmable:
        decision = "confirmado"
        final_percurso_ids = [current_percurso_id]
        automatic = True
        manual = False
        motivos.insert(0, "percurso_confirmado_com_suporte_estrutural_suficiente")
    else:
        decision = "removido"
        final_percurso_ids = []
        automatic = True
        manual = False
        if entry_eval["score"] < 4:
            motivos.append("score_insuficiente_para_confirmacao_conservadora")
        if entry_eval["score"] == 3 and not entry_eval["has_additional_anchor"]:
            motivos.append("sinal_estrutural_minimo_sem_ancoragem_adicional")
        if has_negative_structural_signals:
            motivos.append("sinais_estruturais_ou_de_triagem_desfavoraveis")
        if has_negative_text:
            motivos.append("sinais_textuais_negativos")
        inferencias_prudentes.append(
            "Na dúvida, o percurso não foi mantido. A confirmação automática exige suporte estrutural suficiente e ausência de sinais negativos relevantes."
        )

    return {
        "ramo_id": ramo_id,
        "percurso_field": percurso_field,
        "percurso_ids_anteriores": previous_percurso_ids,
        "percurso_ids_finais": final_percurso_ids,
        "decisao": decision,
        "automatico": automatic,
        "revisao_manual_recomendada": manual,
        "motivos": unique_preserve_order(motivos),
        "evidencias_facto": unique_preserve_order(evidencias_facto),
        "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
        "score_relatorio": entry_eval["score"],
        "reasons_relatorio": entry_eval["reasons"],
        "triagem_motivos": triagem_signals["motivos"],
        "triagem_report_mentions": triagem_report_mentions,
        "validacao_report_mentions": validacao_report_mentions,
    }


def sync_percurso_reverse_links(
    percursos: List[Dict[str, Any]],
    decisions_by_ramo: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    if not percursos:
        return {
            "reverse_links_updated": False,
            "percursos_tocados": [],
            "nota": "Bloco 'percursos' não localizado; não foi possível sincronizar percurso->ramo.",
        }

    touched: Set[str] = set()
    for percurso in percursos:
        if not isinstance(percurso, dict):
            continue
        percurso_id = first_nonempty_string(percurso, ("id",))
        if not percurso_id:
            continue
        field = detect_percurso_ramo_ids_field(percurso)
        ramo_ids = get_first_list_of_strings(percurso, RAMO_IDS_FIELD_CANDIDATES)
        new_ramo_ids = list(ramo_ids)
        changed = False

        for ramo_id, decision in decisions_by_ramo.items():
            final_ids = decision["percurso_ids_finais"]
            should_have = percurso_id in final_ids
            currently_has = ramo_id in new_ramo_ids
            if should_have and not currently_has:
                new_ramo_ids.append(ramo_id)
                changed = True
            elif not should_have and currently_has:
                new_ramo_ids = [item for item in new_ramo_ids if item != ramo_id]
                changed = True

        if changed:
            percurso[field] = unique_preserve_order(new_ramo_ids)
            if field != "ramo_ids":
                percurso["ramo_ids"] = unique_preserve_order(new_ramo_ids)
            touched.add(percurso_id)

    return {
        "reverse_links_updated": True,
        "percursos_tocados": sorted(touched),
        "nota": "Sincronização local percurso->ramo aplicada apenas para os ramos revistos do Grupo B.",
    }


def build_report_text(
    payload: Dict[str, Any],
    tree_location: str,
    percursos_location: Optional[str],
) -> str:
    metadata = payload["metadata"]
    resumo = payload["resumo"]
    details = payload["detalhe_ramos"]
    criteria = payload["criterios_aplicados"]

    lines: List[str] = []
    lines.append("RELATÓRIO DE REVISÃO DE PERCURSOS SUPERIORES V1")
    lines.append("=" * 72)
    lines.append(f"Data/hora UTC: {metadata['timestamp_utc']}")
    lines.append(f"Script: {metadata['script']}")
    lines.append(f"Bloco de ramos localizado em: {tree_location}")
    lines.append(f"Bloco de percursos localizado em: {percursos_location or 'não localizado / não atualizado'}")
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
    lines.append(f"Total de ramos Grupo B analisados: {resumo['grupo_b_analisados']}")
    lines.append(f"Percurso confirmado: {resumo['confirmados']}")
    lines.append(f"Sem percurso final: {resumo['sem_percurso_final']}")
    lines.append(f"Revisão manual recomendada: {resumo['revisao_manual_recomendada']}")
    lines.append(f"Não decididos automaticamente: {resumo['nao_decididos_automaticamente']}")
    lines.append(f"Grupo C confirmado sem alterar: {resumo['grupo_c_confirmado_sem_alterar']}")
    lines.append("")

    lines.append("Critérios aplicados")
    lines.append("-" * 72)
    lines.append(f"Regra dominante: {criteria['regra_dominante']}")
    lines.append(f"Regra de prudência: {criteria['regra_de_prudencia']}")
    lines.append(f"Limite de confirmação: {criteria['limite_confirmacao_automatica']}")
    lines.append("Heurística transparente usada:")
    for item in criteria["heuristicas"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("Listagem detalhada por ramo")
    lines.append("-" * 72)
    if not details:
        lines.append("Nenhum ramo do Grupo B foi analisado.")
    for item in details:
        lines.append(
            f"{item['ramo_id']} | anteriores={','.join(item['percurso_ids_anteriores']) if item['percurso_ids_anteriores'] else '∅'} | "
            f"finais={','.join(item['percurso_ids_finais']) if item['percurso_ids_finais'] else '∅'} | "
            f"decisão={item['decisao']}"
        )
        if item["score_relatorio"] is not None:
            lines.append(f"  score_relatorio: {item['score_relatorio']}")
        if item["reasons_relatorio"]:
            lines.append(f"  reasons_relatorio: {'; '.join(item['reasons_relatorio'])}")
        if item["motivos"]:
            lines.append(f"  motivos: {', '.join(item['motivos'])}")
        if item["evidencias_facto"]:
            lines.append(f"  factos: {' | '.join(item['evidencias_facto'])}")
        if item["inferencias_prudentes"]:
            lines.append(f"  inferências_prudentes: {' | '.join(item['inferencias_prudentes'])}")
        if item["triagem_motivos"]:
            lines.append(f"  triagem_motivos: {', '.join(item['triagem_motivos'])}")
        if item["revisao_manual_recomendada"]:
            lines.append("  revisão_manual_recomendada: sim")
        if item["triagem_report_mentions"]:
            lines.append(f"  menções_triagem: {len(item['triagem_report_mentions'])} linha(s)")
        if item["validacao_report_mentions"]:
            lines.append(f"  menções_validacao_percursos: {len(item['validacao_report_mentions'])} linha(s)")
    lines.append("")

    lines.append("Observações finais")
    lines.append("-" * 72)
    lines.append(
        "Camada de percursos superiores suficientemente estabilizada para o passo seguinte: "
        + ("sim" if payload["observacoes_finais"]["estabilizada_para_revisao_argumentativa"] else "não")
    )
    lines.append(
        "Ramos que exigem atenção manual antes da revisão argumentativa: "
        + (
            ", ".join(payload["observacoes_finais"]["ramos_com_atencao_manual"])
            if payload["observacoes_finais"]["ramos_com_atencao_manual"]
            else "nenhum"
        )
    )
    lines.append(payload["observacoes_finais"]["nota"])
    lines.append(payload["observacoes_finais"]["nota_reverse_links"])
    lines.append("")

    return "\n".join(lines)


def terminal_summary(payload: Dict[str, Any], output_tree: Path, output_report: Path) -> str:
    resumo = payload["resumo"]
    return "\n".join(
        [
            f"Grupo B analisado: {resumo['grupo_b_analisados']}",
            f"Confirmados: {resumo['confirmados']}",
            f"Sem percurso final: {resumo['sem_percurso_final']}",
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
        raise RevisaoPercursosSuperioresError(
            "O ficheiro da árvore tem de ser um objeto JSON no topo."
        )
    triagem = load_json(paths["triagem_json"])
    if not isinstance(triagem, dict):
        raise RevisaoPercursosSuperioresError(
            "O ficheiro de triagem tem de ser um objeto JSON no topo."
        )

    triagem_report_text = load_text(paths["triagem_report"])
    geracao_percursos_text = load_text(paths["report_geracao_percursos"])
    validacao_percursos_text = load_text(paths["report_validacao_percursos"])

    ramos, ramos_location = locate_ramos(tree)
    if not ramos:
        raise RevisaoPercursosSuperioresError(
            "O bloco de ramos foi localizado, mas está vazio."
        )
    percursos, percursos_location = locate_optional_section(tree, ("percursos",), id_prefix="P_")

    group_a = extract_group_items(triagem, "A_rever_argumento")
    group_b = extract_group_items(triagem, "B_rever_percurso_e_depois_argumento")
    group_c = extract_group_items(triagem, "C_sem_subida_nesta_ronda")
    group_d = extract_group_items(triagem, "D_fora_do_ambito_desta_ronda")
    fila_rever_percurso = extract_triagem_queue(triagem, "rever_percurso_primeiro")

    ramo_map: Dict[str, Dict[str, Any]] = {}
    for idx, ramo in enumerate(ramos, start=1):
        if not isinstance(ramo, dict):
            raise RevisaoPercursosSuperioresError(
                f"Elemento inválido em ramos[{idx}]: esperado dict, obtido {type(ramo).__name__}."
            )
        ramo_id = first_nonempty_string(ramo, ("id", "ramo_id"))
        if not ramo_id:
            raise RevisaoPercursosSuperioresError(
                f"Falta 'id' utilizável em ramos[{idx}]."
            )
        ramo_map[ramo_id] = ramo

    missing_group_b = [ramo_id for ramo_id in group_b if ramo_id not in ramo_map]
    if missing_group_b:
        raise RevisaoPercursosSuperioresError(
            "A triagem refere ramos do Grupo B inexistentes na árvore:\n- "
            + "\n- ".join(sorted(missing_group_b, key=ramo_sort_key))
        )

    reverse_percurso_index = build_reverse_ramo_index(percursos, RAMO_IDS_FIELD_CANDIDATES)
    for ramo_id, percurso_ids in reverse_percurso_index.items():
        ramo = ramo_map.get(ramo_id)
        if not isinstance(ramo, dict):
            continue
        current = get_first_list_of_strings(ramo, PERCURSO_FIELD_CANDIDATES)
        if not current and percurso_ids:
            ramo[detect_ramo_percurso_field(ramo)] = list(percurso_ids)

    parsed_generation = parse_generation_percursos_report(geracao_percursos_text)
    triagem_mentions = index_text_mentions_by_ramo(triagem_report_text)
    validacao_mentions = index_text_mentions_by_ramo(validacao_percursos_text)

    decisions: List[Dict[str, Any]] = []
    decisions_by_ramo: Dict[str, Dict[str, Any]] = {}

    for ramo_id in sorted(group_b.keys(), key=ramo_sort_key):
        decision = decide_group_b_ramo(
            ramo_id=ramo_id,
            ramo=ramo_map[ramo_id],
            triagem_item=group_b[ramo_id],
            generation_entries=parsed_generation["entries_by_ramo"].get(ramo_id, []),
            generation_empty_ramos=set(parsed_generation["empty_ramos"]),
            triagem_report_mentions=triagem_mentions.get(ramo_id, []),
            validacao_report_mentions=validacao_mentions.get(ramo_id, []),
        )
        decisions.append(decision)
        decisions_by_ramo[ramo_id] = decision

    for decision in decisions:
        ramo = ramo_map[decision["ramo_id"]]
        field = decision["percurso_field"]
        ramo[field] = list(decision["percurso_ids_finais"])
        if field != "percurso_ids_associados":
            ramo["percurso_ids_associados"] = list(decision["percurso_ids_finais"])

    reverse_sync = sync_percurso_reverse_links(percursos, decisions_by_ramo)

    group_c_confirmed_sem_alterar = 0
    for ramo_id in group_c:
        ramo = ramo_map.get(ramo_id)
        if not isinstance(ramo, dict):
            continue
        percurso_ids = get_first_list_of_strings(ramo, PERCURSO_FIELD_CANDIDATES)
        if not percurso_ids:
            group_c_confirmed_sem_alterar += 1

    confirmados = sum(1 for item in decisions if item["decisao"] == "confirmado")
    revisao_manual_recomendada = sum(1 for item in decisions if item["revisao_manual_recomendada"])
    nao_decididos_automaticamente = sum(1 for item in decisions if not item["automatico"])
    sem_percurso_final = sum(1 for item in decisions if not item["percurso_ids_finais"])

    observacoes_finais = {
        "estabilizada_para_revisao_argumentativa": revisao_manual_recomendada == 0 and nao_decididos_automaticamente == 0,
        "ramos_com_atencao_manual": sorted(
            [item["ramo_id"] for item in decisions if item["revisao_manual_recomendada"]],
            key=ramo_sort_key,
        ),
        "nota": (
            "A camada de percursos superiores só é considerada plenamente estabilizada para a revisão argumentativa quando nenhum ramo do Grupo B fica dependente de revisão manual."
        ),
        "nota_reverse_links": reverse_sync["nota"],
    }

    payload = {
        "metadata": {
            "script": "rever_percursos_superiores_v1.py",
            "timestamp_utc": utc_now_iso(),
            "ficheiros_lidos": {
                "arvore": str(paths["input_tree"]),
                "triagem_json": str(paths["triagem_json"]),
                "triagem_report": str(paths["triagem_report"]),
                "relatorio_geracao_percursos": str(paths["report_geracao_percursos"]),
                "relatorio_validacao_percursos": str(paths["report_validacao_percursos"]),
            },
            "ficheiros_escritos": {
                "arvore_pos_percursos": str(paths["output_tree"]),
                "relatorio_revisao_percursos": str(paths["output_report"]),
            },
            "triagem_group_counts": {
                "A": len(group_a),
                "B": len(group_b),
                "C": len(group_c),
                "D": len(group_d),
            },
            "fila_rever_percurso_identificada_na_triagem": fila_rever_percurso,
        },
        "criterios_aplicados": {
            "regra_dominante": "Função estrutural dominante do ramo, lida de forma prudente através do percurso já associado e dos sinais estruturais explicitados no relatório de geração de percursos.",
            "regra_de_prudencia": "Na dúvida, não manter o percurso. O script não inventa novos percursos nem substitui o percurso atual por outro não já associado ao ramo.",
            "limite_confirmacao_automatica": "Confirmação automática apenas com suporte textual-estrutural suficiente: score>=4 sem sinais negativos relevantes, ou score=3 com ancoragem estrutural forte e ancoragem adicional por passos.",
            "heuristicas": [
                "Grupo B é o único universo diretamente revisto.",
                "Grupo C é apenas confirmado como ausência sem alteração.",
                "Score 4 ou 5 no relatório de geração, sem sinais negativos relevantes, permite confirmar o percurso atual.",
                "Score 3 só confirma quando combina ancoragem estrutural forte (zona/problema/trabalho/utilidade/efeito) com ancoragem adicional por passos.",
                "Mais de um percurso num ramo do Grupo B é tratado como anomalia e não é reduzido sem base textual clara.",
                "Divergência entre estrutura e relatório de geração impede confirmação automática prudente.",
            ],
        },
        "resumo": {
            "grupo_b_analisados": len(decisions),
            "confirmados": confirmados,
            "sem_percurso_final": sem_percurso_final,
            "revisao_manual_recomendada": revisao_manual_recomendada,
            "nao_decididos_automaticamente": nao_decididos_automaticamente,
            "grupo_c_confirmado_sem_alterar": group_c_confirmed_sem_alterar,
        },
        "detalhe_ramos": decisions,
        "observacoes_finais": observacoes_finais,
        "reverse_sync": reverse_sync,
    }

    report_text = build_report_text(payload, ramos_location, percursos_location)
    save_json_atomic(paths["output_tree"], tree)
    write_text(paths["output_report"], report_text)

    print(terminal_summary(payload, paths["output_tree"], paths["output_report"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RevisaoPercursosSuperioresError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)
