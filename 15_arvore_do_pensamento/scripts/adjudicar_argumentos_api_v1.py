# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import sys
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

try:
    from dotenv import load_dotenv
except ImportError as exc:  # pragma: no cover - dependência externa exigida pelo utilizador
    load_dotenv = None  # type: ignore[assignment]
    DOTENV_IMPORT_ERROR = exc
else:
    DOTENV_IMPORT_ERROR = None

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - dependência externa exigida pelo utilizador
    OpenAI = None  # type: ignore[assignment]
    OPENAI_IMPORT_ERROR = exc
else:
    OPENAI_IMPORT_ERROR = None

INPUT_TREE_FILENAME = "arvore_do_pensamento_v1_fecho_superior.json"
INPUT_TRIAGEM_JSON_FILENAME = "triagem_fecho_superior_v1.json"
INPUT_TRIAGEM_REPORT_FILENAME = "relatorio_triagem_fecho_superior_v1.txt"
INPUT_REPORT_REVISAO_PERCURSOS = "relatorio_revisao_percursos_superiores_v1.txt"
INPUT_REPORT_GERACAO_ARGUMENTOS = "relatorio_geracao_argumentos_v1.txt"
INPUT_REPORT_VALIDACAO_ARGUMENTOS = "relatorio_validacao_argumentos_v1.txt"
INPUT_REPORT_REVISAO_ARGUMENTOS = "relatorio_revisao_argumentos_restritiva_v1.txt"

OUTPUT_JSON_FILENAME = "adjudicacao_argumentos_api_v1.json"
OUTPUT_REPORT_FILENAME = "relatorio_adjudicacao_argumentos_api_v1.txt"
OUTPUT_LOGS_JSONL_FILENAME = "adjudicacao_argumentos_api_v1_logs.jsonl"
OUTPUT_STATE_FILENAME = "adjudicacao_argumentos_api_v1_estado.json"

CONFIG: Dict[str, Any] = {
    "model_primary": "gpt-4.1-mini",
    "model_fallback": "gpt-4.1-mini",
    "max_retries_per_stage": 3,
    "retry_backoff_seconds": 2.0,
    "temperature": 0.1,
    "max_output_tokens": 1400,
    "store": False,
    "max_ramos_por_execucao": None,
    "reprocessar_concluidos": False,
    "guardar_logs_intermedios": True,
    "dry_run": False,
    "confianca_minima_manter_1": 0.55,
    "confianca_minima_manter_2": 0.72,
    "confianca_minima_para_revisao_humana": 0.40,
    "comprimento_maximo_resposta_log": 1600,
}

RAMO_ID_RE = re.compile(r"\b(RA_\d{4})\b")
PERCURSO_ID_RE = re.compile(r"\b(P_[A-Z0-9_]+)\b")
ARGUMENTO_ID_RE = re.compile(r"\b(ARG_[A-Z0-9_]+)\b")
WARNING_LINE_RE = re.compile(r"^\s*-\s*(RA_\d{4})\s*->\s*(.*?)\s*\[([A-Za-z_]+)\]:\s*(.*)$")
GENERATION_LOG_RE = re.compile(r"^(RA_\d{4})\s*->\s*(ARG_[A-Z0-9_]+)\s*\|\s*score=(\d+)\s*\|\s*(.*)$")
GENERATION_EMPTY_RE = re.compile(r"^(RA_\d{4})\s*->\s*sem associação suficiente\s*$", re.IGNORECASE)
DETAIL_HEADER_RE = re.compile(
    r"^(RA_\d{4})\s*\|\s*universo=([^|]+)\|\s*percursos=(.*?)\|\s*anteriores=(.*?)\|\s*finais=(.*?)\|\s*decisão=([A-Za-z0-9_]+)\s*$"
)
CANDIDATE_LINE_RE = re.compile(
    r"^-\s*(ARG_[A-Z0-9_]+)\s*\|\s*score=([^|]+)\|\s*rank=([^|]+)\|\s*suficiente=([^|]+)\|\s*aviso=(.*)$"
)
SUMMARY_MANUAL_RE = re.compile(
    r"^Ramos que ainda exigem atenção manual.*?:\s*(.*)$",
    re.IGNORECASE,
)
SUMMARY_TOTAL_RETRIES_RE = re.compile(r"\b(retries|tentativas)\b", re.IGNORECASE)

PERCURSO_FIELD_CANDIDATES = (
    "percurso_ids_associados",
    "percurso_ids",
    "percursos_associados",
    "percursos_ids",
)
ARGUMENTO_FIELD_CANDIDATES = (
    "argumento_ids_associados",
    "argumento_ids",
    "argumentos_associados",
    "argumentos_ids",
)
RAMO_IDS_FIELD_CANDIDATES = (
    "ramo_ids",
    "ramo_ids_associados",
)

PRIORITY_RAMO_KEYS = (
    "titulo",
    "rotulo",
    "descricao",
    "descricao_curta",
    "resumo",
    "sintese",
    "texto",
    "texto_sintese",
    "zona_dominante",
    "problema_dominante",
    "trabalho_dominante",
    "problema_trabalho_dominante",
    "tipo_utilidade",
    "efeito_no_mapa",
    "efeito_mapa",
    "passo_alvo",
    "passos_alvo",
    "conceito_alvo",
    "operacao_dominante",
    "estado_validacao",
    "observacoes",
)

NEGATIVE_MANUAL_KEYWORDS = (
    "revisão manual",
    "revisao manual",
    "não decidido",
    "nao decidido",
    "empate",
    "concorrência",
    "concorrencia",
    "heterogeneidade impeditiva",
    "manual",
)

STAGE1_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "ramo_id": {"type": "string"},
        "funcao_estrutural_dominante": {"type": "string"},
        "operacao_dominante": {"type": "string"},
        "tipo_de_argumento_adequado": {"type": "string"},
        "riscos_identificados": {
            "type": "array",
            "items": {"type": "string"},
        },
        "confianca": {"type": "number"},
    },
    "required": [
        "ramo_id",
        "funcao_estrutural_dominante",
        "operacao_dominante",
        "tipo_de_argumento_adequado",
        "riscos_identificados",
        "confianca",
    ],
}

STAGE2_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "ramo_id": {"type": "string"},
        "avaliacoes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "argumento_id": {"type": "string"},
                    "exprime_funcao_dominante": {"type": "boolean"},
                    "compatibilidade_estrutural": {
                        "type": "string",
                        "enum": ["forte", "moderada", "fraca", "incompativel", "indeterminada"],
                    },
                    "incompatibilidades": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "justificacao_curta": {"type": "string"},
                    "confianca": {"type": "number"},
                },
                "required": [
                    "argumento_id",
                    "exprime_funcao_dominante",
                    "compatibilidade_estrutural",
                    "incompatibilidades",
                    "justificacao_curta",
                    "confianca",
                ],
            },
        },
    },
    "required": ["ramo_id", "avaliacoes"],
}

STAGE3_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "ramo_id": {"type": "string"},
        "decisao_final": {
            "type": "string",
            "enum": ["manter_1", "manter_2_excecional", "manter_0", "revisao_humana_necessaria"],
        },
        "argumentos_mantidos": {
            "type": "array",
            "items": {"type": "string"},
        },
        "argumentos_excluidos": {
            "type": "array",
            "items": {"type": "string"},
        },
        "argumento_dominante": {
            "anyOf": [
                {"type": "string"},
                {"type": "null"},
            ]
        },
        "justificacao_curta": {"type": "string"},
        "motivos_estruturais": {
            "type": "array",
            "items": {"type": "string"},
        },
        "confianca_decisao": {"type": "number"},
        "necessita_revisao_humana": {"type": "boolean"},
    },
    "required": [
        "ramo_id",
        "decisao_final",
        "argumentos_mantidos",
        "argumentos_excluidos",
        "argumento_dominante",
        "justificacao_curta",
        "motivos_estruturais",
        "confianca_decisao",
        "necessita_revisao_humana",
    ],
}

PROMPT_STAGE1_SYSTEM = """\
És um adjudicador estrutural restritivo da zona superior de uma árvore do pensamento.
Trabalhas apenas com os dados fornecidos no dossiê do ramo.

Regras obrigatórias:
- o critério dominante é a função estrutural dominante do ramo;
- não uses mera proximidade temática como justificação suficiente;
- não uses o percurso estabilizado como justificação suficiente para manter argumento;
- não inventes candidatos novos nem dados ausentes;
- na dúvida, assume menor confiança e explicita riscos;
- responde apenas no JSON exigido.
"""

PROMPT_STAGE1_USER = """\
Analisa o seguinte dossiê de ramo manual e devolve a leitura estrutural dominante.

Objetivo:
1. identificar a função estrutural dominante do ramo;
2. identificar a operação dominante que o ramo realiza no sistema;
3. dizer que tipo de argumento seria compatível com essa função;
4. explicitar riscos estruturais de erro nesta adjudicação.

Dossiê do ramo (JSON):
{dossier_json}
"""

PROMPT_STAGE2_SYSTEM = """\
És um avaliador comparativo restritivo de candidatos argumentativos.
Avalia apenas candidatos já presentes no dossiê.

Regras obrigatórias:
- pergunta central: cada candidato exprime ou não a função estrutural dominante do ramo?
- compatibilidade forte exige adequação estrutural, não só afinidade temática;
- marca incompatibilidades quando houver sinais de heterogeneidade de parte, conceito-alvo, nível de operação ou tipo de necessidade;
- não forces cobertura;
- responde apenas no JSON exigido.
"""

PROMPT_STAGE2_USER = """\
Avalia os candidatos argumentativos já existentes para o ramo abaixo.

Objetivo:
1. comparar cada candidato com a função estrutural dominante apurada na etapa 1;
2. dizer se exprime ou não a função dominante;
3. classificar a compatibilidade estrutural;
4. listar incompatibilidades e riscos de heterogeneidade.

Dossiê do ramo (JSON):
{dossier_json}

Saída da etapa 1 (JSON):
{stage1_json}
"""

PROMPT_STAGE3_SYSTEM = """\
És o árbitro final, restritivo e prudente, da adjudicação ramo→argumento.
Só podes escolher entre estas decisões finais:
- manter_1
- manter_2_excecional
- manter_0
- revisao_humana_necessaria

Regras obrigatórias:
- por defeito, o máximo é 1 argumento;
- só pode haver 2 quando ambos são fortemente sustentados e estruturalmente compatíveis;
- nunca mantenhas 2 só porque ambos parecem razoáveis;
- se houver empate sem dominância clara, prefere manter_0 ou revisao_humana_necessaria;
- nunca devolvas argumentos fora da lista de candidatos fornecida;
- responde apenas no JSON exigido.
"""

