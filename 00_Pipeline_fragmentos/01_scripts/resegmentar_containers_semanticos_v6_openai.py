#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
resegmentar_containers_semanticos_v6_openai.py

Ressegmentador semântico em duas fases, auditável e robusto, pensado para
containers de segmentação já estabilizados, com suporte principal à API da OpenAI.

Versão adaptada para a pasta:

    00_Pipeline_fragmentos/

Estrutura esperada:

    00_Pipeline_fragmentos/
    ├── 00_inbox_novos/
    ├── 01_scripts/
    │   └── resegmentar_containers_semanticos_v6_openai.py
    ├── 02_base_referencia/
    ├── 03_runs/
    │   └── <run_name>/
    │       ├── 00_input/
    │       ├── 01_match/
    │       ├── 02_containers/
    │       ├── 03_resegmentacao/
    │       ├── 04_validacao/
    │       └── 05_relatorios/
    ├── 04_outputs_prontos_para_integrar/
    └── 90_arquivo/

Ajustes principais:
1. suporte OpenAI Responses API com json_schema strict;
2. corte interno de containers mono-parágrafo longos, usando unidades internas
   baseadas em frases para permitir resegmentação real;
3. normalização forte para nunca sair com tipo_unidade/criterio/função inválidos;
4. fallback local heurístico para corrida offline;
5. deteção automática da pasta da run quando o input está em:
      03_runs/<run_name>/02_containers/
6. outputs separados em:
      03_resegmentacao/
      04_validacao/
      05_relatorios/
7. cópia automática do JSON final válido para:
      04_outputs_prontos_para_integrar/

Saídas:
- 03_resegmentacao/fragmentos_resegmentados__<run>.json
- 03_resegmentacao/estado_resegmentador__<run>.json
- 03_resegmentacao/falhas_resegmentador__<run>.json
- 04_validacao/relatorio_validacao_fragmentos__<run>.json
- 05_relatorios/relatorio_resegmentador__<run>.txt
- 04_outputs_prontos_para_integrar/fragmentos_resegmentados__<run>.json
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# -----------------------------------------------------------------------------
# Caminhos do pipeline
# -----------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent

INBOX_DIR = PIPELINE_DIR / "00_inbox_novos"
BASE_REF_DIR = PIPELINE_DIR / "02_base_referencia"
RUNS_DIR = PIPELINE_DIR / "03_runs"
READY_DIR = PIPELINE_DIR / "04_outputs_prontos_para_integrar"

load_dotenv()
load_dotenv(SCRIPT_DIR / ".env")
load_dotenv(PIPELINE_DIR / ".env")
load_dotenv(PIPELINE_DIR.parent / ".env")


# -----------------------------------------------------------------------------
# Configuração
# -----------------------------------------------------------------------------

SCRIPT_VERSION = "resegmentador_semantico_v6_0_duas_fases_openai_pipeline"
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_RETRIES = 3
DEFAULT_SLEEP = 1.2

VALID_TIPO_UNIDADE = {
    "afirmacao_curta",
    "desenvolvimento_curto",
    "desenvolvimento_medio",
    "sequencia_argumentativa",
    "distincao_conceptual",
    "fragmento_intuitivo",
}

VALID_CRITERIO_UNIDADE = {
    "container_atomico",
    "continuidade_argumentativa",
    "continuidade_tematica",
    "fecho_local",
    "exemplo_aplicado",
}

VALID_FUNCAO = {
    "afirmacao",
    "desenvolvimento",
    "exploracao",
    "distincao",
    "critica",
    "pergunta_reflexiva",
    "objecao",
    "resposta",
    "transicao",
    "sintese",
}

VALID_GRAU = {"alto", "medio", "baixo"}
VALID_CONFIANCA = {"alta", "media", "baixa"}

RE_MULTI_SPACE = re.compile(r"[ \t]+")
RE_MULTI_NL = re.compile(r"\n{3,}")
RE_SPLIT_SENTENCE = re.compile(
    r'(?<=[.!?])\s+(?=[A-ZÀ-Ý"“«(\[])',
    re.UNICODE,
)

CLIENT = OpenAI() if OpenAI is not None and os.getenv("OPENAI_API_KEY") else None


@dataclass
class ApiConfig:
    model: str
    retries: int = DEFAULT_RETRIES
    sleep_seconds: float = DEFAULT_SLEEP


# -----------------------------------------------------------------------------
# Utilitários de caminhos
# -----------------------------------------------------------------------------

