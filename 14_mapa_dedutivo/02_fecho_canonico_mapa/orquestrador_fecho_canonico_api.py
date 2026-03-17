#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PIPELINE_VERSION = "1.0.0"
DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_CORRIDOR_ORDER = ["P33_P37", "P25_P30", "P42_P48", "P50"]
STEP_ID_RE = re.compile(r"^P\d{2}$")
SUBSTEP_ID_RE = re.compile(r"^P\d{2}_SP\d{2}$")
CORRIDOR_ID_RE = re.compile(r"^P\d{2}(?:_P\d{2})?$")
FRAGMENT_ID_RE = re.compile(r"^F[0-9A-Z_]+$")


class ValidationError(Exception):
    """Erro de validação estrutural."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Orquestrador local e auditável do fecho canónico do mapa dedutivo."
    )
    parser.add_argument(
        "--manifesto",
        default=str(script_dir / "manifesto_fecho_canonico.json"),
        help="Caminho para o manifesto_fecho_canonico.json.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Gera respostas determinísticas sem chamar API externa.",
    )
    parser.add_argument(
        "--fallback-dry-run",
        action="store_true",
        help="Se a chamada ao modelo falhar, usa resposta determinística local.",
    )
    parser.add_argument(
        "--only-corridor",
        dest="only_corridor",
        default=None,
        help="Executa apenas um corredor específico, por exemplo P33_P37.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Limita o número de passos processados por corredor.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("FECHO_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-5.4",
        help="Nome do modelo remoto quando não estiver em dry-run.",
    )
    parser.add_argument(
        "--api-mode",
        choices=["responses", "chat_completions"],
        default=os.getenv("FECHO_API_MODE", "responses"),
        help="Formato da API remota.",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("FECHO_API_URL") or os.getenv("OPENAI_API_URL") or "https://api.openai.com/v1/responses",
        help="URL da API remota.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("FECHO_API_TIMEOUT", str(DEFAULT_TIMEOUT_SECONDS))),
        help="Timeout da chamada HTTP à API.",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("FECHO_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Nível de logging.",
    )
    return parser.parse_args()


def configure_logging(log_dir: Path, level_name: str) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "orquestrador_fecho_canonico_api.log"
    level = getattr(logging, level_name.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def to_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return re.sub(r"\s+", " ", str(value)).strip()


def clean_text_or_none(value: Any) -> Optional[str]:
    text = clean_text(value)
    return text or None


def normalize_string_list(values: Any) -> List[str]:
    result: List[str] = []
    for value in to_list(values):
        text = clean_text(value)
        if text:
            result.append(text)
    return unique_preserve_order(result)


def normalize_fragment_list(values: Any) -> List[str]:
    fragments = []
    for value in to_list(values):
        text = clean_text(value)
        if text and FRAGMENT_ID_RE.match(text):
            fragments.append(text)
    return unique_preserve_order(fragments)


def unique_preserve_order(items: Iterable[Any]) -> List[Any]:
    seen = set()
    result = []
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def resolve_relative_path(base_dir: Path, candidate: str) -> Path:
    path = Path(candidate)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def relative_to_base(path: Path, base_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve()))
    except Exception:
        return os.path.relpath(str(path.resolve()), str(base_dir.resolve()))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_id(value: Any, pattern: re.Pattern[str], label: str) -> str:
    text = clean_text(value)
    require(bool(text), f"{label} vazio.")
    require(bool(pattern.match(text)), f"{label} inválido: {text}")
    return text


def infer_dirs(manifest: Dict[str, Any], base_dir: Path) -> Dict[str, Path]:
    defaults = {
        "dados": base_dir / "dados",
        "prompts": base_dir / "prompts",
        "schemas": base_dir / "schemas",
        "outputs": base_dir / "outputs",
        "logs": base_dir / "logs",
        "prompts_enviados": base_dir / "prompts_enviados",
        "respostas_modelo": base_dir / "respostas_modelo",
    }
    exec_local = manifest.get("execucao_local", {})
    dirs = exec_local.get("diretorios", {})
    result: Dict[str, Path] = {}
    for key, default_path in defaults.items():
        if key in dirs:
            result[key] = resolve_relative_path(base_dir, dirs[key])
        else:
            result[key] = default_path
    return result


def load_manifest(manifest_path: Path) -> Tuple[Dict[str, Any], Path]:
    require(manifest_path.exists(), f"Manifesto não encontrado: {manifest_path}")
    manifest = load_json(manifest_path)
    base_dir = manifest_path.resolve().parent
    return manifest, base_dir


def load_group_entries(
    manifest: Dict[str, Any],
    group_name: str,
    base_dir: Path,
    required_default: bool = True,
    expect_exists: bool = True,
) -> Dict[str, Dict[str, Any]]:
    entries: Dict[str, Dict[str, Any]] = {}
    group = manifest.get(group_name, {})
    require(isinstance(group, dict), f"Grupo do manifesto inválido: {group_name}")
    for name, entry in group.items():
        require(isinstance(entry, dict), f"Entrada inválida em {group_name}.{name}")
        rel_path = entry.get("path")
        require(isinstance(rel_path, str) and rel_path.strip(), f"Path ausente em {group_name}.{name}")
        abs_path = resolve_relative_path(base_dir, rel_path)
        mandatory = bool(entry.get("obrigatorio", required_default))
        payload = {
            "name": name,
            "path": abs_path,
            "rel_path": rel_path,
            "mandatory": mandatory,
            "meta": entry,
            "exists": abs_path.exists(),
            "data": None,
            "text": None,
        }
        if abs_path.exists():
            if abs_path.suffix.lower() == ".json":
                payload["data"] = load_json(abs_path)
            else:
                payload["text"] = abs_path.read_text(encoding="utf-8")
        elif mandatory and expect_exists:
            raise FileNotFoundError(f"Ficheiro obrigatório ausente: {abs_path}")
        entries[name] = payload
    return entries


def load_runtime(manifest: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
    runtime = {
        "manifest": manifest,
        "base_dir": base_dir,
        "dirs": infer_dirs(manifest, base_dir),
        "inputs_nucleares": load_group_entries(manifest, "inputs_nucleares", base_dir, required_default=True),
        "inputs_secundarios": load_group_entries(manifest, "inputs_secundarios", base_dir, required_default=False),
        "prompts": load_group_entries(manifest, "prompts", base_dir, required_default=True),
        "schemas": load_group_entries(manifest, "schemas", base_dir, required_default=True),
        "outputs_intermedios": load_group_entries(manifest, "outputs_intermedios", base_dir, required_default=False, expect_exists=False),
        "outputs_finais": load_group_entries(manifest, "outputs_finais", base_dir, required_default=False, expect_exists=False),
    }
    ensure_runtime_directories(runtime["dirs"])
    return runtime


def ensure_runtime_directories(dirs: Dict[str, Path]) -> None:
    for key in ["dados", "prompts", "schemas", "outputs", "logs", "prompts_enviados", "respostas_modelo"]:
        dirs[key].mkdir(parents=True, exist_ok=True)


def build_indices(runtime: Dict[str, Any]) -> Dict[str, Any]:
    nuclear = runtime["inputs_nucleares"]
    matriz = nuclear["matriz_inevitabilidades_v4"]["data"]
    mapa = nuclear["mapa_dedutivo_precanonico_v4"]["data"]
    relatorio = nuclear["relatorio_fecho_canonico_v4"]["data"]

    matriz_index = {row["id"]: row for row in to_list(matriz.get("linhas", [])) if isinstance(row, dict) and row.get("id")}
    mapa_index = {row["id"]: row for row in to_list(mapa.get("passos", [])) if isinstance(row, dict) and row.get("id")}

    dossiers: Dict[str, Dict[str, Any]] = {}
    for name, entry in nuclear.items():
        if not name.startswith("dossier_corredor_"):
            continue
        data = entry["data"] or {}
        corridor = clean_text(entry["meta"].get("corredor") or name.replace("dossier_corredor_", ""))
        passos_index = {row["id"]: row for row in to_list(data.get("passos", [])) if isinstance(row, dict) and row.get("id")}
        problemas_index = {row["id"]: row for row in to_list(data.get("problemas_ainda_abertos", [])) if isinstance(row, dict) and row.get("id")}
        canonicas_index = {row["id"]: row for row in to_list(data.get("proposicoes_canonicas", [])) if isinstance(row, dict) and row.get("id")}
        dossiers[corridor] = {
            "data": data,
            "entry": entry,
            "passos_index": passos_index,
            "problemas_index": problemas_index,
            "canonicas_index": canonicas_index,
        }

    report_indexes = {
        "abertos": index_list_by_id(relatorio.get("top_passos_mais_abertos")),
        "mediacionais": index_list_by_id(relatorio.get("top_passos_com_fragilidade_mediacional")),
    }

    return {
        "matriz": matriz,
        "mapa": mapa,
        "relatorio": relatorio,
        "matriz_index": matriz_index,
        "mapa_index": mapa_index,
        "dossiers": dossiers,
        "report_indexes": report_indexes,
    }


def index_list_by_id(items: Any) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for item in to_list(items):
        if isinstance(item, dict) and item.get("id"):
            result[item["id"]] = item
    return result


def ordered_corridors(manifest: Dict[str, Any], only_corridor: Optional[str]) -> List[str]:
    if only_corridor:
        validate_id(only_corridor, CORRIDOR_ID_RE, "Corredor")
        return [only_corridor]

    ordered: List[Tuple[int, str]] = []
    raw_order = manifest.get("execucao_local", {}).get("ordem_de_fecho_corredores", [])
    for index, item in enumerate(to_list(raw_order), start=1):
        if isinstance(item, dict):
            corridor = clean_text(item.get("corredor"))
            if not corridor:
                continue
            order_value = int(item.get("ordem", index))
            ordered.append((order_value, corridor))
    if ordered:
        result = [corridor for _, corridor in sorted(ordered, key=lambda pair: (pair[0], pair[1]))]
    else:
        result = list(DEFAULT_CORRIDOR_ORDER)

    if "P33_P37" in result:
        result = ["P33_P37"] + [item for item in result if item != "P33_P37"]
    else:
        result.insert(0, "P33_P37")

    return unique_preserve_order(result)


def safe_get_step(indexes: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    return indexes.get(step_id, {}) if isinstance(indexes, dict) else {}


def get_corridor_summary(relatorio: Dict[str, Any], corridor: str) -> Dict[str, Any]:
    raw = relatorio.get("corredores_criticos", {})
    if isinstance(raw, dict):
        value = raw.get(corridor)
        return value if isinstance(value, dict) else {}
    return {}


def scan_for_step_hits(node: Any, step_id: str, max_hits: int = 3, path: str = "$", out: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    if out is None:
        out = []
    if len(out) >= max_hits:
        return out

    if isinstance(node, dict):
        candidate_id = clean_text(node.get("id") or node.get("passo_id") or node.get("proposicao_id"))
        if candidate_id == step_id:
            out.append({"path": path, "match": node})
            if len(out) >= max_hits:
                return out
        for key, value in node.items():
            if len(out) >= max_hits:
                break
            scan_for_step_hits(value, step_id, max_hits=max_hits, path=f"{path}.{key}", out=out)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            if len(out) >= max_hits:
                break
            scan_for_step_hits(item, step_id, max_hits=max_hits, path=f"{path}[{idx}]", out=out)
    return out


def collect_secondary_context(runtime: Dict[str, Any], step_id: str, corridor: str) -> Dict[str, Any]:
    context: Dict[str, Any] = {}
    for name, entry in runtime["inputs_secundarios"].items():
        if not entry["exists"]:
            context[name] = {
                "path": entry["rel_path"],
                "disponivel": False,
                "recortes": [],
            }
            continue
        data = entry["data"]
        recortes = scan_for_step_hits(data, step_id, max_hits=2)
        context[name] = {
            "path": entry["rel_path"],
            "disponivel": True,
            "corredor": corridor,
            "recortes": recortes,
        }
    return context


def build_step_context(
    runtime: Dict[str, Any],
    indices: Dict[str, Any],
    corridor: str,
    step_id: str,
    sequence: Sequence[str],
) -> Dict[str, Any]:
    matriz_step = safe_get_step(indices["matriz_index"], step_id)
    mapa_step = safe_get_step(indices["mapa_index"], step_id)
    dossier = indices["dossiers"].get(corridor, {})
    dossier_data = dossier.get("data", {})
    dossier_step = safe_get_step(dossier.get("passos_index", {}), step_id)
    dossier_problem = safe_get_step(dossier.get("problemas_index", {}), step_id)
    dossier_canonica = safe_get_step(dossier.get("canonicas_index", {}), step_id)

    require(matriz_step or mapa_step or dossier_step, f"Passo {step_id} não encontrado no contexto mínimo do corredor {corridor}.")

    idx = list(sequence).index(step_id)
    previous_candidates = normalize_step_refs(first_non_empty(matriz_step.get("depende_de"), mapa_step.get("depende_de"), dossier_step.get("depende_de"), []))
    next_candidates = normalize_step_refs(first_non_empty(matriz_step.get("prepara"), mapa_step.get("prepara"), dossier_step.get("prepara"), []))

    previous_step = sequence[idx - 1] if idx > 0 else (previous_candidates[0] if previous_candidates else None)
    next_step = sequence[idx + 1] if idx + 1 < len(sequence) else (next_candidates[0] if next_candidates else None)

    previous_step = clean_text(previous_step) or None
    next_step = clean_text(next_step) or None

    initial_state = clean_text(first_non_empty(
        dossier_problem.get("estado_de_fecho"),
        dossier_step.get("estado_de_fecho"),
        mapa_step.get("estado_de_fecho_canonico"),
        matriz_step.get("estado_de_fecho"),
    )) or "aberto"

    fragilities = first_non_empty(
        dossier_problem.get("tipos_de_fragilidade"),
        dossier_step.get("tipos_de_fragilidade"),
        mapa_step.get("tipos_de_fragilidade"),
        matriz_step.get("tipos_de_fragilidade"),
        [],
    )

    report_step = {
        "mais_aberto": safe_get_step(indices["report_indexes"].get("abertos", {}), step_id),
        "fragilidade_mediacional": safe_get_step(indices["report_indexes"].get("mediacionais", {}), step_id),
    }

    sources = build_step_sources(runtime, corridor)

    return {
        "corredor": corridor,
        "step_id": step_id,
        "sequence": list(sequence),
        "numero_final": first_non_empty(matriz_step.get("numero_final"), mapa_step.get("numero_final"), dossier_step.get("numero_final")),
        "bloco_id": clean_text(first_non_empty(matriz_step.get("bloco_id"), mapa_step.get("bloco_id"), dossier_step.get("bloco_id"))),
        "bloco_titulo": clean_text(first_non_empty(matriz_step.get("bloco_titulo"), mapa_step.get("bloco_titulo"), dossier_step.get("bloco_titulo"))),
        "depende_de": normalize_step_refs(first_non_empty(matriz_step.get("depende_de"), mapa_step.get("depende_de"), dossier_step.get("depende_de"), [])),
        "prepara": normalize_step_refs(first_non_empty(matriz_step.get("prepara"), mapa_step.get("prepara"), dossier_step.get("prepara"), [])),
        "estado_inicial_do_passo": initial_state,
        "tipos_de_fragilidade": normalize_string_list(fragilities),
        "passo_anterior_id": previous_step,
        "passo_seguinte_id": next_step,
        "matriz_step": matriz_step,
        "mapa_step": mapa_step,
        "report_step": report_step,
        "corridor_summary": get_corridor_summary(indices["relatorio"], corridor),
        "dossier_step": dossier_step,
        "dossier_problem": dossier_problem,
        "dossier_canonica": dossier_canonica,
        "dossier_summary": dossier_data.get("resumo", {}),
        "secondary_context": collect_secondary_context(runtime, step_id, corridor),
        "fontes_utilizadas": sources,
    }


def build_step_sources(runtime: Dict[str, Any], corridor: str) -> List[str]:
    nuclear = runtime["inputs_nucleares"]
    paths = [
        nuclear["matriz_inevitabilidades_v4"]["rel_path"],
        nuclear["mapa_dedutivo_precanonico_v4"]["rel_path"],
        nuclear["relatorio_fecho_canonico_v4"]["rel_path"],
    ]
    dossier_name = f"dossier_corredor_{corridor}"
    if dossier_name in nuclear:
        paths.append(nuclear[dossier_name]["rel_path"])
    for entry in runtime["inputs_secundarios"].values():
        if entry["exists"]:
            paths.append(entry["rel_path"])
    return unique_preserve_order(paths)


def normalize_step_refs(values: Any) -> List[str]:
    result = []
    for value in to_list(values):
        text = clean_text(value)
        if text and STEP_ID_RE.match(text):
            result.append(text)
    return unique_preserve_order(result)


def first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        return value
    return None


def render_prompt(template: str, replacements: Dict[str, str]) -> str:
    text = template
    for key, value in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def step_prompt_replacements(context: Dict[str, Any]) -> Dict[str, str]:
    return {
        "CORREDOR_ID": context["corredor"],
        "PASSO_ID": context["step_id"],
        "NUMERO_FINAL": str(context["numero_final"]),
        "BLOCO_ID": context["bloco_id"],
        "BLOCO_TITULO": context["bloco_titulo"],
        "DEPENDE_DE_JSON": json_dumps(context["depende_de"]),
        "PREPARA_JSON": json_dumps(context["prepara"]),
        "ESTADO_INICIAL_DO_PASSO": context["estado_inicial_do_passo"],
        "TIPOS_DE_FRAGILIDADE_JSON": json_dumps(context["tipos_de_fragilidade"]),
        "PASSO_ANTERIOR_ID": context["passo_anterior_id"] or "",
        "PASSO_SEGUINTE_ID": context["passo_seguinte_id"] or "",
        "MATRIZ_INEVITABILIDADES_RECORTE_JSON": json_dumps(context["matriz_step"]),
        "MAPA_PRECANONICO_RECORTE_JSON": json_dumps(context["mapa_step"]),
        "RELATORIO_FECHO_RECORTE_JSON": json_dumps({
            "corredor": context["corridor_summary"],
            "passo": context["report_step"],
        }),
        "DOSSIER_CORREDOR_RECORTE_JSON": json_dumps({
            "resumo": context["dossier_summary"],
            "sequencia_minima_do_corredor": context["sequence"],
            "proposicao_canonica": context["dossier_canonica"],
            "problema_ainda_aberto": context["dossier_problem"],
            "passo": context["dossier_step"],
        }),
        "INPUTS_SECUNDARIOS_RELEVANTES_JSON": json_dumps(context["secondary_context"]),
    }


def build_substep_id(step_id: str, ordinal: int) -> str:
    return f"{step_id}_SP{ordinal:02d}"


def build_substep_context(
    runtime: Dict[str, Any],
    step_context: Dict[str, Any],
    raw_step_response: Dict[str, Any],
    canonical_step: Dict[str, Any],
) -> Dict[str, Any]:
    ordinal = 1
    substep_id = build_substep_id(step_context["step_id"], ordinal)
    return {
        "corredor": step_context["corredor"],
        "passo_pai_id": step_context["step_id"],
        "subpasso_id": substep_id,
        "numero_ordinal_no_passo": ordinal,
        "passo_anterior_id": step_context["passo_anterior_id"],
        "passo_seguinte_id": step_context["passo_seguinte_id"],
        "step_context": step_context,
        "raw_step_response": raw_step_response,
        "canonical_step": canonical_step,
        "fontes_utilizadas": step_context["fontes_utilizadas"],
    }


def substep_prompt_replacements(context: Dict[str, Any]) -> Dict[str, str]:
    step_context = context["step_context"]
    return {
        "CORREDOR_ID": context["corredor"],
        "PASSO_PAI_ID": context["passo_pai_id"],
        "SUBPASSO_ID_SUGERIDO": context["subpasso_id"],
        "NUMERO_ORDINAL_SUGERIDO": str(context["numero_ordinal_no_passo"]),
        "PASSO_ANTERIOR_ID": context["passo_anterior_id"] or "null",
        "PASSO_SEGUINTE_ID": context["passo_seguinte_id"] or "null",
        "DECISAO_POR_PASSO_CANDIDATA_JSON": json_dumps({
            "raw": context["raw_step_response"],
            "canonical": context["canonical_step"],
        }),
        "MATRIZ_INEVITABILIDADES_RECORTE_JSON": json_dumps(step_context["matriz_step"]),
        "MAPA_PRECANONICO_RECORTE_JSON": json_dumps(step_context["mapa_step"]),
        "RELATORIO_FECHO_RECORTE_JSON": json_dumps({
            "corredor": step_context["corridor_summary"],
            "passo": step_context["report_step"],
        }),
        "DOSSIER_CORREDOR_RECORTE_JSON": json_dumps({
            "resumo": step_context["dossier_summary"],
            "sequencia_minima_do_corredor": step_context["sequence"],
            "proposicao_canonica": step_context["dossier_canonica"],
            "problema_ainda_aberto": step_context["dossier_problem"],
            "passo": step_context["dossier_step"],
        }),
        "INPUTS_SECUNDARIOS_RELEVANTES_JSON": json_dumps(step_context["secondary_context"]),
    }


def build_corridor_context(
    runtime: Dict[str, Any],
    indices: Dict[str, Any],
    corridor: str,
    sequence: Sequence[str],
    canonical_step_decisions: List[Dict[str, Any]],
    canonical_substep_decisions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    dossier = indices["dossiers"].get(corridor, {})
    data = dossier.get("data", {})
    sources = build_step_sources(runtime, corridor)
    return {
        "corredor": corridor,
        "sequencia": list(sequence),
        "decisoes_passo": canonical_step_decisions,
        "decisoes_subpasso": canonical_substep_decisions,
        "corridor_summary": get_corridor_summary(indices["relatorio"], corridor),
        "dossier_summary": data.get("resumo", {}),
        "dossier_problemas": data.get("problemas_ainda_abertos", []),
        "fontes_utilizadas": sources,
        "matriz_recorte": [indices["matriz_index"].get(step_id, {}) for step_id in sequence],
        "mapa_recorte": [indices["mapa_index"].get(step_id, {}) for step_id in sequence],
        "secondary_context": {name: {"path": entry["rel_path"], "disponivel": entry["exists"]} for name, entry in runtime["inputs_secundarios"].items()},
    }


def arbitration_prompt_replacements(context: Dict[str, Any]) -> Dict[str, str]:
    return {
        "CORREDOR_ID": context["corredor"],
        "SEQUENCIA_MINIMA_DO_CORREDOR_JSON": json_dumps(context["sequencia"]),
        "DECISOES_POR_PASSO_JSON": json_dumps(context["decisoes_passo"]),
        "DECISOES_POR_SUBPASSO_JSON": json_dumps(context["decisoes_subpasso"]),
        "MATRIZ_INEVITABILIDADES_RECORTE_JSON": json_dumps(context["matriz_recorte"]),
        "MAPA_PRECANONICO_RECORTE_JSON": json_dumps(context["mapa_recorte"]),
        "RELATORIO_FECHO_RECORTE_JSON": json_dumps({"corredor": context["corridor_summary"]}),
        "DOSSIER_CORREDOR_RECORTE_JSON": json_dumps({
            "resumo": context["dossier_summary"],
            "problemas_ainda_abertos": context["dossier_problemas"],
        }),
        "INPUTS_SECUNDARIOS_RELEVANTES_JSON": json_dumps(context["secondary_context"]),
    }


def save_prompt(runtime: Dict[str, Any], corridor: str, stage: str, target_id: str, text: str) -> Path:
    base = runtime["dirs"]["prompts_enviados"] / corridor
    path = base / f"{stage}__{target_id}.txt"
    write_text(path, text)
    return path


def save_model_artifacts(
    runtime: Dict[str, Any],
    corridor: str,
    stage: str,
    target_id: str,
    raw_text: str,
    raw_json: Dict[str, Any],
    normalized_json: Dict[str, Any],
    validation: Dict[str, Any],
    mode: str,
) -> Path:
    base = runtime["dirs"]["respostas_modelo"] / corridor
    base.mkdir(parents=True, exist_ok=True)
    raw_text_path = base / f"{stage}__{target_id}.raw.txt"
    json_path = base / f"{stage}__{target_id}.json"
    write_text(raw_text_path, raw_text)
    payload = {
        "stage": stage,
        "target_id": target_id,
        "mode": mode,
        "gerado_em_utc": utc_now_iso(),
        "raw_json": raw_json,
        "normalized_json": normalized_json,
        "validation": validation,
        "raw_text_path": str(raw_text_path.name),
    }
    write_json(json_path, payload)
    return json_path


def build_request_payload(api_mode: str, model: str, prompt_text: str) -> Dict[str, Any]:
    if api_mode == "chat_completions":
        return {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt_text},
            ],
            "temperature": 0,
        }
    return {
        "model": model,
        "input": prompt_text,
    }


def call_model_api(prompt_text: str, args: argparse.Namespace) -> Tuple[str, Dict[str, Any]]:
    api_key = os.getenv("FECHO_API_KEY") or os.getenv("OPENAI_API_KEY")
    require(bool(api_key), "Variável de ambiente FECHO_API_KEY ou OPENAI_API_KEY ausente.")

    payload = build_request_payload(args.api_mode, args.model, prompt_text)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = json.dumps(payload).encode("utf-8")
    request = Request(args.api_url, data=body, headers=headers, method="POST")

    try:
        with urlopen(request, timeout=args.timeout) as response:
            raw_bytes = response.read()
            response_text = raw_bytes.decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
        raise RuntimeError(f"Erro HTTP ao chamar API: {exc.code} {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Falha de rede ao chamar API: {exc}") from exc

    response_json = json.loads(response_text)
    output_text = extract_output_text(response_json)
    return output_text, response_json


def extract_output_text(response_json: Dict[str, Any]) -> str:
    if isinstance(response_json.get("output_text"), str) and response_json["output_text"].strip():
        return response_json["output_text"]

    if isinstance(response_json.get("choices"), list):
        for choice in response_json["choices"]:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
                if isinstance(content, list):
                    texts = []
                    for item in content:
                        if isinstance(item, dict):
                            text_value = item.get("text")
                            if isinstance(text_value, str) and text_value.strip():
                                texts.append(text_value)
                    if texts:
                        return "\n".join(texts)

    outputs = response_json.get("output")
    if isinstance(outputs, list):
        texts = []
        for output in outputs:
            if not isinstance(output, dict):
                continue
            content = output.get("content")
            if isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") in {"output_text", "text"} and isinstance(item.get("text"), str):
                        texts.append(item["text"])
        if texts:
            return "\n".join(texts)

    if isinstance(response_json.get("text"), str) and response_json["text"].strip():
        return response_json["text"]

    raise RuntimeError("Não foi possível extrair texto de saída da resposta da API.")


def parse_json_object(text: str) -> Dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ValidationError("Resposta vazia do modelo.")
    try:
        payload = json.loads(stripped)
        require(isinstance(payload, dict), "A resposta do modelo não é um objeto JSON.")
        return payload
    except json.JSONDecodeError:
        pass

    candidate = extract_first_json_object(stripped)
    payload = json.loads(candidate)
    require(isinstance(payload, dict), "A resposta do modelo não é um objeto JSON.")
    return payload


def extract_first_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise ValidationError("Não foi encontrado nenhum objeto JSON na resposta do modelo.")

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise ValidationError("Objeto JSON incompleto na resposta do modelo.")


def execute_stage(
    runtime: Dict[str, Any],
    args: argparse.Namespace,
    corridor: str,
    stage: str,
    target_id: str,
    prompt_text: str,
    dry_run_payload: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], Dict[str, Any], str]:
    save_prompt(runtime, corridor, stage, target_id, prompt_text)
    if args.dry_run:
        raw_json = dry_run_payload
        raw_text = json_dumps(raw_json)
        return raw_text, raw_json, {"mode": "dry_run"}, "dry_run"

    try:
        raw_text, api_response = call_model_api(prompt_text, args)
        raw_json = parse_json_object(raw_text)
        return raw_text, raw_json, api_response, "api"
    except Exception as exc:
        if not args.fallback_dry_run:
            raise
        logging.warning("Falha na API para %s/%s; a usar fallback dry-run: %s", stage, target_id, exc)
        raw_json = dry_run_payload
        raw_text = json_dumps(raw_json)
        return raw_text, raw_json, {"mode": "fallback_dry_run", "error": str(exc)}, "fallback_dry_run"


def validate_prompt_step_response(data: Dict[str, Any]) -> None:
    required_fields = [
        "decisao_editorial",
        "formulacao_v2_final",
        "justificacao_expandida_final",
        "ponte_entrada",
        "ponte_saida",
        "porque_o_anterior_nao_basta",
        "porque_nao_pode_ser_suprimido",
        "objecao_letal",
        "bloqueio_curto",
        "objecoes_bloqueadas_final",
        "fragmentos_selecionados_finais",
        "nota_editorial_final",
        "pendencias",
        "precisa_de_subpasso",
    ]
    for field in required_fields:
        require(field in data, f"Campo ausente na resposta de passo: {field}")

    require(data["decisao_editorial"] in {"manter", "densificar", "reformular", "introduzir_subpasso", "reabrir"}, "decisao_editorial inválida")
    require(isinstance(data["precisa_de_subpasso"], bool), "precisa_de_subpasso tem de ser boolean")
    require(isinstance(data["objecoes_bloqueadas_final"], list), "objecoes_bloqueadas_final tem de ser array")
    require(isinstance(data["fragmentos_selecionados_finais"], list), "fragmentos_selecionados_finais tem de ser array")
    require(isinstance(data["pendencias"], list), "pendencias tem de ser array")
    for field in [
        "formulacao_v2_final",
        "justificacao_expandida_final",
        "ponte_entrada",
        "ponte_saida",
        "porque_o_anterior_nao_basta",
        "porque_nao_pode_ser_suprimido",
        "objecao_letal",
        "bloqueio_curto",
        "nota_editorial_final",
    ]:
        require(bool(clean_text(data[field])), f"Campo textual vazio na resposta de passo: {field}")


def infer_step_final_state(raw: Dict[str, Any], substep_approved: bool = False) -> str:
    pendencias = normalize_string_list(raw.get("pendencias"))
    if raw.get("decisao_editorial") == "reabrir":
        return "aberto"
    if raw.get("precisa_de_subpasso") and not substep_approved:
        return "quase_fechado"
    if pendencias:
        return "quase_fechado"
    return "fechado"


def normalize_step_response(raw: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    note = clean_text(raw.get("nota_editorial_final"))
    pendencias = normalize_string_list(raw.get("pendencias"))
    obs = []
    if note:
        obs.append(note)
    obs.extend([f"Pendência: {item}" for item in pendencias])

    substeps = []
    state_final = infer_step_final_state(raw, substep_approved=False)
    reopen = raw.get("decisao_editorial") == "reabrir"

    decision = {
        "tipo_registo": "decisao_passo",
        "corredor": context["corredor"],
        "passo_id": context["step_id"],
        "numero_final": int(context["numero_final"]),
        "bloco_id": context["bloco_id"],
        "bloco_titulo": context["bloco_titulo"],
        "depende_de": context["depende_de"],
        "prepara": context["prepara"],
        "estado_inicial_do_passo": context["estado_inicial_do_passo"],
        "tipos_de_fragilidade_iniciais": context["tipos_de_fragilidade"],
        "decisao_editorial": raw["decisao_editorial"],
        "formulacao_canonica_final": clean_text(raw.get("formulacao_v2_final")),
        "justificacao_minima_suficiente": clean_text(raw.get("justificacao_expandida_final")),
        "ponte_entrada": clean_text(raw.get("ponte_entrada")),
        "ponte_saida": clean_text(raw.get("ponte_saida")),
        "porque_o_anterior_nao_basta": clean_text(raw.get("porque_o_anterior_nao_basta")),
        "porque_nao_pode_ser_suprimido": clean_text(raw.get("porque_nao_pode_ser_suprimido")),
        "objecao_letal_a_bloquear": clean_text(raw.get("objecao_letal")),
        "bloqueio_curto_da_objecao": clean_text(raw.get("bloqueio_curto")),
        "precisa_de_subpasso": bool(raw.get("precisa_de_subpasso")),
        "subpassos_aprovados_ids": substeps,
        "fragmentos_de_apoio_final": normalize_fragment_list(raw.get("fragmentos_selecionados_finais")),
        "objecoes_bloqueadas_final": normalize_string_list(raw.get("objecoes_bloqueadas_final")),
        "fontes_utilizadas": context["fontes_utilizadas"],
        "estado_final_do_passo": state_final,
        "reabrir_em_arbitragem_de_corredor": reopen,
        "justificacao_da_decisao": build_step_decision_justification(raw, context, state_final),
        "observacoes_editoriais": unique_preserve_order(obs),
    }
    return decision


def build_step_decision_justification(raw: Dict[str, Any], context: Dict[str, Any], state_final: str) -> str:
    pieces = [
        f"Foi fixada uma decisão local para {context['step_id']} no corredor {context['corredor']}.",
        f"A formulação final responde ao défice identificado em {context['estado_inicial_do_passo']}.",
        f"A objeção letal bloqueada é: {clean_text(raw.get('objecao_letal'))}.",
    ]
    if raw.get("precisa_de_subpasso"):
        pieces.append("O passo requer decisão mediacional complementar por subpasso.")
    pieces.append(f"Estado final provisório do passo: {state_final}.")
    return " ".join(pieces)


def validate_canonical_step(data: Dict[str, Any]) -> None:
    required_fields = [
        "tipo_registo",
        "corredor",
        "passo_id",
        "numero_final",
        "bloco_id",
        "bloco_titulo",
        "depende_de",
        "prepara",
        "estado_inicial_do_passo",
        "tipos_de_fragilidade_iniciais",
        "decisao_editorial",
        "formulacao_canonica_final",
        "justificacao_minima_suficiente",
        "ponte_entrada",
        "ponte_saida",
        "porque_o_anterior_nao_basta",
        "porque_nao_pode_ser_suprimido",
        "objecao_letal_a_bloquear",
        "bloqueio_curto_da_objecao",
        "precisa_de_subpasso",
        "subpassos_aprovados_ids",
        "fragmentos_de_apoio_final",
        "objecoes_bloqueadas_final",
        "fontes_utilizadas",
        "estado_final_do_passo",
        "reabrir_em_arbitragem_de_corredor",
        "justificacao_da_decisao",
        "observacoes_editoriais",
    ]
    for field in required_fields:
        require(field in data, f"Campo ausente na decisão canónica por passo: {field}")

    require(data["tipo_registo"] == "decisao_passo", "tipo_registo inválido em decisão de passo")
    validate_id(data["corredor"], CORRIDOR_ID_RE, "corredor")
    validate_id(data["passo_id"], STEP_ID_RE, "passo_id")
    require(isinstance(data["numero_final"], int) and data["numero_final"] >= 1, "numero_final inválido")
    require(data["estado_final_do_passo"] in {"aberto", "quase_fechado", "fechado"}, "estado_final_do_passo inválido")
    require(data["decisao_editorial"] in {"manter", "densificar", "reformular", "introduzir_subpasso", "reabrir"}, "decisao_editorial inválida")
    require(isinstance(data["precisa_de_subpasso"], bool), "precisa_de_subpasso tem de ser boolean")
    require(isinstance(data["reabrir_em_arbitragem_de_corredor"], bool), "reabrir_em_arbitragem_de_corredor tem de ser boolean")
    require(isinstance(data["subpassos_aprovados_ids"], list), "subpassos_aprovados_ids tem de ser array")
    require(isinstance(data["fragmentos_de_apoio_final"], list), "fragmentos_de_apoio_final tem de ser array")
    require(isinstance(data["objecoes_bloqueadas_final"], list), "objecoes_bloqueadas_final tem de ser array")
    require(isinstance(data["fontes_utilizadas"], list) and data["fontes_utilizadas"], "fontes_utilizadas tem de ser array não vazio")

    for field in [
        "bloco_id",
        "bloco_titulo",
        "formulacao_canonica_final",
        "justificacao_minima_suficiente",
        "ponte_entrada",
        "ponte_saida",
        "porque_o_anterior_nao_basta",
        "porque_nao_pode_ser_suprimido",
        "objecao_letal_a_bloquear",
        "bloqueio_curto_da_objecao",
        "justificacao_da_decisao",
    ]:
        require(bool(clean_text(data[field])), f"Campo textual vazio em decisão de passo: {field}")

    for substep_id in data["subpassos_aprovados_ids"]:
        validate_id(substep_id, SUBSTEP_ID_RE, "subpasso_id")
    for dep in data["depende_de"]:
        validate_id(dep, STEP_ID_RE, "depende_de")
    for prep in data["prepara"]:
        validate_id(prep, STEP_ID_RE, "prepara")

    if data["precisa_de_subpasso"]:
        require(data["decisao_editorial"] == "introduzir_subpasso" or data["estado_final_do_passo"] in {"quase_fechado", "fechado"}, "Inconsistência entre precisa_de_subpasso e decisão editorial")
    else:
        require(not data["subpassos_aprovados_ids"], "subpassos_aprovados_ids deve estar vazio quando precisa_de_subpasso=false")

    if data["decisao_editorial"] == "reabrir":
        require(data["reabrir_em_arbitragem_de_corredor"] is True, "reabrir exige reabrir_em_arbitragem_de_corredor=true")


def finalize_step_with_substep(step_decision: Dict[str, Any], substep_decision: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not substep_decision:
        validate_canonical_step(step_decision)
        return step_decision

    if substep_decision["decisao_subpasso"] == "aprovado":
        step_decision["subpassos_aprovados_ids"] = unique_preserve_order(
            step_decision.get("subpassos_aprovados_ids", []) + [substep_decision["subpasso_id"]]
        )
        if step_decision["precisa_de_subpasso"]:
            step_decision["estado_final_do_passo"] = infer_step_final_state(
                {
                    "decisao_editorial": step_decision["decisao_editorial"],
                    "precisa_de_subpasso": step_decision["precisa_de_subpasso"],
                    "pendencias": [],
                },
                substep_approved=True,
            )
            step_decision["observacoes_editoriais"] = unique_preserve_order(
                step_decision.get("observacoes_editoriais", []) + [f"Subpasso aprovado: {substep_decision['subpasso_id']}"]
            )
    elif substep_decision["decisao_subpasso"] == "adiado":
        step_decision["estado_final_do_passo"] = "quase_fechado"
        step_decision["observacoes_editoriais"] = unique_preserve_order(
            step_decision.get("observacoes_editoriais", []) + [f"Subpasso adiado: {substep_decision['subpasso_id']}"]
        )
    elif substep_decision["decisao_subpasso"] == "rejeitado" and step_decision["precisa_de_subpasso"]:
        step_decision["estado_final_do_passo"] = "aberto"
        step_decision["reabrir_em_arbitragem_de_corredor"] = True
        step_decision["observacoes_editoriais"] = unique_preserve_order(
            step_decision.get("observacoes_editoriais", []) + [f"Subpasso rejeitado: {substep_decision['subpasso_id']}"]
        )

    validate_canonical_step(step_decision)
    return step_decision


def validate_prompt_substep_response(data: Dict[str, Any]) -> None:
    required_fields = [
        "decisao_subpasso",
        "entra_subpasso",
        "necessidade_detectada",
        "justificacao_da_decisao",
        "formulacao_subpasso",
        "posicao_na_cadeia",
        "funcao_dedutiva",
        "justificacao_minima_suficiente",
        "ponte_entrada",
        "ponte_saida",
        "objecao_letal_a_bloquear",
        "bloqueio_curto",
        "fragmentos_selecionados_finais",
        "objecoes_bloqueadas_final",
        "fontes_utilizadas",
        "estatuto_final_no_mapa",
        "nota_editorial_final",
        "pendencias",
    ]
    for field in required_fields:
        require(field in data, f"Campo ausente na resposta de subpasso: {field}")

    require(data["decisao_subpasso"] in {"aprovado", "rejeitado", "adiado"}, "decisao_subpasso inválida")
    require(isinstance(data["entra_subpasso"], bool), "entra_subpasso tem de ser boolean")
    require(isinstance(data["necessidade_detectada"], bool), "necessidade_detectada tem de ser boolean")
    require(isinstance(data["fragmentos_selecionados_finais"], list), "fragmentos_selecionados_finais tem de ser array")
    require(isinstance(data["objecoes_bloqueadas_final"], list), "objecoes_bloqueadas_final tem de ser array")
    require(isinstance(data["fontes_utilizadas"], list), "fontes_utilizadas tem de ser array")
    require(isinstance(data["pendencias"], list), "pendencias tem de ser array")
    require(bool(clean_text(data["justificacao_da_decisao"])), "justificacao_da_decisao vazia")


def normalize_substep_response(raw: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    note = clean_text(raw.get("nota_editorial_final"))
    pendencias = normalize_string_list(raw.get("pendencias"))
    observations = []
    if note:
        observations.append(note)
    observations.extend([f"Pendência: {item}" for item in pendencias])

    localizacao = raw.get("posicao_na_cadeia") if isinstance(raw.get("posicao_na_cadeia"), dict) else None
    if localizacao is not None:
        localizacao = {
            "modo_de_insercao": clean_text(localizacao.get("modo_de_insercao")),
            "ancorado_no_passo_id": clean_text(localizacao.get("ancorado_no_passo_id") or context["passo_pai_id"]),
            "entra_apos_passo_id": clean_text_or_none(localizacao.get("entra_apos_passo_id")),
            "entra_antes_de_passo_id": clean_text_or_none(localizacao.get("entra_antes_de_passo_id")),
            "justificacao_de_insercao": clean_text(localizacao.get("justificacao_de_insercao")),
        }

    decision = {
        "tipo_registo": "decisao_subpasso",
        "corredor": context["corredor"],
        "passo_pai_id": context["passo_pai_id"],
        "subpasso_id": context["subpasso_id"],
        "numero_ordinal_no_passo": int(context["numero_ordinal_no_passo"]),
        "necessidade_detectada": bool(raw.get("necessidade_detectada")),
        "decisao_subpasso": raw["decisao_subpasso"],
        "justificacao_da_decisao": clean_text(raw.get("justificacao_da_decisao")),
        "formulacao_subpasso": clean_text_or_none(raw.get("formulacao_subpasso")),
        "justificacao_minima_suficiente": clean_text_or_none(raw.get("justificacao_minima_suficiente")),
        "funcao_dedutiva": clean_text_or_none(raw.get("funcao_dedutiva")),
        "localizacao_na_cadeia": localizacao,
        "ponte_entrada": clean_text_or_none(raw.get("ponte_entrada")),
        "ponte_saida": clean_text_or_none(raw.get("ponte_saida")),
        "objecao_letal_a_bloquear": clean_text_or_none(raw.get("objecao_letal_a_bloquear")),
        "bloqueio_curto_da_objecao": clean_text_or_none(raw.get("bloqueio_curto")),
        "fragmentos_de_apoio_final": normalize_fragment_list(raw.get("fragmentos_selecionados_finais")),
        "objecoes_bloqueadas_final": normalize_string_list(raw.get("objecoes_bloqueadas_final")),
        "fontes_utilizadas": unique_preserve_order(normalize_string_list(raw.get("fontes_utilizadas")) + context["fontes_utilizadas"]),
        "estatuto_final_no_mapa": clean_text(raw.get("estatuto_final_no_mapa")),
        "observacoes_editoriais": unique_preserve_order(observations),
    }
    return decision


def validate_canonical_substep(data: Dict[str, Any]) -> None:
    required_fields = [
        "tipo_registo",
        "corredor",
        "passo_pai_id",
        "subpasso_id",
        "numero_ordinal_no_passo",
        "necessidade_detectada",
        "decisao_subpasso",
        "justificacao_da_decisao",
        "formulacao_subpasso",
        "justificacao_minima_suficiente",
        "funcao_dedutiva",
        "localizacao_na_cadeia",
        "ponte_entrada",
        "ponte_saida",
        "objecao_letal_a_bloquear",
        "bloqueio_curto_da_objecao",
        "fragmentos_de_apoio_final",
        "objecoes_bloqueadas_final",
        "fontes_utilizadas",
        "estatuto_final_no_mapa",
        "observacoes_editoriais",
    ]
    for field in required_fields:
        require(field in data, f"Campo ausente na decisão canónica por subpasso: {field}")

    require(data["tipo_registo"] == "decisao_subpasso", "tipo_registo inválido em decisão de subpasso")
    validate_id(data["corredor"], CORRIDOR_ID_RE, "corredor")
    validate_id(data["passo_pai_id"], STEP_ID_RE, "passo_pai_id")
    validate_id(data["subpasso_id"], SUBSTEP_ID_RE, "subpasso_id")
    require(isinstance(data["numero_ordinal_no_passo"], int) and data["numero_ordinal_no_passo"] >= 1, "numero_ordinal_no_passo inválido")
    require(isinstance(data["necessidade_detectada"], bool), "necessidade_detectada tem de ser boolean")
    require(data["decisao_subpasso"] in {"aprovado", "rejeitado", "adiado"}, "decisao_subpasso inválida")
    require(data["estatuto_final_no_mapa"] in {"inserido_no_mapa", "nao_inserido", "pendente"}, "estatuto_final_no_mapa inválido")
    require(isinstance(data["fontes_utilizadas"], list) and data["fontes_utilizadas"], "fontes_utilizadas tem de ser array não vazio")

    if data["decisao_subpasso"] == "aprovado":
        require(bool(data["formulacao_subpasso"]), "Subpasso aprovado exige formulação")
        require(bool(data["funcao_dedutiva"]), "Subpasso aprovado exige função dedutiva")
        require(isinstance(data["localizacao_na_cadeia"], dict), "Subpasso aprovado exige localizacao_na_cadeia")
        require(data["estatuto_final_no_mapa"] == "inserido_no_mapa", "Subpasso aprovado exige estatuto inserido_no_mapa")
    elif data["decisao_subpasso"] == "rejeitado":
        require(data["estatuto_final_no_mapa"] == "nao_inserido", "Subpasso rejeitado exige estatuto nao_inserido")
    elif data["decisao_subpasso"] == "adiado":
        require(data["estatuto_final_no_mapa"] == "pendente", "Subpasso adiado exige estatuto pendente")


def validate_prompt_arbitration_response(data: Dict[str, Any]) -> None:
    required_fields = [
        "sequencia_minima_ficou_fechada",
        "estado_final_do_corredor",
        "passos_a_reabrir",
        "subpassos_aprovados",
        "formulacoes_fixadas",
        "decisoes_por_passo_referenciadas",
        "decisoes_por_subpasso_referenciadas",
        "passos_fechados",
        "passos_quase_fechados",
        "criterio_de_fecho_aplicado",
        "justificacao_da_arbitragem",
        "pendencias_remanescentes",
        "fontes_utilizadas",
        "observacoes_editoriais",
    ]
    for field in required_fields:
        require(field in data, f"Campo ausente na resposta de arbitragem: {field}")

    require(isinstance(data["sequencia_minima_ficou_fechada"], bool), "sequencia_minima_ficou_fechada tem de ser boolean")
    require(data["estado_final_do_corredor"] in {"fechado", "parcial", "reabrir"}, "estado_final_do_corredor inválido")
    for field in [
        "passos_a_reabrir",
        "subpassos_aprovados",
        "formulacoes_fixadas",
        "decisoes_por_passo_referenciadas",
        "decisoes_por_subpasso_referenciadas",
        "passos_fechados",
        "passos_quase_fechados",
        "pendencias_remanescentes",
        "fontes_utilizadas",
        "observacoes_editoriais",
    ]:
        require(isinstance(data[field], list), f"{field} tem de ser array")
    require(bool(clean_text(data["criterio_de_fecho_aplicado"])), "criterio_de_fecho_aplicado vazio")
    require(bool(clean_text(data["justificacao_da_arbitragem"])), "justificacao_da_arbitragem vazia")


def normalize_arbitration_response(raw: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    decision = {
        "tipo_registo": "arbitragem_corredor",
        "corredor": context["corredor"],
        "sequencia_minima_do_corredor": context["sequencia"],
        "decisoes_por_passo_referenciadas": normalize_step_refs(raw.get("decisoes_por_passo_referenciadas")),
        "decisoes_por_subpasso_referenciadas": normalize_substep_refs(raw.get("decisoes_por_subpasso_referenciadas")),
        "passos_fechados": normalize_step_refs(raw.get("passos_fechados")),
        "passos_quase_fechados": normalize_step_refs(raw.get("passos_quase_fechados")),
        "passos_a_reabrir": normalize_step_refs(raw.get("passos_a_reabrir")),
        "subpassos_aprovados": normalize_substep_refs(raw.get("subpassos_aprovados")),
        "formulacoes_fixadas": normalize_formulacoes_fixadas(raw.get("formulacoes_fixadas")),
        "sequencia_minima_ficou_fechada": bool(raw.get("sequencia_minima_ficou_fechada")),
        "estado_final_do_corredor": clean_text(raw.get("estado_final_do_corredor")),
        "criterio_de_fecho_aplicado": clean_text(raw.get("criterio_de_fecho_aplicado")),
        "justificacao_da_arbitragem": clean_text(raw.get("justificacao_da_arbitragem")),
        "pendencias_remanescentes": normalize_string_list(raw.get("pendencias_remanescentes")),
        "fontes_utilizadas": unique_preserve_order(normalize_string_list(raw.get("fontes_utilizadas")) + context["fontes_utilizadas"]),
        "observacoes_editoriais": normalize_string_list(raw.get("observacoes_editoriais")),
    }
    return decision


def normalize_substep_refs(values: Any) -> List[str]:
    result = []
    for value in to_list(values):
        text = clean_text(value)
        if text and SUBSTEP_ID_RE.match(text):
            result.append(text)
    return unique_preserve_order(result)


def normalize_formulacoes_fixadas(values: Any) -> List[Dict[str, str]]:
    result = []
    for value in to_list(values):
        if not isinstance(value, dict):
            continue
        passo_id = clean_text(value.get("passo_id"))
        formulacao = clean_text(value.get("formulacao_canonica_final"))
        if passo_id and formulacao and STEP_ID_RE.match(passo_id):
            result.append({
                "passo_id": passo_id,
                "formulacao_canonica_final": formulacao,
            })
    return unique_preserve_order(result)


def validate_canonical_arbitration(data: Dict[str, Any]) -> None:
    required_fields = [
        "tipo_registo",
        "corredor",
        "sequencia_minima_do_corredor",
        "decisoes_por_passo_referenciadas",
        "decisoes_por_subpasso_referenciadas",
        "passos_fechados",
        "passos_quase_fechados",
        "passos_a_reabrir",
        "subpassos_aprovados",
        "formulacoes_fixadas",
        "sequencia_minima_ficou_fechada",
        "estado_final_do_corredor",
        "criterio_de_fecho_aplicado",
        "justificacao_da_arbitragem",
        "pendencias_remanescentes",
        "fontes_utilizadas",
        "observacoes_editoriais",
    ]
    for field in required_fields:
        require(field in data, f"Campo ausente na arbitragem canónica: {field}")

    require(data["tipo_registo"] == "arbitragem_corredor", "tipo_registo inválido em arbitragem")
    validate_id(data["corredor"], CORRIDOR_ID_RE, "corredor")
    require(isinstance(data["sequencia_minima_ficou_fechada"], bool), "sequencia_minima_ficou_fechada tem de ser boolean")
    require(data["estado_final_do_corredor"] in {"fechado", "parcial", "reabrir"}, "estado_final_do_corredor inválido")
    require(isinstance(data["fontes_utilizadas"], list) and data["fontes_utilizadas"], "fontes_utilizadas tem de ser array não vazio")

    for field in [
        "sequencia_minima_do_corredor",
        "decisoes_por_passo_referenciadas",
        "decisoes_por_subpasso_referenciadas",
        "passos_fechados",
        "passos_quase_fechados",
        "passos_a_reabrir",
        "subpassos_aprovados",
        "formulacoes_fixadas",
        "pendencias_remanescentes",
        "observacoes_editoriais",
    ]:
        require(isinstance(data[field], list), f"{field} tem de ser array")

    for step_id in data["sequencia_minima_do_corredor"]:
        validate_id(step_id, STEP_ID_RE, "sequencia_minima_do_corredor")
    for step_id in data["decisoes_por_passo_referenciadas"]:
        validate_id(step_id, STEP_ID_RE, "decisoes_por_passo_referenciadas")
    for step_id in data["passos_fechados"]:
        validate_id(step_id, STEP_ID_RE, "passos_fechados")
    for step_id in data["passos_quase_fechados"]:
        validate_id(step_id, STEP_ID_RE, "passos_quase_fechados")
    for step_id in data["passos_a_reabrir"]:
        validate_id(step_id, STEP_ID_RE, "passos_a_reabrir")
    for substep_id in data["decisoes_por_subpasso_referenciadas"]:
        validate_id(substep_id, SUBSTEP_ID_RE, "decisoes_por_subpasso_referenciadas")
    for substep_id in data["subpassos_aprovados"]:
        validate_id(substep_id, SUBSTEP_ID_RE, "subpassos_aprovados")
    for item in data["formulacoes_fixadas"]:
        require(isinstance(item, dict), "Cada item de formulacoes_fixadas tem de ser objeto")
        validate_id(item.get("passo_id"), STEP_ID_RE, "formulacoes_fixadas.passo_id")
        require(bool(clean_text(item.get("formulacao_canonica_final"))), "formulacao_canonica_final vazia")

    if data["sequencia_minima_ficou_fechada"]:
        require(data["estado_final_do_corredor"] == "fechado", "Sequência fechada exige estado_final_do_corredor=fechado")
        require(not data["passos_a_reabrir"], "Sequência fechada não pode ter passos_a_reabrir")
    if data["estado_final_do_corredor"] == "reabrir":
        require(bool(data["passos_a_reabrir"]), "Estado reabrir exige passos_a_reabrir não vazio")


def validate_aggregate_output(data: Dict[str, Any]) -> None:
    required_fields = [
        "meta",
        "inputs_utilizados",
        "ordem_de_execucao",
        "decisoes_por_passo",
        "decisoes_por_subpasso",
        "arbitragens_de_corredor",
        "resumo",
    ]
    for field in required_fields:
        require(field in data, f"Campo ausente no output agregado: {field}")

    meta = data["meta"]
    require(isinstance(meta, dict), "meta tem de ser objeto")
    for field in ["gerado_em_utc", "manifesto_utilizado", "modo_execucao", "corredor_inicial_default", "versao_pipeline"]:
        require(field in meta, f"Campo ausente em meta: {field}")

    require(isinstance(data["ordem_de_execucao"], list) and data["ordem_de_execucao"], "ordem_de_execucao tem de ser array não vazio")
    require(isinstance(data["decisoes_por_passo"], list), "decisoes_por_passo tem de ser array")
    require(isinstance(data["decisoes_por_subpasso"], list), "decisoes_por_subpasso tem de ser array")
    require(isinstance(data["arbitragens_de_corredor"], list), "arbitragens_de_corredor tem de ser array")
    require(isinstance(data["resumo"], dict), "resumo tem de ser objeto")

    for item in data["decisoes_por_passo"]:
        validate_canonical_step(item)
    for item in data["decisoes_por_subpasso"]:
        validate_canonical_substep(item)
    for item in data["arbitragens_de_corredor"]:
        validate_canonical_arbitration(item)


def build_dry_run_step_response(context: Dict[str, Any]) -> Dict[str, Any]:
    matriz = context["matriz_step"]
    mapa = context["mapa_step"]
    dossier = context["dossier_step"]
    proble = context["dossier_problem"]

    fragilities = context["tipos_de_fragilidade"]
    precisa = bool(first_non_empty(
        proble.get("subpasso_sugerido"),
        dossier.get("subpasso_sugerido"),
        mapa.get("subpasso_sugerido"),
        matriz.get("subpasso_sugerido"),
    )) or bool(first_non_empty(
        proble.get("precisa_de_subpasso"),
        dossier.get("precisa_de_subpasso"),
        mapa.get("precisa_de_subpasso"),
        matriz.get("precisa_de_subpasso"),
        False,
    ))

    state = context["estado_inicial_do_passo"]
    if precisa:
        decisao_editorial = "introduzir_subpasso"
    elif "formulacao" in fragilities:
        decisao_editorial = "reformular"
    elif "justificacao" in fragilities:
        decisao_editorial = "densificar"
    elif state == "aberto":
        decisao_editorial = "reformular"
    else:
        decisao_editorial = "manter"

    formulacao = clean_text(first_non_empty(
        dossier.get("proposicao_canonica_tecnica"),
        matriz.get("proposicao_canonica_tecnica"),
        mapa.get("proposicao_final"),
        dossier.get("proposicao_canonica_curta"),
        matriz.get("proposicao_canonica_curta"),
        mapa.get("tese_minima"),
    ))
    justificacao = clean_text(first_non_empty(
        mapa.get("justificacao_minima_suficiente"),
        matriz.get("justificacao_minima_canonica"),
        dossier.get("justificacao_minima_canonica"),
    ))
    if not justificacao:
        justificacao = f"{formulacao} é necessário para evitar salto dedutivo entre os passos adjacentes do corredor {context['corredor']}."

    anterior = context["passo_anterior_id"] or "o enquadramento anterior"
    seguinte = context["passo_seguinte_id"] or "o passo seguinte"
    because_previous = clean_text(first_non_empty(
        matriz.get("porque_o_anterior_nao_basta"),
        mapa.get("porque_o_anterior_nao_basta"),
        dossier.get("porque_o_anterior_nao_basta"),
    )) or f"{anterior} ainda não fixa explicitamente o ganho dedutivo próprio de {context['step_id']}."
    non_suppress = clean_text(first_non_empty(
        matriz.get("porque_nao_pode_ser_suprimido"),
        mapa.get("porque_nao_pode_ser_suprimido"),
        dossier.get("porque_nao_pode_ser_suprimido"),
    )) or f"Sem {context['step_id']}, a passagem para {seguinte} fica como salto dedutivo." 
    objecao = clean_text(first_non_empty(
        proble.get("objecao_letal_a_bloquear"),
        matriz.get("objecao_letal_a_bloquear"),
        mapa.get("objecao_letal_a_bloquear"),
        dossier.get("objecao_letal_a_bloquear"),
    )) or "objeção residual não especificada"

    ponte_entrada = f"{anterior} deixa em aberto o ganho que {context['step_id']} fixa; por isso torna-se necessário afirmar que {formulacao}"
    if not context["passo_anterior_id"]:
        ponte_entrada = f"Este passo abre localmente a cadeia do corredor ao fixar que {formulacao}"
    ponte_saida = f"Uma vez fixado que {formulacao}, fica preparado o terreno para {seguinte}."
    if not context["passo_seguinte_id"]:
        ponte_saida = f"Com isto, o corredor {context['corredor']} fecha a função dedutiva atribuída a {context['step_id']}."

    bloqueio_curto = f"Se {objecao} fosse aceite, {context['step_id']} perderia ancoragem no real; mas a justificação mínima mostra que isso destrói a passagem dedutiva local."
    objecoes = normalize_string_list(first_non_empty(
        dossier.get("objecoes_bloqueadas"),
        mapa.get("objecoes_bloqueadas"),
        matriz.get("objecoes_bloqueadas"),
        [objecao],
    ))
    if objecao not in objecoes:
        objecoes.append(objecao)

    fragmentos = normalize_fragment_list(first_non_empty(
        dossier.get("fragmentos_de_apoio_final"),
        mapa.get("fragmentos_de_apoio_final"),
        matriz.get("fragmentos_de_apoio_final"),
        [],
    ))

    pendencias = []
    if state in {"aberto", "quase_fechado"} and precisa:
        pendencias.append("Falta decisão final sobre o subpasso mediacional sugerido.")
    elif state == "aberto" and "mediacao" in fragilities:
        pendencias.append("A mediação local ainda precisa de consolidação explícita.")

    note = f"Fecho local preparado para {context['step_id']} no corredor {context['corredor']}."

    return {
        "decisao_editorial": decisao_editorial,
        "formulacao_v2_final": formulacao,
        "justificacao_expandida_final": justificacao,
        "ponte_entrada": ponte_entrada,
        "ponte_saida": ponte_saida,
        "porque_o_anterior_nao_basta": because_previous,
        "porque_nao_pode_ser_suprimido": non_suppress,
        "objecao_letal": objecao,
        "bloqueio_curto": bloqueio_curto,
        "objecoes_bloqueadas_final": unique_preserve_order(objecoes),
        "fragmentos_selecionados_finais": fragmentos,
        "nota_editorial_final": note,
        "pendencias": pendencias,
        "precisa_de_subpasso": precisa,
    }


def build_dry_run_substep_response(context: Dict[str, Any]) -> Dict[str, Any]:
    step_context = context["step_context"]
    suggestion = clean_text(first_non_empty(
        step_context["dossier_problem"].get("subpasso_sugerido"),
        step_context["dossier_step"].get("subpasso_sugerido"),
        step_context["mapa_step"].get("subpasso_sugerido"),
        step_context["matriz_step"].get("subpasso_sugerido"),
    ))
    need = bool(context["raw_step_response"].get("precisa_de_subpasso") or suggestion)
    if need:
        decisao = "aprovado"
        entra = True
        formula = suggestion or f"Tornar explícita a mediação necessária para {context['passo_pai_id']}."
        modo = "ponte_mediacional" if "mediacao" in step_context["tipos_de_fragilidade"] else "explicitacao_de_pressuposto"
        posicao = {
            "modo_de_insercao": modo,
            "ancorado_no_passo_id": context["passo_pai_id"],
            "entra_apos_passo_id": context["passo_anterior_id"],
            "entra_antes_de_passo_id": context["passo_pai_id"],
            "justificacao_de_insercao": f"O passo {context['passo_pai_id']} precisa de mediação explícita para fechar sem salto.",
        }
        funcao = f"Fazer a ponte inferencial que permite estabilizar {context['passo_pai_id']} sem salto dedutivo."
        justificacao = f"O subpasso é necessário porque a formulação atual de {context['passo_pai_id']} ainda depende de mediação intermédia explícita."
        ponte_entrada = f"A partir de {context['passo_anterior_id'] or 'o contexto anterior'}, explicita-se a condição intermédia que prepara {context['passo_pai_id']}."
        ponte_saida = f"Com o subpasso fixado, {context['passo_pai_id']} pode ser afirmado sem lacuna mediacional." 
        objecao = clean_text(context["raw_step_response"].get("objecao_letal")) or clean_text(step_context["matriz_step"].get("objecao_letal_a_bloquear"))
        bloqueio = f"Sem esta mediação, {objecao or 'a objeção residual'} reabre o salto local; com ela, o passo fica ancorado." if objecao else "O subpasso bloqueia a lacuna mediacional identificada."
        estatuto = "inserido_no_mapa"
        pendencias: List[str] = []
    else:
        decisao = "rejeitado"
        entra = False
        formula = None
        posicao = None
        funcao = None
        justificacao = f"O passo {context['passo_pai_id']} fecha sem necessidade de subpasso autónomo."
        ponte_entrada = None
        ponte_saida = None
        objecao = None
        bloqueio = None
        estatuto = "nao_inserido"
        pendencias = []

    fragmentos = normalize_fragment_list(first_non_empty(
        step_context["dossier_step"].get("fragmentos_de_apoio_final"),
        step_context["mapa_step"].get("fragmentos_de_apoio_final"),
        step_context["matriz_step"].get("fragmentos_de_apoio_final"),
        [],
    ))

    return {
        "decisao_subpasso": decisao,
        "entra_subpasso": entra,
        "necessidade_detectada": need,
        "justificacao_da_decisao": justificacao,
        "formulacao_subpasso": formula,
        "posicao_na_cadeia": posicao,
        "funcao_dedutiva": funcao,
        "justificacao_minima_suficiente": justificacao if need else None,
        "ponte_entrada": ponte_entrada,
        "ponte_saida": ponte_saida,
        "objecao_letal_a_bloquear": objecao,
        "bloqueio_curto": bloqueio,
        "fragmentos_selecionados_finais": fragmentos,
        "objecoes_bloqueadas_final": normalize_string_list([objecao] if objecao else []),
        "fontes_utilizadas": context["fontes_utilizadas"],
        "estatuto_final_no_mapa": estatuto,
        "nota_editorial_final": f"Decisão mediacional local para {context['subpasso_id']}.",
        "pendencias": pendencias,
    }


def build_dry_run_arbitration_response(context: Dict[str, Any]) -> Dict[str, Any]:
    steps = context["decisoes_passo"]
    substeps = context["decisoes_subpasso"]
    step_ids = [item["passo_id"] for item in steps]
    substep_ids = [item["subpasso_id"] for item in substeps]
    fechados = [item["passo_id"] for item in steps if item["estado_final_do_passo"] == "fechado"]
    quase = [item["passo_id"] for item in steps if item["estado_final_do_passo"] == "quase_fechado"]
    reabrir = [item["passo_id"] for item in steps if item["estado_final_do_passo"] == "aberto" or item["reabrir_em_arbitragem_de_corredor"]]
    aprovados = [item["subpasso_id"] for item in substeps if item["decisao_subpasso"] == "aprovado"]
    fixadas = [
        {"passo_id": item["passo_id"], "formulacao_canonica_final": item["formulacao_canonica_final"]}
        for item in steps if item["estado_final_do_passo"] == "fechado"
    ]

    if len(fechados) == len(context["sequencia"]):
        sequencia_fechada = True
        estado = "fechado"
        pendencias: List[str] = []
    elif reabrir:
        sequencia_fechada = False
        estado = "reabrir"
        pendencias = [f"Passos ainda a reabrir: {', '.join(reabrir)}."]
    else:
        sequencia_fechada = False
        estado = "parcial"
        pendencias = ["Persistem lacunas locais apesar do avanço do corredor."]

    return {
        "sequencia_minima_ficou_fechada": sequencia_fechada,
        "estado_final_do_corredor": estado,
        "passos_a_reabrir": reabrir,
        "subpassos_aprovados": aprovados,
        "formulacoes_fixadas": fixadas,
        "decisoes_por_passo_referenciadas": step_ids,
        "decisoes_por_subpasso_referenciadas": substep_ids,
        "passos_fechados": fechados,
        "passos_quase_fechados": quase,
        "criterio_de_fecho_aplicado": "Fecho do corredor apenas quando a sequência mínima fica sem salto impeditivo.",
        "justificacao_da_arbitragem": f"A arbitragem do corredor {context['corredor']} consolida apenas o que já pode ser tomado como estável ao nível local.",
        "pendencias_remanescentes": pendencias,
        "fontes_utilizadas": context["fontes_utilizadas"],
        "observacoes_editoriais": [f"Arbitragem local concluída para {context['corredor']}."],
    }


def should_run_substep(raw_step_response: Dict[str, Any], step_context: Dict[str, Any]) -> bool:
    if bool(raw_step_response.get("precisa_de_subpasso")):
        return True
    if clean_text(first_non_empty(
        step_context["dossier_problem"].get("subpasso_sugerido"),
        step_context["dossier_step"].get("subpasso_sugerido"),
        step_context["mapa_step"].get("subpasso_sugerido"),
        step_context["matriz_step"].get("subpasso_sugerido"),
    )):
        return True
    if "mediacao" in step_context["tipos_de_fragilidade"]:
        return True
    return False


def process_step(
    runtime: Dict[str, Any],
    indices: Dict[str, Any],
    args: argparse.Namespace,
    corridor: str,
    sequence: Sequence[str],
    step_id: str,
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    context = build_step_context(runtime, indices, corridor, step_id, sequence)
    step_prompt = runtime["prompts"]["prompt_passo_nuclear"]["text"]
    rendered_step_prompt = render_prompt(step_prompt, step_prompt_replacements(context))
    dry_step = build_dry_run_step_response(context)

    raw_text, raw_json, api_meta, mode = execute_stage(
        runtime=runtime,
        args=args,
        corridor=corridor,
        stage="passo_nuclear",
        target_id=step_id,
        prompt_text=rendered_step_prompt,
        dry_run_payload=dry_step,
    )
    validate_prompt_step_response(raw_json)
    canonical_step = normalize_step_response(raw_json, context)
    validate_canonical_step(canonical_step)

    raw_substep = None
    canonical_substep = None
    if should_run_substep(raw_json, context):
        substep_context = build_substep_context(runtime, context, raw_json, canonical_step)
        substep_prompt = runtime["prompts"]["prompt_subpasso_mediacional"]["text"]
        rendered_substep_prompt = render_prompt(substep_prompt, substep_prompt_replacements(substep_context))
        dry_substep = build_dry_run_substep_response(substep_context)
        raw_substep_text, raw_substep, api_meta_substep, mode_substep = execute_stage(
            runtime=runtime,
            args=args,
            corridor=corridor,
            stage="subpasso_mediacional",
            target_id=substep_context["subpasso_id"],
            prompt_text=rendered_substep_prompt,
            dry_run_payload=dry_substep,
        )
        validate_prompt_substep_response(raw_substep)
        canonical_substep = normalize_substep_response(raw_substep, substep_context)
        validate_canonical_substep(canonical_substep)
        canonical_step = finalize_step_with_substep(canonical_step, canonical_substep)

        save_model_artifacts(
            runtime=runtime,
            corridor=corridor,
            stage="subpasso_mediacional",
            target_id=substep_context["subpasso_id"],
            raw_text=raw_substep_text,
            raw_json=raw_substep,
            normalized_json=canonical_substep,
            validation={
                "prompt_response_valid": True,
                "canonical_valid": True,
                "api_meta": api_meta_substep,
            },
            mode=mode_substep,
        )

    save_model_artifacts(
        runtime=runtime,
        corridor=corridor,
        stage="passo_nuclear",
        target_id=step_id,
        raw_text=raw_text,
        raw_json=raw_json,
        normalized_json=canonical_step,
        validation={
            "prompt_response_valid": True,
            "canonical_valid": True,
            "api_meta": api_meta,
        },
        mode=mode,
    )

    return canonical_step, canonical_substep


def process_corridor(
    runtime: Dict[str, Any],
    indices: Dict[str, Any],
    args: argparse.Namespace,
    corridor: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    dossier = indices["dossiers"].get(corridor)
    require(dossier is not None, f"Dossier do corredor não encontrado: {corridor}")
    sequence = to_list(dossier["data"].get("sequencia_minima_do_corredor", []))
    require(sequence, f"Sequência mínima ausente no dossier do corredor {corridor}")

    if args.max_steps is not None:
        sequence = sequence[: args.max_steps]

    logging.info("A processar corredor %s com %d passo(s).", corridor, len(sequence))

    step_decisions: List[Dict[str, Any]] = []
    substep_decisions: List[Dict[str, Any]] = []

    for step_id in sequence:
        logging.info("A processar passo %s no corredor %s.", step_id, corridor)
        step_decision, substep_decision = process_step(runtime, indices, args, corridor, sequence, step_id)
        step_decisions.append(step_decision)
        if substep_decision:
            substep_decisions.append(substep_decision)

    corridor_context = build_corridor_context(runtime, indices, corridor, sequence, step_decisions, substep_decisions)
    arbitration_prompt = runtime["prompts"]["prompt_arbitragem_corredor"]["text"]
    rendered_arbitration_prompt = render_prompt(arbitration_prompt, arbitration_prompt_replacements(corridor_context))
    dry_arbitration = build_dry_run_arbitration_response(corridor_context)

    raw_text, raw_json, api_meta, mode = execute_stage(
        runtime=runtime,
        args=args,
        corridor=corridor,
        stage="arbitragem_corredor",
        target_id=corridor,
        prompt_text=rendered_arbitration_prompt,
        dry_run_payload=dry_arbitration,
    )
    validate_prompt_arbitration_response(raw_json)
    canonical_arbitration = normalize_arbitration_response(raw_json, corridor_context)
    validate_canonical_arbitration(canonical_arbitration)

    save_model_artifacts(
        runtime=runtime,
        corridor=corridor,
        stage="arbitragem_corredor",
        target_id=corridor,
        raw_text=raw_text,
        raw_json=raw_json,
        normalized_json=canonical_arbitration,
        validation={
            "prompt_response_valid": True,
            "canonical_valid": True,
            "api_meta": api_meta,
        },
        mode=mode,
    )

    return step_decisions, substep_decisions, canonical_arbitration


def build_inputs_utilizados(runtime: Dict[str, Any]) -> Dict[str, List[str]]:
    nucleares = [entry["rel_path"] for entry in runtime["inputs_nucleares"].values() if entry["exists"]]
    secundarios = [entry["rel_path"] for entry in runtime["inputs_secundarios"].values() if entry["exists"]]
    return {
        "inputs_nucleares": unique_preserve_order(nucleares),
        "inputs_secundarios": unique_preserve_order(secundarios),
    }


def build_summary(
    step_decisions: List[Dict[str, Any]],
    substep_decisions: List[Dict[str, Any]],
    arbitrations: List[Dict[str, Any]],
) -> Dict[str, int]:
    return {
        "total_decisoes_por_passo": len(step_decisions),
        "total_decisoes_por_subpasso": len(substep_decisions),
        "total_arbitragens_de_corredor": len(arbitrations),
        "passos_fechados": sum(1 for item in step_decisions if item["estado_final_do_passo"] == "fechado"),
        "passos_quase_fechados": sum(1 for item in step_decisions if item["estado_final_do_passo"] == "quase_fechado"),
        "passos_abertos": sum(1 for item in step_decisions if item["estado_final_do_passo"] == "aberto"),
        "subpassos_aprovados": sum(1 for item in substep_decisions if item["decisao_subpasso"] == "aprovado"),
        "subpassos_rejeitados": sum(1 for item in substep_decisions if item["decisao_subpasso"] == "rejeitado"),
        "subpassos_adiados": sum(1 for item in substep_decisions if item["decisao_subpasso"] == "adiado"),
        "corredores_fechados": sum(1 for item in arbitrations if item["estado_final_do_corredor"] == "fechado"),
        "corredores_parciais": sum(1 for item in arbitrations if item["estado_final_do_corredor"] == "parcial"),
        "corredores_para_reabrir": sum(1 for item in arbitrations if item["estado_final_do_corredor"] == "reabrir"),
    }


def build_aggregate_output(
    runtime: Dict[str, Any],
    manifest_path: Path,
    order: List[str],
    step_decisions: List[Dict[str, Any]],
    substep_decisions: List[Dict[str, Any]],
    arbitrations: List[Dict[str, Any]],
    mode: str,
) -> Dict[str, Any]:
    manifest_rel = relative_to_base(manifest_path, runtime["base_dir"])
    return {
        "meta": {
            "gerado_em_utc": utc_now_iso(),
            "manifesto_utilizado": manifest_rel,
            "modo_execucao": mode,
            "corredor_inicial_default": "P33_P37",
            "versao_pipeline": PIPELINE_VERSION,
        },
        "inputs_utilizados": build_inputs_utilizados(runtime),
        "ordem_de_execucao": order,
        "decisoes_por_passo": step_decisions,
        "decisoes_por_subpasso": substep_decisions,
        "arbitragens_de_corredor": arbitrations,
        "resumo": build_summary(step_decisions, substep_decisions, arbitrations),
    }


def write_intermediate_output(runtime: Dict[str, Any], aggregate: Dict[str, Any]) -> Path:
    output_entry = runtime["outputs_intermedios"].get("decisoes_canonicas_intermedias")
    require(output_entry is not None, "Output intermédio decisoes_canonicas_intermedias não definido no manifesto.")
    output_path = output_entry["path"]
    write_json(output_path, aggregate)
    return output_path


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifesto).expanduser().resolve()
    temp_base_dir = manifest_path.parent if manifest_path.exists() else Path(__file__).resolve().parent
    temp_dirs = infer_dirs({}, temp_base_dir)
    configure_logging(temp_dirs["logs"], args.log_level)

    logging.info("A iniciar orquestrador do fecho canónico.")
    manifest, base_dir = load_manifest(manifest_path)
    runtime = load_runtime(manifest, base_dir)
    configure_logging(runtime["dirs"]["logs"], args.log_level)

    logging.info("Manifesto carregado: %s", manifest_path)
    indices = build_indices(runtime)
    corridors = ordered_corridors(manifest, args.only_corridor)
    logging.info("Ordem de execução: %s", ", ".join(corridors))

    all_step_decisions: List[Dict[str, Any]] = []
    all_substep_decisions: List[Dict[str, Any]] = []
    all_arbitrations: List[Dict[str, Any]] = []

    for corridor in corridors:
        if corridor not in indices["dossiers"]:
            logging.warning("Corredor %s ignorado por falta de dossier correspondente.", corridor)
            continue
        step_decisions, substep_decisions, arbitration = process_corridor(runtime, indices, args, corridor)
        all_step_decisions.extend(step_decisions)
        all_substep_decisions.extend(substep_decisions)
        all_arbitrations.append(arbitration)

    aggregate = build_aggregate_output(
        runtime=runtime,
        manifest_path=manifest_path,
        order=[corridor for corridor in corridors if corridor in indices["dossiers"]],
        step_decisions=all_step_decisions,
        substep_decisions=all_substep_decisions,
        arbitrations=all_arbitrations,
        mode="local_auditavel_dry_run" if args.dry_run else "local_auditavel_api",
    )
    validate_aggregate_output(aggregate)
    output_path = write_intermediate_output(runtime, aggregate)
    logging.info("Output intermédio escrito em: %s", output_path)
    logging.info("Execução concluída com sucesso.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logging.exception("Execução interrompida por erro: %s", exc)
        raise