PROMPT_STAGE3_USER = """\
Toma a decisão final restritiva para o ramo abaixo.

Objetivo:
1. decidir entre manter_1, manter_2_excecional, manter_0 ou revisao_humana_necessaria;
2. indicar argumentos mantidos e excluídos;
3. indicar o argumento dominante, se existir;
4. justificar de forma curta e estrutural.

Dossiê do ramo (JSON):
{dossier_json}

Saída da etapa 1 (JSON):
{stage1_json}

Saída da etapa 2 (JSON):
{stage2_json}

Se houver dúvida real, preferir manter_0 ou revisao_humana_necessaria.
"""


class AdjudicacaoArgumentosAPIError(RuntimeError):
    """Erro fatal na adjudicação assistida por API."""


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
        "report_revisao_percursos": dados_dir / INPUT_REPORT_REVISAO_PERCURSOS,
        "report_geracao_argumentos": dados_dir / INPUT_REPORT_GERACAO_ARGUMENTOS,
        "report_validacao_argumentos": dados_dir / INPUT_REPORT_VALIDACAO_ARGUMENTOS,
        "report_revisao_argumentos": dados_dir / INPUT_REPORT_REVISAO_ARGUMENTOS,
        "output_json": dados_dir / OUTPUT_JSON_FILENAME,
        "output_report": dados_dir / OUTPUT_REPORT_FILENAME,
        "output_logs_jsonl": dados_dir / OUTPUT_LOGS_JSONL_FILENAME,
        "output_state": dados_dir / OUTPUT_STATE_FILENAME,
    }


def resolve_runtime_config() -> Dict[str, Any]:
    cfg = deepcopy(CONFIG)
    cfg["model_primary"] = os.getenv("OPENAI_MODEL_ARGUMENTOS_API_V1", cfg["model_primary"])
    cfg["model_fallback"] = os.getenv("OPENAI_MODEL_ARGUMENTOS_API_V1_FALLBACK", cfg["model_fallback"])
    cfg["max_retries_per_stage"] = int(os.getenv("OPENAI_MAX_RETRIES_ARGUMENTOS_API_V1", str(cfg["max_retries_per_stage"])))
    cfg["retry_backoff_seconds"] = float(os.getenv("OPENAI_BACKOFF_ARGUMENTOS_API_V1", str(cfg["retry_backoff_seconds"])))
    cfg["temperature"] = float(os.getenv("OPENAI_TEMPERATURE_ARGUMENTOS_API_V1", str(cfg["temperature"])))
    cfg["max_output_tokens"] = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS_ARGUMENTOS_API_V1", str(cfg["max_output_tokens"])))
    cfg["store"] = parse_env_bool(os.getenv("OPENAI_STORE_ARGUMENTOS_API_V1"), cfg["store"])
    cfg["reprocessar_concluidos"] = parse_env_bool(os.getenv("REPROCESSAR_ARGUMENTOS_API_V1"), cfg["reprocessar_concluidos"])
    cfg["guardar_logs_intermedios"] = parse_env_bool(os.getenv("GUARDAR_LOGS_ARGUMENTOS_API_V1"), cfg["guardar_logs_intermedios"])
    cfg["dry_run"] = parse_env_bool(os.getenv("DRY_RUN_ARGUMENTOS_API_V1"), cfg["dry_run"])
    max_ramos_raw = os.getenv("MAX_RAMOS_ARGUMENTOS_API_V1")
    if max_ramos_raw:
        cfg["max_ramos_por_execucao"] = int(max_ramos_raw)
    return cfg


def parse_env_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    lowered = value.strip().lower()
    if lowered in {"1", "true", "sim", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "nao", "não", "no", "n", "off"}:
        return False
    return default


def ensure_dependencies() -> None:
    if DOTENV_IMPORT_ERROR is not None:
        raise AdjudicacaoArgumentosAPIError(
            "A dependência 'python-dotenv' não está disponível. Instala-a antes de executar este script."
        ) from DOTENV_IMPORT_ERROR
    if OPENAI_IMPORT_ERROR is not None:
        raise AdjudicacaoArgumentosAPIError(
            "A dependência 'openai' não está disponível. Instala-a antes de executar este script."
        ) from OPENAI_IMPORT_ERROR


def load_environment(paths: Dict[str, Path]) -> None:
    ensure_dependencies()
    dotenv_paths = [
        paths["script_dir"] / ".env",
        paths["arvore_root"] / ".env",
        paths["arvore_root"].parent / ".env",
        Path.cwd() / ".env",
    ]
    loaded_any = False
    for dotenv_path in dotenv_paths:
        if dotenv_path.exists():
            load_dotenv(dotenv_path=dotenv_path, override=False)
            loaded_any = True


def create_openai_client() -> Any:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AdjudicacaoArgumentosAPIError(
            "A variável de ambiente OPENAI_API_KEY não está definida. Carrega-a via .env ou ambiente do processo."
        )
    base_url = os.getenv("OPENAI_BASE_URL")
    client_kwargs: Dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs)


