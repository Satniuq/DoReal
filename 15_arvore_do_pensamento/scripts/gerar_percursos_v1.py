# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


INPUT_TREE_FILENAME = "arvore_do_pensamento_v1.json"
REPORT_FILENAME = "relatorio_geracao_percursos_v1.txt"

MAX_ASSOCIACOES_POR_RAMO = 2
LIMIAR_ASSOCIACAO = 3
LIMIAR_ASSOCIACAO_FORTE = 4


class PercursoGenerationError(RuntimeError):
    """Erro fatal na geração de percursos."""


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera e associa percursos na árvore do pensamento v1."
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help="Processa apenas os primeiros N ramos, por ordem, para ensaio.",
    )
    parser.add_argument(
        "--forcar",
        action="store_true",
        help="Permite substituir o bloco 'percursos[]' caso já exista conteúdo.",
    )
    args = parser.parse_args(argv)

    if args.limite is not None and args.limite <= 0:
        raise SystemExit("ERRO: --limite tem de ser um inteiro positivo.")

    return args


def build_paths(script_dir: Path) -> Dict[str, Path]:
    arvore_root = script_dir.parent
    project_root = arvore_root.parent

    tree_path = arvore_root / "01_dados" / INPUT_TREE_FILENAME
    report_path = arvore_root / "01_dados" / REPORT_FILENAME

    indice_por_percurso_path = (
        project_root
        / "13_Meta_Indice"
        / "indice"
        / "indice_por_percurso.json"
    )
    meta_referencia_path = (
        project_root
        / "13_Meta_Indice"
        / "meta"
        / "meta_referencia_do_percurso.json"
    )
    indice_de_percursos_path = (
        project_root
        / "13_Meta_Indice"
        / "indices_derivados"
        / "indice_de_percursos.json"
    )
    conteudo_completo_path = (
        project_root
        / "13_Meta_Indice"
        / "percursos"
        / "conteudo_completo.txt"
    )

    return {
        "script_dir": script_dir,
        "arvore_root": arvore_root,
        "project_root": project_root,
        "tree": tree_path,
        "report": report_path,
        "indice_por_percurso": indice_por_percurso_path,
        "meta_referencia": meta_referencia_path,
        "indice_de_percursos": indice_de_percursos_path,
        "conteudo_completo": conteudo_completo_path,
    }


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise PercursoGenerationError(f"Ficheiro não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PercursoGenerationError(f"JSON inválido em {path}: {exc}") from exc
    except OSError as exc:
        raise PercursoGenerationError(f"Não foi possível ler {path}: {exc}") from exc


def load_optional_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    return load_json(path)


def save_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        temp_path.replace(path)
    except OSError as exc:
        raise PercursoGenerationError(f"Não foi possível escrever {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as exc:
        raise PercursoGenerationError(f"Não foi possível escrever o relatório {path}: {exc}") from exc


def require_dict(value: Any, context: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise PercursoGenerationError(
            f"Tipo inválido em {context}: esperado object/dict, obtido {type(value).__name__}."
        )
    return value


def require_list(value: Any, context: str) -> List[Any]:
    if not isinstance(value, list):
        raise PercursoGenerationError(
            f"Tipo inválido em {context}: esperado array/list, obtido {type(value).__name__}."
        )
    return value


def require_key(mapping: Dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise PercursoGenerationError(f"Falta a chave obrigatória '{key}' em {context}.")
    return mapping[key]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def normalize_text(text: Optional[str]) -> str:
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().replace("-", "_").replace("/", "_").replace(" ", "_")


def tokenize_text(text: Optional[str]) -> Set[str]:
    normalized = normalize_text(text)
    cleaned = []
    for ch in normalized:
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    tokens = set()
    for token in "".join(cleaned).split():
        token = token.strip("_")
        if token:
            tokens.add(token)
    return tokens


def parse_prefixed_number(value: str, prefix: str) -> Optional[int]:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value.startswith(prefix):
        return None
    suffix = value[len(prefix):]
    if suffix.isdigit():
        return int(suffix)
    return None


def unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def merge_unique(existing: List[str], incoming: Iterable[str]) -> List[str]:
    return unique_preserve_order(list(existing) + list(incoming))


def mode_preserve_order(values: Iterable[Optional[str]]) -> Optional[str]:
    filtered: List[str] = []
    for value in values:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                filtered.append(stripped)
    if not filtered:
        return None
    counts = Counter(filtered)
    best_count = max(counts.values())
    best = {k for k, v in counts.items() if v == best_count}
    for value in filtered:
        if value in best:
            return value
    return None


def parse_cap_number(cap_id: str) -> Optional[int]:
    if not isinstance(cap_id, str):
        return None
    cap_id = cap_id.strip()
    if not cap_id.startswith("CAP_"):
        return None
    parts = cap_id.split("_")
    if len(parts) >= 2 and parts[1].isdigit():
        return int(parts[1])
    return None


def sort_ramos_by_order(
    ramos: List[Dict[str, Any]],
    microlinha_map: Dict[str, Dict[str, Any]],
    fragment_map: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    def ramo_key(ramo: Dict[str, Any]) -> Tuple[int, str]:
        ramo_id = str(ramo.get("id", ""))
        microlinha_ids = ramo.get("microlinha_ids")
        if not isinstance(microlinha_ids, list) or not microlinha_ids:
            return (10**9, ramo_id)

        orders: List[int] = []
        for microlinha_id in microlinha_ids:
            microlinha = microlinha_map.get(microlinha_id)
            if not isinstance(microlinha, dict):
                continue
            fragment_ids = microlinha.get("fragmento_ids")
            if not isinstance(fragment_ids, list):
                continue
            for fragment_id in fragment_ids:
                fragment = fragment_map.get(fragment_id)
                if not isinstance(fragment, dict):
                    continue
                order = fragment.get("ordem_no_ficheiro")
                if isinstance(order, int):
                    orders.append(order)

        return (min(orders) if orders else 10**9, ramo_id)

    return sorted(ramos, key=ramo_key)


def ensure_tree_minimally_usable(tree: Dict[str, Any], args: argparse.Namespace) -> None:
    if not isinstance(tree, dict):
        raise PercursoGenerationError("O ficheiro da árvore tem de ser um objeto JSON no topo.")

    for key in ("fragmentos", "microlinhas", "ramos", "percursos", "validacao"):
        if key not in tree:
            raise PercursoGenerationError(f"Falta o bloco obrigatório '{key}' na árvore.")

    fragmentos = require_list(tree.get("fragmentos"), "fragmentos")
    microlinhas = require_list(tree.get("microlinhas"), "microlinhas")
    ramos = require_list(tree.get("ramos"), "ramos")
    percursos = require_list(tree.get("percursos"), "percursos")

    if not fragmentos:
        raise PercursoGenerationError("O bloco 'fragmentos' está vazio.")
    if not microlinhas:
        raise PercursoGenerationError("O bloco 'microlinhas' está vazio.")
    if not ramos:
        raise PercursoGenerationError("O bloco 'ramos' está vazio. Gere primeiro os ramos.")

    if percursos and not args.forcar:
        raise PercursoGenerationError(
            "O bloco 'percursos' já contém dados. Use --forcar para regenerar e substituir."
        )

    validacao = require_dict(tree.get("validacao"), "validacao")
    require_dict(require_key(validacao, "metricas", "validacao"), "validacao.metricas")


def collect_maps(
    tree: Dict[str, Any]
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    fragment_map: Dict[str, Dict[str, Any]] = {}
    for idx, fragment in enumerate(require_list(tree["fragmentos"], "fragmentos"), start=1):
        fragment_dict = require_dict(fragment, f"fragmentos[{idx}]")
        fragment_id = require_key(fragment_dict, "id", f"fragmentos[{idx}]")
        if not isinstance(fragment_id, str) or not fragment_id.strip():
            raise PercursoGenerationError(f"fragmentos[{idx}].id é inválido.")
        fragment_map[fragment_id] = fragment_dict

    microlinha_map: Dict[str, Dict[str, Any]] = {}
    for idx, microlinha in enumerate(require_list(tree["microlinhas"], "microlinhas"), start=1):
        microlinha_dict = require_dict(microlinha, f"microlinhas[{idx}]")
        microlinha_id = require_key(microlinha_dict, "id", f"microlinhas[{idx}]")
        if not isinstance(microlinha_id, str) or not microlinha_id.strip():
            raise PercursoGenerationError(f"microlinhas[{idx}].id é inválido.")
        microlinha_map[microlinha_id] = microlinha_dict

    ramo_map: Dict[str, Dict[str, Any]] = {}
    for idx, ramo in enumerate(require_list(tree["ramos"], "ramos"), start=1):
        ramo_dict = require_dict(ramo, f"ramos[{idx}]")
        ramo_id = require_key(ramo_dict, "id", f"ramos[{idx}]")
        if not isinstance(ramo_id, str) or not ramo_id.strip():
            raise PercursoGenerationError(f"ramos[{idx}].id é inválido.")
        ramo_map[ramo_id] = ramo_dict

    existing_percurso_map: Dict[str, Dict[str, Any]] = {}
    for idx, percurso in enumerate(require_list(tree["percursos"], "percursos"), start=1):
        percurso_dict = require_dict(percurso, f"percursos[{idx}]")
        percurso_id = percurso_dict.get("id")
        if isinstance(percurso_id, str) and percurso_id.strip():
            existing_percurso_map[percurso_id] = percurso_dict

    return fragment_map, microlinha_map, ramo_map, existing_percurso_map


def safe_list_of_strings(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    result: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def extract_caps_ids(caps: Any) -> List[str]:
    result: List[str] = []
    if isinstance(caps, list):
        for item in caps:
            if isinstance(item, dict):
                cap_id = item.get("id")
                if isinstance(cap_id, str) and cap_id.strip():
                    result.append(cap_id.strip())
            elif isinstance(item, str) and item.strip():
                result.append(item.strip())
    return unique_preserve_order(result)


def infer_tipo_instancia_from_secondary_index(
    percurso_id: str,
    indice_de_percursos_data: Optional[Dict[str, Any]],
) -> Optional[str]:
    if not isinstance(indice_de_percursos_data, dict):
        return None

    for tipo_instancia, grupo in indice_de_percursos_data.items():
        if isinstance(grupo, dict):
            if percurso_id in grupo:
                return tipo_instancia
            maybe_ids = grupo.get("ids")
            if isinstance(maybe_ids, list) and percurso_id in maybe_ids:
                return tipo_instancia
        elif isinstance(grupo, list):
            if percurso_id in grupo:
                return tipo_instancia
    return None


def infer_meta_from_optional_sources(
    percurso_id: str,
    indice_item: Dict[str, Any],
    meta_ref_data: Optional[Dict[str, Any]],
    indice_de_percursos_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    meta = indice_item.get("meta")
    if isinstance(meta, dict):
        meta = dict(meta)
    else:
        meta = {}

    if meta_ref_data and percurso_id in meta_ref_data and isinstance(meta_ref_data[percurso_id], dict):
        ref_meta = meta_ref_data[percurso_id]
        for key in ("tipo_instancia", "pressupoe_percursos", "observacao"):
            if key not in meta and key in ref_meta:
                meta[key] = ref_meta[key]

    if "pressupoe_percursos" not in meta:
        meta["pressupoe_percursos"] = []

    if "observacao" not in meta:
        meta["observacao"] = ""

    if "tipo_instancia" not in meta:
        guessed_tipo = infer_tipo_instancia_from_secondary_index(percurso_id, indice_de_percursos_data)
        meta["tipo_instancia"] = guessed_tipo or ""

    return {
        "tipo_instancia": meta.get("tipo_instancia", "") if isinstance(meta.get("tipo_instancia"), str) else "",
        "pressupoe_percursos": safe_list_of_strings(meta.get("pressupoe_percursos", [])),
        "observacao": meta.get("observacao", "") if isinstance(meta.get("observacao"), str) else "",
    }


def build_percurso_summary(
    percurso_id: str,
    indice_item: Dict[str, Any],
    existing_percurso_map: Dict[str, Dict[str, Any]],
    meta_ref_data: Optional[Dict[str, Any]],
    indice_de_percursos_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    existing = existing_percurso_map.get(percurso_id, {})

    meta = infer_meta_from_optional_sources(
        percurso_id=percurso_id,
        indice_item=indice_item,
        meta_ref_data=meta_ref_data,
        indice_de_percursos_data=indice_de_percursos_data,
    )

    pressupostos_fecho_ids = safe_list_of_strings(indice_item.get("pressupostos_fecho", []))

    directo = indice_item.get("directo")
    if not isinstance(directo, dict):
        directo = {}

    com_pressupostos = indice_item.get("com_pressupostos")
    if not isinstance(com_pressupostos, dict):
        com_pressupostos = {}

    direct_caps_ids = extract_caps_ids(directo.get("caps_ids") or directo.get("caps"))
    cap_ids_axiais = extract_caps_ids(directo.get("axial"))
    cap_ids_participantes = extract_caps_ids(directo.get("participante"))

    com_percursos_base_ids = safe_list_of_strings(
        com_pressupostos.get("percursos_base", com_pressupostos.get("percursos_base_ids", []))
    )
    com_caps_ids = extract_caps_ids(com_pressupostos.get("caps_ids") or com_pressupostos.get("caps"))
    com_resumo = com_pressupostos.get("resumo", "")
    if not isinstance(com_resumo, str):
        com_resumo = ""

    previous_convergencias = safe_list_of_strings(existing.get("convergencia_ids", []))

    return {
        "id": percurso_id,
        "tipo_no": "percurso",
        "meta": meta,
        "pressupostos_fecho_ids": pressupostos_fecho_ids,
        "directo": {
            "caps_ids": direct_caps_ids,
            "cap_ids_axiais": cap_ids_axiais,
            "cap_ids_participantes": cap_ids_participantes,
        },
        "com_pressupostos": {
            "percursos_base_ids": com_percursos_base_ids,
            "caps_ids": com_caps_ids,
            "resumo": com_resumo,
        },
        "ramo_ids": [],
        "convergencia_ids": previous_convergencias,
        "estado_validacao": "valido",
    }


def infer_aliases_for_percurso(percurso_id: str, tokens: Set[str]) -> Tuple[Set[str], Set[str], Set[str]]:
    normalized_id = normalize_text(percurso_id)

    aliases_map: Dict[str, Dict[str, Set[str]]] = {
        "P_EIXO_ONTOLOGICO_NUCLEAR": {
            "zones": {"ontologia", "ontologico", "eixo_ontologico", "ontologico_nuclear", "fundacional"},
            "themes": {"distincao", "relacionalidade", "estrutura", "limite", "ser", "nao_ser", "real"},
            "problems": {"fundacao", "fundacional", "ontologia", "determinacao"},
        },
        "P_ESTRUTURA_OPERACIONAL_DO_REAL": {
            "zones": {"estrutura_operacional", "operacional", "estrutura_operacional_do_real", "real"},
            "themes": {"poder_ser", "potencialidade", "atualizacao", "continuidade", "campo", "tempo", "contingencia"},
            "problems": {"operacao", "dinamica", "real", "estrutura"},
        },
        "P_TRANSICAO_ANTROPOLOGICA_ONTOLOGICA": {
            "zones": {"transicao_antropologica", "antropologica", "transicao_antropologica_ontologica"},
            "themes": {"localidade", "ponto_de_vista", "apreensao", "humano", "transicao"},
            "problems": {"transicao", "antropologico", "localizacao"},
        },
        "P_EIXO_CAMPO_E_LOCALIZACAO": {
            "zones": {"campo_localizacao", "campo", "localizacao", "localidade"},
            "themes": {"campo", "circulo", "escala", "localidade", "fecho"},
            "problems": {"campo", "localizacao", "escala"},
        },
        "P_EIXO_SIMBOLICO_MEDIACIONAL": {
            "zones": {"simbolico_mediacional", "simbolico", "mediacao", "mediacional"},
            "themes": {"representacao", "simbolo", "linguagem", "consciencia", "memoria", "mediacao"},
            "problems": {"simbolico", "mediacao", "linguagem"},
        },
        "P_EIXO_EPISTEMOLOGICO": {
            "zones": {"epistemologia", "epistemologico", "conhecimento"},
            "themes": {"adequacao", "verdade", "criterio", "juizo", "conhecimento", "epistemologia"},
            "problems": {"verdade", "erro", "adequacao", "epistemologia"},
        },
        "P_EIXO_ESCALA_E_ERRO_DE_ESCALA": {
            "zones": {"escala", "erro_escala"},
            "themes": {"escala", "erro", "erro_de_escala", "nivel", "colapso"},
            "problems": {"erro_escala", "escala"},
        },
        "P_EIXO_ETICO_NARRATIVO": {
            "zones": {"etica", "etico_narrativo", "narrativo"},
            "themes": {"liberdade", "responsabilidade", "bem", "mal", "virtude", "vida_boa", "narrativa"},
            "problems": {"etica", "bem", "mal", "vida_boa"},
        },
        "P_CRITICA_SISTEMICA_E_REINTEGRACAO_ONTOLOGICA": {
            "zones": {"critica_sistemica", "sistemica", "reintegracao_ontologica"},
            "themes": {"sistema", "critica", "reintegracao", "totalizacao", "reducionismo"},
            "problems": {"critica", "sistema", "reintegracao"},
        },
        "P_PERCURSO_DO_ERRO_E_CORRECAO": {
            "zones": {"erro_correcao", "erro", "correcao"},
            "themes": {"erro", "correcao", "criterio", "retificacao"},
            "problems": {"erro", "correcao"},
        },
        "P_PERCURSO_DO_ERRO_E_DA_DEGENERACAO": {
            "zones": {"erro_degeneracao", "degeneracao", "erro"},
            "themes": {"erro", "degeneracao", "desvio"},
            "problems": {"erro", "degeneracao"},
        },
        "P_PERCURSO_DA_DEGENERACAO_ETICA": {
            "zones": {"degeneracao_etica", "etica", "degeneracao"},
            "themes": {"degeneracao", "etica", "responsabilidade", "bem", "mal"},
            "problems": {"degeneracao", "etica"},
        },
        "P_PERCURSO_DA_VIDA_BOA": {
            "zones": {"vida_boa", "etica", "pratico"},
            "themes": {"vida_boa", "prudencia", "virtude", "bem"},
            "problems": {"vida_boa", "etica"},
        },
        "P_PERCURSO_DA_VIDA_BOA_FILOSOFICA": {
            "zones": {"vida_boa_filosofica", "vida_boa", "filosofica"},
            "themes": {"vida_boa", "filosofica", "reflexao"},
            "problems": {"vida_boa", "filosofia_pratica"},
        },
        "P_PERCURSO_DA_VIDA_BOA_FILOSOFICA_ESPIRAL": {
            "zones": {"vida_boa_filosofica_espiral", "espiral", "vida_boa"},
            "themes": {"vida_boa", "espiral", "retorno", "aprofundamento"},
            "problems": {"vida_boa", "espiral"},
        },
        "P_PERCURSO_INTEGRAL_DO_REAL_A_VIDA_BOA": {
            "zones": {"integral", "real_a_vida_boa", "vida_boa"},
            "themes": {"integral", "real", "vida_boa", "sintese"},
            "problems": {"integracao", "vida_boa", "totalidade"},
        },
        "P_PERCURSO_ONTOLOGICAMENTE_ESTERIL_POR_INVERSAO_DIRECIONAL": {
            "zones": {"inversao_direcional", "esteril", "erro"},
            "themes": {"inversao", "esteril", "desorientacao"},
            "problems": {"inversao", "esterilidade"},
        },
    }

    entry = aliases_map.get(percurso_id, {"zones": set(), "themes": set(), "problems": set()})
    zones = set(entry["zones"])
    themes = set(entry["themes"])
    problems = set(entry["problems"])

    if "ontologico" in normalized_id:
        zones.add("ontologia")
        themes.add("ontologico")
    if "epistemologico" in normalized_id:
        zones.add("epistemologia")
        themes.add("epistemologia")
    if "simbolico" in normalized_id or "mediacional" in normalized_id:
        zones.add("simbolico")
        themes.add("mediacao")
    if "etico" in normalized_id or "vida_boa" in normalized_id:
        zones.add("etica")
        themes.add("vida_boa")
    if "erro" in normalized_id:
        themes.add("erro")
        problems.add("erro")
    if "sistemica" in normalized_id:
        zones.add("critica_sistemica")
        themes.add("sistema")

    zones.update(token for token in tokens if token in {
        "ontologia", "ontologico", "epistemologia", "epistemologico", "simbolo",
        "simbolico", "mediacao", "etica", "narrativo", "escala", "erro",
        "transicao", "antropologica", "campo", "localidade", "sistema", "vida_boa"
    })
    return zones, themes, problems


def base_profile_for_percurso(
    percurso_id: str,
    percurso_summary: Dict[str, Any],
    indice_item: Dict[str, Any],
) -> Dict[str, Any]:
    all_caps = []
    direct = indice_item.get("directo", {})
    comp = indice_item.get("com_pressupostos", {})

    if isinstance(direct, dict):
        for key in ("axial", "participante", "caps"):
            value = direct.get(key)
            if isinstance(value, list):
                all_caps.extend(value)
    if isinstance(comp, dict):
        value = comp.get("caps")
        if isinstance(value, list):
            all_caps.extend(value)

    cap_titles: List[str] = []
    cap_orders: List[int] = []
    cap_fields: List[str] = []
    cap_ids: List[str] = []

    for cap in all_caps:
        if isinstance(cap, dict):
            cap_id = cap.get("id")
            if isinstance(cap_id, str) and cap_id.strip():
                cap_ids.append(cap_id.strip())
                cap_n = parse_cap_number(cap_id.strip())
                if cap_n is not None:
                    cap_orders.append(cap_n)

            order = cap.get("ordem")
            if isinstance(order, int):
                cap_orders.append(order)

            title = cap.get("titulo")
            if isinstance(title, str) and title.strip():
                cap_titles.append(title.strip())

            fields = cap.get("campos")
            if isinstance(fields, list):
                for field in fields:
                    if isinstance(field, str) and field.strip():
                        cap_fields.append(field.strip())

    direct_summary = percurso_summary.get("directo", {})
    if isinstance(direct_summary, dict):
        for cap_id in safe_list_of_strings(direct_summary.get("caps_ids", [])):
            cap_ids.append(cap_id)
            cap_n = parse_cap_number(cap_id)
            if cap_n is not None:
                cap_orders.append(cap_n)

    meta = percurso_summary.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}

    tokens: Set[str] = set()
    tokens.update(tokenize_text(percurso_id))
    tokens.update(tokenize_text(meta.get("tipo_instancia")))
    tokens.update(tokenize_text(meta.get("observacao")))
    for title in cap_titles:
        tokens.update(tokenize_text(title))
    for field in cap_fields:
        tokens.update(tokenize_text(field))

    zone_aliases, theme_aliases, problem_aliases = infer_aliases_for_percurso(
        percurso_id=percurso_id,
        tokens=tokens,
    )

    return {
        "percurso_id": percurso_id,
        "step_nums": sorted(set(cap_orders)),
        "cap_ids": unique_preserve_order(cap_ids),
        "tokens": tokens,
        "zone_aliases": zone_aliases,
        "theme_aliases": theme_aliases,
        "problem_aliases": problem_aliases,
    }


def infer_ramo_profile(
    ramo: Dict[str, Any],
    microlinha_map: Dict[str, Dict[str, Any]],
    fragment_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    ramo_id = str(ramo.get("id", ""))
    microlinha_ids = ramo.get("microlinha_ids")
    if not isinstance(microlinha_ids, list):
        microlinha_ids = []

    zone_values: List[str] = []
    problem_values: List[str] = []
    direction_values: List[str] = []
    utility_values: List[str] = []
    effect_values: List[str] = []
    work_values: List[str] = []
    step_ids: List[str] = []
    step_nums: List[int] = []
    tokens: Set[str] = set()
    fragment_ids_seen: Set[str] = set()
    has_exception = False

    tokens.update(tokenize_text(ramo.get("titulo")))
    tokens.update(tokenize_text(ramo.get("descricao_funcional")))
    tokens.update(tokenize_text(ramo.get("criterio_de_unidade")))

    ramo_steps = ramo.get("passo_ids_alvo")
    if isinstance(ramo_steps, list):
        for step_id in ramo_steps:
            if isinstance(step_id, str) and step_id.strip():
                step_id = step_id.strip()
                step_ids.append(step_id)
                n = parse_prefixed_number(step_id, "P")
                if n is not None:
                    step_nums.append(n)

    if isinstance(ramo.get("estado_excecao"), str) and ramo.get("estado_excecao") in {"ativa_tolerada", "ativa_prioritaria"}:
        has_exception = True

    for microlinha_id in microlinha_ids:
        microlinha = microlinha_map.get(microlinha_id)
        if not isinstance(microlinha, dict):
            continue

        tokens.update(tokenize_text(microlinha.get("titulo")))
        tokens.update(tokenize_text(microlinha.get("descricao_funcional")))

        criterio = microlinha.get("criterio_de_agregacao")
        if isinstance(criterio, dict):
            for key in (
                "problema_filosofico_dominante",
                "direcao_movimento_dominante",
                "tipo_de_utilidade_dominante",
                "base_dominante",
            ):
                value = criterio.get(key)
                if isinstance(value, str) and value.strip():
                    tokens.update(tokenize_text(value))

            problema = criterio.get("problema_filosofico_dominante")
            if isinstance(problema, str) and problema.strip():
                problem_values.append(problema.strip())

            direcao = criterio.get("direcao_movimento_dominante")
            if isinstance(direcao, str) and direcao.strip():
                direction_values.append(direcao.strip())

            utilidade = criterio.get("tipo_de_utilidade_dominante")
            if isinstance(utilidade, str) and utilidade.strip():
                utility_values.append(utilidade.strip())

        microlinha_exception = microlinha.get("estado_excecao")
        if isinstance(microlinha_exception, str) and microlinha_exception in {"ativa_tolerada", "ativa_prioritaria"}:
            has_exception = True

        fragment_ids = microlinha.get("fragmento_ids")
        if not isinstance(fragment_ids, list):
            continue

        for fragment_id in fragment_ids:
            if not isinstance(fragment_id, str) or not fragment_id.strip():
                continue
            fragment_ids_seen.add(fragment_id)
            fragment = fragment_map.get(fragment_id)
            if not isinstance(fragment, dict):
                continue

            cadencia = fragment.get("cadencia")
            if isinstance(cadencia, dict):
                zona = cadencia.get("zona_provavel_percurso")
                if isinstance(zona, str) and zona.strip():
                    zone_values.append(zona.strip())
                    tokens.update(tokenize_text(zona))

                direcao = cadencia.get("direcao_movimento")
                if isinstance(direcao, str) and direcao.strip():
                    direction_values.append(direcao.strip())
                    tokens.update(tokenize_text(direcao))

                funcao = cadencia.get("funcao_cadencia_principal")
                if isinstance(funcao, str) and funcao.strip():
                    tokens.update(tokenize_text(funcao))

            tratamento = fragment.get("tratamento_filosofico")
            if isinstance(tratamento, dict):
                problema = tratamento.get("problema_filosofico_central")
                if isinstance(problema, str) and problema.strip():
                    problem_values.append(problema.strip())
                    tokens.update(tokenize_text(problema))

                trabalho = tratamento.get("trabalho_no_sistema")
                if isinstance(trabalho, str) and trabalho.strip():
                    work_values.append(trabalho.strip())
                    tokens.update(tokenize_text(trabalho))

            impacto = fragment.get("impacto_mapa")
            if isinstance(impacto, dict):
                utilidade = impacto.get("tipo_de_utilidade_principal")
                if isinstance(utilidade, str) and utilidade.strip():
                    utility_values.append(utilidade.strip())
                    tokens.update(tokenize_text(utilidade))

                efeito = impacto.get("efeito_principal_no_mapa")
                if isinstance(efeito, str) and efeito.strip():
                    effect_values.append(efeito.strip())
                    tokens.update(tokenize_text(efeito))

                proposicoes = impacto.get("proposicoes_do_mapa_tocadas")
                if isinstance(proposicoes, list):
                    for proposicao in proposicoes:
                        if isinstance(proposicao, dict):
                            proposicao_id = proposicao.get("proposicao_id")
                            if isinstance(proposicao_id, str) and proposicao_id.strip():
                                p_id = proposicao_id.strip()
                                step_ids.append(p_id)
                                n = parse_prefixed_number(p_id, "P")
                                if n is not None:
                                    step_nums.append(n)

    dominant_zone = mode_preserve_order(zone_values)
    dominant_problem = mode_preserve_order(problem_values)
    dominant_direction = mode_preserve_order(direction_values)
    dominant_utility = mode_preserve_order(utility_values)
    dominant_effect = mode_preserve_order(effect_values)
    dominant_work = mode_preserve_order(work_values)

    if dominant_zone:
        tokens.update(tokenize_text(dominant_zone))
    if dominant_problem:
        tokens.update(tokenize_text(dominant_problem))
    if dominant_direction:
        tokens.update(tokenize_text(dominant_direction))
    if dominant_utility:
        tokens.update(tokenize_text(dominant_utility))
    if dominant_effect:
        tokens.update(tokenize_text(dominant_effect))
    if dominant_work:
        tokens.update(tokenize_text(dominant_work))

    return {
        "ramo_id": ramo_id,
        "microlinha_ids": [m for m in microlinha_ids if isinstance(m, str)],
        "fragment_ids": sorted(fragment_ids_seen),
        "dominant_zone": dominant_zone,
        "dominant_problem": dominant_problem,
        "dominant_direction": dominant_direction,
        "dominant_utility": dominant_utility,
        "dominant_effect": dominant_effect,
        "dominant_work": dominant_work,
        "step_ids": sorted(set(step_ids), key=lambda x: (parse_prefixed_number(x, "P") or 10**9, x)),
        "step_nums": sorted(set(step_nums)),
        "tokens": tokens,
        "has_exception": has_exception,
    }


def score_ramo_against_percurso(
    ramo_profile: Dict[str, Any],
    percurso_profile: Dict[str, Any],
) -> Tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []

    ramo_tokens: Set[str] = set(ramo_profile["tokens"])
    percurso_tokens: Set[str] = set(percurso_profile["tokens"])
    percurso_zones: Set[str] = set(percurso_profile["zone_aliases"])
    percurso_themes: Set[str] = set(percurso_profile["theme_aliases"])
    percurso_problems: Set[str] = set(percurso_profile["problem_aliases"])
    ramo_step_nums: List[int] = list(ramo_profile["step_nums"])
    percurso_step_nums: List[int] = list(percurso_profile["step_nums"])

    dominant_zone = ramo_profile.get("dominant_zone")
    if isinstance(dominant_zone, str) and dominant_zone.strip():
        zone_norm = normalize_text(dominant_zone)
        if zone_norm in percurso_zones or zone_norm in percurso_tokens:
            score += 2
            reasons.append("zona dominante coincidente")
        else:
            zone_parts = tokenize_text(dominant_zone)
            if zone_parts.intersection(percurso_zones.union(percurso_tokens)):
                score += 1
                reasons.append("zona dominante parcialmente compatível")

    dominant_problem = ramo_profile.get("dominant_problem")
    dominant_work = ramo_profile.get("dominant_work")
    dominant_direction = ramo_profile.get("dominant_direction")
    dominant_utility = ramo_profile.get("dominant_utility")
    dominant_effect = ramo_profile.get("dominant_effect")

    if isinstance(dominant_problem, str) and tokenize_text(dominant_problem).intersection(percurso_problems.union(percurso_themes).union(percurso_tokens)):
        score += 1
        reasons.append("problema dominante compatível")

    if isinstance(dominant_work, str) and tokenize_text(dominant_work).intersection(percurso_themes.union(percurso_tokens)):
        score += 1
        reasons.append("trabalho dominante compatível")

    if isinstance(dominant_direction, str) and tokenize_text(dominant_direction).intersection(percurso_themes.union(percurso_tokens)):
        score += 1
        reasons.append("direção local compatível")

    if isinstance(dominant_utility, str) and tokenize_text(dominant_utility).intersection(percurso_themes.union(percurso_tokens)):
        score += 1
        reasons.append("tipo de utilidade compatível")

    if isinstance(dominant_effect, str) and tokenize_text(dominant_effect).intersection(percurso_themes.union(percurso_tokens)):
        score += 1
        reasons.append("efeito no mapa compatível")

    if ramo_step_nums and percurso_step_nums:
        overlap = sorted(set(ramo_step_nums).intersection(percurso_step_nums))
        if overlap:
            score += 2
            reasons.append(f"passos-alvo compatíveis ({', '.join('P' + str(n) for n in overlap[:3])})")
        else:
            min_gap = min(abs(a - b) for a in ramo_step_nums for b in percurso_step_nums)
            if min_gap <= 1:
                score += 1
                reasons.append("passos-alvo adjacentes à faixa do percurso")

    token_overlap = ramo_tokens.intersection(percurso_themes.union(percurso_tokens).union(percurso_zones))
    if token_overlap:
        score += 1
        reasons.append(f"evidência textual acumulada ({', '.join(sorted(list(token_overlap))[:4])})")

    return score, reasons


def select_percurso_ids_for_ramo(
    ramo_profile: Dict[str, Any],
    percurso_profiles: Dict[str, Dict[str, Any]],
) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
    scored: List[Tuple[str, int, List[str]]] = []

    for percurso_id, profile in percurso_profiles.items():
        score, reasons = score_ramo_against_percurso(ramo_profile, profile)
        if score >= LIMIAR_ASSOCIACAO:
            scored.append((percurso_id, score, reasons))

    scored.sort(key=lambda item: (-item[1], item[0]))

    if not scored:
        return [], {}

    selected: List[Tuple[str, int, List[str]]] = []
    top_score = scored[0][1]

    for percurso_id, score, reasons in scored:
        if len(selected) >= MAX_ASSOCIACOES_POR_RAMO:
            break
        if score < LIMIAR_ASSOCIACAO:
            continue
        if not selected:
            selected.append((percurso_id, score, reasons))
            continue
        if score >= LIMIAR_ASSOCIACAO_FORTE and score >= top_score - 1:
            selected.append((percurso_id, score, reasons))

    selected_ids = [item[0] for item in selected]
    details = {
        percurso_id: {"score": score, "reasons": reasons}
        for percurso_id, score, reasons in selected
    }
    return selected_ids, details


def clear_percurso_links(tree: Dict[str, Any]) -> None:
    for ramo in require_list(tree.get("ramos"), "ramos"):
        ramo_dict = require_dict(ramo, "ramo")
        ramo_dict["percurso_ids_associados"] = []

    for microlinha in require_list(tree.get("microlinhas"), "microlinhas"):
        microlinha_dict = require_dict(microlinha, "microlinha")
        microlinha_dict["percurso_ids_sugeridos"] = []

    for fragment in require_list(tree.get("fragmentos"), "fragmentos"):
        fragment_dict = require_dict(fragment, "fragmento")
        ligacoes = require_dict(
            require_key(fragment_dict, "ligacoes_arvore", f"fragmento {fragment_dict.get('id', '?')}"),
            f"fragmento {fragment_dict.get('id', '?')}.ligacoes_arvore",
        )
        ligacoes["percurso_ids"] = []


def update_tree_with_percursos(
    tree: Dict[str, Any],
    imported_percursos: List[Dict[str, Any]],
    ramo_to_percurso_ids: Dict[str, List[str]],
    microlinha_map: Dict[str, Dict[str, Any]],
    fragment_map: Dict[str, Dict[str, Any]],
    args: argparse.Namespace,
) -> None:
    if args.forcar:
        clear_percurso_links(tree)

    percurso_map = {p["id"]: p for p in imported_percursos}

    for percurso in imported_percursos:
        percurso["ramo_ids"] = []

    ramo_map_in_tree: Dict[str, Dict[str, Any]] = {}
    for ramo in require_list(tree.get("ramos"), "ramos"):
        ramo_dict = require_dict(ramo, "ramo")
        ramo_id = ramo_dict.get("id")
        if isinstance(ramo_id, str):
            ramo_map_in_tree[ramo_id] = ramo_dict

    for ramo_id, percurso_ids in ramo_to_percurso_ids.items():
        ramo_dict = ramo_map_in_tree.get(ramo_id)
        if ramo_dict is None:
            continue

        existing = safe_list_of_strings(ramo_dict.get("percurso_ids_associados", []))
        ramo_dict["percurso_ids_associados"] = merge_unique(existing, percurso_ids)

        for percurso_id in percurso_ids:
            percurso = percurso_map.get(percurso_id)
            if percurso is not None:
                percurso["ramo_ids"] = merge_unique(
                    safe_list_of_strings(percurso.get("ramo_ids", [])),
                    [ramo_id],
                )

    for ramo in require_list(tree.get("ramos"), "ramos"):
        ramo_dict = require_dict(ramo, "ramo")
        percurso_ids = safe_list_of_strings(ramo_dict.get("percurso_ids_associados", []))
        microlinha_ids = ramo_dict.get("microlinha_ids")
        if not isinstance(microlinha_ids, list):
            continue

        for microlinha_id in microlinha_ids:
            microlinha = microlinha_map.get(microlinha_id)
            if not isinstance(microlinha, dict):
                continue
            existing = safe_list_of_strings(microlinha.get("percurso_ids_sugeridos", []))
            microlinha["percurso_ids_sugeridos"] = merge_unique(existing, percurso_ids)

            fragment_ids = microlinha.get("fragmento_ids")
            if not isinstance(fragment_ids, list):
                continue
            for fragment_id in fragment_ids:
                fragment = fragment_map.get(fragment_id)
                if not isinstance(fragment, dict):
                    continue
                ligacoes = require_dict(
                    require_key(fragment, "ligacoes_arvore", f"fragmento {fragment_id}"),
                    f"fragmento {fragment_id}.ligacoes_arvore",
                )
                existing_frag = safe_list_of_strings(ligacoes.get("percurso_ids", []))
                ligacoes["percurso_ids"] = merge_unique(existing_frag, percurso_ids)

    for percurso in imported_percursos:
        ramo_ids = safe_list_of_strings(percurso.get("ramo_ids", []))
        if not ramo_ids:
            percurso["estado_validacao"] = "valido_com_avisos"
            continue

        has_exception = False
        for ramo_id in ramo_ids:
            ramo_dict = ramo_map_in_tree.get(ramo_id)
            if isinstance(ramo_dict, dict):
                ramo_exc = ramo_dict.get("estado_excecao")
                if isinstance(ramo_exc, str) and ramo_exc in {"ativa_tolerada", "ativa_prioritaria"}:
                    has_exception = True
                    break

        percurso["estado_validacao"] = "valido_com_avisos" if has_exception else "valido"

    tree["percursos"] = imported_percursos

    validacao = require_dict(require_key(tree, "validacao", "raiz"), "validacao")
    metricas = require_dict(require_key(validacao, "metricas", "validacao"), "validacao.metricas")
    metricas["total_percursos"] = len(imported_percursos)

    observacoes = validacao.get("observacoes")
    if observacoes is None:
        observacoes = []
        validacao["observacoes"] = observacoes
    elif not isinstance(observacoes, list):
        raise PercursoGenerationError("O campo 'validacao.observacoes' existe mas não é array/list.")

    prefixos_controlados = (
        "Percursos v1:",
        "Geração de percursos v1:",
    )
    validacao["observacoes"] = [
        item for item in observacoes
        if not (isinstance(item, str) and item.startswith(prefixos_controlados))
    ]
    observacoes = validacao["observacoes"]

    total_ramos = len(require_list(tree.get("ramos"), "ramos"))
    ramos_sem_percurso = 0
    for ramo in require_list(tree.get("ramos"), "ramos"):
        ramo_dict = require_dict(ramo, "ramo")
        if not safe_list_of_strings(ramo_dict.get("percurso_ids_associados", [])):
            ramos_sem_percurso += 1

    percursos_vazios = sum(1 for p in imported_percursos if not safe_list_of_strings(p.get("ramo_ids", [])))

    if total_ramos > 0 and ramos_sem_percurso / total_ramos >= 0.35:
        observacoes.append(
            f"Percursos v1: número relevante de ramos sem percurso associado ({ramos_sem_percurso}/{total_ramos})."
        )

    if imported_percursos and percursos_vazios / len(imported_percursos) >= 0.40:
        observacoes.append(
            f"Percursos v1: vários percursos importados ficaram sem ramos associados ({percursos_vazios}/{len(imported_percursos)})."
        )


def build_report_text(
    tree_path: Path,
    indice_path: Path,
    meta_path: Path,
    indice_secundario_path: Path,
    conteudo_path: Path,
    total_percursos_importados: int,
    total_ramos_lidos: int,
    total_ramos_processados: int,
    total_ramos_associados: int,
    total_ramos_sem_percurso: int,
    total_associacoes: int,
    total_percursos_vazios: int,
    args: argparse.Namespace,
    association_logs: List[str],
) -> str:
    lines: List[str] = []
    lines.append("RELATÓRIO DE GERAÇÃO DE PERCURSOS V1")
    lines.append("=" * 72)
    lines.append(f"Data/hora UTC: {utc_now_iso()}")
    lines.append(f"Ficheiro atualizado: {tree_path}")
    lines.append(f"Fonte obrigatória usada: {indice_path}")
    lines.append(f"Fonte opcional meta_referencia_do_percurso.json: {meta_path if meta_path.exists() else 'não localizado'}")
    lines.append(f"Fonte opcional indice_de_percursos.json: {indice_secundario_path if indice_secundario_path.exists() else 'não localizado'}")
    lines.append(f"Fonte opcional conteudo_completo.txt: {conteudo_path if conteudo_path.exists() else 'não localizado'}")
    lines.append("")
    lines.append("Critérios usados")
    lines.append("-" * 72)
    lines.append("1. Importação determinística de todos os percursos do índice por percurso.")
    lines.append("2. Associação ramo→percurso por heurística explícita e auditável.")
    lines.append("3. Sinais considerados: zona dominante, passos-alvo, problema/trabalho dominante e evidência textual acumulada.")
    lines.append("4. Pontuação mínima de associação: 3.")
    lines.append("5. Associação forte preferencial: 4 ou mais.")
    lines.append("6. Parcimónia: no máximo 2 percursos por ramo, apenas quando a evidência é forte e próxima do melhor candidato.")
    lines.append("")
    lines.append("Resumo")
    lines.append("-" * 72)
    lines.append(f"Percursos importados: {total_percursos_importados}")
    lines.append(f"Ramos lidos: {total_ramos_lidos}")
    lines.append(f"Ramos processados nesta execução: {total_ramos_processados}")
    lines.append(f"Ramos associados a pelo menos um percurso: {total_ramos_associados}")
    lines.append(f"Ramos sem percurso (entre os processados): {total_ramos_sem_percurso}")
    lines.append(f"Associações ramo→percurso geradas: {total_associacoes}")
    lines.append(f"Percursos sem ramos associados: {total_percursos_vazios}")
    lines.append(f"Modo de execução: {'teste limitado' if args.limite is not None else 'geração total'}")
    if args.limite is not None:
        lines.append(f"Limite aplicado: {args.limite}")
    lines.append(f"Reescrita forçada: {'sim' if args.forcar else 'não'}")
    lines.append("")
    lines.append("Log de associações")
    lines.append("-" * 72)
    if association_logs:
        lines.extend(association_logs)
    else:
        lines.append("Sem associações registadas.")
    lines.append("")
    lines.append("Conclusão final")
    lines.append("-" * 72)
    lines.append(
        f"Geração concluída com {total_percursos_importados} percursos importados, "
        f"{total_associacoes} associação(ões) e {total_percursos_vazios} percurso(s) vazios."
    )
    lines.append("")
    return "\n".join(lines)


def build_terminal_summary(
    total_percursos_importados: int,
    total_ramos_lidos: int,
    total_ramos_associados: int,
    total_ramos_sem_percurso: int,
    total_percursos_vazios: int,
    report_path: Path,
) -> str:
    lines = [
        f"Percursos importados: {total_percursos_importados}",
        f"Ramos lidos: {total_ramos_lidos}",
        f"Ramos associados a pelo menos um percurso: {total_ramos_associados}",
        f"Ramos sem percurso: {total_ramos_sem_percurso}",
        f"Percursos sem ramos associados: {total_percursos_vazios}",
        "Conclusão final: geração concluída.",
        f"Relatório escrito em: {report_path}",
    ]
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    script_dir = Path(__file__).resolve().parent
    paths = build_paths(script_dir)

    if not paths["indice_por_percurso"].exists():
        raise PercursoGenerationError(
            f"Ficheiro obrigatório não encontrado: {paths['indice_por_percurso']}"
        )

    tree = load_json(paths["tree"])
    ensure_tree_minimally_usable(tree, args)

    indice_por_percurso = load_json(paths["indice_por_percurso"])
    indice_por_percurso = require_dict(indice_por_percurso, "indice_por_percurso")
    percursos_source = require_dict(
        require_key(indice_por_percurso, "percursos", "indice_por_percurso"),
        "indice_por_percurso.percursos",
    )

    meta_ref_loaded = load_optional_json(paths["meta_referencia"])
    meta_ref_data = require_dict(meta_ref_loaded, "meta_referencia_do_percurso") if meta_ref_loaded is not None else None

    indice_secundario_loaded = load_optional_json(paths["indice_de_percursos"])
    indice_secundario_data = require_dict(indice_secundario_loaded, "indice_de_percursos") if indice_secundario_loaded is not None else None

    fragment_map, microlinha_map, ramo_map, existing_percurso_map = collect_maps(tree)

    ramos_ordenados = sort_ramos_by_order(
        list(ramo_map.values()),
        microlinha_map=microlinha_map,
        fragment_map=fragment_map,
    )
    total_ramos_lidos = len(ramos_ordenados)

    if args.limite is not None:
        ramos_processados = ramos_ordenados[:args.limite]
    else:
        ramos_processados = ramos_ordenados

    imported_percursos: List[Dict[str, Any]] = []
    percurso_profiles: Dict[str, Dict[str, Any]] = {}

    for percurso_id in sorted(percursos_source.keys()):
        indice_item = require_dict(percursos_source[percurso_id], f"indice_por_percurso.percursos[{percurso_id}]")
        percurso_summary = build_percurso_summary(
            percurso_id=percurso_id,
            indice_item=indice_item,
            existing_percurso_map=existing_percurso_map,
            meta_ref_data=meta_ref_data,
            indice_de_percursos_data=indice_secundario_data,
        )
        imported_percursos.append(percurso_summary)
        percurso_profiles[percurso_id] = base_profile_for_percurso(
            percurso_id=percurso_id,
            percurso_summary=percurso_summary,
            indice_item=indice_item,
        )

    association_logs: List[str] = []
    ramo_to_percurso_ids: Dict[str, List[str]] = {}
    total_associacoes = 0
    total_ramos_associados = 0

    for ramo in ramos_processados:
        ramo_id = str(ramo.get("id", ""))
        ramo_profile = infer_ramo_profile(
            ramo=ramo,
            microlinha_map=microlinha_map,
            fragment_map=fragment_map,
        )
        selected_ids, details = select_percurso_ids_for_ramo(
            ramo_profile=ramo_profile,
            percurso_profiles=percurso_profiles,
        )
        ramo_to_percurso_ids[ramo_id] = selected_ids

        if selected_ids:
            total_ramos_associados += 1
            total_associacoes += len(selected_ids)
            for percurso_id in selected_ids:
                detail = details[percurso_id]
                reasons = "; ".join(detail["reasons"]) if detail["reasons"] else "sem detalhe"
                association_logs.append(
                    f"{ramo_id} -> {percurso_id} | score={detail['score']} | {reasons}"
                )
        else:
            association_logs.append(f"{ramo_id} -> sem associação suficiente")

    update_tree_with_percursos(
        tree=tree,
        imported_percursos=imported_percursos,
        ramo_to_percurso_ids=ramo_to_percurso_ids,
        microlinha_map=microlinha_map,
        fragment_map=fragment_map,
        args=args,
    )

    save_json_atomic(paths["tree"], tree)

    total_percursos_importados = len(imported_percursos)
    total_ramos_sem_percurso = len(ramos_processados) - total_ramos_associados
    total_percursos_vazios = sum(1 for p in imported_percursos if not safe_list_of_strings(p.get("ramo_ids", [])))

    report_text = build_report_text(
        tree_path=paths["tree"],
        indice_path=paths["indice_por_percurso"],
        meta_path=paths["meta_referencia"],
        indice_secundario_path=paths["indice_de_percursos"],
        conteudo_path=paths["conteudo_completo"],
        total_percursos_importados=total_percursos_importados,
        total_ramos_lidos=total_ramos_lidos,
        total_ramos_processados=len(ramos_processados),
        total_ramos_associados=total_ramos_associados,
        total_ramos_sem_percurso=total_ramos_sem_percurso,
        total_associacoes=total_associacoes,
        total_percursos_vazios=total_percursos_vazios,
        args=args,
        association_logs=association_logs,
    )
    write_text(paths["report"], report_text)

    print(
        build_terminal_summary(
            total_percursos_importados=total_percursos_importados,
            total_ramos_lidos=total_ramos_lidos,
            total_ramos_associados=total_ramos_associados,
            total_ramos_sem_percurso=total_ramos_sem_percurso,
            total_percursos_vazios=total_percursos_vazios,
            report_path=paths["report"],
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PercursoGenerationError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)