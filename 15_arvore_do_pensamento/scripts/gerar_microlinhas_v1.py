# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
import re


INPUT_FILENAME = "arvore_do_pensamento_v1.json"
REPORT_FILENAME = "relatorio_geracao_microlinhas_v1.txt"

MAX_MICROLINHA_SIZE = 5
MAX_ORDER_GAP = 3


class MicrolinhaGenerationError(RuntimeError):
    """Erro fatal na geração de microlinhas."""


@dataclass(frozen=True)
class FragmentFeatures:
    fragment_id: str
    ordem: int
    zona: Optional[str]
    area: Optional[str]
    funcao: Optional[str]
    direcao: Optional[str]
    centralidade: Optional[str]
    estatuto: Optional[str]
    problema: Optional[str]
    trabalho: Optional[str]
    descricao: Optional[str]
    tipo_utilidade: Optional[str]
    efeito: Optional[str]
    prop_ids: Tuple[str, ...]
    prop_nums: Tuple[int, ...]
    estado_validacao: Optional[str]
    estado_excecao: Optional[str]
    excecao_ids: Tuple[str, ...]
    fragment_ref: Dict[str, Any]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera a camada de microlinhas da árvore do pensamento v1."
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help="Processa apenas os primeiros N fragmentos por ordem, para ensaio.",
    )
    parser.add_argument(
        "--forcar",
        action="store_true",
        help="Permite regenerar e substituir 'microlinhas[]' caso já exista conteúdo.",
    )
    args = parser.parse_args(argv)

    if args.limite is not None and args.limite <= 0:
        raise SystemExit("ERRO: --limite tem de ser um inteiro positivo.")

    return args


