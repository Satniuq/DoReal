# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


INPUT_FILENAME = "arvore_do_pensamento_v1.json"
REPORT_FILENAME = "relatorio_geracao_ramos_v1.txt"

MAX_RAMO_SIZE = 8
MAX_ORDER_GAP = 18
MAX_FIRST_TO_CANDIDATE_GAP = 36


class RamoGenerationError(RuntimeError):
    """Erro fatal na geração de ramos."""


@dataclass(frozen=True)
class MicrolinhaFeatures:
    microlinha_id: str
    ordem_inicial: int
    ordem_final: int
    fragmento_ids: Tuple[str, ...]
    zona_titulo: Optional[str]
    titulo: Optional[str]
    descricao_funcional: Optional[str]
    base_dominante: Optional[str]
    problema_dominante: Optional[str]
    direcao_dominante: Optional[str]
    utilidade_dominante: Optional[str]
    zona_fragmentos_dominante: Optional[str]
    funcao_cadencia_dominante: Optional[str]
    direcao_fragmentos_dominante: Optional[str]
    problema_fragmentos_dominante: Optional[str]
    trabalho_fragmentos_dominante: Optional[str]
    utilidade_fragmentos_dominante: Optional[str]
    efeito_fragmentos_dominante: Optional[str]
    passo_ids: Tuple[str, ...]
    passo_nums: Tuple[int, ...]
    faixa_local_mapa: Optional[str]
    estado_validacao: Optional[str]
    estado_excecao: Optional[str]
    excecao_ids: Tuple[str, ...]
    prioridade_de_consolidacao: Optional[str]
    microlinha_ref: Dict[str, Any]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera a camada de ramos da árvore do pensamento v1."
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help="Processa apenas as primeiras N microlinhas por ordem, para ensaio.",
    )
    parser.add_argument(
        "--forcar",
        action="store_true",
        help="Permite regenerar e substituir 'ramos[]' caso já exista conteúdo.",
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
        raise RamoGenerationError(f"Ficheiro não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RamoGenerationError(f"JSON inválido em {path}: {exc}") from exc
    except OSError as exc:
        raise RamoGenerationError(f"Não foi possível ler {path}: {exc}") from exc


def save_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        temp_path.replace(path)
    except OSError as exc:
        raise RamoGenerationError(f"Não foi possível escrever {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as exc:
        raise RamoGenerationError(f"Não foi possível escrever o relatório {path}: {exc}") from exc


def require_key(mapping: Dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise RamoGenerationError(f"Falta a chave obrigatória '{key}' em {context}.")
    return mapping[key]


def require_dict(value: Any, context: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise RamoGenerationError(
            f"Tipo inválido em {context}: esperado object/dict, obtido {type(value).__name__}."
        )
    return value


def require_list(value: Any, context: str) -> List[Any]:
    if not isinstance(value, list):
        raise RamoGenerationError(
            f"Tipo inválido em {context}: esperado array/list, obtido {type(value).__name__}."
        )
    return value


def slug_human(text: Optional[str]) -> str:
    if not isinstance(text, str) or not text.strip():
        return "nao_determinado"
    return text.strip().replace("_", " ")


def truncate(text: str, limit: int = 120) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def parse_prop_number(prop_id: str) -> Optional[int]:
    match = re.fullmatch(r"P(\d+)", prop_id.strip()) if isinstance(prop_id, str) else None
    return int(match.group(1)) if match else None


def mode_preserve_order(
    values: Iterable[Optional[str]],
    ignore: Optional[Set[str]] = None,
) -> Optional[str]:
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


def first_nonempty(values: Iterable[Optional[str]]) -> Optional[str]:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def normalise_zone_from_title(titulo: Optional[str]) -> Optional[str]:
    if not isinstance(titulo, str):
        return None
    prefix = titulo.split("—", 1)[0].strip().replace(" ", "_")
    if prefix == "nao_determinado":
        return None
    return prefix or None


def faixa_local_do_mapa_from_nums(nums: Iterable[int]) -> Optional[str]:
    unique = sorted(set(nums))
    if not unique:
        return None
    inicio = ((unique[0] - 1) // 5) * 5 + 1
    fim = inicio + 4
    return f"P{inicio:02d}-P{fim:02d}"


def consecutive_or_close_directions(left: Optional[str], right: Optional[str]) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True

    allowed_pairs = {
        ("introduz", "prepara"),
        ("introduz", "prolonga"),
        ("introduz", "articula"),
        ("prepara", "prolonga"),
        ("prepara", "articula"),
        ("prolonga", "articula"),
        ("prolonga", "retoma"),
        ("prolonga", "fecha"),
        ("articula", "fecha"),
        ("retoma", "prolonga"),
        ("retoma", "articula"),
        ("distincao_conceptual", "consequencia"),
    }
    return (left, right) in allowed_pairs


def cadence_function_compatible(left: Optional[str], right: Optional[str]) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True

    allowed_pairs = {
        ("abertura_de_problema", "formulacao_inicial"),
        ("formulacao_inicial", "desenvolvimento"),
        ("formulacao_inicial", "distincao_conceptual"),
        ("desenvolvimento", "aprofundamento"),
        ("desenvolvimento", "distincao_conceptual"),
        ("desenvolvimento", "consequencia"),
        ("aprofundamento", "consequencia"),
        ("distincao_conceptual", "consequencia"),
        ("transicao", "desenvolvimento"),
        ("transicao", "aprofundamento"),
        ("critica_de_erro", "desenvolvimento"),
        ("critica_de_erro", "consequencia"),
        ("nota_de_apoio", "desenvolvimento"),
        ("objecao", "resposta"),
        ("resposta", "consequencia"),
    }
    return (left, right) in allowed_pairs


def choose_criterio_de_unidade(group: List[MicrolinhaFeatures]) -> str:
    group_problem = dominant_problem(group)
    group_work = dominant_work(group)
    group_direction = dominant_direction(group)
    prop_ids = collect_step_ids(group)
    zones = {m.zona_fragmentos_dominante for m in group if m.zona_fragmentos_dominante}
    works = {m.trabalho_fragmentos_dominante for m in group if m.trabalho_fragmentos_dominante}

    if len(prop_ids) >= 3 and len(zones) == 1:
        return "percurso"
    if group_problem and len({m.problema_fragmentos_dominante for m in group if m.problema_fragmentos_dominante}) == 1:
        return "problema"
    if group_work and len(works) == 1:
        return "operacao"
    if group_direction in {"introduz", "prepara", "prolonga", "articula", "retoma", "fecha"}:
        return "transicao"
    if len(prop_ids) >= 4:
        return "convergencia"
    return "misto"


def collect_step_ids(group: List[MicrolinhaFeatures]) -> Set[str]:
    result: Set[str] = set()
    for item in group:
        result.update(item.passo_ids)
    return result


def collect_step_nums(group: List[MicrolinhaFeatures]) -> Set[int]:
    result: Set[int] = set()
    for item in group:
        result.update(item.passo_nums)
    return result


def dominant_zone(group: List[MicrolinhaFeatures]) -> Optional[str]:
    zone = mode_preserve_order(
        (m.zona_fragmentos_dominante for m in group),
        ignore={"indefinida"},
    )
    if zone is not None:
        return zone
    return mode_preserve_order((m.zona_titulo for m in group), ignore={"indefinida"})


def dominant_problem(group: List[MicrolinhaFeatures]) -> Optional[str]:
    return mode_preserve_order((m.problema_fragmentos_dominante for m in group))


def dominant_work(group: List[MicrolinhaFeatures]) -> Optional[str]:
    return mode_preserve_order((m.trabalho_fragmentos_dominante for m in group))


def dominant_direction(group: List[MicrolinhaFeatures]) -> Optional[str]:
    return mode_preserve_order(
        (m.direcao_dominante or m.direcao_fragmentos_dominante for m in group)
    )


def dominant_funcao_cadencia(group: List[MicrolinhaFeatures]) -> Optional[str]:
    return mode_preserve_order((m.funcao_cadencia_dominante for m in group))


def dominant_utilidade(group: List[MicrolinhaFeatures]) -> Optional[str]:
    return mode_preserve_order(
        (m.utilidade_dominante or m.utilidade_fragmentos_dominante for m in group)
    )


def dominant_efeito(group: List[MicrolinhaFeatures]) -> Optional[str]:
    return mode_preserve_order((m.efeito_fragmentos_dominante for m in group))


def dominant_base(group: List[MicrolinhaFeatures]) -> Optional[str]:
    return mode_preserve_order((m.base_dominante for m in group))


def dominant_faixa(group: List[MicrolinhaFeatures]) -> Optional[str]:
    nums = collect_step_nums(group)
    return faixa_local_do_mapa_from_nums(nums)


def count_steps(group: List[MicrolinhaFeatures]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for item in group:
        counter.update(item.passo_ids)
    return counter


def top_step_ids(group: List[MicrolinhaFeatures], limit: int = 5) -> List[str]:
    counter = count_steps(group)
    if not counter:
        return []
    ordered = sorted(counter.items(), key=lambda kv: (-kv[1], parse_prop_number(kv[0]) or 9999, kv[0]))
    return [step_id for step_id, _ in ordered[:limit]]


def infer_prioridade_ramo(group: List[MicrolinhaFeatures]) -> str:
    if any(m.estado_excecao == "ativa_prioritaria" for m in group):
        return "alta"

    utilidade = dominant_utilidade(group)
    efeito = dominant_efeito(group)
    if utilidade in {"justificativa", "mediacional"} and efeito in {"explicita", "medeia"}:
        return "alta"

    if len(group) >= 3:
        return "media"

    prioridades = [m.prioridade_de_consolidacao for m in group if m.prioridade_de_consolidacao]
    if "alta" in prioridades:
        return "alta"
    if "media" in prioridades:
        return "media"
    return "baixa"


def determine_ramo_estado_excecao(group: List[MicrolinhaFeatures]) -> Tuple[str, List[str]]:
    all_exception_ids: List[str] = []
    has_prioritaria = False
    has_tolerada = False

    for item in group:
        for exc_id in item.excecao_ids:
            if exc_id not in all_exception_ids:
                all_exception_ids.append(exc_id)

        if item.estado_excecao == "ativa_prioritaria":
            has_prioritaria = True
        elif item.estado_excecao == "ativa_tolerada":
            has_tolerada = True

    if has_prioritaria:
        return "ativa_prioritaria", sorted(all_exception_ids)
    if has_tolerada or all_exception_ids:
        return "ativa_tolerada", sorted(all_exception_ids)
    return "sem_excecao", []


def determine_ramo_estado_validacao(group: List[MicrolinhaFeatures], ramo_estado_excecao: str) -> str:
    if len(group) == 1:
        return "valido_com_avisos"

    if ramo_estado_excecao in {"ativa_prioritaria", "ativa_tolerada"}:
        return "valido_com_avisos"

    if any(item.estado_validacao in {"valido_com_avisos", "invalido_tolerado", "invalido_bloqueante"} for item in group):
        return "valido_com_avisos"

    return "valido"


def clear_all_ramo_links(tree: Dict[str, Any]) -> None:
    fragmentos = require_list(tree.get("fragmentos"), "fragmentos")
    for idx, fragment in enumerate(fragmentos, start=1):
        fragment_dict = require_dict(fragment, f"fragmentos[{idx}]")
        ligacoes = require_dict(
            require_key(fragment_dict, "ligacoes_arvore", f"fragmentos[{idx}]"),
            f"fragmentos[{idx}].ligacoes_arvore",
        )
        ligacoes["ramo_ids"] = []

    microlinhas = require_list(tree.get("microlinhas"), "microlinhas")
    for idx, microlinha in enumerate(microlinhas, start=1):
        microlinha_dict = require_dict(microlinha, f"microlinhas[{idx}]")
        microlinha_dict["ordem_no_ramo"] = None


def extract_microlinha_features(
    microlinha: Dict[str, Any],
    index: int,
    fragment_map: Dict[str, Dict[str, Any]],
) -> MicrolinhaFeatures:
    context = f"microlinhas[{index}]"

    microlinha_id = require_key(microlinha, "id", context)
    if not isinstance(microlinha_id, str) or not microlinha_id.strip():
        raise RamoGenerationError(f"{context}.id tem de ser uma string não vazia.")

    fragmento_ids = require_list(require_key(microlinha, "fragmento_ids", context), f"{context}.fragmento_ids")
    if not fragmento_ids:
        raise RamoGenerationError(f"{context}.fragmento_ids não pode estar vazio.")

    criterio = require_dict(
        require_key(microlinha, "criterio_de_agregacao", context),
        f"{context}.criterio_de_agregacao",
    )

    for key in (
        "base_dominante",
        "problema_filosofico_dominante",
        "direcao_movimento_dominante",
        "tipo_de_utilidade_dominante",
    ):
        require_key(criterio, key, f"{context}.criterio_de_agregacao")

    microlinha_fragments: List[Dict[str, Any]] = []
    ordens: List[int] = []
    zonas: List[str] = []
    funcoes: List[str] = []
    direcoes: List[str] = []
    problemas: List[str] = []
    trabalhos: List[str] = []
    utilidades: List[str] = []
    efeitos: List[str] = []
    passo_ids: List[str] = []
    passo_nums: List[int] = []

    for frag_idx, fragment_id in enumerate(fragmento_ids, start=1):
        if not isinstance(fragment_id, str) or not fragment_id.strip():
            raise RamoGenerationError(f"{context}.fragmento_ids[{frag_idx}] é inválido.")
        fragment = fragment_map.get(fragment_id)
        if fragment is None:
            raise RamoGenerationError(
                f"{context} refere o fragmento inexistente '{fragment_id}'."
            )
        microlinha_fragments.append(fragment)

        ordem = fragment.get("ordem_no_ficheiro")
        if not isinstance(ordem, int):
            raise RamoGenerationError(
                f"O fragmento '{fragment_id}' não tem 'ordem_no_ficheiro' inteiro."
            )
        ordens.append(ordem)

        cadencia = require_dict(require_key(fragment, "cadencia", f"fragmento {fragment_id}"), f"fragmento {fragment_id}.cadencia")
        impacto = require_dict(require_key(fragment, "impacto_mapa", f"fragmento {fragment_id}"), f"fragmento {fragment_id}.impacto_mapa")
        tratamento = fragment.get("tratamento_filosofico")
        if tratamento is not None:
            tratamento = require_dict(tratamento, f"fragmento {fragment_id}.tratamento_filosofico")

        zona = cadencia.get("zona_provavel_percurso")
        if isinstance(zona, str) and zona.strip():
            zonas.append(zona.strip())

        funcao = cadencia.get("funcao_cadencia_principal")
        if isinstance(funcao, str) and funcao.strip():
            funcoes.append(funcao.strip())

        direcao = cadencia.get("direcao_movimento")
        if isinstance(direcao, str) and direcao.strip():
            direcoes.append(direcao.strip())

        if isinstance(tratamento, dict):
            problema = tratamento.get("problema_filosofico_central")
            if isinstance(problema, str) and problema.strip():
                problemas.append(problema.strip())

            trabalho = tratamento.get("trabalho_no_sistema")
            if isinstance(trabalho, str) and trabalho.strip():
                trabalhos.append(trabalho.strip())

        utilidade = impacto.get("tipo_de_utilidade_principal")
        if isinstance(utilidade, str) and utilidade.strip():
            utilidades.append(utilidade.strip())

        efeito = impacto.get("efeito_principal_no_mapa")
        if isinstance(efeito, str) and efeito.strip():
            efeitos.append(efeito.strip())

        proposicoes = require_list(
            require_key(impacto, "proposicoes_do_mapa_tocadas", f"fragmento {fragment_id}.impacto_mapa"),
            f"fragmento {fragment_id}.impacto_mapa.proposicoes_do_mapa_tocadas",
        )
        for p_idx, proposicao in enumerate(proposicoes, start=1):
            p_ctx = f"fragmento {fragment_id}.impacto_mapa.proposicoes_do_mapa_tocadas[{p_idx}]"
            p_dict = require_dict(proposicao, p_ctx)
            step_id = p_dict.get("proposicao_id")
            if isinstance(step_id, str) and step_id.strip():
                clean_step_id = step_id.strip()
                passo_ids.append(clean_step_id)
                number = parse_prop_number(clean_step_id)
                if number is not None:
                    passo_nums.append(number)

    excecao_ids = microlinha.get("excecao_ids", [])
    if not isinstance(excecao_ids, list):
        raise RamoGenerationError(f"{context}.excecao_ids tem de ser array/list.")

    zona_titulo = normalise_zone_from_title(microlinha.get("titulo"))
    zona_fragmentos_dominante = mode_preserve_order(zonas, ignore={"indefinida"})
    if zona_fragmentos_dominante is None:
        zona_fragmentos_dominante = mode_preserve_order(zonas)

    return MicrolinhaFeatures(
        microlinha_id=microlinha_id,
        ordem_inicial=min(ordens),
        ordem_final=max(ordens),
        fragmento_ids=tuple(str(x) for x in fragmento_ids),
        zona_titulo=zona_titulo,
        titulo=microlinha.get("titulo") if isinstance(microlinha.get("titulo"), str) else None,
        descricao_funcional=microlinha.get("descricao_funcional") if isinstance(microlinha.get("descricao_funcional"), str) else None,
        base_dominante=criterio.get("base_dominante") if isinstance(criterio.get("base_dominante"), str) else None,
        problema_dominante=criterio.get("problema_filosofico_dominante") if isinstance(criterio.get("problema_filosofico_dominante"), str) else None,
        direcao_dominante=criterio.get("direcao_movimento_dominante") if isinstance(criterio.get("direcao_movimento_dominante"), str) else None,
        utilidade_dominante=criterio.get("tipo_de_utilidade_dominante") if isinstance(criterio.get("tipo_de_utilidade_dominante"), str) else None,
        zona_fragmentos_dominante=zona_fragmentos_dominante,
        funcao_cadencia_dominante=mode_preserve_order(funcoes),
        direcao_fragmentos_dominante=mode_preserve_order(direcoes),
        problema_fragmentos_dominante=mode_preserve_order(problemas),
        trabalho_fragmentos_dominante=mode_preserve_order(trabalhos),
        utilidade_fragmentos_dominante=mode_preserve_order(utilidades),
        efeito_fragmentos_dominante=mode_preserve_order(efeitos),
        passo_ids=tuple(sorted(set(passo_ids), key=lambda x: (parse_prop_number(x) or 9999, x))),
        passo_nums=tuple(sorted(set(passo_nums))),
        faixa_local_mapa=faixa_local_do_mapa_from_nums(passo_nums),
        estado_validacao=microlinha.get("estado_validacao") if isinstance(microlinha.get("estado_validacao"), str) else None,
        estado_excecao=microlinha.get("estado_excecao") if isinstance(microlinha.get("estado_excecao"), str) else None,
        excecao_ids=tuple(str(x) for x in excecao_ids),
        prioridade_de_consolidacao=microlinha.get("prioridade_de_consolidacao") if isinstance(microlinha.get("prioridade_de_consolidacao"), str) else None,
        microlinha_ref=microlinha,
    )


def sort_microlinha_features(features: List[MicrolinhaFeatures]) -> List[MicrolinhaFeatures]:
    return sorted(features, key=lambda x: (x.ordem_inicial, x.ordem_final, x.microlinha_id))


def step_overlap_or_adjacency(group: List[MicrolinhaFeatures], candidate: MicrolinhaFeatures) -> Tuple[int, List[str]]:
    reasons: List[str] = []
    group_ids = collect_step_ids(group)
    group_nums = collect_step_nums(group)
    cand_ids = set(candidate.passo_ids)
    cand_nums = set(candidate.passo_nums)

    overlap = sorted(group_ids.intersection(cand_ids), key=lambda x: (parse_prop_number(x) or 9999, x))
    if overlap:
        reasons.append(f"partilha passo(s) do mapa ({', '.join(overlap[:3])})")
        return 3, reasons

    if group_nums and cand_nums:
        min_gap = min(abs(a - b) for a in group_nums for b in cand_nums)
        if min_gap <= 1:
            reasons.append("toca passo(s) adjacentes do mapa")
            return 2, reasons
        if min_gap <= 3:
            reasons.append("toca mesma faixa local do mapa")
            return 1, reasons

    return 0, reasons


def compute_ramo_compatibility(group: List[MicrolinhaFeatures], candidate: MicrolinhaFeatures) -> Tuple[bool, Dict[str, Any]]:
    """
    Heurística explícita, determinística e auditável para geração de ramos.
    """
    last = group[-1]
    first = group[0]
    info: Dict[str, Any] = {
        "score": 0,
        "reasons": [],
        "hard_break": None,
    }

    if len(group) >= MAX_RAMO_SIZE:
        info["hard_break"] = "tamanho_maximo"
        return False, info

    order_gap = candidate.ordem_inicial - last.ordem_final
    if order_gap > MAX_ORDER_GAP:
        info["hard_break"] = f"distancia_local={order_gap}"
        return False, info

    first_gap = candidate.ordem_inicial - first.ordem_inicial
    if first_gap > MAX_FIRST_TO_CANDIDATE_GAP:
        info["hard_break"] = f"amplitude_excessiva={first_gap}"
        return False, info

    group_zone = dominant_zone(group)
    group_problem = dominant_problem(group)
    group_work = dominant_work(group)
    group_direction = dominant_direction(group)
    group_funcao = dominant_funcao_cadencia(group)
    group_utilidade = dominant_utilidade(group)
    group_efeito = dominant_efeito(group)
    group_faixa = dominant_faixa(group)

    step_strength, step_reasons = step_overlap_or_adjacency(group, candidate)
    info["score"] += step_strength
    info["reasons"].extend(step_reasons)

    same_zone = False
    if candidate.zona_fragmentos_dominante and candidate.zona_fragmentos_dominante != "indefinida":
        if group_zone and candidate.zona_fragmentos_dominante == group_zone:
            same_zone = True
            info["score"] += 3
            info["reasons"].append("partilha zona filosófica dominante")
        elif last.zona_fragmentos_dominante and candidate.zona_fragmentos_dominante == last.zona_fragmentos_dominante:
            same_zone = True
            info["score"] += 2
            info["reasons"].append("mantém continuidade de zona com a microlinha anterior")

    if candidate.problema_fragmentos_dominante and group_problem and candidate.problema_fragmentos_dominante == group_problem:
        info["score"] += 3
        info["reasons"].append("partilha problema filosófico central")

    if candidate.trabalho_fragmentos_dominante and group_work and candidate.trabalho_fragmentos_dominante == group_work:
        info["score"] += 2
        info["reasons"].append("partilha trabalho dominante no sistema")

    if candidate.faixa_local_mapa and group_faixa and candidate.faixa_local_mapa == group_faixa:
        info["score"] += 1
        info["reasons"].append("permanece na mesma faixa local do mapa")

    movement_strength = 0
    if cadence_function_compatible(last.funcao_cadencia_dominante, candidate.funcao_cadencia_dominante):
        movement_strength += 2
        info["reasons"].append("continuidade plausível de cadência")

    if consecutive_or_close_directions(last.direcao_dominante or last.direcao_fragmentos_dominante,
                                       candidate.direcao_dominante or candidate.direcao_fragmentos_dominante):
        movement_strength += 2
        info["reasons"].append("continuidade plausível de direção local do movimento")

    if candidate.utilidade_dominante and group_utilidade and candidate.utilidade_dominante == group_utilidade:
        info["score"] += 1
        info["reasons"].append("partilha tipo de utilidade dominante")

    if candidate.efeito_fragmentos_dominante and group_efeito and candidate.efeito_fragmentos_dominante == group_efeito:
        info["score"] += 2
        info["reasons"].append("partilha impacto estrutural dominante no mapa")

    info["score"] += movement_strength

    zone_conflict = (
        candidate.zona_fragmentos_dominante not in (None, "", "indefinida")
        and group_zone not in (None, "", "indefinida")
        and candidate.zona_fragmentos_dominante != group_zone
    )
    problem_conflict = (
        candidate.problema_fragmentos_dominante not in (None, "")
        and group_problem not in (None, "")
        and candidate.problema_fragmentos_dominante != group_problem
    )
    impact_disjoint = step_strength == 0 and (
        candidate.efeito_fragmentos_dominante != group_efeito
        and candidate.faixa_local_mapa != group_faixa
    )

    if zone_conflict and problem_conflict and impact_disjoint and movement_strength < 2:
        info["hard_break"] = "divergencia_filosofica_e_de_impacto"
        return False, info

    isolated_candidate = (
        candidate.problema_fragmentos_dominante is None
        and candidate.trabalho_fragmentos_dominante is None
        and not candidate.passo_ids
        and candidate.efeito_fragmentos_dominante == "sem_impacto_relevante"
    )
    if isolated_candidate and step_strength == 0 and movement_strength == 0 and not same_zone:
        info["hard_break"] = "microlinha_isolada_sem_apoio_comum"
        return False, info

    join = False
    if step_strength >= 2 and movement_strength >= 1:
        join = True
    elif same_zone and (movement_strength >= 2 or info["score"] >= 5):
        join = True
    elif info["score"] >= 6:
        join = True

    return join, info


def generate_ramo_groups(features: List[MicrolinhaFeatures]) -> Tuple[List[List[MicrolinhaFeatures]], List[str]]:
    groups: List[List[MicrolinhaFeatures]] = []
    log_lines: List[str] = []

    if not features:
        return groups, log_lines

    current_group: List[MicrolinhaFeatures] = [features[0]]

    for candidate in features[1:]:
        join, info = compute_ramo_compatibility(current_group, candidate)
        if join:
            current_group.append(candidate)
            log_lines.append(
                f"JOIN  {candidate.microlinha_id} -> ramo corrente "
                f"(score={info['score']}; razões={'; '.join(info['reasons']) if info['reasons'] else 'n/a'})"
            )
        else:
            reason = info["hard_break"] or f"score_insuficiente={info['score']}"
            log_lines.append(f"SPLIT {candidate.microlinha_id} -> novo ramo ({reason})")
            groups.append(current_group)
            current_group = [candidate]

    groups.append(current_group)
    return groups, log_lines


def build_ramo_title(group: List[MicrolinhaFeatures]) -> str:
    zone = slug_human(dominant_zone(group))
    problem = slug_human(dominant_problem(group))
    direction = slug_human(dominant_direction(group))
    effect = slug_human(dominant_efeito(group))

    title = f"{zone} — {problem}"
    if direction != "nao_determinado":
        title += f" — {direction}"
    if effect != "nao_determinado" and effect not in title:
        title += f" ({effect})"

    if title.strip() == "nao_determinado — nao_determinado":
        title = "Ramo local técnico"

    return truncate(title, 110)


def build_ramo_description(group: List[MicrolinhaFeatures]) -> str:
    n = len(group)
    zone = slug_human(dominant_zone(group))
    problem = slug_human(dominant_problem(group))
    work = slug_human(dominant_work(group))
    direction = slug_human(dominant_direction(group))
    effect = slug_human(dominant_efeito(group))
    faixa = slug_human(dominant_faixa(group))
    return truncate(
        f"Unidade macro-local de {n} microlinha(s), dominada por zona {zone}, "
        f"problema {problem}, trabalho {work}, direção {direction}, "
        f"impacto {effect} e faixa local {faixa}.",
        240,
    )


def build_ramo_object(group: List[MicrolinhaFeatures], ramo_number: int) -> Dict[str, Any]:
    ramo_id = f"RA_{ramo_number:04d}"
    estado_excecao, excecao_ids = determine_ramo_estado_excecao(group)
    estado_validacao = determine_ramo_estado_validacao(group, estado_excecao)

    observacoes: List[str] = []
    if len(group) == 1:
        observacoes.append("Ramo unitário; requer consolidação posterior.")
    if excecao_ids:
        observacoes.append("Contém microlinhas com exceção ativa.")

    ramo = {
        "id": ramo_id,
        "tipo_no": "ramo",
        "titulo": build_ramo_title(group),
        "descricao_funcional": build_ramo_description(group),
        "criterio_de_unidade": choose_criterio_de_unidade(group),
        "microlinha_ids": [m.microlinha_id for m in group],
        "percurso_ids_associados": [],
        "argumento_ids_associados": [],
        "passo_ids_alvo": top_step_ids(group, limit=5),
        "convergencia_ids": [],
        "prioridade_de_consolidacao": infer_prioridade_ramo(group),
        "estado_validacao": estado_validacao,
        "estado_excecao": estado_excecao,
        "excecao_ids": excecao_ids,
        "observacoes": observacoes,
    }
    return ramo


def size_distribution(groups: List[List[MicrolinhaFeatures]]) -> Dict[int, int]:
    dist: Dict[int, int] = {}
    for group in groups:
        dist[len(group)] = dist.get(len(group), 0) + 1
    return dict(sorted(dist.items(), key=lambda kv: kv[0]))


def update_tree_with_ramos(
    tree: Dict[str, Any],
    ramos: List[Dict[str, Any]],
) -> None:
    tree["ramos"] = ramos

    fragmentos = require_list(tree.get("fragmentos"), "fragmentos")
    microlinhas = require_list(tree.get("microlinhas"), "microlinhas")

    fragment_map: Dict[str, Dict[str, Any]] = {}
    for idx, fragment in enumerate(fragmentos, start=1):
        fragment_dict = require_dict(fragment, f"fragmentos[{idx}]")
        fragment_id = require_key(fragment_dict, "id", f"fragmentos[{idx}]")
        if isinstance(fragment_id, str):
            fragment_map[fragment_id] = fragment_dict

    microlinha_map: Dict[str, Dict[str, Any]] = {}
    for idx, microlinha in enumerate(microlinhas, start=1):
        microlinha_dict = require_dict(microlinha, f"microlinhas[{idx}]")
        microlinha_id = require_key(microlinha_dict, "id", f"microlinhas[{idx}]")
        if isinstance(microlinha_id, str):
            microlinha_map[microlinha_id] = microlinha_dict

    for ramo in ramos:
        ramo_id = ramo["id"]
        microlinha_ids = ramo["microlinha_ids"]

        for ordem_no_ramo, microlinha_id in enumerate(microlinha_ids, start=1):
            microlinha_dict = microlinha_map.get(microlinha_id)
            if microlinha_dict is None:
                raise RamoGenerationError(
                    f"O ramo '{ramo_id}' refere a microlinha inexistente '{microlinha_id}'."
                )

            microlinha_dict["ordem_no_ramo"] = ordem_no_ramo

            fragmento_ids = require_list(
                require_key(microlinha_dict, "fragmento_ids", f"microlinha {microlinha_id}"),
                f"microlinha {microlinha_id}.fragmento_ids",
            )
            for fragment_id in fragmento_ids:
                fragment_dict = fragment_map.get(fragment_id)
                if fragment_dict is None:
                    raise RamoGenerationError(
                        f"A microlinha '{microlinha_id}' refere o fragmento inexistente '{fragment_id}'."
                    )
                ligacoes = require_dict(
                    require_key(fragment_dict, "ligacoes_arvore", f"fragmento {fragment_id}"),
                    f"fragmento {fragment_id}.ligacoes_arvore",
                )
                ligacoes["ramo_ids"] = [ramo_id]

    validacao = require_dict(require_key(tree, "validacao", "raiz"), "validacao")
    metricas = require_dict(require_key(validacao, "metricas", "validacao"), "validacao.metricas")
    metricas["total_ramos"] = len(ramos)

    observacoes = validacao.get("observacoes")
    if observacoes is None:
        observacoes = []
        validacao["observacoes"] = observacoes
    elif not isinstance(observacoes, list):
        raise RamoGenerationError("O campo 'validacao.observacoes' existe mas não é array/list.")

    prefixos_controlados = (
        "Ramos v1:",
        "Geração de ramos v1:",
    )
    validacao["observacoes"] = [
        item for item in observacoes
        if not (isinstance(item, str) and item.startswith(prefixos_controlados))
    ]
    observacoes = validacao["observacoes"]

    unitarios = sum(1 for r in ramos if len(r["microlinha_ids"]) == 1)
    if ramos and unitarios >= 3 and unitarios / len(ramos) >= 0.35:
        observacoes.append(
            f"Ramos v1: proporção relevante de ramos unitários ({unitarios}/{len(ramos)})."
        )


def build_report_text(
    input_path: Path,
    total_microlinhas_lidas: int,
    total_microlinhas_processadas: int,
    ramos: List[Dict[str, Any]],
    grouping_log: List[str],
    args: argparse.Namespace,
) -> str:
    now_utc = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    dist = size_distribution([[None] * len(r["microlinha_ids"]) for r in ramos])  # type: ignore[list-item]
    unitary_count = sum(1 for r in ramos if len(r["microlinha_ids"]) == 1)
    with_exceptions_count = sum(1 for r in ramos if r["estado_excecao"] != "sem_excecao")

    lines: List[str] = []
    lines.append("RELATÓRIO DE GERAÇÃO DE RAMOS V1")
    lines.append("=" * 60)
    lines.append(f"Data/hora UTC: {now_utc}")
    lines.append(f"Ficheiro atualizado: {input_path}")
    lines.append(f"Microlinhas lidas na árvore: {total_microlinhas_lidas}")
    lines.append(f"Microlinhas processadas nesta geração: {total_microlinhas_processadas}")
    lines.append(f"Modo de execução: {'teste limitado' if args.limite is not None else 'geração total'}")
    if args.limite is not None:
        lines.append(f"Limite aplicado: {args.limite}")
    lines.append(f"Reescrita forçada: {'sim' if args.forcar else 'não'}")
    lines.append("")

    lines.append("Critérios usados")
    lines.append("-" * 60)
    lines.append("1. Ordenação das microlinhas pela posição inicial do primeiro fragmento.")
    lines.append("2. Agrupamento sequencial e determinístico por compatibilidade suficiente.")
    lines.append("3. Compatibilidade por zona/problema/trabalho, movimento local, impacto no mapa e continuidade plausível.")
    lines.append("4. Fecho do ramo quando a compatibilidade cai abaixo do limiar ou quando há rutura forte.")
    lines.append(f"5. Tamanho máximo por ramo: {MAX_RAMO_SIZE} microlinhas.")
    lines.append(f"6. Distância máxima local entre microlinhas adjacentes: {MAX_ORDER_GAP}.")
    lines.append(f"7. Amplitude máxima entre a primeira microlinha do ramo e uma candidata: {MAX_FIRST_TO_CANDIDATE_GAP}.")
    lines.append("")

    lines.append("Resumo")
    lines.append("-" * 60)
    lines.append(f"Ramos gerados: {len(ramos)}")
    lines.append(f"Ramos unitários: {unitary_count}")
    lines.append(f"Ramos com exceções: {with_exceptions_count}")
    if dist:
        parts = [f"{size}: {count}" for size, count in dist.items()]
        lines.append("Distribuição de tamanhos: " + " | ".join(parts))
    else:
        lines.append("Distribuição de tamanhos: n/a")
    lines.append("")

    lines.append("Ramos gerados")
    lines.append("-" * 60)
    if not ramos:
        lines.append("Nenhum ramo gerado.")
    else:
        for ramo in ramos:
            lines.append(
                f"{ramo['id']} | n={len(ramo['microlinha_ids'])} | "
                f"{ramo['titulo']} | unidade={ramo['criterio_de_unidade']} | "
                f"estado={ramo['estado_validacao']} | excecao={ramo['estado_excecao']}"
            )
            lines.append(f"  microlinhas: {', '.join(ramo['microlinha_ids'])}")
            if ramo["passo_ids_alvo"]:
                lines.append(f"  passos-alvo: {', '.join(ramo['passo_ids_alvo'])}")
            if ramo["observacoes"]:
                for note in ramo["observacoes"]:
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
        f"Geração concluída com {len(ramos)} ramos, "
        f"{unitary_count} unitários e {with_exceptions_count} com exceções."
    )
    lines.append("")
    return "\n".join(lines)


def build_terminal_summary(
    input_path: Path,
    total_microlinhas_lidas: int,
    total_microlinhas_processadas: int,
    ramos: List[Dict[str, Any]],
    report_path: Path,
) -> str:
    unitary_count = sum(1 for r in ramos if len(r["microlinha_ids"]) == 1)
    with_exceptions_count = sum(1 for r in ramos if r["estado_excecao"] != "sem_excecao")

    lines = [
        f"Ficheiro atualizado: {input_path}",
        f"Microlinhas lidas: {total_microlinhas_lidas}",
        f"Microlinhas processadas: {total_microlinhas_processadas}",
        f"Ramos gerados: {len(ramos)}",
        f"Ramos unitários: {unitary_count}",
        f"Ramos com exceções: {with_exceptions_count}",
        "Conclusão final: geração concluída.",
        f"Relatório escrito em: {report_path}",
    ]
    return "\n".join(lines)


def ensure_tree_is_minimally_usable(tree: Dict[str, Any], args: argparse.Namespace) -> None:
    if not isinstance(tree, dict):
        raise RamoGenerationError("O ficheiro da árvore tem de ser um objeto JSON no topo.")

    required_top = [
        "fragmentos",
        "microlinhas",
        "ramos",
        "validacao",
    ]
    for key in required_top:
        if key not in tree:
            raise RamoGenerationError(f"Falta o bloco obrigatório '{key}' na árvore.")

    fragmentos = require_list(tree.get("fragmentos"), "fragmentos")
    microlinhas = require_list(tree.get("microlinhas"), "microlinhas")
    ramos = require_list(tree.get("ramos"), "ramos")

    if not microlinhas:
        raise RamoGenerationError(
            "O bloco 'microlinhas' está vazio. Gere primeiro as microlinhas."
        )

    if ramos and not args.forcar:
        raise RamoGenerationError(
            "O bloco 'ramos' já contém dados. Use --forcar para regenerar e substituir."
        )

    for idx, fragment in enumerate(fragmentos, start=1):
        fragment_dict = require_dict(fragment, f"fragmentos[{idx}]")
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

    for idx, microlinha in enumerate(microlinhas, start=1):
        microlinha_dict = require_dict(microlinha, f"microlinhas[{idx}]")
        for field in (
            "id",
            "titulo",
            "descricao_funcional",
            "criterio_de_agregacao",
            "fragmento_ids",
            "estado_validacao",
            "estado_excecao",
            "excecao_ids",
        ):
            require_key(microlinha_dict, field, f"microlinhas[{idx}]")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    script_dir = Path(__file__).resolve().parent
    paths = build_paths(script_dir)

    tree = load_json(paths["input"])
    ensure_tree_is_minimally_usable(tree, args)

    fragmentos = require_list(tree.get("fragmentos"), "fragmentos")
    microlinhas = require_list(tree.get("microlinhas"), "microlinhas")
    total_microlinhas_lidas = len(microlinhas)

    fragment_map: Dict[str, Dict[str, Any]] = {}
    for idx, fragment in enumerate(fragmentos, start=1):
        fragment_dict = require_dict(fragment, f"fragmentos[{idx}]")
        fragment_id = require_key(fragment_dict, "id", f"fragmentos[{idx}]")
        if isinstance(fragment_id, str):
            fragment_map[fragment_id] = fragment_dict

    clear_all_ramo_links(tree)

    features: List[MicrolinhaFeatures] = []
    for idx, microlinha in enumerate(microlinhas, start=1):
        microlinha_dict = require_dict(microlinha, f"microlinhas[{idx}]")
        features.append(extract_microlinha_features(microlinha_dict, idx, fragment_map))

    features = sort_microlinha_features(features)
    if args.limite is not None:
        features = features[: args.limite]

    groups, grouping_log = generate_ramo_groups(features)
    ramos = [
        build_ramo_object(group, ramo_number=i)
        for i, group in enumerate(groups, start=1)
    ]

    update_tree_with_ramos(tree, ramos)
    save_json_atomic(paths["input"], tree)

    report_text = build_report_text(
        input_path=paths["input"],
        total_microlinhas_lidas=total_microlinhas_lidas,
        total_microlinhas_processadas=len(features),
        ramos=ramos,
        grouping_log=grouping_log,
        args=args,
    )
    write_text(paths["report"], report_text)

    print(
        build_terminal_summary(
            input_path=paths["input"],
            total_microlinhas_lidas=total_microlinhas_lidas,
            total_microlinhas_processadas=len(features),
            ramos=ramos,
            report_path=paths["report"],
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RamoGenerationError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)