def ensure_required_files(paths: Dict[str, Path]) -> None:
    required = [
        paths["input_tree"],
        paths["triagem_json"],
        paths["triagem_report"],
        paths["report_revisao_percursos"],
        paths["report_geracao_argumentos"],
        paths["report_validacao_argumentos"],
        paths["report_revisao_argumentos"],
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise AdjudicacaoArgumentosAPIError(
            "Faltam ficheiros obrigatórios para a adjudicação assistida por API:\n- "
            + "\n- ".join(missing)
        )


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise AdjudicacaoArgumentosAPIError(f"Ficheiro não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AdjudicacaoArgumentosAPIError(f"JSON inválido em {path}: {exc}") from exc
    except OSError as exc:
        raise AdjudicacaoArgumentosAPIError(f"Não foi possível ler {path}: {exc}") from exc


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise AdjudicacaoArgumentosAPIError(f"Ficheiro não encontrado: {path}") from exc
    except OSError as exc:
        raise AdjudicacaoArgumentosAPIError(f"Não foi possível ler {path}: {exc}") from exc


def save_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        temp_path.replace(path)
    except OSError as exc:
        raise AdjudicacaoArgumentosAPIError(f"Não foi possível escrever {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as exc:
        raise AdjudicacaoArgumentosAPIError(f"Não foi possível escrever o relatório {path}: {exc}") from exc


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError as exc:
        raise AdjudicacaoArgumentosAPIError(f"Não foi possível escrever o log {path}: {exc}") from exc


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    raise AdjudicacaoArgumentosAPIError(
        "Não foi possível localizar um bloco de ramos utilizável na árvore final."
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


def split_csv_like_ids(raw: str, regex: re.Pattern[str]) -> List[str]:
    if not raw:
        return []
    return unique_preserve_order(regex.findall(raw))


def normalize_scalar_for_report(value: str) -> Optional[int]:
    value = value.strip()
    if not value or value.lower() in {"none", "null", "∅"}:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_generation_argumentos_report(text: str) -> Dict[str, Any]:
    by_ramo: Dict[str, List[Dict[str, Any]]] = {}
    empty_ramos: Set[str] = set()
    in_log = False
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
        match = GENERATION_LOG_RE.match(line)
        if match:
            ramo_id, argumento_id, score_raw, reasons_raw = match.groups()
            reasons = [part.strip() for part in reasons_raw.split(";") if part.strip()]
            by_ramo.setdefault(ramo_id, []).append(
                {
                    "argumento_id": argumento_id,
                    "score": int(score_raw),
                    "reasons": reasons,
                }
            )
            continue
        match_empty = GENERATION_EMPTY_RE.match(line)
        if match_empty:
            empty_ramos.add(match_empty.group(1))
    return {
        "entries_by_ramo": by_ramo,
        "empty_ramos": empty_ramos,
    }


def parse_validation_argumentos_report(text: str) -> Dict[str, Any]:
    warnings_by_ramo: Dict[str, List[Dict[str, Any]]] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = WARNING_LINE_RE.match(line)
        if not match:
            continue
        ramo_id, target_block, warning_type, description = match.groups()
        warnings_by_ramo.setdefault(ramo_id, []).append(
            {
                "tipo": warning_type.strip().lower(),
                "descricao": description.strip(),
                "argumento_ids": unique_preserve_order(ARGUMENTO_ID_RE.findall(target_block)),
                "texto_bruto": line,
            }
        )
    return {"warnings_by_ramo": warnings_by_ramo}


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


def parse_revisao_argumentos_report(text: str) -> Dict[str, Any]:
    details: Dict[str, Dict[str, Any]] = {}
    manual_from_summary: List[str] = []
    in_details = False
    current_ramo_id: Optional[str] = None
    current_candidate: Optional[Dict[str, Any]] = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("Listagem detalhada por ramo"):
            in_details = True
            current_ramo_id = None
            current_candidate = None
            continue
        if stripped.startswith("Observações finais"):
            in_details = False
            current_ramo_id = None
            current_candidate = None
            continue

        summary_match = SUMMARY_MANUAL_RE.match(stripped)
        if summary_match:
            manual_from_summary = sorted(
                unique_preserve_order(RAMO_ID_RE.findall(summary_match.group(1))),
                key=ramo_sort_key,
            )
            continue

        if not in_details:
            continue

        header_match = DETAIL_HEADER_RE.match(stripped)
        if header_match:
            ramo_id, universo, percursos_raw, anteriores_raw, finais_raw, decisao = header_match.groups()
            details.setdefault(
                ramo_id,
                {
                    "ramo_id": ramo_id,
                    "universo": universo.strip(),
                    "percurso_ids": split_csv_like_ids(percursos_raw, PERCURSO_ID_RE),
                    "argumento_ids_anteriores": split_csv_like_ids(anteriores_raw, ARGUMENTO_ID_RE),
                    "argumento_ids_finais": split_csv_like_ids(finais_raw, ARGUMENTO_ID_RE),
                    "decisao": decisao.strip(),
                    "motivos": [],
                    "triagem_motivos": [],
                    "factos": [],
                    "inferencias_prudentes": [],
                    "pair_support_reasons": [],
                    "pair_blocking_reasons": [],
                    "manual": decisao.strip() == "revisao_manual_recomendada",
                    "candidatos": [],
                },
            )
            current_ramo_id = ramo_id
            current_candidate = None
            continue

        if current_ramo_id is None:
            continue

        current = details[current_ramo_id]
        candidate_match = CANDIDATE_LINE_RE.match(stripped)
        if candidate_match:
            argumento_id, score_raw, rank_raw, suficiente_raw, aviso_raw = candidate_match.groups()
            current_candidate = {
                "argumento_id": argumento_id,
                "score": normalize_scalar_for_report(score_raw),
                "rank": normalize_scalar_for_report(rank_raw),
                "suficiente": suficiente_raw.strip().lower() == "true",
                "warning_types": [] if aviso_raw.strip() in {"∅", "", "none", "None"} else [part.strip() for part in aviso_raw.split(",") if part.strip()],
                "categorias": [],
                "percurso_overlap": [],
                "reasons": [],
            }
            current["candidatos"].append(current_candidate)
            continue

        if stripped.startswith("motivos:"):
            current["motivos"] = unique_preserve_order(part.strip() for part in stripped.split(":", 1)[1].split(",") if part.strip())
            continue
        if stripped.startswith("triagem_motivos:"):
            current["triagem_motivos"] = unique_preserve_order(part.strip() for part in stripped.split(":", 1)[1].split(",") if part.strip())
            continue
        if stripped.startswith("fundamentos_do_par_excecional:"):
            current["pair_support_reasons"] = unique_preserve_order(part.strip() for part in stripped.split(":", 1)[1].split(",") if part.strip())
            continue
        if stripped.startswith("bloqueios_da_decisao_binaria:"):
            current["pair_blocking_reasons"] = unique_preserve_order(part.strip() for part in stripped.split(":", 1)[1].split(",") if part.strip())
            continue
        if stripped.startswith("factos:"):
            current["factos"] = unique_preserve_order(part.strip() for part in stripped.split(":", 1)[1].split("|") if part.strip())
            continue
        if stripped.startswith("inferências_prudentes:") or stripped.startswith("inferencias_prudentes:"):
            current["inferencias_prudentes"] = unique_preserve_order(part.strip() for part in stripped.split(":", 1)[1].split("|") if part.strip())
            continue
        if stripped.startswith("revisão_manual_recomendada:") or stripped.startswith("revisao_manual_recomendada:"):
            current["manual"] = "sim" in stripped.lower()
            continue
        if current_candidate is not None and stripped.startswith("categorias:"):
            current_candidate["categorias"] = unique_preserve_order(part.strip() for part in stripped.split(":", 1)[1].split(",") if part.strip())
            continue
        if current_candidate is not None and stripped.startswith("percurso_overlap:"):
            current_candidate["percurso_overlap"] = split_csv_like_ids(stripped.split(":", 1)[1], PERCURSO_ID_RE)
            continue
        if current_candidate is not None and stripped.startswith("reasons:"):
            current_candidate["reasons"] = [part.strip() for part in stripped.split(":", 1)[1].split(";") if part.strip()]
            continue

    manual_explicit = sorted(
        unique_preserve_order(
            [
                ramo_id
                for ramo_id, item in details.items()
                if item.get("manual") or item.get("decisao") == "revisao_manual_recomendada"
            ]
        ),
        key=ramo_sort_key,
    )

    return {
        "details_by_ramo": details,
        "manual_from_detail": manual_explicit,
        "manual_from_summary": manual_from_summary,
    }


def parse_text_mentions_by_ramo(text: str) -> Dict[str, List[str]]:
    mentions: Dict[str, List[str]] = {}
    for raw_line in text.splitlines():
        ids = RAMO_ID_RE.findall(raw_line)
        if not ids:
            continue
        for ramo_id in unique_preserve_order(ids):
            mentions.setdefault(ramo_id, []).append(raw_line.strip())
    return mentions


def best_generation_entries_by_argumento(entries: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    by_arg: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        argumento_id = entry.get("argumento_id")
        if not isinstance(argumento_id, str) or not argumento_id:
            continue
        previous = by_arg.get(argumento_id)
        if previous is None:
            by_arg[argumento_id] = dict(entry)
            continue
        prev_score = int(previous.get("score", 0))
        score = int(entry.get("score", 0))
        if score > prev_score:
            by_arg[argumento_id] = dict(entry)
            continue
        if score == prev_score and len(entry.get("reasons", [])) > len(previous.get("reasons", [])):
            by_arg[argumento_id] = dict(entry)
    return by_arg


def build_argumento_profiles(argumentos: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    profiles: Dict[str, Dict[str, Any]] = {}
    for argumento in argumentos:
        if not isinstance(argumento, dict):
            continue
        argumento_id = first_nonempty_string(argumento, ("id",))
        if not argumento_id:
            continue
        fundamenta = argumento.get("fundamenta") if isinstance(argumento.get("fundamenta"), dict) else {}
        estrutura_logica = argumento.get("estrutura_logica") if isinstance(argumento.get("estrutura_logica"), dict) else {}
        proposicoes_fonte = argumento.get("proposicoes_fonte") if isinstance(argumento.get("proposicoes_fonte"), dict) else {}
        profiles[argumento_id] = {
            "id": argumento_id,
            "capitulo": first_nonempty_string(argumento, ("capitulo",)) or "",
            "parte": first_nonempty_string(argumento, ("parte",)) or "",
            "conceito_alvo": first_nonempty_string(argumento, ("conceito_alvo",)) or "",
            "tipo_de_necessidade": first_nonempty_string(argumento, ("tipo_de_necessidade",)) or "",
            "nivel_de_operacao": first_nonempty_string(argumento, ("nivel_de_operacao",)) or "",
            "natureza": first_nonempty_string(argumento, ("natureza",)) or "",
            "criterio_ultimo": first_nonempty_string(argumento, ("criterio_ultimo",)) or "",
            "nivel": argumento.get("nivel"),
            "fundamenta_percursos": safe_list_of_strings(fundamenta.get("percursos")),
            "regimes": safe_list_of_strings(fundamenta.get("regimes")),
            "modulos": safe_list_of_strings(fundamenta.get("modulos")),
            "operacoes_chave": safe_list_of_strings(argumento.get("operacoes_chave")),
            "outputs_instalados": safe_list_of_strings(argumento.get("outputs_instalados")),
            "depende_de_argumentos": safe_list_of_strings(
                (argumento.get("ligacoes_narrativas") or {}).get("depende_de_argumentos")
                if isinstance(argumento.get("ligacoes_narrativas"), dict)
                else []
            ),
            "prepara_argumentos": safe_list_of_strings(
                (argumento.get("ligacoes_narrativas") or {}).get("prepara_argumentos")
                if isinstance(argumento.get("ligacoes_narrativas"), dict)
                else []
            ),
            "conclusao": first_nonempty_string(estrutura_logica, ("conclusao",)) or "",
            "premissas": safe_list_of_strings(estrutura_logica.get("premissas")),
            "deducoes": safe_list_of_strings(estrutura_logica.get("deducoes_necessarias")),
            "proposicoes_premissas": safe_list_of_strings(proposicoes_fonte.get("premissas")),
            "proposicoes_deducoes": safe_list_of_strings(proposicoes_fonte.get("deducoes")),
        }
    return profiles


def evaluate_candidate(
    ramo_id: str,
    argumento_id: str,
    ramo_percurso_ids: List[str],
    current_argumento_ids: List[str],
    argumento_profile: Optional[Dict[str, Any]],
    generation_entry: Optional[Dict[str, Any]],
    warnings_for_ramo: List[Dict[str, Any]],
    review_candidate: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    reasons = list(generation_entry.get("reasons", [])) if isinstance(generation_entry, dict) else []
    score = int(generation_entry.get("score", 0)) if isinstance(generation_entry, dict) else 0
    categories = parse_reason_categories(reasons)
    strong_signal_count = sum(
        1
        for item in categories
        if item in {"passo_forte", "problema_trabalho", "conceito_operacao"}
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
        "modulos": [],
        "operacoes_chave": [],
        "outputs_instalados": [],
        "conclusao": "",
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
        sufficient_for_single = False

    review_rank = review_candidate.get("rank") if isinstance(review_candidate, dict) else None
    if isinstance(review_rank, int):
        rank = review_rank
    else:
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
    if isinstance(review_candidate, dict) and review_candidate:
        factos.append("presente_no_relatorio_restritivo")

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
        "warning_descriptions": [
            warning.get("descricao", "")
            for warning in relevant_warnings
            if isinstance(warning.get("descricao"), str)
        ],
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
        "review_candidate": deepcopy(review_candidate) if isinstance(review_candidate, dict) else {},
    }


def are_pair_compatible(first: Dict[str, Any], second: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
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


def collect_triagem_map(triagem: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    grupos = triagem.get("grupos") if isinstance(triagem.get("grupos"), dict) else {}
    for grupo_key, items in grupos.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            ramo_id = first_nonempty_string(item, ("ramo_id", "id"))
            if not ramo_id:
                continue
            mapping[ramo_id] = {
                "grupo": grupo_key,
                "motivos": safe_list_of_strings(item.get("motivos")),
                "evidencias": item.get("evidencias") if isinstance(item.get("evidencias"), dict) else {},
            }
    return mapping


def extract_local_structural_evidence(ramo: Dict[str, Any]) -> Dict[str, Any]:
    evidence: Dict[str, Any] = {
        "id": first_nonempty_string(ramo, ("id", "ramo_id")) or "",
        "microlinha_ids": get_first_list_of_strings(ramo, ("microlinha_ids", "microlinhas_ids")),
    }
    for key in PRIORITY_RAMO_KEYS:
        value = ramo.get(key)
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            evidence[key] = value
        elif isinstance(value, list):
            simple_items = [item for item in value if isinstance(item, (str, int, float, bool))]
            if simple_items:
                evidence[key] = simple_items[:20]
    extra_simple_fields = 0
    for key, value in ramo.items():
        if key in evidence or key in {"id", "ramo_id"}:
            continue
        if extra_simple_fields >= 8:
            break
        if isinstance(value, (str, int, float, bool)):
            evidence[key] = value
            extra_simple_fields += 1
    return evidence


def extract_argumento_summary(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "argumento_id": profile.get("id", ""),
        "capitulo": profile.get("capitulo", ""),
        "parte": profile.get("parte", ""),
        "conceito_alvo": profile.get("conceito_alvo", ""),
        "tipo_de_necessidade": profile.get("tipo_de_necessidade", ""),
        "nivel_de_operacao": profile.get("nivel_de_operacao", ""),
        "natureza": profile.get("natureza", ""),
        "criterio_ultimo": profile.get("criterio_ultimo", ""),
        "fundamenta_percursos": safe_list_of_strings(profile.get("fundamenta_percursos", [])),
        "regimes": safe_list_of_strings(profile.get("regimes", [])),
        "modulos": safe_list_of_strings(profile.get("modulos", [])),
        "operacoes_chave": safe_list_of_strings(profile.get("operacoes_chave", [])),
        "outputs_instalados": safe_list_of_strings(profile.get("outputs_instalados", [])),
        "conclusao": profile.get("conclusao", ""),
    }


def build_manual_universe(
    triagem_map: Dict[str, Dict[str, Any]],
    ramos_map: Dict[str, Dict[str, Any]],
    revisao_report_data: Dict[str, Any],
    validation_data: Dict[str, Any],
) -> Dict[str, Any]:
    manual_from_detail = set(revisao_report_data.get("manual_from_detail", []))
    manual_from_summary = set(revisao_report_data.get("manual_from_summary", []))
    combined_manual = sorted(unique_preserve_order(list(manual_from_detail) + list(manual_from_summary)), key=ramo_sort_key)

    fallback_added: List[str] = []
    limitations: List[str] = []

    if not combined_manual:
        warnings_by_ramo = validation_data.get("warnings_by_ramo", {})
        fallback_candidates: List[str] = []
        for ramo_id, triagem_item in triagem_map.items():
            if triagem_item.get("grupo") != "A_rever_argumento":
                continue
            ramo = ramos_map.get(ramo_id)
            if not isinstance(ramo, dict):
                continue
            current_argumentos = get_first_list_of_strings(ramo, ARGUMENTO_FIELD_CANDIDATES)
            if len(current_argumentos) == 0 or len(current_argumentos) >= 2 or ramo_id in warnings_by_ramo:
                fallback_candidates.append(ramo_id)
        fallback_added = sorted(unique_preserve_order(fallback_candidates), key=ramo_sort_key)
        combined_manual = fallback_added[:]
        limitations.append(
            "O relatório de revisão restritiva não permitiu extrair casos manuais com segurança suficiente; foi usado um fallback prudente sobre o Grupo A e sinais estruturais atuais."
        )

    return {
        "ramos_manuais": combined_manual,
        "ramos_extraidos_do_relatorio": sorted(manual_from_detail.union(manual_from_summary), key=ramo_sort_key),
        "ramos_adicionados_por_fallback": fallback_added,
        "limitacoes": limitations,
    }


def contains_keyword_substrings(lines: Sequence[str], keywords: Sequence[str]) -> bool:
    lowered_lines = "\n".join(line.lower() for line in lines if isinstance(line, str))
    return any(keyword.lower() in lowered_lines for keyword in keywords)


def build_pairwise_matrix(candidate_evaluations: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    matrix: List[Dict[str, Any]] = []
    items = list(candidate_evaluations)
    for idx, first in enumerate(items):
        for second in items[idx + 1 :]:
            compatible, support, blocking = are_pair_compatible(first, second)
            matrix.append(
                {
                    "argumentos": [first["argumento_id"], second["argumento_id"]],
                    "compativeis_localmente": compatible,
                    "support_reasons": support,
                    "blocking_reasons": blocking,
                }
            )
    return matrix


def build_dossier_for_ramo(
    ramo_id: str,
    ramo: Dict[str, Any],
    triagem_item: Optional[Dict[str, Any]],
    triagem_report_mentions: List[str],
    percursos_review_mentions: List[str],
    generation_entries: List[Dict[str, Any]],
    generation_empty_ramos: Set[str],
    warnings_for_ramo: List[Dict[str, Any]],
    revisao_report_item: Optional[Dict[str, Any]],
    argumento_profiles: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    current_percursos = get_first_list_of_strings(ramo, PERCURSO_FIELD_CANDIDATES)
    current_argumentos = get_first_list_of_strings(ramo, ARGUMENTO_FIELD_CANDIDATES)
    triagem_motivos = triagem_item.get("motivos", []) if isinstance(triagem_item, dict) else []
    generation_by_arg = best_generation_entries_by_argumento(generation_entries)

    review_candidates_by_arg: Dict[str, Dict[str, Any]] = {}
    if isinstance(revisao_report_item, dict):
        for candidate in revisao_report_item.get("candidatos", []):
            if not isinstance(candidate, dict):
                continue
            argumento_id = first_nonempty_string(candidate, ("argumento_id",))
            if argumento_id:
                review_candidates_by_arg[argumento_id] = candidate

    warning_candidate_ids: List[str] = []
    for warning in warnings_for_ramo:
        warning_candidate_ids.extend(safe_list_of_strings(warning.get("argumento_ids")))

    candidate_ids = unique_preserve_order(
        list(current_argumentos)
        + list(generation_by_arg.keys())
        + list(review_candidates_by_arg.keys())
        + warning_candidate_ids
    )

    candidate_evaluations: List[Dict[str, Any]] = []
    missing_profiles: List[str] = []
    for argumento_id in candidate_ids:
        profile = argumento_profiles.get(argumento_id)
        if profile is None:
            missing_profiles.append(argumento_id)
        evaluation = evaluate_candidate(
            ramo_id=ramo_id,
            argumento_id=argumento_id,
            ramo_percurso_ids=current_percursos,
            current_argumento_ids=current_argumentos,
            argumento_profile=profile,
            generation_entry=generation_by_arg.get(argumento_id),
            warnings_for_ramo=warnings_for_ramo,
            review_candidate=review_candidates_by_arg.get(argumento_id),
        )
        evaluation["argumento_summary"] = extract_argumento_summary(evaluation["argumento_profile"])
        candidate_evaluations.append(evaluation)

    candidate_evaluations = sorted(
        candidate_evaluations,
        key=lambda item: (-int(item.get("rank", 0)), -int(item.get("score", 0)), item.get("argumento_id", "")),
    )
    pairwise_matrix = build_pairwise_matrix(candidate_evaluations)

    notas_prudencia: List[str] = []
    if not current_percursos:
        notas_prudencia.append(
            "O ramo está sem percurso estabilizado na árvore final desta fase; o percurso não pode servir como âncora suficiente para manter argumento."
        )
    if ramo_id in generation_empty_ramos:
        notas_prudencia.append(
            "O relatório original de geração marcou o ramo como sem associação suficiente; qualquer manutenção posterior exige prudência acrescida."
        )
    if contains_keyword_substrings(percursos_review_mentions, NEGATIVE_MANUAL_KEYWORDS):
        notas_prudencia.append(
            "O relatório de percursos superiores contém sinais textuais de instabilidade local; não usar esse percurso como justificação suficiente para manter argumento."
        )
    if len(candidate_ids) > 2:
        notas_prudencia.append(
            "Há mais de dois candidatos presentes no dossiê; o critério continua a ser restritivo e não inflacionário."
        )

    lacunas_dados: List[str] = []
    if missing_profiles:
        lacunas_dados.append(
            "Perfis de argumento não localizados na árvore final para: " + ", ".join(sorted(unique_preserve_order(missing_profiles)))
        )
    if not candidate_ids:
        lacunas_dados.append("Nenhum candidato argumentativo foi recuperado com segurança a partir da árvore e dos relatórios.")
    if not triagem_report_mentions:
        lacunas_dados.append("Sem menções específicas ao ramo no relatório de triagem.")
    if not percursos_review_mentions:
        lacunas_dados.append("Sem menções específicas ao ramo no relatório de revisão de percursos.")

    review_decision = first_nonempty_string(revisao_report_item or {}, ("decisao",)) or ""
    universo_anterior = first_nonempty_string(revisao_report_item or {}, ("universo",)) or ""

    return {
        "ramo_id": ramo_id,
        "grupo_original": first_nonempty_string(triagem_item or {}, ("grupo",)) or "desconhecido",
        "triagem_motivos": safe_list_of_strings(triagem_motivos),
        "percurso_ids_estabilizados": current_percursos,
        "argumento_ids_atuais": current_argumentos,
        "evidencia_estrutural_local": extract_local_structural_evidence(ramo),
        "candidatos_argumentativos": [
            {
                "argumento_id": item["argumento_id"],
                "score_geracao": item["score"],
                "rank_restritivo": item.get("review_candidate", {}).get("rank"),
                "suficiente_no_restritivo": item.get("review_candidate", {}).get("suficiente"),
                "reasons_geracao": item["reasons"],
                "categorias_de_razao": item["reason_categories"],
                "percurso_overlap": item["percurso_overlap"],
                "warning_types": item["warning_types"],
                "warning_descriptions": item["warning_descriptions"],
                "factos_locais": item["factos"],
                "inferencias_prudentes_locais": item["inferencias"],
                "perfil_argumento": item["argumento_summary"],
            }
            for item in candidate_evaluations
        ],
        "pairwise_matrix_local": pairwise_matrix,
        "avisos_validacao_ramo": warnings_for_ramo,
        "triagem_report_mentions": triagem_report_mentions,
        "percursos_review_mentions": percursos_review_mentions,
        "revisao_restritiva_anterior": {
            "decisao": review_decision,
            "universo": universo_anterior,
            "motivos": safe_list_of_strings((revisao_report_item or {}).get("motivos")),
            "triagem_motivos": safe_list_of_strings((revisao_report_item or {}).get("triagem_motivos")),
            "factos": safe_list_of_strings((revisao_report_item or {}).get("factos")),
            "inferencias_prudentes": safe_list_of_strings((revisao_report_item or {}).get("inferencias_prudentes")),
            "pair_support_reasons": safe_list_of_strings((revisao_report_item or {}).get("pair_support_reasons")),
            "pair_blocking_reasons": safe_list_of_strings((revisao_report_item or {}).get("pair_blocking_reasons")),
        },
        "notas_de_prudencia": unique_preserve_order(notas_prudencia),
        "lacunas_dados": unique_preserve_order(lacunas_dados),
    }


def compress_dossier_for_prompt(dossier: Dict[str, Any]) -> Dict[str, Any]:
    compressed = {
        "ramo_id": dossier["ramo_id"],
        "grupo_original": dossier["grupo_original"],
        "triagem_motivos": dossier["triagem_motivos"],
        "percurso_ids_estabilizados": dossier["percurso_ids_estabilizados"],
        "argumento_ids_atuais": dossier["argumento_ids_atuais"],
        "evidencia_estrutural_local": dossier["evidencia_estrutural_local"],
        "candidatos_argumentativos": dossier["candidatos_argumentativos"],
        "pairwise_matrix_local": dossier["pairwise_matrix_local"],
        "avisos_validacao_ramo": dossier["avisos_validacao_ramo"],
        "revisao_restritiva_anterior": dossier["revisao_restritiva_anterior"],
        "notas_de_prudencia": dossier["notas_de_prudencia"],
        "lacunas_dados": dossier["lacunas_dados"],
    }
    return compressed


def minimal_json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_messages(stage: str, dossier: Dict[str, Any], stage1: Optional[Dict[str, Any]] = None, stage2: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    dossier_json = minimal_json_dumps(compress_dossier_for_prompt(dossier))
    if stage == "stage1":
        return [
            {"role": "system", "content": PROMPT_STAGE1_SYSTEM},
            {"role": "user", "content": PROMPT_STAGE1_USER.format(dossier_json=dossier_json)},
        ]
    if stage == "stage2":
        if stage1 is None:
            raise ValueError("stage1 é obrigatório para a etapa 2")
        return [
            {"role": "system", "content": PROMPT_STAGE2_SYSTEM},
            {
                "role": "user",
                "content": PROMPT_STAGE2_USER.format(
                    dossier_json=dossier_json,
                    stage1_json=minimal_json_dumps(stage1),
                ),
            },
        ]
    if stage == "stage3":
        if stage1 is None or stage2 is None:
            raise ValueError("stage1 e stage2 são obrigatórios para a etapa 3")
        return [
            {"role": "system", "content": PROMPT_STAGE3_SYSTEM},
            {
                "role": "user",
                "content": PROMPT_STAGE3_USER.format(
                    dossier_json=dossier_json,
                    stage1_json=minimal_json_dumps(stage1),
                    stage2_json=minimal_json_dumps(stage2),
                ),
            },
        ]
    raise ValueError(f"Etapa desconhecida: {stage}")


def get_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = getattr(response, "output", None)
    texts: List[str] = []
    if isinstance(output, list):
        for item in output:
            if isinstance(item, dict):
                content = item.get("content")
            else:
                content = getattr(item, "content", None)
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        text_value = part.get("text") or part.get("output_text")
                    else:
                        text_value = getattr(part, "text", None) or getattr(part, "output_text", None)
                    if isinstance(text_value, str) and text_value.strip():
                        texts.append(text_value.strip())
    if texts:
        return "\n".join(texts)

    try:
        as_dict = response.to_dict()  # type: ignore[attr-defined]
    except Exception:
        as_dict = None
    if isinstance(as_dict, dict):
        maybe_text = as_dict.get("output_text")
        if isinstance(maybe_text, str) and maybe_text.strip():
            return maybe_text.strip()
    raise AdjudicacaoArgumentosAPIError("Resposta da API sem texto estruturado recuperável.")


def call_responses_api(
    client: Any,
    messages: List[Dict[str, str]],
    schema_name: str,
    schema: Dict[str, Any],
    model: str,
    runtime_config: Dict[str, Any],
) -> Any:
    request_kwargs: Dict[str, Any] = {
        "model": model,
        "input": messages,
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": schema,
                "strict": True,
            }
        },
        "store": runtime_config["store"],
        "max_output_tokens": runtime_config["max_output_tokens"],
    }
    temperature = runtime_config.get("temperature")
    if temperature is not None:
        request_kwargs["temperature"] = temperature
    return client.responses.create(**request_kwargs)


def clamp_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number < 0.0:
        return 0.0
    if number > 1.0:
        return 1.0
    return number


def validate_stage1_payload(payload: Dict[str, Any], ramo_id: str) -> Dict[str, Any]:
    required = [
        "ramo_id",
        "funcao_estrutural_dominante",
        "operacao_dominante",
        "tipo_de_argumento_adequado",
        "riscos_identificados",
        "confianca",
    ]
    for key in required:
        if key not in payload:
            raise AdjudicacaoArgumentosAPIError(f"Etapa 1 inválida: falta o campo '{key}'.")
    if payload["ramo_id"] != ramo_id:
        raise AdjudicacaoArgumentosAPIError("Etapa 1 inválida: ramo_id incoerente.")
    if not isinstance(payload["riscos_identificados"], list):
        raise AdjudicacaoArgumentosAPIError("Etapa 1 inválida: 'riscos_identificados' tem de ser lista.")
    payload["riscos_identificados"] = unique_preserve_order(str(item) for item in payload["riscos_identificados"] if isinstance(item, str))
    payload["confianca"] = clamp_confidence(payload["confianca"])
    return payload


def validate_stage2_payload(payload: Dict[str, Any], ramo_id: str, candidate_ids: Sequence[str]) -> Dict[str, Any]:
    if payload.get("ramo_id") != ramo_id:
        raise AdjudicacaoArgumentosAPIError("Etapa 2 inválida: ramo_id incoerente.")
    avaliacoes = payload.get("avaliacoes")
    if not isinstance(avaliacoes, list):
        raise AdjudicacaoArgumentosAPIError("Etapa 2 inválida: 'avaliacoes' tem de ser lista.")
    candidate_set = set(candidate_ids)
    seen: Set[str] = set()
    normalized: List[Dict[str, Any]] = []
    for item in avaliacoes:
        if not isinstance(item, dict):
            continue
        argumento_id = first_nonempty_string(item, ("argumento_id",))
        if not argumento_id or argumento_id not in candidate_set or argumento_id in seen:
            continue
        seen.add(argumento_id)
        compat = first_nonempty_string(item, ("compatibilidade_estrutural",)) or "indeterminada"
        if compat not in {"forte", "moderada", "fraca", "incompativel", "indeterminada"}:
            compat = "indeterminada"
        normalized.append(
            {
                "argumento_id": argumento_id,
                "exprime_funcao_dominante": bool(item.get("exprime_funcao_dominante")),
                "compatibilidade_estrutural": compat,
                "incompatibilidades": unique_preserve_order(
                    str(value) for value in item.get("incompatibilidades", []) if isinstance(value, str)
                ),
                "justificacao_curta": str(item.get("justificacao_curta", "")).strip(),
                "confianca": clamp_confidence(item.get("confianca")),
            }
        )
    missing = sorted(candidate_set.difference(seen))
    if missing:
        raise AdjudicacaoArgumentosAPIError(
            "Etapa 2 inválida: faltam avaliações para candidato(s): " + ", ".join(missing)
        )
    return {"ramo_id": ramo_id, "avaliacoes": normalized}


def validate_stage3_payload(payload: Dict[str, Any], ramo_id: str, candidate_ids: Sequence[str]) -> Dict[str, Any]:
    if payload.get("ramo_id") != ramo_id:
        raise AdjudicacaoArgumentosAPIError("Etapa 3 inválida: ramo_id incoerente.")
    decision = first_nonempty_string(payload, ("decisao_final",))
    if decision not in {"manter_1", "manter_2_excecional", "manter_0", "revisao_humana_necessaria"}:
        raise AdjudicacaoArgumentosAPIError("Etapa 3 inválida: decisão final fora do conjunto permitido.")
    candidate_set = set(candidate_ids)
    kept = unique_preserve_order(
        item for item in safe_list_of_strings(payload.get("argumentos_mantidos")) if item in candidate_set
    )
    excluded = unique_preserve_order(
        item for item in safe_list_of_strings(payload.get("argumentos_excluidos")) if item in candidate_set
    )
    dominant = payload.get("argumento_dominante")
    if dominant is not None and (not isinstance(dominant, str) or dominant not in candidate_set):
        dominant = None
    normalized = {
        "ramo_id": ramo_id,
        "decisao_final": decision,
        "argumentos_mantidos": kept,
        "argumentos_excluidos": excluded,
        "argumento_dominante": dominant,
        "justificacao_curta": str(payload.get("justificacao_curta", "")).strip(),
        "motivos_estruturais": unique_preserve_order(
            str(item) for item in payload.get("motivos_estruturais", []) if isinstance(item, str)
        ),
        "confianca_decisao": clamp_confidence(payload.get("confianca_decisao")),
        "necessita_revisao_humana": bool(payload.get("necessita_revisao_humana")),
    }
    return normalized


def log_attempt(
    logs_path: Path,
    runtime_config: Dict[str, Any],
    ramo_id: str,
    stage_name: str,
    attempt: int,
    status: str,
    model: str,
    payload: Optional[Any] = None,
    error: Optional[str] = None,
) -> None:
    if not runtime_config.get("guardar_logs_intermedios", True):
        return
    serialized_payload = None
    if payload is not None:
        try:
            serialized_payload = json.dumps(payload, ensure_ascii=False)
        except Exception:
            serialized_payload = str(payload)
        max_len = int(runtime_config.get("comprimento_maximo_resposta_log", 1600))
        if len(serialized_payload) > max_len:
            serialized_payload = serialized_payload[: max_len - 3] + "..."
    append_jsonl(
        logs_path,
        {
            "timestamp_utc": utc_now_iso(),
            "ramo_id": ramo_id,
            "stage": stage_name,
            "attempt": attempt,
            "status": status,
            "model": model,
            "payload": serialized_payload,
            "error": error,
        },
    )


def run_stage_with_retries(
    client: Any,
    runtime_config: Dict[str, Any],
    logs_path: Path,
    ramo_id: str,
    stage_name: str,
    messages: List[Dict[str, str]],
    schema_name: str,
    schema: Dict[str, Any],
    validator,
    validator_kwargs: Dict[str, Any],
    model: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    last_error: Optional[str] = None
    attempts_used = 0
    for attempt in range(1, int(runtime_config["max_retries_per_stage"]) + 1):
        attempts_used = attempt
        try:
            if runtime_config.get("dry_run"):
                raise AdjudicacaoArgumentosAPIError("Modo dry_run ativo; etapa não enviada à API.")
            response = call_responses_api(
                client=client,
                messages=messages,
                schema_name=schema_name,
                schema=schema,
                model=model,
                runtime_config=runtime_config,
            )
            text = get_response_text(response)
            parsed = json.loads(text)
            validated = validator(parsed, **validator_kwargs)
            log_attempt(
                logs_path,
                runtime_config,
                ramo_id,
                stage_name,
                attempt,
                "success",
                model,
                payload=validated,
            )
            meta = {
                "attempts": attempt,
                "model": model,
                "response_id": getattr(response, "id", None),
            }
            return validated, meta
        except Exception as exc:
            last_error = str(exc)
            log_attempt(
                logs_path,
                runtime_config,
                ramo_id,
                stage_name,
                attempt,
                "error",
                model,
                error=last_error,
            )
            if attempt < int(runtime_config["max_retries_per_stage"]):
                time.sleep(float(runtime_config["retry_backoff_seconds"]) * attempt)
    raise AdjudicacaoArgumentosAPIError(
        f"Falha na {stage_name} do ramo {ramo_id} após {attempts_used} tentativa(s): {last_error}"
    )


def index_stage2_evaluations(stage2_payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        item["argumento_id"]: item
        for item in stage2_payload.get("avaliacoes", [])
        if isinstance(item, dict) and isinstance(item.get("argumento_id"), str)
    }


def index_local_candidates(dossier: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for item in dossier.get("candidatos_argumentativos", []):
        if not isinstance(item, dict):
            continue
        argumento_id = first_nonempty_string(item, ("argumento_id",))
        if argumento_id:
            mapping[argumento_id] = item
    return mapping


def get_pair_local_constraints(dossier: Dict[str, Any], kept: Sequence[str]) -> Tuple[bool, List[str], List[str]]:
    if len(kept) != 2:
        return False, [], ["par_nao_tem_exatamente_dois_argumentos"]
    target = set(kept)
    for item in dossier.get("pairwise_matrix_local", []):
        if not isinstance(item, dict):
            continue
        pair = set(safe_list_of_strings(item.get("argumentos")))
        if pair == target:
            return bool(item.get("compativeis_localmente")), safe_list_of_strings(item.get("support_reasons")), safe_list_of_strings(item.get("blocking_reasons"))
    return False, [], ["par_nao_avaliado_localmente"]


def arbitrate_final_decision(
    ramo_id: str,
    dossier: Dict[str, Any],
    stage2_payload: Dict[str, Any],
    stage3_payload: Dict[str, Any],
    runtime_config: Dict[str, Any],
) -> Tuple[Dict[str, Any], Optional[str]]:
    candidate_ids = [item["argumento_id"] for item in dossier.get("candidatos_argumentativos", []) if isinstance(item, dict) and isinstance(item.get("argumento_id"), str)]
    candidate_set = set(candidate_ids)
    stage2_index = index_stage2_evaluations(stage2_payload)
    local_candidates = index_local_candidates(dossier)

    decision = stage3_payload["decisao_final"]
    kept = unique_preserve_order(item for item in stage3_payload["argumentos_mantidos"] if item in candidate_set)
    excluded = unique_preserve_order(item for item in stage3_payload["argumentos_excluidos"] if item in candidate_set and item not in kept)
    dominant = stage3_payload["argumento_dominante"]
    if isinstance(dominant, str) and dominant not in kept:
        dominant = None

    if decision == "manter_1":
        if len(kept) != 1:
            return {}, "decisao_manter_1_sem_exatamente_um_argumento"
        candidate_eval = stage2_index.get(kept[0], {})
        compat = candidate_eval.get("compatibilidade_estrutural")
        if compat not in {"forte", "moderada"}:
            return {}, "manter_1_com_compatibilidade_insuficiente_na_etapa_2"
        if not candidate_eval.get("exprime_funcao_dominante"):
            return {}, "manter_1_sem_expressao_da_funcao_dominante"
        if stage3_payload["confianca_decisao"] < float(runtime_config["confianca_minima_manter_1"]):
            return {
                "ramo_id": ramo_id,
                "decisao_final": "revisao_humana_necessaria",
                "argumentos_mantidos": [],
                "argumentos_excluidos": candidate_ids,
                "argumento_dominante": None,
                "justificacao_curta": "Confiança insuficiente para manter automaticamente um único argumento.",
                "motivos_estruturais": ["confianca_baixa_para_manter_1"],
                "confianca_decisao": stage3_payload["confianca_decisao"],
                "necessita_revisao_humana": True,
                "avisos_arbitragem": ["downgrade_para_revisao_humana_por_confianca_baixa"],
            }, None
        return {
            "ramo_id": ramo_id,
            "decisao_final": decision,
            "argumentos_mantidos": kept,
            "argumentos_excluidos": excluded or [item for item in candidate_ids if item not in kept],
            "argumento_dominante": dominant or kept[0],
            "justificacao_curta": stage3_payload["justificacao_curta"],
            "motivos_estruturais": stage3_payload["motivos_estruturais"],
            "confianca_decisao": stage3_payload["confianca_decisao"],
            "necessita_revisao_humana": False,
            "avisos_arbitragem": [],
        }, None

    if decision == "manter_2_excecional":
        if len(kept) != 2:
            return {}, "decisao_manter_2_sem_exatamente_dois_argumentos"
        if stage3_payload["confianca_decisao"] < float(runtime_config["confianca_minima_manter_2"]):
            return {}, "confianca_insuficiente_para_manter_2_excecional"
        pair_compatible, pair_support, pair_blocking = get_pair_local_constraints(dossier, kept)
        if not pair_compatible:
            return {}, "par_incompativel_localmente:" + ",".join(pair_blocking)
        for argumento_id in kept:
            candidate_eval = stage2_index.get(argumento_id, {})
            if not candidate_eval.get("exprime_funcao_dominante"):
                return {}, f"manter_2_com_candidato_sem_expressao_funcao:{argumento_id}"
            if candidate_eval.get("compatibilidade_estrutural") not in {"forte", "moderada"}:
                return {}, f"manter_2_com_compatibilidade_insuficiente:{argumento_id}"
            local_warning_types = safe_list_of_strings(local_candidates.get(argumento_id, {}).get("warning_types"))
            if "associacao_fraca" in local_warning_types:
                return {}, f"manter_2_com_associacao_fraca:{argumento_id}"
        return {
            "ramo_id": ramo_id,
            "decisao_final": decision,
            "argumentos_mantidos": kept,
            "argumentos_excluidos": excluded or [item for item in candidate_ids if item not in kept],
            "argumento_dominante": dominant if isinstance(dominant, str) and dominant in kept else kept[0],
            "justificacao_curta": stage3_payload["justificacao_curta"],
            "motivos_estruturais": unique_preserve_order(stage3_payload["motivos_estruturais"] + pair_support),
            "confianca_decisao": stage3_payload["confianca_decisao"],
            "necessita_revisao_humana": False,
            "avisos_arbitragem": [],
        }, None

    if decision == "manter_0":
        if kept:
            return {}, "decisao_manter_0_com_argumentos_mantidos"
        return {
            "ramo_id": ramo_id,
            "decisao_final": decision,
            "argumentos_mantidos": [],
            "argumentos_excluidos": excluded or candidate_ids,
            "argumento_dominante": None,
            "justificacao_curta": stage3_payload["justificacao_curta"],
            "motivos_estruturais": stage3_payload["motivos_estruturais"],
            "confianca_decisao": stage3_payload["confianca_decisao"],
            "necessita_revisao_humana": False,
            "avisos_arbitragem": [],
        }, None

    if decision == "revisao_humana_necessaria":
        return {
            "ramo_id": ramo_id,
            "decisao_final": decision,
            "argumentos_mantidos": [],
            "argumentos_excluidos": excluded or candidate_ids,
            "argumento_dominante": None,
            "justificacao_curta": stage3_payload["justificacao_curta"],
            "motivos_estruturais": stage3_payload["motivos_estruturais"],
            "confianca_decisao": stage3_payload["confianca_decisao"],
            "necessita_revisao_humana": True,
            "avisos_arbitragem": [],
        }, None

    return {}, "decisao_final_desconhecida"


def run_api_pipeline_for_ramo(
    client: Any,
    runtime_config: Dict[str, Any],
    logs_path: Path,
    ramo_id: str,
    dossier: Dict[str, Any],
) -> Dict[str, Any]:
    candidate_ids = [
        item["argumento_id"]
        for item in dossier.get("candidatos_argumentativos", [])
        if isinstance(item, dict) and isinstance(item.get("argumento_id"), str)
    ]
    if not candidate_ids:
        return {
            "ramo_id": ramo_id,
            "decisao_final": "manter_0",
            "argumentos_mantidos": [],
            "argumentos_excluidos": [],
            "argumento_dominante": None,
            "justificacao_curta": "Sem candidatos recuperáveis com segurança no dossiê; o ramo fica sem argumento.",
            "motivos_estruturais": ["sem_candidatos_no_dossie"],
            "confianca_decisao": 1.0,
            "necessita_revisao_humana": False,
            "stage_outputs": {},
            "meta_api": {"usou_api": False, "retries_total": 0, "falhas": []},
            "avisos": ["decisao_trivial_sem_api"],
        }

    stage1_messages = build_messages("stage1", dossier)
    stage1_payload, stage1_meta = run_stage_with_retries(
        client=client,
        runtime_config=runtime_config,
        logs_path=logs_path,
        ramo_id=ramo_id,
        stage_name="etapa_1_funcao_estrutural",
        messages=stage1_messages,
        schema_name="funcao_estrutural_ramo",
        schema=STAGE1_SCHEMA,
        validator=validate_stage1_payload,
        validator_kwargs={"ramo_id": ramo_id},
        model=runtime_config["model_primary"],
    )

    stage2_messages = build_messages("stage2", dossier, stage1=stage1_payload)
    stage2_payload, stage2_meta = run_stage_with_retries(
        client=client,
        runtime_config=runtime_config,
        logs_path=logs_path,
        ramo_id=ramo_id,
        stage_name="etapa_2_avaliacao_candidatos",
        messages=stage2_messages,
        schema_name="avaliacao_candidatos_argumentativos",
        schema=STAGE2_SCHEMA,
        validator=validate_stage2_payload,
        validator_kwargs={"ramo_id": ramo_id, "candidate_ids": candidate_ids},
        model=runtime_config["model_primary"],
    )

    stage3_attempt_errors: List[str] = []
    stage3_valid_signatures: List[str] = []
    accepted_stage3: Optional[Dict[str, Any]] = None
    accepted_arbitrated: Optional[Dict[str, Any]] = None
    stage3_meta: Dict[str, Any] = {"attempts": 0, "model": runtime_config["model_primary"], "response_id": None}

    for attempt in range(1, int(runtime_config["max_retries_per_stage"]) + 1):
        stage3_meta["attempts"] = attempt
        try:
            if runtime_config.get("dry_run"):
                raise AdjudicacaoArgumentosAPIError("Modo dry_run ativo; etapa não enviada à API.")
            messages = build_messages("stage3", dossier, stage1=stage1_payload, stage2=stage2_payload)
            response = call_responses_api(
                client=client,
                messages=messages,
                schema_name="decisao_final_argumentos_ramo",
                schema=STAGE3_SCHEMA,
                model=runtime_config["model_primary"],
                runtime_config=runtime_config,
            )
            text = get_response_text(response)
            parsed = json.loads(text)
            validated = validate_stage3_payload(parsed, ramo_id=ramo_id, candidate_ids=candidate_ids)
            signature = json.dumps(
                {
                    "decisao_final": validated["decisao_final"],
                    "argumentos_mantidos": validated["argumentos_mantidos"],
                    "argumento_dominante": validated["argumento_dominante"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            stage3_valid_signatures.append(signature)
            arbitrated, arbitration_error = arbitrate_final_decision(
                ramo_id=ramo_id,
                dossier=dossier,
                stage2_payload=stage2_payload,
                stage3_payload=validated,
                runtime_config=runtime_config,
            )
            if arbitration_error is not None:
                stage3_attempt_errors.append(arbitration_error)
                log_attempt(
                    logs_path,
                    runtime_config,
                    ramo_id,
                    "etapa_3_decisao_final",
                    attempt,
                    "error",
                    runtime_config["model_primary"],
                    payload=validated,
                    error=arbitration_error,
                )
                if attempt < int(runtime_config["max_retries_per_stage"]):
                    time.sleep(float(runtime_config["retry_backoff_seconds"]) * attempt)
                    continue
                break
            accepted_stage3 = validated
            accepted_arbitrated = arbitrated
            stage3_meta["response_id"] = getattr(response, "id", None)
            log_attempt(
                logs_path,
                runtime_config,
                ramo_id,
                "etapa_3_decisao_final",
                attempt,
                "success",
                runtime_config["model_primary"],
                payload=arbitrated,
            )
            break
        except Exception as exc:
            stage3_attempt_errors.append(str(exc))
            log_attempt(
                logs_path,
                runtime_config,
                ramo_id,
                "etapa_3_decisao_final",
                attempt,
                "error",
                runtime_config["model_primary"],
                error=str(exc),
            )
            if attempt < int(runtime_config["max_retries_per_stage"]):
                time.sleep(float(runtime_config["retry_backoff_seconds"]) * attempt)

    if accepted_arbitrated is None or accepted_stage3 is None:
        oscillating = len(set(stage3_valid_signatures)) >= 2
        fallback_decision = {
            "ramo_id": ramo_id,
            "decisao_final": "revisao_humana_necessaria",
            "argumentos_mantidos": [],
            "argumentos_excluidos": candidate_ids,
            "argumento_dominante": None,
            "justificacao_curta": "A adjudicação assistida não fechou de forma prudente após os retries previstos.",
            "motivos_estruturais": unique_preserve_order(
                ["fallback_prudente_pos_falha_api"] + (["oscilacao_entre_retries"] if oscillating else [])
            ),
            "confianca_decisao": 0.0,
            "necessita_revisao_humana": True,
            "avisos_arbitragem": unique_preserve_order(stage3_attempt_errors),
        }
        return {
            **fallback_decision,
            "stage_outputs": {
                "etapa_1": stage1_payload,
                "etapa_2": stage2_payload,
                "etapa_3": accepted_stage3,
            },
            "meta_api": {
                "usou_api": True,
                "retries_total": int(stage1_meta["attempts"]) + int(stage2_meta["attempts"]) + int(stage3_meta["attempts"]),
                "falhas": stage3_attempt_errors,
                "oscilacao_entre_retries": oscillating,
                "modelos": [runtime_config["model_primary"]],
            },
            "avisos": ["fallback_para_revisao_humana"],
        }

    return {
        **accepted_arbitrated,
        "stage_outputs": {
            "etapa_1": stage1_payload,
            "etapa_2": stage2_payload,
            "etapa_3": accepted_stage3,
        },
        "meta_api": {
            "usou_api": True,
            "retries_total": int(stage1_meta["attempts"]) + int(stage2_meta["attempts"]) + int(stage3_meta["attempts"]),
            "falhas": stage3_attempt_errors,
            "oscilacao_entre_retries": len(set(stage3_valid_signatures)) >= 2,
            "modelos": [runtime_config["model_primary"]],
        },
        "avisos": accepted_arbitrated.get("avisos_arbitragem", []),
    }


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "metadata": {
                "script": "adjudicar_argumentos_api_v1.py",
                "created_at_utc": utc_now_iso(),
            },
            "ramos": {},
        }
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {
            "metadata": {
                "script": "adjudicar_argumentos_api_v1.py",
                "created_at_utc": utc_now_iso(),
                "nota": "Estado anterior inválido; reiniciado nesta execução.",
            },
            "ramos": {},
        }
    if not isinstance(data, dict):
        data = {"metadata": {}, "ramos": {}}
    data.setdefault("metadata", {})
    data.setdefault("ramos", {})
    return data


def update_state(state: Dict[str, Any], ramo_id: str, result: Dict[str, Any]) -> None:
    state.setdefault("ramos", {})[ramo_id] = {
        "updated_at_utc": utc_now_iso(),
        "decisao_final": result.get("decisao_final"),
        "argumentos_mantidos": result.get("argumentos_mantidos", []),
        "necessita_revisao_humana": bool(result.get("necessita_revisao_humana")),
        "retries_total": (result.get("meta_api") or {}).get("retries_total", 0),
        "status": "concluido",
    }


def build_output_payload(
    runtime_config: Dict[str, Any],
    paths: Dict[str, Path],
    universe_info: Dict[str, Any],
    decisions: List[Dict[str, Any]],
    skipped_existing: List[str],
    unresolved_failures: List[str],
    extraction_limits: List[str],
) -> Dict[str, Any]:
    total_considerados = len(universe_info.get("ramos_manuais", []))
    processados = len(decisions)
    manter_1 = sum(1 for item in decisions if item["decisao_final"] == "manter_1")
    manter_2 = sum(1 for item in decisions if item["decisao_final"] == "manter_2_excecional")
    manter_0 = sum(1 for item in decisions if item["decisao_final"] == "manter_0")
    revisao_humana = sum(1 for item in decisions if item["decisao_final"] == "revisao_humana_necessaria")
    automaticos = sum(1 for item in decisions if not item.get("necessita_revisao_humana"))
    retries_total = sum(int((item.get("meta_api") or {}).get("retries_total", 0)) for item in decisions)
    falhas_total = sum(len((item.get("meta_api") or {}).get("falhas", [])) for item in decisions)

    return {
        "metadata": {
            "script": "adjudicar_argumentos_api_v1.py",
            "timestamp_utc": utc_now_iso(),
            "modelos_usados": [runtime_config["model_primary"], runtime_config["model_fallback"]],
            "config_execucao": {
                "max_retries_per_stage": runtime_config["max_retries_per_stage"],
                "temperature": runtime_config["temperature"],
                "max_output_tokens": runtime_config["max_output_tokens"],
                "max_ramos_por_execucao": runtime_config["max_ramos_por_execucao"],
                "reprocessar_concluidos": runtime_config["reprocessar_concluidos"],
                "guardar_logs_intermedios": runtime_config["guardar_logs_intermedios"],
                "dry_run": runtime_config["dry_run"],
            },
            "ficheiros_lidos": {
                "arvore_final": str(paths["input_tree"]),
                "triagem_json": str(paths["triagem_json"]),
                "triagem_report": str(paths["triagem_report"]),
                "revisao_percursos_report": str(paths["report_revisao_percursos"]),
                "geracao_argumentos_report": str(paths["report_geracao_argumentos"]),
                "validacao_argumentos_report": str(paths["report_validacao_argumentos"]),
                "revisao_argumentos_report": str(paths["report_revisao_argumentos"]),
            },
            "ficheiros_escritos": {
                "json_principal": str(paths["output_json"]),
                "relatorio_txt": str(paths["output_report"]),
                "logs_jsonl": str(paths["output_logs_jsonl"]),
                "estado_json": str(paths["output_state"]),
            },
        },
        "universo_adjudicacao": {
            "ramos_extraidos_do_relatorio": universe_info.get("ramos_extraidos_do_relatorio", []),
            "ramos_adicionados_por_fallback": universe_info.get("ramos_adicionados_por_fallback", []),
            "ramos_finais_a_adjudicar": universe_info.get("ramos_manuais", []),
            "limitacoes": unique_preserve_order(universe_info.get("limitacoes", []) + extraction_limits),
        },
        "resumo": {
            "total_ramos_considerados": total_considerados,
            "total_processados_nesta_execucao": processados,
            "total_adjudicado_sem_revisao_humana": automaticos,
            "total_manter_1": manter_1,
            "total_manter_2_excecional": manter_2,
            "total_manter_0": manter_0,
            "total_revisao_humana_necessaria": revisao_humana,
            "total_retries": retries_total,
            "total_falhas_ou_retries_erro": falhas_total,
            "total_ignorados_por_estado_previo": len(skipped_existing),
            "total_falhas_irrecuperaveis": len(unresolved_failures),
        },
        "criterios_aplicados": {
            "regra_dominante": "Função estrutural dominante do ramo.",
            "regra_de_prudencia": "Na dúvida, preferir manter_0 ou revisao_humana_necessaria em vez de inflacionar argumentos.",
            "politica_fallback": "Falhas de rede, schema inválido, argumentos inventados, incompatibilidades locais ou oscilação entre retries convertem para revisao_humana_necessaria.",
        },
        "ramos_adjudicados": decisions,
        "estado_execucao": {
            "ignorados_por_estado_previo": skipped_existing,
            "falhas_irrecuperaveis": unresolved_failures,
            "logs_jsonl": str(paths["output_logs_jsonl"]),
            "estado_json": str(paths["output_state"]),
        },
        "observacoes_finais": {
            "zona_superior_suficientemente_adjudicada": revisao_humana == 0 and not unresolved_failures,
            "ramos_ainda_dependentes_de_decisao_humana": sorted(
                [item["ramo_id"] for item in decisions if item.get("necessita_revisao_humana")],
                key=ramo_sort_key,
            ),
            "nota": "Este script não altera a árvore nem cria argumentos novos; adjudica casos manuais com base na estrutura já produzida.",
        },
    }


def build_report_text(payload: Dict[str, Any]) -> str:
    metadata = payload["metadata"]
    resumo = payload["resumo"]
    universo = payload["universo_adjudicacao"]
    criterios = payload["criterios_aplicados"]
    items = payload["ramos_adjudicados"]

    lines: List[str] = []
    lines.append("RELATÓRIO DE ADJUDICAÇÃO ASSISTIDA DE ARGUMENTOS VIA API V1")
    lines.append("=" * 72)
    lines.append(f"Data/hora UTC: {metadata['timestamp_utc']}")
    lines.append(f"Script: {metadata['script']}")
    lines.append(f"Modelos usados: {', '.join(metadata['modelos_usados'])}")
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
    lines.append(f"Total de ramos considerados: {resumo['total_ramos_considerados']}")
    lines.append(f"Total processado nesta execução: {resumo['total_processados_nesta_execucao']}")
    lines.append(f"Total adjudicado sem revisão humana: {resumo['total_adjudicado_sem_revisao_humana']}")
    lines.append(f"Total mantido com 1 argumento: {resumo['total_manter_1']}")
    lines.append(f"Total mantido com 2 argumentos: {resumo['total_manter_2_excecional']}")
    lines.append(f"Total mantido com 0 argumentos: {resumo['total_manter_0']}")
    lines.append(f"Total em revisão humana: {resumo['total_revisao_humana_necessaria']}")
    lines.append(f"Total de retries: {resumo['total_retries']}")
    lines.append(f"Total de falhas/retries com erro: {resumo['total_falhas_ou_retries_erro']}")
    lines.append("")

    lines.append("Critérios aplicados")
    lines.append("-" * 72)
    lines.append(f"Regra dominante: {criterios['regra_dominante']}")
    lines.append(f"Regra de prudência: {criterios['regra_de_prudencia']}")
    lines.append(f"Política de fallback: {criterios['politica_fallback']}")
    lines.append("")

    lines.append("Universo de adjudicação")
    lines.append("-" * 72)
    lines.append(
        "Ramos extraídos do relatório de revisão restritiva: "
        + (", ".join(universo["ramos_extraidos_do_relatorio"]) if universo["ramos_extraidos_do_relatorio"] else "nenhum")
    )
    lines.append(
        "Ramos adicionados por fallback estrutural: "
        + (", ".join(universo["ramos_adicionados_por_fallback"]) if universo["ramos_adicionados_por_fallback"] else "nenhum")
    )
    if universo.get("limitacoes"):
        lines.append("Limitações da extração:")
        for item in universo["limitacoes"]:
            lines.append(f"- {item}")
    lines.append("")

    lines.append("Listagem por ramo")
    lines.append("-" * 72)
    if not items:
        lines.append("Nenhum ramo foi adjudicado nesta execução.")
    for item in items:
        lines.append(
            f"{item['ramo_id']} | grupo={item['grupo_original']} | percursos={','.join(item['percurso_ids']) if item['percurso_ids'] else '∅'} | "
            f"candidatos={','.join(item['candidatos_iniciais']) if item['candidatos_iniciais'] else '∅'} | decisao={item['decisao_final']}"
        )
        lines.append(
            f"  mantidos: {','.join(item['argumentos_mantidos']) if item['argumentos_mantidos'] else '∅'} | "
            f"excluidos: {','.join(item['argumentos_excluidos']) if item['argumentos_excluidos'] else '∅'}"
        )
        lines.append(f"  argumento_dominante: {item['argumento_dominante'] or '∅'}")
        lines.append(f"  justificação: {item['justificacao_curta']}")
        lines.append(f"  confiança: {item['confianca_decisao']:.2f}")
        lines.append(f"  revisão_humana: {'sim' if item['necessita_revisao_humana'] else 'não'}")
        if item.get("motivos_estruturais"):
            lines.append(f"  motivos_estruturais: {', '.join(item['motivos_estruturais'])}")
        if item.get("avisos"):
            lines.append(f"  avisos: {', '.join(item['avisos'])}")
        retries = int((item.get("meta_api") or {}).get("retries_total", 0))
        lines.append(f"  retries_total: {retries}")
        lines.append("")

    lines.append("Observações finais")
    lines.append("-" * 72)
    lines.append(
        "Zona superior suficientemente adjudicada: "
        + ("sim" if payload["observacoes_finais"]["zona_superior_suficientemente_adjudicada"] else "não")
    )
    lines.append(
        "Ramos ainda dependentes de decisão humana: "
        + (
            ", ".join(payload["observacoes_finais"]["ramos_ainda_dependentes_de_decisao_humana"])
            if payload["observacoes_finais"]["ramos_ainda_dependentes_de_decisao_humana"]
            else "nenhum"
        )
    )
    lines.append(payload["observacoes_finais"]["nota"])
    lines.append("")
    return "\n".join(lines)


def terminal_summary(payload: Dict[str, Any], output_json: Path, output_report: Path) -> str:
    resumo = payload["resumo"]
    return "\n".join(
        [
            f"Ramos considerados: {resumo['total_ramos_considerados']}",
            f"Processados nesta execução: {resumo['total_processados_nesta_execucao']}",
            f"Manter 1: {resumo['total_manter_1']}",
            f"Manter 2: {resumo['total_manter_2_excecional']}",
            f"Manter 0: {resumo['total_manter_0']}",
            f"Revisão humana: {resumo['total_revisao_humana_necessaria']}",
            f"JSON escrito em: {output_json}",
            f"Relatório escrito em: {output_report}",
        ]
    )


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    paths = build_paths(script_dir)
    load_environment(paths)
    runtime_config = resolve_runtime_config()
    ensure_required_files(paths)

    tree = load_json(paths["input_tree"])
    if not isinstance(tree, dict):
        raise AdjudicacaoArgumentosAPIError("A árvore final tem de ser um objeto JSON no topo.")
    triagem = load_json(paths["triagem_json"])
    if not isinstance(triagem, dict):
        raise AdjudicacaoArgumentosAPIError("A triagem tem de ser um objeto JSON no topo.")

    triagem_report_text = load_text(paths["triagem_report"])
    revisao_percursos_text = load_text(paths["report_revisao_percursos"])
    geracao_argumentos_text = load_text(paths["report_geracao_argumentos"])
    validacao_argumentos_text = load_text(paths["report_validacao_argumentos"])
    revisao_argumentos_text = load_text(paths["report_revisao_argumentos"])

    ramos, ramos_location = locate_ramos(tree)
    if not ramos:
        raise AdjudicacaoArgumentosAPIError("O bloco de ramos foi localizado, mas está vazio.")
    argumentos, argumentos_location = locate_optional_section(tree, ("argumentos",), id_prefix="ARG_")
    if not argumentos:
        raise AdjudicacaoArgumentosAPIError(
            "Não foi possível localizar o bloco de argumentos na árvore final."
        )

    triagem_map = collect_triagem_map(triagem)
    geracao_argumentos = parse_generation_argumentos_report(geracao_argumentos_text)
    validacao_argumentos = parse_validation_argumentos_report(validacao_argumentos_text)
    revisao_report_data = parse_revisao_argumentos_report(revisao_argumentos_text)
    triagem_mentions = parse_text_mentions_by_ramo(triagem_report_text)
    percursos_mentions = parse_text_mentions_by_ramo(revisao_percursos_text)

    ramos_map: Dict[str, Dict[str, Any]] = {}
    for idx, ramo in enumerate(ramos, start=1):
        if not isinstance(ramo, dict):
            raise AdjudicacaoArgumentosAPIError(
                f"Elemento inválido em ramos[{idx}]: esperado dict, obtido {type(ramo).__name__}."
            )
        ramo_id = first_nonempty_string(ramo, ("id", "ramo_id"))
        if not ramo_id:
            raise AdjudicacaoArgumentosAPIError(f"Falta 'id' utilizável em ramos[{idx}].")
        ramos_map[ramo_id] = ramo

    argumento_profiles = build_argumento_profiles(argumentos)
    universe_info = build_manual_universe(
        triagem_map=triagem_map,
        ramos_map=ramos_map,
        revisao_report_data=revisao_report_data,
        validation_data=validacao_argumentos,
    )

    extraction_limits: List[str] = []
    if revisao_report_data.get("manual_from_detail") and not revisao_report_data.get("manual_from_summary"):
        extraction_limits.append(
            "A lista final de casos manuais foi inferida sobretudo da listagem detalhada do relatório de revisão restritiva; a linha-resumo não estava plenamente disponível."
        )

    state = load_state(paths["output_state"])
    client = None
    if not runtime_config.get("dry_run"):
        client = create_openai_client()

    decisions: List[Dict[str, Any]] = []
    skipped_existing: List[str] = []
    unresolved_failures: List[str] = []

    manual_ramos = universe_info.get("ramos_manuais", [])
    if runtime_config.get("max_ramos_por_execucao"):
        manual_ramos = manual_ramos[: int(runtime_config["max_ramos_por_execucao"])]

    for ramo_id in manual_ramos:
        if not runtime_config.get("reprocessar_concluidos"):
            existing_state = (state.get("ramos") or {}).get(ramo_id)
            if isinstance(existing_state, dict) and existing_state.get("status") == "concluido":
                skipped_existing.append(ramo_id)
                continue

        ramo = ramos_map.get(ramo_id)
        if not isinstance(ramo, dict):
            unresolved_failures.append(ramo_id)
            log_attempt(
                paths["output_logs_jsonl"],
                runtime_config,
                ramo_id,
                "preparacao_dossie",
                1,
                "error",
                runtime_config["model_primary"],
                error="Ramo não localizado na árvore final.",
            )
            continue

        dossier = build_dossier_for_ramo(
            ramo_id=ramo_id,
            ramo=ramo,
            triagem_item=triagem_map.get(ramo_id),
            triagem_report_mentions=triagem_mentions.get(ramo_id, []),
            percursos_review_mentions=percursos_mentions.get(ramo_id, []),
            generation_entries=geracao_argumentos["entries_by_ramo"].get(ramo_id, []),
            generation_empty_ramos=geracao_argumentos["empty_ramos"],
            warnings_for_ramo=validacao_argumentos["warnings_by_ramo"].get(ramo_id, []),
            revisao_report_item=revisao_report_data["details_by_ramo"].get(ramo_id),
            argumento_profiles=argumento_profiles,
        )

        try:
            result = run_api_pipeline_for_ramo(
                client=client,
                runtime_config=runtime_config,
                logs_path=paths["output_logs_jsonl"],
                ramo_id=ramo_id,
                dossier=dossier,
            )
        except Exception as exc:
            log_attempt(
                paths["output_logs_jsonl"],
                runtime_config,
                ramo_id,
                "pipeline_ramo",
                1,
                "error",
                runtime_config["model_primary"],
                error=str(exc),
            )
            result = {
                "ramo_id": ramo_id,
                "decisao_final": "revisao_humana_necessaria",
                "argumentos_mantidos": [],
                "argumentos_excluidos": [
                    item["argumento_id"]
                    for item in dossier.get("candidatos_argumentativos", [])
                    if isinstance(item, dict) and isinstance(item.get("argumento_id"), str)
                ],
                "argumento_dominante": None,
                "justificacao_curta": "Falha irrecuperável no pipeline de adjudicação assistida; o ramo permanece para revisão humana.",
                "motivos_estruturais": ["falha_pipeline_api"],
                "confianca_decisao": 0.0,
                "necessita_revisao_humana": True,
                "stage_outputs": {},
                "meta_api": {"usou_api": client is not None, "retries_total": 0, "falhas": [str(exc)]},
                "avisos": ["pipeline_falhou"],
            }

        decision_record = {
            "ramo_id": ramo_id,
            "grupo_original": dossier["grupo_original"],
            "percurso_ids": dossier["percurso_ids_estabilizados"],
            "candidatos_iniciais": [
                item["argumento_id"]
                for item in dossier.get("candidatos_argumentativos", [])
                if isinstance(item, dict) and isinstance(item.get("argumento_id"), str)
            ],
            "decisao_final": result["decisao_final"],
            "argumentos_mantidos": result["argumentos_mantidos"],
            "argumentos_excluidos": result["argumentos_excluidos"],
            "argumento_dominante": result["argumento_dominante"],
            "justificacao_curta": result["justificacao_curta"],
            "motivos_estruturais": result["motivos_estruturais"],
            "confianca_decisao": result["confianca_decisao"],
            "necessita_revisao_humana": result["necessita_revisao_humana"],
            "avisos": unique_preserve_order(result.get("avisos", [])),
            "meta_api": result.get("meta_api", {}),
            "dossier": compress_dossier_for_prompt(dossier),
            "stage_outputs": result.get("stage_outputs", {}),
        }
        decisions.append(decision_record)
        update_state(state, ramo_id, result)
        save_json_atomic(paths["output_state"], state)

    payload = build_output_payload(
        runtime_config=runtime_config,
        paths=paths,
        universe_info=universe_info,
        decisions=sorted(decisions, key=lambda item: ramo_sort_key(item["ramo_id"])),
        skipped_existing=sorted(skipped_existing, key=ramo_sort_key),
        unresolved_failures=sorted(unresolved_failures, key=ramo_sort_key),
        extraction_limits=extraction_limits,
    )
    report_text = build_report_text(payload)

    save_json_atomic(paths["output_json"], payload)
    write_text(paths["output_report"], report_text)
    save_json_atomic(paths["output_state"], state)

    print(terminal_summary(payload, paths["output_json"], paths["output_report"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AdjudicacaoArgumentosAPIError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)