def build_paths(script_dir: Path) -> Dict[str, Path]:
    arvore_root = script_dir.parent
    return {
        "script_dir": script_dir,
        "arvore_root": arvore_root,
        "input": arvore_root / "01_dados" / INPUT_FILENAME,
        "report": arvore_root / "01_dados" / REPORT_FILENAME,
    }


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise MicrolinhaGenerationError(f"Ficheiro não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MicrolinhaGenerationError(f"JSON inválido em {path}: {exc}") from exc
    except OSError as exc:
        raise MicrolinhaGenerationError(f"Não foi possível ler {path}: {exc}") from exc


def save_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        temp_path.replace(path)
    except OSError as exc:
        raise MicrolinhaGenerationError(f"Não foi possível escrever {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as exc:
        raise MicrolinhaGenerationError(f"Não foi possível escrever o relatório {path}: {exc}") from exc


def require_key(mapping: Dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise MicrolinhaGenerationError(f"Falta a chave obrigatória '{key}' em {context}.")
    return mapping[key]


def require_dict(value: Any, context: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise MicrolinhaGenerationError(
            f"Tipo inválido em {context}: esperado object/dict, obtido {type(value).__name__}."
        )
    return value


def require_list(value: Any, context: str) -> List[Any]:
    if not isinstance(value, list):
        raise MicrolinhaGenerationError(
            f"Tipo inválido em {context}: esperado array/list, obtido {type(value).__name__}."
        )
    return value


def slug_human(text: Optional[str]) -> str:
    if not isinstance(text, str) or not text.strip():
        return "nao_determinado"
    return text.strip().replace("_", " ")


def parse_prop_number(prop_id: str) -> Optional[int]:
    match = re.fullmatch(r"P(\d+)", prop_id.strip()) if isinstance(prop_id, str) else None
    return int(match.group(1)) if match else None


def mode_preserve_order(values: Iterable[Optional[str]], ignore: Optional[Set[str]] = None) -> Optional[str]:
    ignore = ignore or set()
    filtered: List[str] = []
    for value in values:
        if isinstance(value, str):
            v = value.strip()
            if v and v not in ignore:
                filtered.append(v)

    if not filtered:
        return None

    counts = Counter(filtered)
    best_count = max(counts.values())
    best_values = {value for value, count in counts.items() if count == best_count}

    for value in filtered:
        if value in best_values:
            return value
    return None


def derive_area_from_zone(zona: Optional[str]) -> Optional[str]:
    mapping = {
        "ontologia": "ontologia",
        "estrutura_operacional_do_real": "ontologia",
        "campo_e_localizacao": "ontologia",
        "transicao_antropologica": "antropologia",
        "mediacao_simbolica": "mediacao",
        "epistemologia": "epistemologia",
        "escala_e_erro_de_escala": "epistemologia",
        "etica_e_narrativa": "etica",
        "vida_boa": "etica",
        "critica_sistemica_e_reintegracao": "critica",
        "percurso_do_erro_e_correcao": "critica",
        "metaestrutura_do_livro": "metaestrutura",
        "indefinida": None,
    }
    return mapping.get(zona) if isinstance(zona, str) else None


def extract_fragment_features(fragment: Dict[str, Any], index: int) -> FragmentFeatures:
    context = f"fragmentos[{index}]"

    fragment_id = require_key(fragment, "id", context)
    if not isinstance(fragment_id, str) or not fragment_id.strip():
        raise MicrolinhaGenerationError(f"{context}.id tem de ser uma string não vazia.")

    ordem = require_key(fragment, "ordem_no_ficheiro", context)
    if not isinstance(ordem, int):
        raise MicrolinhaGenerationError(f"{context}.ordem_no_ficheiro tem de ser inteiro.")

    cadencia = require_dict(require_key(fragment, "cadencia", context), f"{context}.cadencia")
    impacto = require_dict(require_key(fragment, "impacto_mapa", context), f"{context}.impacto_mapa")
    ligacoes = require_dict(require_key(fragment, "ligacoes_arvore", context), f"{context}.ligacoes_arvore")
    tratamento = fragment.get("tratamento_filosofico")

    # Verificação mínima necessária ao gerador.
    for key in (
        "funcao_cadencia_principal",
        "direcao_movimento",
        "centralidade",
        "estatuto_no_percurso",
        "zona_provavel_percurso",
    ):
        require_key(cadencia, key, f"{context}.cadencia")

    require_key(impacto, "tipo_de_utilidade_principal", f"{context}.impacto_mapa")
    require_key(impacto, "efeito_principal_no_mapa", f"{context}.impacto_mapa")
    prop_list = require_list(
        require_key(impacto, "proposicoes_do_mapa_tocadas", f"{context}.impacto_mapa"),
        f"{context}.impacto_mapa.proposicoes_do_mapa_tocadas",
    )

    if tratamento is not None:
        tratamento = require_dict(tratamento, f"{context}.tratamento_filosofico")

    # Garante que o campo existe para ser depois atualizado.
    if "microlinha_ids" not in ligacoes or not isinstance(ligacoes.get("microlinha_ids"), list):
        ligacoes["microlinha_ids"] = []

    zona = cadencia.get("zona_provavel_percurso")
    area = None
    if isinstance(impacto.get("zona_filosofica_dominante"), str) and impacto["zona_filosofica_dominante"].strip():
        area = impacto["zona_filosofica_dominante"].strip()
    elif isinstance(tratamento, dict):
        tipo_problema = tratamento.get("tipo_de_problema")
        if isinstance(tipo_problema, str) and tipo_problema.strip():
            area = tipo_problema.strip()
    if area is None:
        area = derive_area_from_zone(zona if isinstance(zona, str) else None)

    prop_ids: List[str] = []
    prop_nums: List[int] = []
    for pidx, item in enumerate(prop_list, start=1):
        item_context = f"{context}.impacto_mapa.proposicoes_do_mapa_tocadas[{pidx}]"
        item_dict = require_dict(item, item_context)
        prop_id = require_key(item_dict, "proposicao_id", item_context)
        if isinstance(prop_id, str) and prop_id.strip():
            prop_ids.append(prop_id.strip())
            prop_num = parse_prop_number(prop_id.strip())
            if prop_num is not None:
                prop_nums.append(prop_num)

    problema = None
    trabalho = None
    descricao = None
    if isinstance(tratamento, dict):
        problema = tratamento.get("problema_filosofico_central")
        trabalho = tratamento.get("trabalho_no_sistema")
        descricao = tratamento.get("descricao_funcional_curta")

    excecao_ids = fragment.get("excecao_ids", [])
    if not isinstance(excecao_ids, list):
        raise MicrolinhaGenerationError(f"{context}.excecao_ids tem de ser array/list.")

    return FragmentFeatures(
        fragment_id=fragment_id,
        ordem=ordem,
        zona=zona if isinstance(zona, str) else None,
        area=area,
        funcao=cadencia.get("funcao_cadencia_principal"),
        direcao=cadencia.get("direcao_movimento"),
        centralidade=cadencia.get("centralidade"),
        estatuto=cadencia.get("estatuto_no_percurso"),
        problema=problema if isinstance(problema, str) else None,
        trabalho=trabalho if isinstance(trabalho, str) else None,
        descricao=descricao if isinstance(descricao, str) else None,
        tipo_utilidade=impacto.get("tipo_de_utilidade_principal") if isinstance(impacto.get("tipo_de_utilidade_principal"), str) else None,
        efeito=impacto.get("efeito_principal_no_mapa") if isinstance(impacto.get("efeito_principal_no_mapa"), str) else None,
        prop_ids=tuple(prop_ids),
        prop_nums=tuple(sorted(set(prop_nums))),
        estado_validacao=fragment.get("estado_validacao") if isinstance(fragment.get("estado_validacao"), str) else None,
        estado_excecao=fragment.get("estado_excecao") if isinstance(fragment.get("estado_excecao"), str) else None,
        excecao_ids=tuple(str(x) for x in excecao_ids),
        fragment_ref=fragment,
    )


def sort_fragment_features(features: List[FragmentFeatures]) -> List[FragmentFeatures]:
    return sorted(features, key=lambda x: (x.ordem, x.fragment_id))


def allowed_function_pair(left: Optional[str], right: Optional[str]) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True

    allowed_pairs = {
        ("abertura_de_problema", "formulacao_inicial"),
        ("abertura_de_problema", "desenvolvimento"),
        ("formulacao_inicial", "desenvolvimento"),
        ("formulacao_inicial", "aprofundamento"),
        ("formulacao_inicial", "distincao_conceptual"),
        ("formulacao_inicial", "consequencia"),
        ("desenvolvimento", "desenvolvimento"),
        ("desenvolvimento", "aprofundamento"),
        ("desenvolvimento", "consequencia"),
        ("desenvolvimento", "distincao_conceptual"),
        ("distincao_conceptual", "desenvolvimento"),
        ("distincao_conceptual", "consequencia"),
        ("aprofundamento", "consequencia"),
        ("objecao", "resposta"),
        ("resposta", "consequencia"),
        ("transicao", "desenvolvimento"),
        ("transicao", "aprofundamento"),
        ("sintese_provisoria", "consequencia"),
        ("nota_de_apoio", "desenvolvimento"),
        ("critica_de_erro", "desenvolvimento"),
        ("critica_de_erro", "consequencia"),
    }
    return (left, right) in allowed_pairs


def line_direction_compatible(left: Optional[str], right: Optional[str]) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    line_directions = {"introduz", "prepara", "prolonga", "articula", "retoma"}
    return left in line_directions and right in line_directions


def dominant_zone(group: List[FragmentFeatures]) -> Optional[str]:
    zone = mode_preserve_order((f.zona for f in group), ignore={"indefinida"})
    if zone is not None:
        return zone
    return mode_preserve_order((f.zona for f in group))


def dominant_area(group: List[FragmentFeatures]) -> Optional[str]:
    return mode_preserve_order((f.area for f in group))


def dominant_problem(group: List[FragmentFeatures]) -> Optional[str]:
    return mode_preserve_order((f.problema for f in group))


def dominant_work(group: List[FragmentFeatures]) -> Optional[str]:
    return mode_preserve_order((f.trabalho for f in group))


def dominant_func(group: List[FragmentFeatures]) -> Optional[str]:
    return mode_preserve_order((f.funcao for f in group))


def dominant_direction(group: List[FragmentFeatures]) -> Optional[str]:
    return mode_preserve_order((f.direcao for f in group))


def dominant_status(group: List[FragmentFeatures]) -> Optional[str]:
    return mode_preserve_order((f.estatuto for f in group))


def dominant_impact_type(group: List[FragmentFeatures]) -> Optional[str]:
    return mode_preserve_order((f.tipo_utilidade for f in group))


def dominant_effect(group: List[FragmentFeatures]) -> Optional[str]:
    return mode_preserve_order((f.efeito for f in group))


def collect_prop_ids(group: List[FragmentFeatures]) -> Set[str]:
    result: Set[str] = set()
    for fragment in group:
        result.update(fragment.prop_ids)
    return result


def collect_prop_nums(group: List[FragmentFeatures]) -> Set[int]:
    result: Set[int] = set()
    for fragment in group:
        result.update(fragment.prop_nums)
    return result


def has_prop_overlap_or_adjacency(group: List[FragmentFeatures], candidate: FragmentFeatures) -> Tuple[int, List[str]]:
    reasons: List[str] = []
    group_prop_ids = collect_prop_ids(group)
    group_prop_nums = collect_prop_nums(group)
    candidate_prop_ids = set(candidate.prop_ids)
    candidate_prop_nums = set(candidate.prop_nums)

    overlap = sorted(group_prop_ids.intersection(candidate_prop_ids))
    if overlap:
        reasons.append(f"partilha proposição do mapa ({', '.join(overlap[:3])})")
        return 3, reasons

    if group_prop_nums and candidate_prop_nums:
        min_gap = min(abs(a - b) for a in group_prop_nums for b in candidate_prop_nums)
        if min_gap <= 1:
            reasons.append("toca proposições adjacentes do mapa")
            return 2, reasons

    return 0, reasons


def compute_compatibility(group: List[FragmentFeatures], candidate: FragmentFeatures) -> Tuple[bool, Dict[str, Any]]:
    """
    Compatibilidade determinística e auditável.
    Decide se o candidato entra na microlinha corrente.
    """
    last = group[-1]
    info: Dict[str, Any] = {
        "score": 0,
        "reasons": [],
        "hard_break": None,
    }

    if len(group) >= MAX_MICROLINHA_SIZE:
        info["hard_break"] = "tamanho_maximo"
        return False, info

    order_gap = candidate.ordem - last.ordem
    if order_gap > MAX_ORDER_GAP:
        info["hard_break"] = f"distancia_na_ordem={order_gap}"
        return False, info

    group_zone = dominant_zone(group)
    group_area = dominant_area(group)
    group_problem = dominant_problem(group)
    group_work = dominant_work(group)
    group_func = dominant_func(group)
    group_direction = dominant_direction(group)
    group_status = dominant_status(group)
    group_impact_type = dominant_impact_type(group)
    group_effect = dominant_effect(group)

    movement_strength = 0
    prop_strength, prop_reasons = has_prop_overlap_or_adjacency(group, candidate)
    if prop_strength:
        info["score"] += prop_strength
        info["reasons"].extend(prop_reasons)

    same_zone = False
    if candidate.zona and candidate.zona != "indefinida":
        if group_zone and candidate.zona == group_zone:
            same_zone = True
            info["score"] += 3
            info["reasons"].append("partilha zona provável de percurso")
        elif last.zona and last.zona != "indefinida" and candidate.zona == last.zona:
            same_zone = True
            info["score"] += 2
            info["reasons"].append("mantém continuidade de zona com o fragmento anterior")

    if candidate.area and group_area and candidate.area == group_area:
        info["score"] += 2
        info["reasons"].append("partilha área filosófica dominante")

    if candidate.problema and group_problem and candidate.problema == group_problem:
        info["score"] += 2
        info["reasons"].append("partilha problema filosófico central")

    if candidate.trabalho and group_work and candidate.trabalho == group_work:
        info["score"] += 1
        info["reasons"].append("partilha função filosófica no sistema")

    if allowed_function_pair(last.funcao, candidate.funcao):
        movement_strength += 2
        info["reasons"].append("continuidade plausível de função de cadência")

    if line_direction_compatible(last.direcao, candidate.direcao):
        movement_strength += 1
        info["reasons"].append("continuidade plausível de direção do movimento")

    if candidate.estatuto and (candidate.estatuto == last.estatuto or candidate.estatuto == group_status):
        movement_strength += 1
        info["reasons"].append("mantém estatuto local compatível")

    info["score"] += movement_strength

    if candidate.tipo_utilidade and group_impact_type and candidate.tipo_utilidade == group_impact_type:
        info["score"] += 1
        info["reasons"].append("partilha tipo de utilidade principal no mapa")

    if candidate.efeito and group_effect and candidate.efeito == group_effect:
        info["score"] += 1
        info["reasons"].append("partilha efeito principal no mapa")

    # Restrições fortes para evitar agrupamento arbitrário.
    zone_conflict = (
        candidate.zona not in (None, "", "indefinida")
        and group_zone not in (None, "", "indefinida")
        and candidate.zona != group_zone
    )
    area_conflict = (
        candidate.area not in (None, "")
        and group_area not in (None, "")
        and candidate.area != group_area
    )
    impact_disjoint = prop_strength == 0 and (
        candidate.tipo_utilidade != group_impact_type or candidate.efeito != group_effect
    )

    if zone_conflict and area_conflict and impact_disjoint and movement_strength < 2:
        info["hard_break"] = "divergencia_filosofica_e_de_impacto"
        return False, info

    unstable_candidate = (
        candidate.centralidade in {"dispersivo_aproveitavel", "nota_de_apoio"}
        and candidate.efeito == "sem_impacto_relevante"
        and candidate.problema is None
        and candidate.trabalho is None
    )
    if unstable_candidate and prop_strength == 0 and movement_strength == 0 and not same_zone:
        info["hard_break"] = "material_instavel_sem_apoio_convergente"
        return False, info

    join = False
    if prop_strength >= 2 and movement_strength >= 1:
        join = True
    elif same_zone and movement_strength >= 2:
        join = True
    elif info["score"] >= 5:
        join = True

    return join, info


def truncate(text: str, limit: int = 120) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def build_microlinha_title(group: List[FragmentFeatures]) -> str:
    zone = dominant_zone(group)
    area = dominant_area(group)
    direction = dominant_direction(group)
    problem = dominant_problem(group)

    part_a = slug_human(zone if zone not in (None, "", "indefinida") else area)
    part_b = slug_human(direction or dominant_func(group))
    title = f"{part_a} — {part_b}"

    if problem:
        title += f": {slug_human(problem)}"

    title = title.strip()
    if title == "nao determinado — nao determinado":
        title = "Microlinha local técnica"

    return truncate(title, 110)


def choose_base_dominante(group: List[FragmentFeatures]) -> str:
    impact_type = dominant_impact_type(group)
    effect = dominant_effect(group)
    problem = dominant_problem(group)
    work = dominant_work(group)

    if collect_prop_ids(group) and (impact_type is not None or effect is not None):
        return "impacto_mapa"
    if problem or work:
        return "tratamento_filosofico"
    return "cadencia"


def build_regra_curta(base_dominante: str) -> str:
    if base_dominante == "impacto_mapa":
        return "continuidade local por impacto no mapa com suporte de cadência"
    if base_dominante == "tratamento_filosofico":
        return "afinidade de problema e função filosófica com continuidade local"
    return "continuidade local de zona e movimento de cadência"


def build_microlinha_description(group: List[FragmentFeatures], base_dominante: str) -> str:
    n = len(group)
    direction = slug_human(dominant_direction(group) or dominant_func(group))
    problem = slug_human(dominant_problem(group))
    impact_type = slug_human(dominant_impact_type(group))
    return truncate(
        f"Agrupamento local de {n} fragmento(s), com dominância {slug_human(base_dominante)}, "
        f"movimento {direction}, problema {problem} e utilidade {impact_type}.",
        220,
    )


def determine_prioridade(group: List[FragmentFeatures]) -> str:
    if any(f.estado_excecao == "ativa_prioritaria" for f in group):
        return "alta"

    dominant_util = dominant_impact_type(group)
    dominant_eff = dominant_effect(group)
    if dominant_util in {"justificativa", "mediacional"} and dominant_eff in {"explicita", "medeia"}:
        return "alta"

    if len(group) > 1 or bool(collect_prop_ids(group)):
        return "media"

    return "baixa"


def determine_estado_excecao(group: List[FragmentFeatures]) -> Tuple[str, List[str]]:
    all_exception_ids: List[str] = []
    has_prioritaria = False
    has_tolerada = False

    for fragment in group:
        for exc_id in fragment.excecao_ids:
            if exc_id not in all_exception_ids:
                all_exception_ids.append(exc_id)

        if fragment.estado_excecao == "ativa_prioritaria":
            has_prioritaria = True
        elif fragment.estado_excecao == "ativa_tolerada":
            has_tolerada = True

    if has_prioritaria:
        return "ativa_prioritaria", sorted(all_exception_ids)
    if has_tolerada or all_exception_ids:
        return "ativa_tolerada", sorted(all_exception_ids)
    return "sem_excecao", []


def determine_estado_validacao(group: List[FragmentFeatures], microlinha_estado_excecao: str) -> str:
    if len(group) == 1:
        return "valido_com_avisos"

    if microlinha_estado_excecao in {"ativa_prioritaria", "ativa_tolerada"}:
        return "valido_com_avisos"

    if any(f.estado_validacao in {"valido_com_avisos", "invalido_tolerado", "invalido_bloqueante"} for f in group):
        return "valido_com_avisos"

    return "valido"


def build_microlinha_object(group: List[FragmentFeatures], microlinha_number: int) -> Dict[str, Any]:
    microlinha_id = f"ML_{microlinha_number:04d}"
    base_dominante = choose_base_dominante(group)
    estado_excecao, excecao_ids = determine_estado_excecao(group)
    estado_validacao = determine_estado_validacao(group, estado_excecao)

    titulo = build_microlinha_title(group)
    descricao_funcional = build_microlinha_description(group, base_dominante)

    observacoes: List[str] = []
    if len(group) == 1:
        observacoes.append("Microlinha unitária; requer consolidação posterior.")
    if excecao_ids:
        observacoes.append("Contém fragmentos com exceção ativa.")

    microlinha = {
        "id": microlinha_id,
        "tipo_no": "microlinha",
        "titulo": titulo,
        "descricao_funcional": descricao_funcional,
        "criterio_de_agregacao": {
            "base_dominante": base_dominante,
            "regra_curta": build_regra_curta(base_dominante),
            "problema_filosofico_dominante": dominant_problem(group),
            "direcao_movimento_dominante": dominant_direction(group),
            "tipo_de_utilidade_dominante": dominant_impact_type(group),
        },
        "fragmento_ids": [f.fragment_id for f in group],
        "relacao_ids_internas": [],
        "percurso_ids_sugeridos": [],
        "argumento_ids_sugeridos": [],
        "convergencia_ids": [],
        "ordem_no_ramo": None,
        "prioridade_de_consolidacao": determine_prioridade(group),
        "estado_validacao": estado_validacao,
        "estado_excecao": estado_excecao,
        "excecao_ids": excecao_ids,
        "observacoes": observacoes,
    }
    return microlinha


def clear_all_microlinha_links(tree: Dict[str, Any]) -> None:
    fragmentos = require_list(tree.get("fragmentos"), "fragmentos")
    for idx, fragment in enumerate(fragmentos, start=1):
        fragment_dict = require_dict(fragment, f"fragmentos[{idx}]")
        ligacoes = require_dict(
            require_key(fragment_dict, "ligacoes_arvore", f"fragmentos[{idx}]"),
            f"fragmentos[{idx}].ligacoes_arvore",
        )
        ligacoes["microlinha_ids"] = []


def generate_groups(features: List[FragmentFeatures]) -> Tuple[List[List[FragmentFeatures]], List[str]]:
    groups: List[List[FragmentFeatures]] = []
    log_lines: List[str] = []

    if not features:
        return groups, log_lines

    current_group: List[FragmentFeatures] = [features[0]]

    for candidate in features[1:]:
        join, info = compute_compatibility(current_group, candidate)
        if join:
            current_group.append(candidate)
            log_lines.append(
                f"JOIN  {candidate.fragment_id} -> grupo corrente "
                f"(score={info['score']}; razões={'; '.join(info['reasons']) if info['reasons'] else 'n/a'})"
            )
        else:
            reason = info["hard_break"] or f"score_insuficiente={info['score']}"
            log_lines.append(f"SPLIT {candidate.fragment_id} -> nova microlinha ({reason})")
            groups.append(current_group)
            current_group = [candidate]

    groups.append(current_group)
    return groups, log_lines


def size_distribution(groups: List[List[FragmentFeatures]]) -> Dict[int, int]:
    dist: Dict[int, int] = {}
    for group in groups:
        dist[len(group)] = dist.get(len(group), 0) + 1
    return dict(sorted(dist.items(), key=lambda kv: kv[0]))


def update_tree_with_microlinhas(
    tree: Dict[str, Any],
    microlinhas: List[Dict[str, Any]],
    selected_features: List[FragmentFeatures],
) -> None:
    tree["microlinhas"] = microlinhas

    id_to_fragment: Dict[str, Dict[str, Any]] = {}
    fragmentos = require_list(tree.get("fragmentos"), "fragmentos")
    for idx, fragment in enumerate(fragmentos, start=1):
        fragment_dict = require_dict(fragment, f"fragmentos[{idx}]")
        fragment_id = require_key(fragment_dict, "id", f"fragmentos[{idx}]")
        if isinstance(fragment_id, str):
            id_to_fragment[fragment_id] = fragment_dict

    for microlinha in microlinhas:
        microlinha_id = microlinha["id"]
        for fragment_id in microlinha["fragmento_ids"]:
            fragment_dict = id_to_fragment.get(fragment_id)
            if fragment_dict is None:
                raise MicrolinhaGenerationError(
                    f"A microlinha '{microlinha_id}' refere o fragmento inexistente '{fragment_id}'."
                )
            ligacoes = require_dict(fragment_dict["ligacoes_arvore"], f"fragmento {fragment_id}.ligacoes_arvore")
            ligacoes["microlinha_ids"] = [microlinha_id]

    validacao = require_dict(require_key(tree, "validacao", "raiz"), "validacao")
    metricas = require_dict(require_key(validacao, "metricas", "validacao"), "validacao.metricas")
    metricas["total_microlinhas"] = len(microlinhas)

    observacoes = validacao.get("observacoes")
    if observacoes is None:
        observacoes = []
        validacao["observacoes"] = observacoes
    elif not isinstance(observacoes, list):
        raise MicrolinhaGenerationError(
            "O campo 'validacao.observacoes' existe mas não é array/list."
        )

    # Remove notas anteriores desta geração para não acumular duplicados.
    prefixos_controlados = (
        "Microlinhas v1:",
        "Geração de microlinhas v1:",
    )
    validacao["observacoes"] = [
        item for item in observacoes
        if not (isinstance(item, str) and item.startswith(prefixos_controlados))
    ]
    observacoes = validacao["observacoes"]

    unitarias = sum(1 for m in microlinhas if len(m["fragmento_ids"]) == 1)
    if microlinhas and unitarias >= 3 and unitarias / len(microlinhas) >= 0.5:
        observacoes.append(
            f"Microlinhas v1: elevada proporção de microlinhas unitárias ({unitarias}/{len(microlinhas)})."
        )


def build_report_text(
    input_path: Path,
    total_fragmentos_lidos: int,
    total_fragmentos_processados: int,
    microlinhas: List[Dict[str, Any]],
    grouping_log: List[str],
    args: argparse.Namespace,
) -> str:
    now_utc = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    dist = size_distribution([[None] * len(m["fragmento_ids"]) for m in microlinhas])  # type: ignore[list-item]
    unitary_count = sum(1 for m in microlinhas if len(m["fragmento_ids"]) == 1)
    with_exceptions_count = sum(1 for m in microlinhas if m["estado_excecao"] != "sem_excecao")

    lines: List[str] = []
    lines.append("RELATÓRIO DE GERAÇÃO DE MICROLINHAS V1")
    lines.append("=" * 60)
    lines.append(f"Data/hora UTC: {now_utc}")
    lines.append(f"Ficheiro atualizado: {input_path}")
    lines.append(f"Fragmentos lidos na árvore: {total_fragmentos_lidos}")
    lines.append(f"Fragmentos processados nesta geração: {total_fragmentos_processados}")
    lines.append(f"Modo de execução: {'teste limitado' if args.limite is not None else 'geração total'}")
    if args.limite is not None:
        lines.append(f"Limite aplicado: {args.limite}")
    lines.append(f"Reescrita forçada: {'sim' if args.forcar else 'não'}")
    lines.append("")

    lines.append("Critérios usados")
    lines.append("-" * 60)
    lines.append("1. Percurso sequencial por ordem dos fragmentos.")
    lines.append("2. Compatibilidade por zona/cadência, área/problema filosófico, impacto local no mapa e vizinhança de ordem.")
    lines.append("3. Fecho da microlinha quando a compatibilidade cai abaixo do limiar ou quando há rutura forte.")
    lines.append(f"4. Tamanho máximo por microlinha: {MAX_MICROLINHA_SIZE} fragmentos.")
    lines.append(f"5. Distância máxima de ordem para continuidade local: {MAX_ORDER_GAP}.")
    lines.append("")

    lines.append("Resumo")
    lines.append("-" * 60)
    lines.append(f"Microlinhas geradas: {len(microlinhas)}")
    lines.append(f"Microlinhas unitárias: {unitary_count}")
    lines.append(f"Microlinhas com exceções: {with_exceptions_count}")
    if dist:
        parts = [f"{size}: {count}" for size, count in dist.items()]
        lines.append("Distribuição de tamanhos: " + " | ".join(parts))
    else:
        lines.append("Distribuição de tamanhos: n/a")
    lines.append("")

    lines.append("Microlinhas geradas")
    lines.append("-" * 60)
    if not microlinhas:
        lines.append("Nenhuma microlinha gerada.")
    else:
        for microlinha in microlinhas:
            lines.append(
                f"{microlinha['id']} | n={len(microlinha['fragmento_ids'])} | "
                f"{microlinha['titulo']} | estado={microlinha['estado_validacao']} | "
                f"excecao={microlinha['estado_excecao']}"
            )
            lines.append(f"  fragmentos: {', '.join(microlinha['fragmento_ids'])}")
            if microlinha["observacoes"]:
                for note in microlinha["observacoes"]:
                    lines.append(f"  nota: {note}")
    lines.append("")

    lines.append("Log de agrupamento")
    lines.append("-" * 60)
    if grouping_log:
        lines.extend(grouping_log)
    else:
        lines.append("Sem eventos de agrupamento relevantes.")
    lines.append("")

    lines.append("Conclusão final")
    lines.append("-" * 60)
    lines.append(
        f"Geração concluída com {len(microlinhas)} microlinhas, "
        f"{unitary_count} unitárias e {with_exceptions_count} com exceções."
    )
    lines.append("")
    return "\n".join(lines)


def build_terminal_summary(
    input_path: Path,
    total_fragmentos_lidos: int,
    total_fragmentos_processados: int,
    microlinhas: List[Dict[str, Any]],
    report_path: Path,
) -> str:
    unitary_count = sum(1 for m in microlinhas if len(m["fragmento_ids"]) == 1)
    with_exceptions_count = sum(1 for m in microlinhas if m["estado_excecao"] != "sem_excecao")

    lines = [
        f"Ficheiro atualizado: {input_path}",
        f"Fragmentos lidos: {total_fragmentos_lidos}",
        f"Fragmentos processados: {total_fragmentos_processados}",
        f"Microlinhas geradas: {len(microlinhas)}",
        f"Microlinhas unitárias: {unitary_count}",
        f"Microlinhas com exceções: {with_exceptions_count}",
        "Conclusão final: geração concluída.",
        f"Relatório escrito em: {report_path}",
    ]
    return "\n".join(lines)


def ensure_tree_is_minimally_usable(tree: Dict[str, Any], args: argparse.Namespace) -> None:
    if not isinstance(tree, dict):
        raise MicrolinhaGenerationError("O ficheiro da árvore tem de ser um objeto JSON no topo.")

    required_top = [
        "fragmentos",
        "microlinhas",
        "validacao",
    ]
    for key in required_top:
        if key not in tree:
            raise MicrolinhaGenerationError(f"Falta o bloco obrigatório '{key}' na árvore.")

    fragmentos = require_list(tree.get("fragmentos"), "fragmentos")
    microlinhas = require_list(tree.get("microlinhas"), "microlinhas")

    if microlinhas and not args.forcar:
        raise MicrolinhaGenerationError(
            "O bloco 'microlinhas' já contém dados. Use --forcar para regenerar e substituir."
        )

    for idx, fragment in enumerate(fragmentos, start=1):
        fragment_dict = require_dict(fragment, f"fragmentos[{idx}]")
        # Apenas o mínimo que o gerador precisa.
        for field in (
            "id",
            "ordem_no_ficheiro",
            "cadencia",
            "impacto_mapa",
            "ligacoes_arvore",
            "estado_validacao",
            "estado_excecao",
            "excecao_ids",
        ):
            require_key(fragment_dict, field, f"fragmentos[{idx}]")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    script_dir = Path(__file__).resolve().parent
    paths = build_paths(script_dir)

    tree = load_json(paths["input"])
    ensure_tree_is_minimally_usable(tree, args)

    fragmentos = require_list(tree.get("fragmentos"), "fragmentos")
    total_fragmentos_lidos = len(fragmentos)

    clear_all_microlinha_links(tree)

    features: List[FragmentFeatures] = []
    for idx, fragment in enumerate(fragmentos, start=1):
        features.append(extract_fragment_features(fragment, idx))

    features = sort_fragment_features(features)
    if args.limite is not None:
        features = features[: args.limite]

    groups, grouping_log = generate_groups(features)
    microlinhas = [
        build_microlinha_object(group, microlinha_number=i)
        for i, group in enumerate(groups, start=1)
    ]

    update_tree_with_microlinhas(tree, microlinhas, features)
    save_json_atomic(paths["input"], tree)

    report_text = build_report_text(
        input_path=paths["input"],
        total_fragmentos_lidos=total_fragmentos_lidos,
        total_fragmentos_processados=len(features),
        microlinhas=microlinhas,
        grouping_log=grouping_log,
        args=args,
    )
    write_text(paths["report"], report_text)

    print(
        build_terminal_summary(
            input_path=paths["input"],
            total_fragmentos_lidos=total_fragmentos_lidos,
            total_fragmentos_processados=len(features),
            microlinhas=microlinhas,
            report_path=paths["report"],
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MicrolinhaGenerationError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)