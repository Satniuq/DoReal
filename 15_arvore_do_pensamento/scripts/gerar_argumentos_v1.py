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
INPUT_ARGUMENTOS_FILENAME = "argumentos_unificados.json"
REPORT_FILENAME = "relatorio_geracao_argumentos_v1.txt"

MAX_ASSOCIACOES_POR_RAMO = 3
LIMIAR_ASSOCIACAO = 3
LIMIAR_ASSOCIACAO_FORTE = 4


class ArgumentoGenerationError(RuntimeError):
    """Erro fatal na geração de argumentos."""


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera e associa argumentos na árvore do pensamento v1."
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
        help="Permite substituir o bloco 'argumentos[]' caso já exista conteúdo.",
    )
    args = parser.parse_args(argv)

    if args.limite is not None and args.limite <= 0:
        raise SystemExit("ERRO: --limite tem de ser um inteiro positivo.")

    return args


def build_paths(script_dir: Path) -> Dict[str, Path]:
    arvore_root = script_dir.parent
    project_root = arvore_root.parent

    return {
        "script_dir": script_dir,
        "arvore_root": arvore_root,
        "project_root": project_root,
        "tree": arvore_root / "01_dados" / INPUT_TREE_FILENAME,
        "report": arvore_root / "01_dados" / REPORT_FILENAME,
        "argumentos_unificados": (
            project_root
            / "13_Meta_Indice"
            / "indice"
            / "argumentos"
            / INPUT_ARGUMENTOS_FILENAME
        ),
    }


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise ArgumentoGenerationError(f"Ficheiro não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArgumentoGenerationError(f"JSON inválido em {path}: {exc}") from exc
    except OSError as exc:
        raise ArgumentoGenerationError(f"Não foi possível ler {path}: {exc}") from exc


def save_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        temp_path.replace(path)
    except OSError as exc:
        raise ArgumentoGenerationError(f"Não foi possível escrever {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as exc:
        raise ArgumentoGenerationError(f"Não foi possível escrever o relatório {path}: {exc}") from exc


def require_dict(value: Any, context: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ArgumentoGenerationError(
            f"Tipo inválido em {context}: esperado object/dict, obtido {type(value).__name__}."
        )
    return value


def require_list(value: Any, context: str) -> List[Any]:
    if not isinstance(value, list):
        raise ArgumentoGenerationError(
            f"Tipo inválido em {context}: esperado array/list, obtido {type(value).__name__}."
        )
    return value


def require_key(mapping: Dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ArgumentoGenerationError(f"Falta a chave obrigatória '{key}' em {context}.")
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


def safe_list_of_strings(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    result: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


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


def ensure_tree_minimally_usable(tree: Dict[str, Any], args: argparse.Namespace) -> None:
    if not isinstance(tree, dict):
        raise ArgumentoGenerationError("O ficheiro da árvore tem de ser um objeto JSON no topo.")

    for key in ("fragmentos", "microlinhas", "ramos", "percursos", "argumentos", "validacao"):
        if key not in tree:
            raise ArgumentoGenerationError(f"Falta o bloco obrigatório '{key}' na árvore.")

    fragmentos = require_list(tree.get("fragmentos"), "fragmentos")
    microlinhas = require_list(tree.get("microlinhas"), "microlinhas")
    ramos = require_list(tree.get("ramos"), "ramos")
    percursos = require_list(tree.get("percursos"), "percursos")
    argumentos = require_list(tree.get("argumentos"), "argumentos")

    if not fragmentos:
        raise ArgumentoGenerationError("O bloco 'fragmentos' está vazio.")
    if not microlinhas:
        raise ArgumentoGenerationError("O bloco 'microlinhas' está vazio.")
    if not ramos:
        raise ArgumentoGenerationError("O bloco 'ramos' está vazio.")
    if not percursos:
        raise ArgumentoGenerationError("O bloco 'percursos' está vazio. Gere primeiro os percursos.")

    if argumentos and not args.forcar:
        raise ArgumentoGenerationError(
            "O bloco 'argumentos' já contém dados. Use --forcar para regenerar e substituir."
        )

    validacao = require_dict(tree.get("validacao"), "validacao")
    require_dict(require_key(validacao, "metricas", "validacao"), "validacao.metricas")


def collect_maps(
    tree: Dict[str, Any]
) -> Tuple[
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
]:
    fragment_map: Dict[str, Dict[str, Any]] = {}
    for idx, fragment in enumerate(require_list(tree["fragmentos"], "fragmentos"), start=1):
        fragment_dict = require_dict(fragment, f"fragmentos[{idx}]")
        fragment_id = require_key(fragment_dict, "id", f"fragmentos[{idx}]")
        if not isinstance(fragment_id, str) or not fragment_id.strip():
            raise ArgumentoGenerationError(f"fragmentos[{idx}].id é inválido.")
        fragment_map[fragment_id] = fragment_dict

    microlinha_map: Dict[str, Dict[str, Any]] = {}
    for idx, microlinha in enumerate(require_list(tree["microlinhas"], "microlinhas"), start=1):
        microlinha_dict = require_dict(microlinha, f"microlinhas[{idx}]")
        microlinha_id = require_key(microlinha_dict, "id", f"microlinhas[{idx}]")
        if not isinstance(microlinha_id, str) or not microlinha_id.strip():
            raise ArgumentoGenerationError(f"microlinhas[{idx}].id é inválido.")
        microlinha_map[microlinha_id] = microlinha_dict

    ramo_map: Dict[str, Dict[str, Any]] = {}
    for idx, ramo in enumerate(require_list(tree["ramos"], "ramos"), start=1):
        ramo_dict = require_dict(ramo, f"ramos[{idx}]")
        ramo_id = require_key(ramo_dict, "id", f"ramos[{idx}]")
        if not isinstance(ramo_id, str) or not ramo_id.strip():
            raise ArgumentoGenerationError(f"ramos[{idx}].id é inválido.")
        ramo_map[ramo_id] = ramo_dict

    percurso_map: Dict[str, Dict[str, Any]] = {}
    for idx, percurso in enumerate(require_list(tree["percursos"], "percursos"), start=1):
        percurso_dict = require_dict(percurso, f"percursos[{idx}]")
        percurso_id = require_key(percurso_dict, "id", f"percursos[{idx}]")
        if not isinstance(percurso_id, str) or not percurso_id.strip():
            raise ArgumentoGenerationError(f"percursos[{idx}].id é inválido.")
        percurso_map[percurso_id] = percurso_dict

    existing_argumento_map: Dict[str, Dict[str, Any]] = {}
    for idx, argumento in enumerate(require_list(tree["argumentos"], "argumentos"), start=1):
        argumento_dict = require_dict(argumento, f"argumentos[{idx}]")
        argumento_id = argumento_dict.get("id")
        if isinstance(argumento_id, str) and argumento_id.strip():
            existing_argumento_map[argumento_id] = argumento_dict

    return fragment_map, microlinha_map, ramo_map, percurso_map, existing_argumento_map


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


def deduplicate_argumentos(argumentos_raw: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    dedup: Dict[str, Dict[str, Any]] = {}

    for idx, item in enumerate(argumentos_raw, start=1):
        argumento = require_dict(item, f"argumentos_unificados[{idx}]")
        argumento_id = require_key(argumento, "id", f"argumentos_unificados[{idx}]")
        if not isinstance(argumento_id, str) or not argumento_id.strip():
            raise ArgumentoGenerationError(f"argumentos_unificados[{idx}].id é inválido.")
        argumento_id = argumento_id.strip()

        origem = argumento.get("_ficheiro_origem")
        origem_list = [origem.strip()] if isinstance(origem, str) and origem.strip() else []

        if argumento_id not in dedup:
            merged = dict(argumento)
            merged["fontes_argumento"] = origem_list
            dedup[argumento_id] = merged
            continue

        current = dedup[argumento_id]
        current["fontes_argumento"] = merge_unique(
            safe_list_of_strings(current.get("fontes_argumento", [])),
            origem_list,
        )

        for key, value in argumento.items():
            if key == "_ficheiro_origem":
                continue

            existing_value = current.get(key)

            if existing_value is None:
                current[key] = value
                continue

            if isinstance(existing_value, list) and isinstance(value, list):
                merged_list = []
                for item_value in existing_value + value:
                    if item_value not in merged_list:
                        merged_list.append(item_value)
                current[key] = merged_list
                continue

            if isinstance(existing_value, dict) and isinstance(value, dict):
                merged_dict = dict(existing_value)
                for subkey, subvalue in value.items():
                    if subkey not in merged_dict:
                        merged_dict[subkey] = subvalue
                    else:
                        if isinstance(merged_dict[subkey], list) and isinstance(subvalue, list):
                            merged_dict[subkey] = merge_unique(
                                safe_list_of_strings(merged_dict[subkey]),
                                safe_list_of_strings(subvalue),
                            )
                current[key] = merged_dict
                continue

    return dedup


def build_argumento_summary(
    argumento_id: str,
    source: Dict[str, Any],
    existing_argumento_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    existing = existing_argumento_map.get(argumento_id, {})

    fundamenta = source.get("fundamenta")
    if not isinstance(fundamenta, dict):
        fundamenta = {}

    ligacoes_narrativas = source.get("ligacoes_narrativas")
    if not isinstance(ligacoes_narrativas, dict):
        ligacoes_narrativas = {}

    estrutura_logica = source.get("estrutura_logica")
    if not isinstance(estrutura_logica, dict):
        estrutura_logica = {}

    reducao_ao_absurdo = source.get("reducao_ao_absurdo")
    if not isinstance(reducao_ao_absurdo, dict):
        reducao_ao_absurdo = {}

    previous_convergencias = safe_list_of_strings(existing.get("convergencia_ids", []))

    return {
        "id": argumento_id,
        "tipo_no": "argumento",
        "fontes_argumento": safe_list_of_strings(source.get("fontes_argumento", [])),
        "capitulo": source.get("capitulo", "") if isinstance(source.get("capitulo"), str) else "",
        "parte": source.get("parte", "") if isinstance(source.get("parte"), str) else "",
        "nivel": source.get("nivel", "") if isinstance(source.get("nivel"), (int, str)) else "",
        "conceito_alvo": source.get("conceito_alvo", "") if isinstance(source.get("conceito_alvo"), str) else "",
        "criterio_ultimo": source.get("criterio_ultimo", "") if isinstance(source.get("criterio_ultimo"), str) else "",
        "natureza": source.get("natureza", "") if isinstance(source.get("natureza"), str) else "",
        "tipo_de_necessidade": source.get("tipo_de_necessidade", "") if isinstance(source.get("tipo_de_necessidade"), str) else "",
        "nivel_de_operacao": source.get("nivel_de_operacao", "") if isinstance(source.get("nivel_de_operacao"), str) else "",
        "fundamenta": {
            "regimes": safe_list_of_strings(fundamenta.get("regimes", [])),
            "percursos": safe_list_of_strings(fundamenta.get("percursos", [])),
            "modulos": safe_list_of_strings(fundamenta.get("modulos", [])),
        },
        "pressupostos_ontologicos": safe_list_of_strings(source.get("pressupostos_ontologicos", [])),
        "outputs_instalados": safe_list_of_strings(source.get("outputs_instalados", [])),
        "operacoes_chave": safe_list_of_strings(source.get("operacoes_chave", [])),
        "estrutura_logica": estrutura_logica,
        "reducao_ao_absurdo": reducao_ao_absurdo,
        "ligacoes_narrativas": {
            "depende_de_argumentos": safe_list_of_strings(ligacoes_narrativas.get("depende_de_argumentos", [])),
            "prepara_argumentos": safe_list_of_strings(ligacoes_narrativas.get("prepara_argumentos", [])),
            "back_links": safe_list_of_strings(ligacoes_narrativas.get("back_links", [])),
            "forward_links": safe_list_of_strings(ligacoes_narrativas.get("forward_links", [])),
        },
        "observacoes": safe_list_of_strings(source.get("observacoes", [])),
        "ramo_ids": [],
        "convergencia_ids": previous_convergencias,
        "estado_validacao": "valido",
    }


def infer_argumento_profile(argumento: Dict[str, Any]) -> Dict[str, Any]:
    tokens: Set[str] = set()

    capitulo = argumento.get("capitulo")
    parte = argumento.get("parte")
    conceito_alvo = argumento.get("conceito_alvo")
    criterio_ultimo = argumento.get("criterio_ultimo")
    natureza = argumento.get("natureza")
    tipo_de_necessidade = argumento.get("tipo_de_necessidade")
    nivel_de_operacao = argumento.get("nivel_de_operacao")
    nivel = argumento.get("nivel")

    for value in (
        argumento.get("id"),
        capitulo,
        parte,
        conceito_alvo,
        criterio_ultimo,
        natureza,
        tipo_de_necessidade,
        nivel_de_operacao,
        str(nivel) if nivel != "" else "",
    ):
        tokens.update(tokenize_text(value))

    for value in safe_list_of_strings(argumento.get("pressupostos_ontologicos", [])):
        tokens.update(tokenize_text(value))
    for value in safe_list_of_strings(argumento.get("outputs_instalados", [])):
        tokens.update(tokenize_text(value))
    for value in safe_list_of_strings(argumento.get("operacoes_chave", [])):
        tokens.update(tokenize_text(value))
    for value in safe_list_of_strings(argumento.get("observacoes", [])):
        tokens.update(tokenize_text(value))

    fundamenta = argumento.get("fundamenta")
    if not isinstance(fundamenta, dict):
        fundamenta = {}

    percursos_fundamenta = safe_list_of_strings(fundamenta.get("percursos", []))
    regimes = safe_list_of_strings(fundamenta.get("regimes", []))
    modulos = safe_list_of_strings(fundamenta.get("modulos", []))

    for value in percursos_fundamenta + regimes + modulos:
        tokens.update(tokenize_text(value))

    ligacoes = argumento.get("ligacoes_narrativas")
    if isinstance(ligacoes, dict):
        for key in ("depende_de_argumentos", "prepara_argumentos", "back_links", "forward_links"):
            for value in safe_list_of_strings(ligacoes.get(key, [])):
                tokens.update(tokenize_text(value))

    chapter_num = parse_cap_number(capitulo) if isinstance(capitulo, str) else None

    return {
        "argumento_id": argumento["id"],
        "chapter_num": chapter_num,
        "percursos_fundamenta": percursos_fundamenta,
        "tokens": tokens,
        "conceito_alvo": conceito_alvo if isinstance(conceito_alvo, str) else "",
        "tipo_de_necessidade": tipo_de_necessidade if isinstance(tipo_de_necessidade, str) else "",
        "nivel_de_operacao": nivel_de_operacao if isinstance(nivel_de_operacao, str) else "",
        "natureza": natureza if isinstance(natureza, str) else "",
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
    has_exception = False

    tokens.update(tokenize_text(ramo.get("titulo")))
    tokens.update(tokenize_text(ramo.get("descricao_funcional")))
    tokens.update(tokenize_text(ramo.get("criterio_de_unidade")))

    for percurso_id in safe_list_of_strings(ramo.get("percurso_ids_associados", [])):
        tokens.update(tokenize_text(percurso_id))

    ramo_steps = ramo.get("passo_ids_alvo")
    if isinstance(ramo_steps, list):
        for step_id in ramo_steps:
            if isinstance(step_id, str) and step_id.strip():
                step_id = step_id.strip()
                step_ids.append(step_id)
                n = parse_prefixed_number(step_id, "P")
                if n is not None:
                    step_nums.append(n)

    estado_excecao = ramo.get("estado_excecao")
    if isinstance(estado_excecao, str) and estado_excecao in {"ativa_tolerada", "ativa_prioritaria"}:
        has_exception = True

    for microlinha_id in microlinha_ids:
        microlinha = microlinha_map.get(microlinha_id)
        if not isinstance(microlinha, dict):
            continue

        tokens.update(tokenize_text(microlinha.get("titulo")))
        tokens.update(tokenize_text(microlinha.get("descricao_funcional")))

        criterio = microlinha.get("criterio_de_agregacao")
        if isinstance(criterio, dict):
            problema = criterio.get("problema_filosofico_dominante")
            direcao = criterio.get("direcao_movimento_dominante")
            utilidade = criterio.get("tipo_de_utilidade_dominante")
            base = criterio.get("base_dominante")

            if isinstance(problema, str) and problema.strip():
                problem_values.append(problema.strip())
                tokens.update(tokenize_text(problema))
            if isinstance(direcao, str) and direcao.strip():
                direction_values.append(direcao.strip())
                tokens.update(tokenize_text(direcao))
            if isinstance(utilidade, str) and utilidade.strip():
                utility_values.append(utilidade.strip())
                tokens.update(tokenize_text(utilidade))
            if isinstance(base, str) and base.strip():
                tokens.update(tokenize_text(base))

        microlinha_estado_exc = microlinha.get("estado_excecao")
        if isinstance(microlinha_estado_exc, str) and microlinha_estado_exc in {"ativa_tolerada", "ativa_prioritaria"}:
            has_exception = True

        fragment_ids = microlinha.get("fragmento_ids")
        if not isinstance(fragment_ids, list):
            continue

        for fragment_id in fragment_ids:
            if not isinstance(fragment_id, str) or not fragment_id.strip():
                continue
            fragment = fragment_map.get(fragment_id)
            if not isinstance(fragment, dict):
                continue

            cadencia = fragment.get("cadencia")
            if isinstance(cadencia, dict):
                zona = cadencia.get("zona_provavel_percurso")
                direcao = cadencia.get("direcao_movimento")
                funcao = cadencia.get("funcao_cadencia_principal")

                if isinstance(zona, str) and zona.strip():
                    zone_values.append(zona.strip())
                    tokens.update(tokenize_text(zona))
                if isinstance(direcao, str) and direcao.strip():
                    direction_values.append(direcao.strip())
                    tokens.update(tokenize_text(direcao))
                if isinstance(funcao, str) and funcao.strip():
                    tokens.update(tokenize_text(funcao))

            tratamento = fragment.get("tratamento_filosofico")
            if isinstance(tratamento, dict):
                problema = tratamento.get("problema_filosofico_central")
                trabalho = tratamento.get("trabalho_no_sistema")
                if isinstance(problema, str) and problema.strip():
                    problem_values.append(problema.strip())
                    tokens.update(tokenize_text(problema))
                if isinstance(trabalho, str) and trabalho.strip():
                    work_values.append(trabalho.strip())
                    tokens.update(tokenize_text(trabalho))

            impacto = fragment.get("impacto_mapa")
            if isinstance(impacto, dict):
                utilidade = impacto.get("tipo_de_utilidade_principal")
                efeito = impacto.get("efeito_principal_no_mapa")
                if isinstance(utilidade, str) and utilidade.strip():
                    utility_values.append(utilidade.strip())
                    tokens.update(tokenize_text(utilidade))
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

    return {
        "ramo_id": ramo_id,
        "step_ids": sorted(set(step_ids), key=lambda x: (parse_prefixed_number(x, "P") or 10**9, x)),
        "step_nums": sorted(set(step_nums)),
        "percurso_ids": safe_list_of_strings(ramo.get("percurso_ids_associados", [])),
        "dominant_zone": mode_preserve_order(zone_values),
        "dominant_problem": mode_preserve_order(problem_values),
        "dominant_direction": mode_preserve_order(direction_values),
        "dominant_utility": mode_preserve_order(utility_values),
        "dominant_effect": mode_preserve_order(effect_values),
        "dominant_work": mode_preserve_order(work_values),
        "tokens": tokens,
        "has_exception": has_exception,
    }


def score_ramo_against_argumento(
    ramo_profile: Dict[str, Any],
    argumento_profile: Dict[str, Any],
) -> Tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []

    ramo_step_nums: List[int] = list(ramo_profile["step_nums"])
    chapter_num = argumento_profile["chapter_num"]

    if ramo_step_nums and chapter_num is not None:
        if chapter_num in ramo_step_nums:
            score += 2
            reasons.append(f"passo-alvo fortemente compatível com {chapter_num}")
        else:
            min_gap = min(abs(step_num - chapter_num) for step_num in ramo_step_nums)
            if min_gap <= 1:
                score += 1
                reasons.append("passo-alvo adjacente ao capítulo do argumento")

    ramo_percursos = set(ramo_profile["percurso_ids"])
    argumento_percursos = set(argumento_profile["percursos_fundamenta"])
    if ramo_percursos and argumento_percursos:
        overlap = sorted(ramo_percursos.intersection(argumento_percursos))
        if overlap:
            score += 1
            reasons.append(f"percurso compatível ({', '.join(overlap[:2])})")

    ramo_tokens = set(ramo_profile["tokens"])
    argumento_tokens = set(argumento_profile["tokens"])

    problem_work_tokens = set()
    for value in (
        ramo_profile.get("dominant_problem"),
        ramo_profile.get("dominant_work"),
        ramo_profile.get("dominant_zone"),
        ramo_profile.get("dominant_utility"),
        ramo_profile.get("dominant_effect"),
    ):
        problem_work_tokens.update(tokenize_text(value if isinstance(value, str) else ""))

    if problem_work_tokens.intersection(argumento_tokens):
        score += 1
        reasons.append("problema/trabalho dominante compatível")

    concept_tokens = set()
    for value in (
        argumento_profile.get("conceito_alvo"),
        argumento_profile.get("tipo_de_necessidade"),
        argumento_profile.get("nivel_de_operacao"),
        argumento_profile.get("natureza"),
    ):
        concept_tokens.update(tokenize_text(value if isinstance(value, str) else ""))

    if concept_tokens.intersection(ramo_tokens):
        score += 1
        reasons.append("conceito-alvo/operação compatível")

    generic_overlap = ramo_tokens.intersection(argumento_tokens)
    if generic_overlap:
        score += 1
        reasons.append(f"evidência textual acumulada ({', '.join(sorted(list(generic_overlap))[:4])})")

    if ramo_profile.get("has_exception") and score < LIMIAR_ASSOCIACAO_FORTE:
        score -= 1
        reasons.append("parcimónia aplicada por exceção ativa no ramo")

    return max(score, 0), reasons


def select_argumento_ids_for_ramo(
    ramo_profile: Dict[str, Any],
    argumento_profiles: Dict[str, Dict[str, Any]],
) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
    scored: List[Tuple[str, int, List[str]]] = []

    for argumento_id, profile in argumento_profiles.items():
        score, reasons = score_ramo_against_argumento(ramo_profile, profile)
        if score >= LIMIAR_ASSOCIACAO:
            scored.append((argumento_id, score, reasons))

    scored.sort(key=lambda item: (-item[1], item[0]))

    if not scored:
        return [], {}

    selected: List[Tuple[str, int, List[str]]] = []
    top_score = scored[0][1]

    for argumento_id, score, reasons in scored:
        if len(selected) >= MAX_ASSOCIACOES_POR_RAMO:
            break
        if score < LIMIAR_ASSOCIACAO:
            continue
        if not selected:
            selected.append((argumento_id, score, reasons))
            continue
        if score >= LIMIAR_ASSOCIACAO_FORTE and score >= top_score - 1:
            selected.append((argumento_id, score, reasons))

    selected_ids = [item[0] for item in selected]
    details = {
        argumento_id: {"score": score, "reasons": reasons}
        for argumento_id, score, reasons in selected
    }
    return selected_ids, details


def clear_argumento_links(tree: Dict[str, Any]) -> None:
    for ramo in require_list(tree.get("ramos"), "ramos"):
        ramo_dict = require_dict(ramo, "ramo")
        ramo_dict["argumento_ids_associados"] = []

    for microlinha in require_list(tree.get("microlinhas"), "microlinhas"):
        microlinha_dict = require_dict(microlinha, "microlinha")
        microlinha_dict["argumento_ids_sugeridos"] = []

    for fragment in require_list(tree.get("fragmentos"), "fragmentos"):
        fragment_dict = require_dict(fragment, "fragmento")
        ligacoes = require_dict(
            require_key(fragment_dict, "ligacoes_arvore", f"fragmento {fragment_dict.get('id', '?')}"),
            f"fragmento {fragment_dict.get('id', '?')}.ligacoes_arvore",
        )
        ligacoes["argumento_ids"] = []


def update_tree_with_argumentos(
    tree: Dict[str, Any],
    imported_argumentos: List[Dict[str, Any]],
    ramo_to_argumento_ids: Dict[str, List[str]],
    microlinha_map: Dict[str, Dict[str, Any]],
    fragment_map: Dict[str, Dict[str, Any]],
    args: argparse.Namespace,
) -> None:
    if args.forcar:
        clear_argumento_links(tree)

    argumento_map = {a["id"]: a for a in imported_argumentos}
    for argumento in imported_argumentos:
        argumento["ramo_ids"] = []

    ramo_map_in_tree: Dict[str, Dict[str, Any]] = {}
    for ramo in require_list(tree.get("ramos"), "ramos"):
        ramo_dict = require_dict(ramo, "ramo")
        ramo_id = ramo_dict.get("id")
        if isinstance(ramo_id, str):
            ramo_map_in_tree[ramo_id] = ramo_dict

    for ramo_id, argumento_ids in ramo_to_argumento_ids.items():
        ramo_dict = ramo_map_in_tree.get(ramo_id)
        if ramo_dict is None:
            continue

        existing = safe_list_of_strings(ramo_dict.get("argumento_ids_associados", []))
        ramo_dict["argumento_ids_associados"] = merge_unique(existing, argumento_ids)

        for argumento_id in argumento_ids:
            argumento = argumento_map.get(argumento_id)
            if argumento is not None:
                argumento["ramo_ids"] = merge_unique(
                    safe_list_of_strings(argumento.get("ramo_ids", [])),
                    [ramo_id],
                )

    for ramo in require_list(tree.get("ramos"), "ramos"):
        ramo_dict = require_dict(ramo, "ramo")
        argumento_ids = safe_list_of_strings(ramo_dict.get("argumento_ids_associados", []))
        microlinha_ids = ramo_dict.get("microlinha_ids")
        if not isinstance(microlinha_ids, list):
            continue

        for microlinha_id in microlinha_ids:
            microlinha = microlinha_map.get(microlinha_id)
            if not isinstance(microlinha, dict):
                continue

            existing = safe_list_of_strings(microlinha.get("argumento_ids_sugeridos", []))
            microlinha["argumento_ids_sugeridos"] = merge_unique(existing, argumento_ids)

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
                existing_frag = safe_list_of_strings(ligacoes.get("argumento_ids", []))
                ligacoes["argumento_ids"] = merge_unique(existing_frag, argumento_ids)

    for argumento in imported_argumentos:
        ramo_ids = safe_list_of_strings(argumento.get("ramo_ids", []))
        if not ramo_ids:
            argumento["estado_validacao"] = "valido_com_avisos"
            continue

        has_exception = False
        for ramo_id in ramo_ids:
            ramo_dict = ramo_map_in_tree.get(ramo_id)
            if isinstance(ramo_dict, dict):
                estado_excecao = ramo_dict.get("estado_excecao")
                if isinstance(estado_excecao, str) and estado_excecao in {"ativa_tolerada", "ativa_prioritaria"}:
                    has_exception = True
                    break

        argumento["estado_validacao"] = "valido_com_avisos" if has_exception else "valido"

    tree["argumentos"] = imported_argumentos

    validacao = require_dict(require_key(tree, "validacao", "raiz"), "validacao")
    metricas = require_dict(require_key(validacao, "metricas", "validacao"), "validacao.metricas")
    metricas["total_argumentos"] = len(imported_argumentos)

    observacoes = validacao.get("observacoes")
    if observacoes is None:
        observacoes = []
        validacao["observacoes"] = observacoes
    elif not isinstance(observacoes, list):
        raise ArgumentoGenerationError("O campo 'validacao.observacoes' existe mas não é array/list.")

    prefixos_controlados = (
        "Argumentos v1:",
        "Geração de argumentos v1:",
    )
    validacao["observacoes"] = [
        item for item in observacoes
        if not (isinstance(item, str) and item.startswith(prefixos_controlados))
    ]
    observacoes = validacao["observacoes"]

    total_ramos = len(require_list(tree.get("ramos"), "ramos"))
    ramos_sem_argumento = 0
    for ramo in require_list(tree.get("ramos"), "ramos"):
        ramo_dict = require_dict(ramo, "ramo")
        if not safe_list_of_strings(ramo_dict.get("argumento_ids_associados", [])):
            ramos_sem_argumento += 1

    argumentos_vazios = sum(1 for a in imported_argumentos if not safe_list_of_strings(a.get("ramo_ids", [])))

    if total_ramos > 0 and ramos_sem_argumento / total_ramos >= 0.35:
        observacoes.append(
            f"Argumentos v1: número relevante de ramos sem argumento associado ({ramos_sem_argumento}/{total_ramos})."
        )

    if imported_argumentos and argumentos_vazios / len(imported_argumentos) >= 0.40:
        observacoes.append(
            f"Argumentos v1: vários argumentos importados ficaram sem ramos associados ({argumentos_vazios}/{len(imported_argumentos)})."
        )


def build_report_text(
    tree_path: Path,
    argumentos_path: Path,
    total_argumentos_importados: int,
    total_ramos_lidos: int,
    total_ramos_processados: int,
    total_ramos_associados: int,
    total_ramos_sem_argumento: int,
    total_associacoes: int,
    total_argumentos_vazios: int,
    args: argparse.Namespace,
    association_logs: List[str],
) -> str:
    lines: List[str] = []
    lines.append("RELATÓRIO DE GERAÇÃO DE ARGUMENTOS V1")
    lines.append("=" * 72)
    lines.append(f"Data/hora UTC: {utc_now_iso()}")
    lines.append(f"Ficheiro atualizado: {tree_path}")
    lines.append(f"Fonte obrigatória usada: {argumentos_path}")
    lines.append("")
    lines.append("Critérios usados")
    lines.append("-" * 72)
    lines.append("1. Importação determinística dos argumentos de referência a partir de argumentos_unificados.json.")
    lines.append("2. Deduplicação obrigatória por id, com agregação de fontes em 'fontes_argumento'.")
    lines.append("3. Associação ramo→argumento por heurística explícita e auditável.")
    lines.append("4. Sinais considerados: passos-alvo, percurso do ramo, problema/trabalho dominante, conceito-alvo/operação e evidência textual acumulada.")
    lines.append("5. Pontuação mínima de associação: 3.")
    lines.append("6. Associação forte preferencial: 4 ou mais.")
    lines.append("7. Parcimónia: no máximo 3 argumentos por ramo, apenas quando a evidência adicional é forte e próxima do melhor candidato.")
    lines.append("")
    lines.append("Resumo")
    lines.append("-" * 72)
    lines.append(f"Argumentos importados: {total_argumentos_importados}")
    lines.append(f"Ramos lidos: {total_ramos_lidos}")
    lines.append(f"Ramos processados nesta execução: {total_ramos_processados}")
    lines.append(f"Ramos associados a pelo menos um argumento: {total_ramos_associados}")
    lines.append(f"Ramos sem argumento (entre os processados): {total_ramos_sem_argumento}")
    lines.append(f"Associações ramo→argumento geradas: {total_associacoes}")
    lines.append(f"Argumentos sem ramos associados: {total_argumentos_vazios}")
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
        f"Geração concluída com {total_argumentos_importados} argumentos importados, "
        f"{total_associacoes} associação(ões) e {total_argumentos_vazios} argumento(s) vazios."
    )
    lines.append("")
    return "\n".join(lines)


def build_terminal_summary(
    total_argumentos_importados: int,
    total_ramos_lidos: int,
    total_ramos_associados: int,
    total_ramos_sem_argumento: int,
    total_argumentos_vazios: int,
    report_path: Path,
) -> str:
    lines = [
        f"Argumentos importados: {total_argumentos_importados}",
        f"Ramos lidos: {total_ramos_lidos}",
        f"Ramos associados a pelo menos um argumento: {total_ramos_associados}",
        f"Ramos sem argumento: {total_ramos_sem_argumento}",
        f"Argumentos sem ramos associados: {total_argumentos_vazios}",
        "Conclusão final: geração concluída.",
        f"Relatório escrito em: {report_path}",
    ]
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    script_dir = Path(__file__).resolve().parent
    paths = build_paths(script_dir)

    if not paths["argumentos_unificados"].exists():
        raise ArgumentoGenerationError(
            f"Ficheiro obrigatório não encontrado: {paths['argumentos_unificados']}"
        )

    tree = load_json(paths["tree"])
    ensure_tree_minimally_usable(tree, args)

    argumentos_raw = load_json(paths["argumentos_unificados"])
    argumentos_raw = require_list(argumentos_raw, "argumentos_unificados")

    fragment_map, microlinha_map, ramo_map, _percurso_map, existing_argumento_map = collect_maps(tree)

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

    argumentos_dedup = deduplicate_argumentos(argumentos_raw)

    imported_argumentos: List[Dict[str, Any]] = []
    argumento_profiles: Dict[str, Dict[str, Any]] = {}

    for argumento_id in sorted(argumentos_dedup.keys()):
        source = argumentos_dedup[argumento_id]
        argumento_summary = build_argumento_summary(
            argumento_id=argumento_id,
            source=source,
            existing_argumento_map=existing_argumento_map,
        )
        imported_argumentos.append(argumento_summary)
        argumento_profiles[argumento_id] = infer_argumento_profile(argumento_summary)

    association_logs: List[str] = []
    ramo_to_argumento_ids: Dict[str, List[str]] = {}
    total_associacoes = 0
    total_ramos_associados = 0

    for ramo in ramos_processados:
        ramo_id = str(ramo.get("id", ""))
        ramo_profile = infer_ramo_profile(
            ramo=ramo,
            microlinha_map=microlinha_map,
            fragment_map=fragment_map,
        )
        selected_ids, details = select_argumento_ids_for_ramo(
            ramo_profile=ramo_profile,
            argumento_profiles=argumento_profiles,
        )
        ramo_to_argumento_ids[ramo_id] = selected_ids

        if selected_ids:
            total_ramos_associados += 1
            total_associacoes += len(selected_ids)
            for argumento_id in selected_ids:
                detail = details[argumento_id]
                reasons = "; ".join(detail["reasons"]) if detail["reasons"] else "sem detalhe"
                association_logs.append(
                    f"{ramo_id} -> {argumento_id} | score={detail['score']} | {reasons}"
                )
        else:
            association_logs.append(f"{ramo_id} -> sem associação suficiente")

    update_tree_with_argumentos(
        tree=tree,
        imported_argumentos=imported_argumentos,
        ramo_to_argumento_ids=ramo_to_argumento_ids,
        microlinha_map=microlinha_map,
        fragment_map=fragment_map,
        args=args,
    )

    save_json_atomic(paths["tree"], tree)

    total_argumentos_importados = len(imported_argumentos)
    total_ramos_sem_argumento = len(ramos_processados) - total_ramos_associados
    total_argumentos_vazios = sum(1 for a in imported_argumentos if not safe_list_of_strings(a.get("ramo_ids", [])))

    report_text = build_report_text(
        tree_path=paths["tree"],
        argumentos_path=paths["argumentos_unificados"],
        total_argumentos_importados=total_argumentos_importados,
        total_ramos_lidos=total_ramos_lidos,
        total_ramos_processados=len(ramos_processados),
        total_ramos_associados=total_ramos_associados,
        total_ramos_sem_argumento=total_ramos_sem_argumento,
        total_associacoes=total_associacoes,
        total_argumentos_vazios=total_argumentos_vazios,
        args=args,
        association_logs=association_logs,
    )
    write_text(paths["report"], report_text)

    print(
        build_terminal_summary(
            total_argumentos_importados=total_argumentos_importados,
            total_ramos_lidos=total_ramos_lidos,
            total_ramos_associados=total_ramos_associados,
            total_ramos_sem_argumento=total_ramos_sem_argumento,
            total_argumentos_vazios=total_argumentos_vazios,
            report_path=paths["report"],
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ArgumentoGenerationError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)