def resolve_input_path(input_arg: str) -> Path:
    """
    Resolve o input de modo flexível.

    Aceita:
    - caminho absoluto;
    - caminho relativo ao diretório atual;
    - caminho relativo à pasta 01_scripts;
    - caminho relativo à pasta 00_Pipeline_fragmentos.
    """

    raw = Path(input_arg)

    if raw.is_absolute():
        candidates = [raw]
    else:
        candidates = [
            Path.cwd() / raw,
            SCRIPT_DIR / raw,
            PIPELINE_DIR / raw,
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    tried = "\n".join(f"- {c}" for c in candidates)
    raise SystemExit(
        "[erro] Ficheiro de input não encontrado.\n"
        f"Input recebido: {input_arg}\n"
        f"Caminhos testados:\n{tried}"
    )


def resolve_relative_path(path_arg: str) -> Path:
    raw = Path(path_arg)
    if raw.is_absolute():
        return raw.resolve()
    return (Path.cwd() / raw).resolve()


def infer_output_dirs(input_path: Path, output_dir_arg: str) -> Tuple[Path, Path, Path, Path]:
    """
    Infere as pastas de output.

    Caso normal:
        input em 03_runs/<run>/02_containers/<containers>.json

    Então:
        reseg_dir   = 03_runs/<run>/03_resegmentacao
        valid_dir   = 03_runs/<run>/04_validacao
        reports_dir = 03_runs/<run>/05_relatorios

    Se --output-dir for indicado:
        - se apontar para a pasta da run, usa as subpastas internas;
        - se apontar para 03_resegmentacao/04_validacao/05_relatorios,
          sobe para a pasta da run;
        - caso contrário, trata esse output-dir como pasta da run.
    """

    if output_dir_arg and output_dir_arg != ".":
        base = resolve_relative_path(output_dir_arg)

        if base.name in {"03_resegmentacao", "04_validacao", "05_relatorios"}:
            run_dir = base.parent
        else:
            run_dir = base

    elif input_path.parent.name == "02_containers":
        run_dir = input_path.parent.parent

    else:
        # Fallback: se o ficheiro estiver fora da estrutura normal,
        # cria subpastas ao lado do próprio input.
        run_dir = input_path.parent

    reseg_dir = run_dir / "03_resegmentacao"
    valid_dir = run_dir / "04_validacao"
    reports_dir = run_dir / "05_relatorios"

    return run_dir, reseg_dir, valid_dir, reports_dir


# -----------------------------------------------------------------------------
# Utilitários gerais
# -----------------------------------------------------------------------------

def utc_ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00A0", " ")
    text = RE_MULTI_SPACE.sub(" ", text)
    text = RE_MULTI_NL.sub("\n\n", text)
    return text.strip()


def split_sentences(text: str) -> List[str]:
    """
    Segmentação frásica conservadora.

    Só separa em fronteiras fortes; se ficar demasiado partido, o agrupador
    heurístico e/ou a fase 1 volta a juntar.
    """

    text = normalize_text(text)
    if not text:
        return []

    parts = [p.strip() for p in RE_SPLIT_SENTENCE.split(text) if p.strip()]
    if len(parts) <= 1:
        return [text]

    merged: List[str] = []
    for part in parts:
        if merged and len(part) < 40:
            merged[-1] = merged[-1].rstrip() + " " + part
        else:
            merged.append(part)

    return merged


def sentence_count(text: str) -> int:
    text = normalize_text(text)
    if not text:
        return 0
    parts = split_sentences(text)
    return max(1, len(parts))


def density_label(n_chars: int) -> str:
    if n_chars < 150:
        return "baixa"
    if n_chars < 800:
        return "media"
    return "alta"


def coerce_list_str(value: Any, max_items: int = 5) -> List[str]:
    if value is None:
        return []

    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            s = str(item).strip()
            if s and s not in out:
                out.append(s)
        return out[:max_items]

    s = str(value).strip()
    return [s] if s else []


def discover_run_name(input_path: Path) -> str:
    """
    A partir de:
        containers_segmentacao__run_x.json

    devolve:
        run_x
    """

    stem = input_path.stem
    if stem.startswith("containers_segmentacao__"):
        return stem.removeprefix("containers_segmentacao__")
    return stem


# -----------------------------------------------------------------------------
# Preparação de unidades
# -----------------------------------------------------------------------------

def build_units(container: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Constrói a unidade de trabalho para a fase 1.

    - Se houver vários parágrafos: cada parágrafo é uma unidade.
    - Se houver só um parágrafo mas suficientemente longo: cria unidades internas por frase.
    """

    paragraphs = container.get("paragrafos", []) or []
    units: List[Dict[str, Any]] = []

    if len(paragraphs) > 1:
        for p in paragraphs:
            units.append({
                "unit_id": p["paragrafo_id"],
                "source_paragraph_id": p["paragrafo_id"],
                "text": p["texto"],
                "mode": "paragraph",
            })
        return units, False

    if len(paragraphs) == 1:
        p = paragraphs[0]
        text = p["texto"]
        n_chars = len(normalize_text(text))
        sents = split_sentences(text)

        if n_chars < 550 or len(sents) <= 3:
            return [{
                "unit_id": p["paragrafo_id"],
                "source_paragraph_id": p["paragrafo_id"],
                "text": p["texto"],
                "mode": "paragraph",
            }], False

        for i, sent in enumerate(sents, start=1):
            units.append({
                "unit_id": f"{container['container_id']}_U{i:02d}",
                "source_paragraph_id": p["paragrafo_id"],
                "text": sent,
                "mode": "internal_sentence",
            })
        return units, True

    return [], False


# -----------------------------------------------------------------------------
# OpenAI / JSON strict
# -----------------------------------------------------------------------------

def _normalizar_schema_para_strict(schema: Any) -> Any:
    if isinstance(schema, list):
        return [_normalizar_schema_para_strict(x) for x in schema]

    if not isinstance(schema, dict):
        return schema

    schema = copy.deepcopy(schema)

    for k in [
        "$schema",
        "$id",
        "title",
        "description",
        "default",
        "examples",
        "minItems",
        "maxItems",
        "minLength",
        "maxLength",
        "pattern",
        "format",
        "uniqueItems",
    ]:
        schema.pop(k, None)

    if schema.get("type") == "object":
        schema.setdefault("additionalProperties", False)

    if "properties" in schema and isinstance(schema["properties"], dict):
        schema["properties"] = {
            k: _normalizar_schema_para_strict(v)
            for k, v in schema["properties"].items()
        }

    if "items" in schema:
        schema["items"] = _normalizar_schema_para_strict(schema["items"])

    if "anyOf" in schema and isinstance(schema["anyOf"], list):
        schema["anyOf"] = [_normalizar_schema_para_strict(x) for x in schema["anyOf"]]

    if "oneOf" in schema and isinstance(schema["oneOf"], list):
        schema["oneOf"] = [_normalizar_schema_para_strict(x) for x in schema["oneOf"]]

    if "allOf" in schema and isinstance(schema["allOf"], list):
        schema["allOf"] = [_normalizar_schema_para_strict(x) for x in schema["allOf"]]

    return schema


def _extrair_texto_output(response: Any) -> str:
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text

    parts: List[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text_value = getattr(content, "text", None)
            if text_value:
                parts.append(text_value)

    return "\n".join(parts).strip()


def openai_generate_json(
    api: ApiConfig,
    prompt: str,
    schema_obj: Dict[str, Any],
    schema_name: str,
) -> Any:
    if CLIENT is None:
        raise RuntimeError("biblioteca_openai_indisponivel_ou_sem_api_key")

    schema_strict = _normalizar_schema_para_strict(copy.deepcopy(schema_obj))
    last_err: Optional[Exception] = None

    for attempt in range(1, api.retries + 1):
        try:
            response = CLIENT.responses.create(
                model=api.model,
                input=prompt,
                store=False,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "schema": schema_strict,
                        "strict": True,
                    }
                },
            )
            text = _extrair_texto_output(response)
            if not text:
                raise ValueError("resposta_vazia_do_modelo")
            return json.loads(text)

        except Exception as e:
            last_err = e
            if attempt < api.retries:
                time.sleep(api.sleep_seconds)

    raise RuntimeError(f"Falha OpenAI após {api.retries} tentativas: {last_err}")


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

def phase1_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["grupos"],
        "properties": {
            "grupos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["unidades_origem"],
                    "properties": {
                        "unidades_origem": {
                            "type": "array",
                            "items": {"type": "string"},
                        }
                    },
                },
            }
        },
    }


def phase2_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["grupos"],
        "properties": {
            "grupos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "indice",
                        "tipo_unidade",
                        "criterio_de_unidade",
                        "funcao_textual_dominante",
                        "tema_dominante_provisorio",
                        "conceitos_relevantes_provisorios",
                        "integridade_semantica_grau",
                        "confianca_segmentacao",
                        "requer_revisao_manual_prioritaria",
                    ],
                    "properties": {
                        "indice": {"type": "integer"},
                        "tipo_unidade": {
                            "type": "string",
                            "enum": sorted(VALID_TIPO_UNIDADE),
                        },
                        "criterio_de_unidade": {
                            "type": "string",
                            "enum": sorted(VALID_CRITERIO_UNIDADE),
                        },
                        "funcao_textual_dominante": {
                            "type": "string",
                            "enum": sorted(VALID_FUNCAO),
                        },
                        "tema_dominante_provisorio": {"type": "string"},
                        "conceitos_relevantes_provisorios": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "integridade_semantica_grau": {
                            "type": "string",
                            "enum": sorted(VALID_GRAU),
                        },
                        "confianca_segmentacao": {
                            "type": "string",
                            "enum": sorted(VALID_CONFIANCA),
                        },
                        "requer_revisao_manual_prioritaria": {"type": "boolean"},
                    },
                }
            }
        },
    }


# -----------------------------------------------------------------------------
# Prompts
# -----------------------------------------------------------------------------

def build_phase1_prompt(
    container: Dict[str, Any],
    units: List[Dict[str, Any]],
    internal_mode: bool,
) -> str:
    meta = {
        "container_id": container.get("container_id"),
        "titulo_container": container.get("titulo_container"),
        "data": container.get("data"),
        "tipo_material_fonte": container.get("tipo_material_fonte"),
        "n_paragrafos": container.get("n_paragrafos"),
        "n_chars_total": sum(
            int(p.get("n_chars", 0))
            for p in container.get("paragrafos", [])
        ),
        "modo_interno": internal_mode,
    }

    lines = [f"[{u['unit_id']}] {u['text']}" for u in units]

    return f"""
És um segmentador semântico rigoroso e conservador.

TAREFA:
Agrupa as unidades consecutivas deste container em fragmentos semanticamente íntegros.

REGRAS OBRIGATÓRIAS:
1. Não reescrevas o texto.
2. Não expliques a decisão.
3. Não comentes o conteúdo.
4. Não mudes a ordem.
5. Não repitas unidades.
6. Não deixes unidades por usar.
7. Cada grupo tem de conter apenas IDs consecutivos e na ordem original.
8. Prefere preservar uma unidade isolada se a fusão não for claramente vantajosa.
9. Só separa dentro de um parágrafo quando houver mudança semântica real.
10. Responde APENAS JSON válido.

NOTA:
- Se o container tiver só um parágrafo longo, as unidades já podem ser internas.
- Nesse caso, podes devolver vários grupos dentro do mesmo parágrafo, desde que uses todas as unidades em ordem.

METADADOS:
{json.dumps(meta, ensure_ascii=False, indent=2)}

UNIDADES:
{os.linesep.join(lines)}

DEVOLVE APENAS UM OBJETO JSON VÁLIDO com esta forma:
{{
  "grupos": [
    {{"unidades_origem": ["ID1", "ID2"]}},
    {{"unidades_origem": ["ID3"]}}
  ]
}}
""".strip()


def build_phase2_prompt(
    container: Dict[str, Any],
    units: List[Dict[str, Any]],
    groups: List[Dict[str, List[str]]],
    internal_mode: bool,
) -> str:
    unit_map = {u["unit_id"]: u for u in units}

    entries = []
    for i, group in enumerate(groups, start=1):
        ids = group["unidades_origem"]
        textos = [unit_map[x]["text"] for x in ids]
        entries.append({
            "indice": i,
            "unidades_origem": ids,
            "modo_interno": internal_mode,
            "texto_fragmento": "\n\n".join(textos),
        })

    return f"""
És um anotador de fragmentos semânticos rigoroso e disciplinado.

TAREFA:
Para cada grupo abaixo, anota APENAS os campos permitidos.

REGRAS OBRIGATÓRIAS:
1. O texto manda; tema e conceitos são auxiliares.
2. Não inventes conteúdo que não esteja no fragmento.
3. Não uses valores fora dos enums permitidos.
4. Em caso de dúvida, prefere classificação conservadora.
5. Responde APENAS JSON válido.

ENUMS PERMITIDOS:
- tipo_unidade: {sorted(VALID_TIPO_UNIDADE)}
- criterio_de_unidade: {sorted(VALID_CRITERIO_UNIDADE)}
- funcao_textual_dominante: {sorted(VALID_FUNCAO)}
- integridade_semantica_grau: {sorted(VALID_GRAU)}
- confianca_segmentacao: {sorted(VALID_CONFIANCA)}

NOTA CRÍTICA:
'exploracao' e 'pergunta_reflexiva' só são válidos em funcao_textual_dominante.
Nunca são válidos em tipo_unidade.

GRUPOS:
{json.dumps(entries, ensure_ascii=False, indent=2)}

DEVOLVE APENAS:
{{
  "grupos": [
    {{
      "indice": 1,
      "tipo_unidade": "desenvolvimento_curto",
      "criterio_de_unidade": "continuidade_argumentativa",
      "funcao_textual_dominante": "desenvolvimento",
      "tema_dominante_provisorio": "tema breve",
      "conceitos_relevantes_provisorios": ["conceito1", "conceito2"],
      "integridade_semantica_grau": "medio",
      "confianca_segmentacao": "media",
      "requer_revisao_manual_prioritaria": false
    }}
  ]
}}
""".strip()


# -----------------------------------------------------------------------------
# Validação do plano de segmentação
# -----------------------------------------------------------------------------

def validate_plan(units: List[Dict[str, Any]], plan_obj: Any) -> Tuple[bool, str]:
    if not isinstance(plan_obj, dict):
        return False, "plano não é objeto"

    groups = plan_obj.get("grupos")
    if not isinstance(groups, list) or not groups:
        return False, "plano sem grupos válidos"

    expected = [u["unit_id"] for u in units]
    flat: List[str] = []

    for group in groups:
        if not isinstance(group, dict):
            return False, "grupo não é objeto"

        ids = group.get("unidades_origem")
        if not isinstance(ids, list) or not ids:
            return False, "grupo sem unidades_origem"

        if any(not isinstance(x, str) for x in ids):
            return False, "id inválido no grupo"

        flat.extend(ids)

        if not all(x in expected for x in ids):
            return False, "grupo contém ID fora das unidades"

        positions = [expected.index(x) for x in ids]
        if positions != list(range(positions[0], positions[0] + len(positions))):
            return False, "grupo quebra consecutividade"

    if flat != expected:
        return False, "cobertura/ordem divergente"

    return True, "ok"


# -----------------------------------------------------------------------------
# Fallback heurístico
# -----------------------------------------------------------------------------

def heuristic_plan(units: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not units:
        return {"grupos": []}

    if len(units) == 1:
        return {"grupos": [{"unidades_origem": [units[0]["unit_id"]]}]}

    def wants_merge(a: str, b: str) -> bool:
        a_n = normalize_text(a)
        b_n = normalize_text(b)

        if len(a_n) < 120 and len(b_n) < 500:
            return True

        if a_n.endswith(":"):
            return True

        starts = (
            "e ",
            "mas ",
            "ou ",
            "porque ",
            "portanto ",
            "logo ",
            "aliás ",
            "depois ",
            "assim ",
            "por isso ",
            "então ",
            "contudo ",
            "no entanto ",
        )

        if b_n.lower().startswith(starts):
            return True

        return False

    groups: List[List[str]] = []
    current = [units[0]["unit_id"]]

    for prev, nxt in zip(units, units[1:]):
        if wants_merge(prev["text"], nxt["text"]) and len(current) < 4:
            current.append(nxt["unit_id"])
        else:
            groups.append(current)
            current = [nxt["unit_id"]]

    groups.append(current)

    return {"grupos": [{"unidades_origem": g} for g in groups]}


def heuristic_annotation(fragment_text: str) -> Dict[str, Any]:
    text = normalize_text(fragment_text)
    lower = text.lower()
    n_chars = len(text)
    n_sent = sentence_count(text)

    if n_chars <= 80:
        tipo = "afirmacao_curta"
        func = "afirmacao"
        criterio = "container_atomico"

    elif "?" in text and n_sent <= 4:
        tipo = "fragmento_intuitivo"
        func = "pergunta_reflexiva"
        criterio = "continuidade_tematica"

    elif any(k in lower for k in ["não", "erro", "crítica", "critica", "falso", "absurdo"]):
        tipo = "desenvolvimento_curto" if n_chars < 500 else "desenvolvimento_medio"
        func = "critica"
        criterio = "continuidade_argumentativa"

    elif any(k in lower for k in ["ou seja", "disting", "diferença", "diferenca"]):
        tipo = "distincao_conceptual"
        func = "distincao"
        criterio = "continuidade_tematica"

    elif n_sent >= 6 or n_chars >= 700:
        tipo = "desenvolvimento_medio"
        func = "desenvolvimento"
        criterio = "continuidade_argumentativa"

    else:
        tipo = "desenvolvimento_curto"
        func = "exploracao"
        criterio = "continuidade_tematica"

    conceitos = []
    candidates = [
        "real",
        "consciência",
        "consciencia",
        "representação",
        "representacao",
        "símbolo",
        "simbolo",
        "linguagem",
        "verdade",
        "erro",
        "correção",
        "correcao",
        "campo",
        "potencialidades",
        "liberdade",
        "dignidade",
        "sistema",
        "descrição",
        "descricao",
        "apreensão",
        "apreensao",
    ]

    for c in candidates:
        if c in lower:
            v = (
                c.replace("consciencia", "consciência")
                .replace("representacao", "representação")
                .replace("simbolo", "símbolo")
                .replace("correcao", "correção")
                .replace("descricao", "descrição")
                .replace("apreensao", "apreensão")
            )

            if v not in conceitos:
                conceitos.append(v)

        if len(conceitos) >= 5:
            break

    tema = ", ".join(conceitos[:3]) if conceitos else "tema a rever"
    grau = "alto" if n_chars > 160 else "medio"
    confianca = "alta" if n_chars > 300 else "media"
    requer = n_chars < 120 or "whatever" in lower or "pq " in lower or "qnd" in lower

    return {
        "tipo_unidade": tipo,
        "criterio_de_unidade": criterio,
        "funcao_textual_dominante": func,
        "tema_dominante_provisorio": tema,
        "conceitos_relevantes_provisorios": conceitos[:5],
        "integridade_semantica_grau": grau,
        "confianca_segmentacao": confianca,
        "requer_revisao_manual_prioritaria": requer,
    }


# -----------------------------------------------------------------------------
# Normalização de anotações
# -----------------------------------------------------------------------------

def normalize_annotation(data: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(data)

    tipo = str(out.get("tipo_unidade", "")).strip().lower()
    tipo_map = {
        "exploracao": "fragmento_intuitivo",
        "pergunta_reflexiva": "fragmento_intuitivo",
        "afirmação_curta": "afirmacao_curta",
        "desenvolvimento_médio": "desenvolvimento_medio",
        "sequência_argumentativa": "sequencia_argumentativa",
        "distinção_conceptual": "distincao_conceptual",
    }
    tipo = tipo_map.get(tipo, tipo)

    if tipo not in VALID_TIPO_UNIDADE:
        tipo = "desenvolvimento_curto"

    out["tipo_unidade"] = tipo

    criterio = str(out.get("criterio_de_unidade", "")).strip().lower()
    crit_map = {
        "continuidade argumentativa": "continuidade_argumentativa",
        "continuidade temática": "continuidade_tematica",
        "container atómico": "container_atomico",
        "exemplo aplicado": "exemplo_aplicado",
    }
    criterio = crit_map.get(criterio, criterio)

    if criterio not in VALID_CRITERIO_UNIDADE:
        criterio = "continuidade_argumentativa"

    out["criterio_de_unidade"] = criterio

    func = str(out.get("funcao_textual_dominante", "")).strip().lower()
    func_map = {
        "afirmação": "afirmacao",
        "crítica": "critica",
        "distinção": "distincao",
        "síntese": "sintese",
    }
    func = func_map.get(func, func)

    if func not in VALID_FUNCAO:
        func = "desenvolvimento"

    out["funcao_textual_dominante"] = func

    tema = str(out.get("tema_dominante_provisorio", "")).strip()
    out["tema_dominante_provisorio"] = tema[:160] if tema else "tema a rever"

    out["conceitos_relevantes_provisorios"] = coerce_list_str(
        out.get("conceitos_relevantes_provisorios"),
        max_items=5,
    )

    grau = str(out.get("integridade_semantica_grau", "")).strip().lower()
    if grau not in VALID_GRAU:
        grau = "medio"

    out["integridade_semantica_grau"] = grau

    conf = str(out.get("confianca_segmentacao", "")).strip().lower()
    if conf not in VALID_CONFIANCA:
        conf = "media"

    out["confianca_segmentacao"] = conf

    out["requer_revisao_manual_prioritaria"] = bool(
        out.get("requer_revisao_manual_prioritaria", False)
    )

    return out


# -----------------------------------------------------------------------------
# Construção dos fragmentos
# -----------------------------------------------------------------------------

def build_group_text(unit_map: Dict[str, Dict[str, Any]], ids: List[str]) -> str:
    return "\n\n".join(unit_map[x]["text"] for x in ids)


def annotate_groups(
    container: Dict[str, Any],
    units: List[Dict[str, Any]],
    groups: List[Dict[str, List[str]]],
    api: ApiConfig,
    use_api: bool,
    internal_mode: bool,
) -> List[Dict[str, Any]]:
    unit_map = {u["unit_id"]: u for u in units}
    by_idx: Dict[int, Dict[str, Any]] = {}

    if use_api:
        raw = openai_generate_json(
            api,
            build_phase2_prompt(container, units, groups, internal_mode),
            phase2_schema(),
            "phase2_segment_annotations",
        )

        if not isinstance(raw, dict) or not isinstance(raw.get("grupos"), list):
            raise RuntimeError("Fase 2 não devolveu objeto com grupos")

        for item in raw["grupos"]:
            if isinstance(item, dict) and "indice" in item:
                by_idx[int(item["indice"])] = normalize_annotation(item)

    out: List[Dict[str, Any]] = []

    for i, group in enumerate(groups, start=1):
        if i in by_idx:
            ann = by_idx[i]
        else:
            fragment_text = build_group_text(unit_map, group["unidades_origem"])
            ann = normalize_annotation(heuristic_annotation(fragment_text))

        out.append(ann)

    return out


def build_fragment(
    container: Dict[str, Any],
    units: List[Dict[str, Any]],
    group: Dict[str, List[str]],
    ann: Dict[str, Any],
    idx: int,
    model_name: str,
    internal_mode: bool,
) -> Dict[str, Any]:
    unit_map = {u["unit_id"]: u for u in units}
    ids = group["unidades_origem"]
    texts = [unit_map[x]["text"] for x in ids]
    text = "\n\n".join(texts)
    text_norm = normalize_text(text)

    source_paragraph_ids: List[str] = []
    for uid in ids:
        pid = unit_map[uid]["source_paragraph_id"]
        if pid not in source_paragraph_ids:
            source_paragraph_ids.append(pid)

    frag_id = f"{container['container_id']}_SEG_{idx:03d}"

    return {
        "fragment_id": frag_id,
        "origem": {
            "ficheiro": container.get("origem_ficheiro"),
            "origem_id": container.get("container_id"),
            "data": container.get("data"),
            "titulo_container": container.get("titulo_container"),
            "tem_header_formal": container.get("tem_header_formal"),
            "header_original": container.get("header_original"),
            "ordem_no_ficheiro": container.get("ordem_no_ficheiro"),
            "blocos_fonte": [
                {
                    "bloco_id": container.get("container_id"),
                    "paragrafos_origem": source_paragraph_ids,
                    "unidades_origem": ids,
                }
            ],
        },
        "tipo_material_fonte": container.get("tipo_material_fonte"),
        "texto_fragmento": text,
        "texto_normalizado": text_norm,
        "texto_fonte_reconstituido": text,
        "paragrafos_agregados": len(source_paragraph_ids),
        "frases_aproximadas": sentence_count(text),
        "n_chars_fragmento": len(text_norm),
        "densidade_aprox": density_label(len(text_norm)),
        "segmentacao": {
            "tipo_unidade": ann["tipo_unidade"],
            "criterio_de_unidade": ann["criterio_de_unidade"],
            "houve_fusao_de_paragrafos": len(source_paragraph_ids) > 1,
            "houve_corte_interno": internal_mode or (len(ids) < len(units)),
            "container_tipo_segmentacao": "segmentacao_semantica_duas_fases",
        },
        "funcao_textual_dominante": ann["funcao_textual_dominante"],
        "tema_dominante_provisorio": ann["tema_dominante_provisorio"],
        "conceitos_relevantes_provisorios": ann["conceitos_relevantes_provisorios"],
        "integridade_semantica": {
            "grau": ann["integridade_semantica_grau"],
        },
        "confianca_segmentacao": ann["confianca_segmentacao"],
        "relacoes_locais": {
            "fragmento_anterior": None,
            "fragmento_seguinte": None,
            "continua_anterior": False,
            "prepara_seguinte": False,
        },
        "estado_revisao": "segmentado_auto",
        "sinalizador_para_cadencia": {
            "pronto_para_extrator_cadencia": True,
            "requer_revisao_manual_prioritaria": ann["requer_revisao_manual_prioritaria"],
        },
        "_metadados_segmentador": {
            "modelo": model_name,
            "versao_segmentador": SCRIPT_VERSION,
            "timestamp": utc_ts(),
            "hash_texto_normalizado": sha256_text(text_norm),
            "modo_interno": internal_mode,
        },
    }


def wire_local_relations(frags: List[Dict[str, Any]]) -> None:
    for i, frag in enumerate(frags):
        prev = frags[i - 1]["fragment_id"] if i > 0 else None
        nxt = frags[i + 1]["fragment_id"] if i + 1 < len(frags) else None

        frag["relacoes_locais"]["fragmento_anterior"] = prev
        frag["relacoes_locais"]["fragmento_seguinte"] = nxt
        frag["relacoes_locais"]["continua_anterior"] = i > 0
        frag["relacoes_locais"]["prepara_seguinte"] = i + 1 < len(frags)


# -----------------------------------------------------------------------------
# Validação do output
# -----------------------------------------------------------------------------

def validate_output(fragments: List[Dict[str, Any]]) -> Dict[str, Any]:
    errors: List[Dict[str, str]] = []
    ids = set()

    for frag in fragments:
        fid = frag.get("fragment_id")

        if fid in ids:
            errors.append({
                "fragment_id": str(fid),
                "codigo": "fragment_id_duplicado",
                "detalhe": str(fid),
            })

        ids.add(fid)

        tipo = frag.get("segmentacao", {}).get("tipo_unidade")
        if tipo not in VALID_TIPO_UNIDADE:
            errors.append({
                "fragment_id": str(fid),
                "codigo": "tipo_unidade_invalido",
                "detalhe": f"tipo_unidade inválido: {tipo}",
            })

        criterio = frag.get("segmentacao", {}).get("criterio_de_unidade")
        if criterio not in VALID_CRITERIO_UNIDADE:
            errors.append({
                "fragment_id": str(fid),
                "codigo": "criterio_unidade_invalido",
                "detalhe": f"criterio_de_unidade inválido: {criterio}",
            })

        func = frag.get("funcao_textual_dominante")
        if func not in VALID_FUNCAO:
            errors.append({
                "fragment_id": str(fid),
                "codigo": "funcao_textual_invalida",
                "detalhe": f"funcao_textual_dominante inválida: {func}",
            })

    return {
        "ficheiro": "fragmentos_resegmentados.json",
        "n_fragmentos": len(fragments),
        "n_erros": len(errors),
        "n_avisos": 0,
        "valido": len(errors) == 0,
        "erros": errors,
        "avisos": [],
    }


# -----------------------------------------------------------------------------
# Processamento dos containers
# -----------------------------------------------------------------------------

def process_container(
    container: Dict[str, Any],
    api: ApiConfig,
    use_api: bool,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
    state = {
        "status": "ok",
        "versao_segmentador": SCRIPT_VERSION,
        "ts": utc_ts(),
        "tentativas": api.retries if use_api else 1,
        "last_error": None,
        "n_fragmentos_gerados": 0,
        "modo": "duas_fases",
    }

    failures: List[Dict[str, Any]] = []

    try:
        units, internal_mode = build_units(container)

        if not units:
            raise RuntimeError("container sem unidades válidas")

        if len(units) == 1:
            plan_obj = {"grupos": [{"unidades_origem": [units[0]["unit_id"]]}]}

        else:
            if use_api:
                plan_obj = openai_generate_json(
                    api,
                    build_phase1_prompt(container, units, internal_mode),
                    phase1_schema(),
                    "phase1_segment_plan",
                )

                ok, msg = validate_plan(units, plan_obj)
                if not ok:
                    raise RuntimeError(f"plano inválido: {msg}")

            else:
                plan_obj = heuristic_plan(units)

        groups = plan_obj["grupos"]

        anns = annotate_groups(
            container=container,
            units=units,
            groups=groups,
            api=api,
            use_api=use_api,
            internal_mode=internal_mode,
        )

        frags = [
            build_fragment(
                container=container,
                units=units,
                group=grp,
                ann=ann,
                idx=i,
                model_name=api.model if use_api else "heuristico_local",
                internal_mode=internal_mode,
            )
            for i, (grp, ann) in enumerate(zip(groups, anns), start=1)
        ]

        wire_local_relations(frags)

        state["n_fragmentos_gerados"] = len(frags)
        state["modo_interno"] = internal_mode

        return frags, state, failures

    except Exception as e:
        state["status"] = "erro"
        state["last_error"] = str(e)

        failures.append({
            "container_id": container.get("container_id"),
            "fase": "resegmentacao",
            "erro": str(e),
            "timestamp": utc_ts(),
        })

        return [], state, failures


# -----------------------------------------------------------------------------
# Relatório TXT
# -----------------------------------------------------------------------------

def build_txt_report(
    run_name: str,
    input_path: Path,
    output_json: Path,
    validation: Dict[str, Any],
    states: Dict[str, Any],
    failures: List[Dict[str, Any]],
    run_dir: Path,
    reseg_dir: Path,
    valid_dir: Path,
    reports_dir: Path,
    ready_copy: Optional[Path],
) -> str:
    ok_count = sum(1 for s in states.values() if s.get("status") == "ok")
    err_count = sum(1 for s in states.values() if s.get("status") != "ok")
    total_frags = sum(int(s.get("n_fragmentos_gerados", 0)) for s in states.values())
    internal_count = sum(1 for s in states.values() if s.get("modo_interno") is True)

    lines: List[str] = []

    lines.append("RESSEGMENTADOR SEMÂNTICO — RELATÓRIO")
    lines.append("=" * 72)
    lines.append(f"Input: {input_path.name}")
    lines.append(f"Output JSON: {output_json.name}")
    lines.append(f"Versão: {SCRIPT_VERSION}")
    lines.append("")
    lines.append("Pastas")
    lines.append("-" * 72)
    lines.append(f"- run_dir={run_dir}")
    lines.append(f"- resegmentacao={reseg_dir}")
    lines.append(f"- validacao={valid_dir}")
    lines.append(f"- relatorios={reports_dir}")
    if ready_copy:
        lines.append(f"- pronto_para_integrar={ready_copy}")
    else:
        lines.append("- pronto_para_integrar=∅")
    lines.append("")
    lines.append("Resumo")
    lines.append("-" * 72)
    lines.append(f"- containers_ok={ok_count}")
    lines.append(f"- containers_erro={err_count}")
    lines.append(f"- containers_com_corte_interno={internal_count}")
    lines.append(f"- total_fragmentos={total_frags}")
    lines.append(f"- validacao_valido={validation['valido']}")
    lines.append(f"- n_erros_validacao={validation['n_erros']}")

    if failures:
        lines.append("")
        lines.append("Falhas")
        lines.append("-" * 72)
        for f in failures:
            lines.append(f"- {f['container_id']}: {f['erro']}")

    return "\n".join(lines) + "\n"


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ressegmentador semântico em duas fases para containers estabilizados."
    )

    parser.add_argument(
        "input_json",
        help="JSON de containers de entrada. Normalmente: 03_runs/<run>/02_containers/containers_segmentacao__<run>.json",
    )

    parser.add_argument(
        "--output-dir",
        default=".",
        help=(
            "Opcional. Pasta da run. Se omitido, o script infere a run a partir "
            "do input em 03_runs/<run>/02_containers/."
        ),
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Modelo OpenAI.",
    )

    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Força modo heurístico local, sem API.",
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help="Número de tentativas para chamadas OpenAI.",
    )

    args = parser.parse_args()

    input_path = resolve_input_path(args.input_json)

    run_dir, reseg_dir, valid_dir, reports_dir = infer_output_dirs(
        input_path=input_path,
        output_dir_arg=args.output_dir,
    )

    for d in [run_dir, reseg_dir, valid_dir, reports_dir, READY_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    containers = read_json(input_path)
    if not isinstance(containers, list):
        raise SystemExit("O input tem de ser uma lista de containers.")

    run_name = discover_run_name(input_path)

    output_json = reseg_dir / f"fragmentos_resegmentados__{run_name}.json"
    state_json = reseg_dir / f"estado_resegmentador__{run_name}.json"
    failures_json = reseg_dir / f"falhas_resegmentador__{run_name}.json"
    validation_json = valid_dir / f"relatorio_validacao_fragmentos__{run_name}.json"
    report_txt = reports_dir / f"relatorio_resegmentador__{run_name}.txt"

    api = ApiConfig(
        model=args.model,
        retries=max(1, args.retries),
    )

    use_api = CLIENT is not None and not args.local_only

    all_frags: List[Dict[str, Any]] = []
    states: Dict[str, Any] = {}
    failures: List[Dict[str, Any]] = []

    for container in containers:
        frags, state, fail = process_container(
            container=container,
            api=api,
            use_api=use_api,
        )

        if frags:
            all_frags.extend(frags)

        states[str(container.get("container_id"))] = state
        failures.extend(fail)

    validation = validate_output(all_frags)

    write_json(output_json, all_frags)
    write_json(state_json, {
        "versao_segmentador": SCRIPT_VERSION,
        "containers": states,
    })
    write_json(failures_json, failures)
    write_json(validation_json, validation)

    ready_copy: Optional[Path] = None
    if validation["valido"]:
        ready_copy = READY_DIR / output_json.name
        shutil.copy2(output_json, ready_copy)

    report_txt.write_text(
        build_txt_report(
            run_name=run_name,
            input_path=input_path,
            output_json=output_json,
            validation=validation,
            states=states,
            failures=failures,
            run_dir=run_dir,
            reseg_dir=reseg_dir,
            valid_dir=valid_dir,
            reports_dir=reports_dir,
            ready_copy=ready_copy,
        ),
        encoding="utf-8",
    )

    print("=" * 72)
    print("RESSEGMENTADOR SEMÂNTICO")
    print("=" * 72)
    print(f"Input:               {input_path}")
    print(f"Modo:                {'api_openai' if use_api else 'heuristico_local'}")
    print(f"Run dir:             {run_dir}")
    print(f"Containers:          {len(containers)}")
    print(f"Fragmentos gerados:  {len(all_frags)}")
    print(f"Validação ok:        {validation['valido']}")
    print("-" * 72)
    print(f"Output:              {output_json}")
    print(f"Estado:              {state_json}")
    print(f"Falhas:              {failures_json}")
    print(f"Validação:           {validation_json}")
    print(f"Relatório:           {report_txt}")
    if ready_copy:
        print(f"Pronto a integrar:   {ready_copy}")
    else:
        print("Pronto a integrar:   ∅")
    print("=" * 72)

    return 0 if validation["valido"] else 1


if __name__ == "__main__":
    raise SystemExit(main())