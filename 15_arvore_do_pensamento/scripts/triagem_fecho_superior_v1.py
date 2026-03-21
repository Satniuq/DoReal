# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

INPUT_TREE_FILENAME = "arvore_do_pensamento_v1.json"
INPUT_REPORT_GERACAO_PERCURSOS = "relatorio_geracao_percursos_v1.txt"
INPUT_REPORT_VALIDACAO_PERCURSOS = "relatorio_validacao_percursos_v1.txt"
INPUT_REPORT_GERACAO_ARGUMENTOS = "relatorio_geracao_argumentos_v1.txt"
INPUT_REPORT_VALIDACAO_ARGUMENTOS = "relatorio_validacao_argumentos_v1.txt"

OUTPUT_JSON_FILENAME = "triagem_fecho_superior_v1.json"
OUTPUT_REPORT_FILENAME = "relatorio_triagem_fecho_superior_v1.txt"

RAMO_ID_RE = re.compile(r"\b(RA_\d{4})\b")
PERCURSO_ID_RE = re.compile(r"\b(P_[A-Z0-9_]+)\b")
ARGUMENTO_ID_RE = re.compile(r"\b(ARG_[A-Z0-9_]+)\b")
WARNING_LINE_RE = re.compile(
    r"^-\s*(RA_\d{4})\s*->\s*(.*?)\s*\[([A-Za-z_]+)\]:\s*(.*)$"
)


class TriagemFechoSuperiorError(RuntimeError):
    """Erro fatal na triagem do fecho superior."""


def build_paths(script_dir: Path) -> Dict[str, Path]:
    arvore_root = script_dir.parent
    dados_dir = arvore_root / "01_dados"
    return {
        "script_dir": script_dir,
        "arvore_root": arvore_root,
        "dados_dir": dados_dir,
        "input_tree": dados_dir / INPUT_TREE_FILENAME,
        "report_geracao_percursos": dados_dir / INPUT_REPORT_GERACAO_PERCURSOS,
        "report_validacao_percursos": dados_dir / INPUT_REPORT_VALIDACAO_PERCURSOS,
        "report_geracao_argumentos": dados_dir / INPUT_REPORT_GERACAO_ARGUMENTOS,
        "report_validacao_argumentos": dados_dir / INPUT_REPORT_VALIDACAO_ARGUMENTOS,
        "output_json": dados_dir / OUTPUT_JSON_FILENAME,
        "output_report": dados_dir / OUTPUT_REPORT_FILENAME,
    }


def ensure_required_files(paths: Dict[str, Path]) -> None:
    required = [
        paths["input_tree"],
        paths["report_geracao_percursos"],
        paths["report_validacao_percursos"],
        paths["report_geracao_argumentos"],
        paths["report_validacao_argumentos"],
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise TriagemFechoSuperiorError(
            "Faltam ficheiros obrigatórios para a triagem:\n- " + "\n- ".join(missing)
        )


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise TriagemFechoSuperiorError(f"Ficheiro não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TriagemFechoSuperiorError(f"JSON inválido em {path}: {exc}") from exc
    except OSError as exc:
        raise TriagemFechoSuperiorError(f"Não foi possível ler {path}: {exc}") from exc


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise TriagemFechoSuperiorError(f"Ficheiro não encontrado: {path}") from exc
    except OSError as exc:
        raise TriagemFechoSuperiorError(f"Não foi possível ler {path}: {exc}") from exc


def save_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        temp_path.replace(path)
    except OSError as exc:
        raise TriagemFechoSuperiorError(f"Não foi possível escrever {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as exc:
        raise TriagemFechoSuperiorError(f"Não foi possível escrever o relatório {path}: {exc}") from exc


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
        result: List[str] = []
        for item in value:
            if isinstance(item, str):
                stripped = item.strip()
                if stripped:
                    result.append(stripped)
        return unique_preserve_order(result)
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
            values = safe_list_of_strings(mapping.get(key))
            if values:
                return values
            if isinstance(mapping.get(key), list):
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
        if "percurso_ids_associados" in item or "argumento_ids_associados" in item:
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
        candidate_id = first_nonempty_string(item, ("id",))
        if candidate_id and candidate_id.startswith(id_prefix):
            matched += 1
    return checked > 0 and matched >= max(1, checked // 2)


def locate_ramos(tree: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    preferred_keys = ("ramos", "nos_ramo", "bloco_ramos")
    for key in preferred_keys:
        value = tree.get(key)
        if looks_like_ramos_list(value):
            return value, f"raiz.{key}"

    for trail, value in iter_object_graph(tree):
        if trail == "raiz":
            continue
        if looks_like_ramos_list(value):
            return value, trail

    raise TriagemFechoSuperiorError(
        "Não foi possível localizar um bloco de ramos utilizável na árvore. "
        "A triagem exige uma árvore com a camada de ramos já gerada."
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


def build_reverse_ramo_index(
    section_items: List[Dict[str, Any]],
    ramo_id_keys: Sequence[str],
) -> Dict[str, List[str]]:
    reverse: Dict[str, List[str]] = {}
    for item in section_items:
        item_id = first_nonempty_string(item, ("id",))
        if not item_id:
            continue
        ramo_ids = get_first_list_of_strings(item, ramo_id_keys)
        for ramo_id in ramo_ids:
            reverse.setdefault(ramo_id, []).append(item_id)
    for ramo_id, ids in reverse.items():
        reverse[ramo_id] = unique_preserve_order(ids)
    return reverse


def parse_generation_association_report(text: str, target: str) -> Dict[str, Any]:
    if target not in {"percurso", "argumento"}:
        raise ValueError("target inválido")

    pattern = PERCURSO_ID_RE if target == "percurso" else ARGUMENTO_ID_RE
    lower_empty = "sem associação suficiente"

    in_log = False
    mapped: Dict[str, List[str]] = {}
    sem_associacao: Set[str] = set()
    total_ra_lines = 0

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

        match = re.match(r"^(RA_\d{4})\s*->\s*(.+)$", line)
        if not match:
            continue

        ramo_id = match.group(1)
        rhs = match.group(2).strip()
        total_ra_lines += 1

        if lower_empty in rhs.lower():
            sem_associacao.add(ramo_id)
            mapped.setdefault(ramo_id, [])
            continue

        ids = pattern.findall(rhs)
        if ids:
            mapped.setdefault(ramo_id, []).extend(ids)
        else:
            mapped.setdefault(ramo_id, [])

    for ramo_id, ids in mapped.items():
        mapped[ramo_id] = unique_preserve_order(ids)

    limitacoes: List[str] = []
    if total_ra_lines == 0:
        limitacoes.append(
            f"Não foram encontradas linhas ramo→{target} no bloco 'Log de associações'."
        )

    return {
        "target": target,
        "associacoes_por_ramo": mapped,
        "ramos_sem_associacao": sorted(sem_associacao, key=ramo_sort_key),
        "linhas_ramo_detectadas": total_ra_lines,
        "ramos_com_mapeamento": len(mapped),
        "limitacoes": limitacoes,
    }


def parse_validation_argumentos_report(text: str) -> Dict[str, Any]:
    warnings_by_ramo: Dict[str, List[Dict[str, Any]]] = {}
    warning_types_counter: Dict[str, int] = {}
    total_warning_lines = 0

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

    limitacoes: List[str] = []
    if total_warning_lines == 0:
        limitacoes.append(
            "Não foram encontradas linhas de aviso ramo→argumento no formato esperado."
        )

    return {
        "warnings_por_ramo": warnings_by_ramo,
        "total_warning_lines": total_warning_lines,
        "warning_types_counter": warning_types_counter,
        "limitacoes": limitacoes,
    }


def extract_count(text: str, label: str) -> Optional[int]:
    pattern = re.compile(rf"{re.escape(label)}\s*:\s*(\d+)")
    match = pattern.search(text)
    return int(match.group(1)) if match else None


def build_report_extraction_summary(
    geracao_percursos: Dict[str, Any],
    validacao_percursos_text: str,
    geracao_argumentos: Dict[str, Any],
    validacao_argumentos: Dict[str, Any],
) -> Dict[str, Any]:
    resumo = {
        "relatorio_geracao_percursos_v1.txt": {
            "ramos_com_mapeamento": geracao_percursos["ramos_com_mapeamento"],
            "linhas_ramo_detectadas": geracao_percursos["linhas_ramo_detectadas"],
            "ramos_sem_associacao_explicitados": len(geracao_percursos["ramos_sem_associacao"]),
            "limitacoes": geracao_percursos["limitacoes"],
        },
        "relatorio_validacao_percursos_v1.txt": {
            "ramos_sem_percurso_contagem_global": extract_count(validacao_percursos_text, "Ramos sem percurso"),
            "ramos_com_percurso_contagem_global": extract_count(validacao_percursos_text, "Ramos associados a pelo menos um percurso"),
            "ramos_com_avisos_mapeados": len(set(RAMO_ID_RE.findall(validacao_percursos_text))),
            "limitacoes": [
                "A validação de percursos pode trazer apenas contagens globais, sem sempre listar cada ramo individualmente."
            ],
        },
        "relatorio_geracao_argumentos_v1.txt": {
            "ramos_com_mapeamento": geracao_argumentos["ramos_com_mapeamento"],
            "linhas_ramo_detectadas": geracao_argumentos["linhas_ramo_detectadas"],
            "ramos_sem_associacao_explicitados": len(geracao_argumentos["ramos_sem_associacao"]),
            "limitacoes": geracao_argumentos["limitacoes"],
        },
        "relatorio_validacao_argumentos_v1.txt": {
            "ramos_com_avisos_mapeados": len(validacao_argumentos["warnings_por_ramo"]),
            "linhas_de_aviso_mapeadas": validacao_argumentos["total_warning_lines"],
            "tipos_de_aviso": validacao_argumentos["warning_types_counter"],
            "limitacoes": validacao_argumentos["limitacoes"],
        },
    }

    limitacoes_globais: List[str] = []
    if resumo["relatorio_validacao_percursos_v1.txt"]["ramos_com_avisos_mapeados"] == 0:
        limitacoes_globais.append(
            "O relatório de validação de percursos não forneceu, com o parser prudente atual, uma listagem ramo a ramo utilizável; foi usado sobretudo para contagens globais."
        )
    if resumo["relatorio_validacao_argumentos_v1.txt"]["linhas_de_aviso_mapeadas"] == 0:
        limitacoes_globais.append(
            "O relatório de validação de argumentos não expôs avisos ramo a ramo no formato esperado; a triagem ficou então mais dependente da estrutura e do relatório de geração."
        )

    resumo["limitacoes_globais"] = limitacoes_globais
    return resumo


def build_ramo_profiles(
    tree: Dict[str, Any],
    ramos: List[Dict[str, Any]],
    percursos: List[Dict[str, Any]],
    argumentos: List[Dict[str, Any]],
    geracao_percursos: Dict[str, Any],
    geracao_argumentos: Dict[str, Any],
    validacao_argumentos: Dict[str, Any],
) -> List[Dict[str, Any]]:
    reverse_percursos = build_reverse_ramo_index(
        percursos,
        ramo_id_keys=("ramo_ids", "ramo_ids_associados"),
    )
    reverse_argumentos = build_reverse_ramo_index(
        argumentos,
        ramo_id_keys=("ramo_ids", "ramo_ids_associados"),
    )

    profiles: List[Dict[str, Any]] = []

    for idx, ramo in enumerate(ramos, start=1):
        if not isinstance(ramo, dict):
            raise TriagemFechoSuperiorError(
                f"Elemento inválido em ramos[{idx}]: esperado dict, obtido {type(ramo).__name__}."
            )

        ramo_id = first_nonempty_string(ramo, ("id", "ramo_id"))
        if not ramo_id:
            raise TriagemFechoSuperiorError(f"Falta 'id' utilizável em ramos[{idx}].")

        microlinha_ids = get_first_list_of_strings(ramo, ("microlinha_ids", "microlinhas_ids"))

        percurso_ids_estrutura = get_first_list_of_strings(
            ramo,
            (
                "percurso_ids_associados",
                "percurso_ids",
                "percursos_associados",
                "percursos_ids",
            ),
        )
        if not percurso_ids_estrutura:
            percurso_ids_estrutura = reverse_percursos.get(ramo_id, [])

        argumento_ids_estrutura = get_first_list_of_strings(
            ramo,
            (
                "argumento_ids_associados",
                "argumento_ids",
                "argumentos_associados",
                "argumentos_ids",
            ),
        )
        if not argumento_ids_estrutura:
            argumento_ids_estrutura = reverse_argumentos.get(ramo_id, [])

        percurso_ids_relatorio = geracao_percursos["associacoes_por_ramo"].get(ramo_id, [])
        argumento_ids_relatorio = geracao_argumentos["associacoes_por_ramo"].get(ramo_id, [])
        warnings_argumento = validacao_argumentos["warnings_por_ramo"].get(ramo_id, [])

        divergencias: List[str] = []
        if percurso_ids_relatorio and set(percurso_ids_estrutura) != set(percurso_ids_relatorio):
            divergencias.append("divergencia_estrutura_relatorio_percursos")
        if argumento_ids_relatorio and set(argumento_ids_estrutura) != set(argumento_ids_relatorio):
            divergencias.append("divergencia_estrutura_relatorio_argumentos")

        profiles.append(
            {
                "ramo_id": ramo_id,
                "microlinha_ids": microlinha_ids,
                "n_microlinhas": len(microlinha_ids),
                "percurso_ids": unique_preserve_order(percurso_ids_estrutura),
                "argumento_ids": unique_preserve_order(argumento_ids_estrutura),
                "n_percursos": len(unique_preserve_order(percurso_ids_estrutura)),
                "n_argumentos": len(unique_preserve_order(argumento_ids_estrutura)),
                "percurso_ids_relatorio": unique_preserve_order(percurso_ids_relatorio),
                "argumento_ids_relatorio": unique_preserve_order(argumento_ids_relatorio),
                "warnings_argumento": warnings_argumento,
                "divergencias": divergencias,
                "observacoes_ramo": safe_list_of_strings(ramo.get("observacoes", [])),
                "estado_validacao": first_nonempty_string(ramo, ("estado_validacao",)) or "desconhecido",
                "raw": ramo,
            }
        )

    return sorted(profiles, key=lambda item: ramo_sort_key(item["ramo_id"]))


def classify_ramo(profile: Dict[str, Any]) -> Dict[str, Any]:
    ramo_id = profile["ramo_id"]
    percurso_ids = profile["percurso_ids"]
    argumento_ids = profile["argumento_ids"]
    n_percursos = profile["n_percursos"]
    n_argumentos = profile["n_argumentos"]
    warnings_argumento = profile["warnings_argumento"]
    divergencias = profile["divergencias"]

    motivos: List[str] = []
    factos_estrutura: List[str] = []
    factos_relatorios: List[str] = []
    inferencias_prudentes: List[str] = []

    factos_estrutura.append(f"n_percursos={n_percursos}")
    factos_estrutura.append(f"n_argumentos={n_argumentos}")
    if profile["n_microlinhas"]:
        factos_estrutura.append(f"n_microlinhas={profile['n_microlinhas']}")

    for warning in warnings_argumento:
        tipo = warning.get("tipo")
        if isinstance(tipo, str) and tipo:
            motivos.append(tipo)
            factos_relatorios.append(f"aviso_validacao_argumentos:{tipo}")

    if n_argumentos > 2:
        motivos.append("mais_de_2_argumentos")
        inferencias_prudentes.append(
            "Estrutura local sugere inflação argumentativa simples: o ramo tem mais de dois argumentos associados."
        )

    for divergencia in divergencias:
        motivos.append(divergencia)
        factos_relatorios.append(divergencia)

    if n_percursos == 0 and n_argumentos == 0:
        grupo_key = "C_sem_subida_nesta_ronda"
        motivos.insert(0, "sem_percurso_sem_argumento")
        factos_estrutura.append("ramo_sem_subida_superior_na_estrutura")

    elif n_percursos > 0 and n_argumentos == 0:
        grupo_key = "B_rever_percurso_e_depois_argumento"
        motivos.insert(0, "tem_percurso_sem_argumento")
        factos_estrutura.append("ramo_tem_percurso_sem_argumento")

    elif n_percursos > 0 and n_argumentos > 0:
        review_triggers = {
            "plausibilidade",
            "heterogeneidade_excessiva",
            "associacao_fraca",
            "mais_de_2_argumentos",
            "divergencia_estrutura_relatorio_percursos",
            "divergencia_estrutura_relatorio_argumentos",
        }
        if any(motivo in review_triggers for motivo in motivos):
            grupo_key = "A_rever_argumento"
            factos_estrutura.append("ramo_com_percurso_e_argumento_mas_com_sinal_de_revisao")
        else:
            grupo_key = "D_fora_do_ambito_desta_ronda"
            motivos = ["estavel_nesta_fase"]
            factos_estrutura.append("ramo_com_percurso_e_argumento_sem_sinais_de_revisao")

    else:
        grupo_key = "A_rever_argumento"
        motivos.insert(0, "anomalia_argumento_sem_percurso")
        inferencias_prudentes.append(
            "Foi detetado pelo menos um argumento associado sem percurso associado. "
            "O ramo entra em revisão por prudência, sem assumir explicação adicional não suportada."
        )

    motivos = unique_preserve_order(motivos) or ["classificacao_sem_motivo_expresso"]

    return {
        "ramo_id": ramo_id,
        "grupo": grupo_key,
        "n_microlinhas": profile["n_microlinhas"],
        "microlinha_ids": profile["microlinha_ids"],
        "n_percursos": n_percursos,
        "n_argumentos": n_argumentos,
        "associacoes": {
            "percurso_ids": percurso_ids,
            "argumento_ids": argumento_ids,
        },
        "motivos": motivos,
        "evidencias": {
            "factos_estrutura": unique_preserve_order(factos_estrutura),
            "factos_relatorios": unique_preserve_order(factos_relatorios),
            "inferencias_prudentes": unique_preserve_order(inferencias_prudentes),
        },
        "sinais_relatorios": {
            "percurso_ids_log_geracao": profile["percurso_ids_relatorio"],
            "argumento_ids_log_geracao": profile["argumento_ids_relatorio"],
            "avisos_validacao_argumentos": [
                {
                    "tipo": warning.get("tipo"),
                    "descricao": warning.get("descricao"),
                    "argumento_ids": warning.get("argumento_ids", []),
                }
                for warning in profile["warnings_argumento"]
            ],
        },
        "estado_validacao_ramo": profile["estado_validacao"],
        "observacoes_ramo": profile["observacoes_ramo"],
    }


def build_triagem_payload(
    classifications: List[Dict[str, Any]],
    paths: Dict[str, Path],
    extraction_summary: Dict[str, Any],
) -> Dict[str, Any]:
    grupos: Dict[str, List[Dict[str, Any]]] = {
        "A_rever_argumento": [],
        "B_rever_percurso_e_depois_argumento": [],
        "C_sem_subida_nesta_ronda": [],
        "D_fora_do_ambito_desta_ronda": [],
    }

    for item in classifications:
        grupo_key = item["grupo"]
        grupos[grupo_key].append(item)

    for key in grupos:
        grupos[key] = sorted(grupos[key], key=lambda item: ramo_sort_key(item["ramo_id"]))

    resumo = {
        "A": len(grupos["A_rever_argumento"]),
        "B": len(grupos["B_rever_percurso_e_depois_argumento"]),
        "C": len(grupos["C_sem_subida_nesta_ronda"]),
        "D": len(grupos["D_fora_do_ambito_desta_ronda"]),
    }
    total_ramos = sum(resumo.values())

    fila_operacional = {
        "rever_percurso_primeiro": [
            item["ramo_id"]
            for item in grupos["B_rever_percurso_e_depois_argumento"]
        ] + [
            item["ramo_id"]
            for item in grupos["A_rever_argumento"]
            if "anomalia_argumento_sem_percurso" in item["motivos"]
        ],
        "rever_argumento_apos_percurso": [
            item["ramo_id"] for item in grupos["A_rever_argumento"]
        ] + [
            item["ramo_id"] for item in grupos["B_rever_percurso_e_depois_argumento"]
        ],
        "marcar_sem_subida_nesta_ronda": [
            item["ramo_id"] for item in grupos["C_sem_subida_nesta_ronda"]
        ],
        "fora_do_ambito": [
            item["ramo_id"] for item in grupos["D_fora_do_ambito_desta_ronda"]
        ],
    }
    for key in fila_operacional:
        fila_operacional[key] = sorted(unique_preserve_order(fila_operacional[key]), key=ramo_sort_key)

    manual_review = sorted(
        unique_preserve_order(
            [
                item["ramo_id"]
                for item in classifications
                if (
                    item["evidencias"]["inferencias_prudentes"]
                    or any(m.startswith("divergencia_") for m in item["motivos"])
                    or "anomalia_argumento_sem_percurso" in item["motivos"]
                )
            ]
        ),
        key=ramo_sort_key,
    )

    triagem_fechada = total_ramos > 0 and total_ramos == len(classifications)

    return {
        "metadata": {
            "script": "triagem_fecho_superior_v1.py",
            "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "total_ramos": total_ramos,
            "ficheiros_lidos": {
                "arvore": str(paths["input_tree"]),
                "relatorio_geracao_percursos": str(paths["report_geracao_percursos"]),
                "relatorio_validacao_percursos": str(paths["report_validacao_percursos"]),
                "relatorio_geracao_argumentos": str(paths["report_geracao_argumentos"]),
                "relatorio_validacao_argumentos": str(paths["report_validacao_argumentos"]),
            },
            "ficheiros_escritos": {
                "triagem_json": str(paths["output_json"]),
                "relatorio_txt": str(paths["output_report"]),
            },
        },
        "criterios_aplicados": {
            "regras_classificacao": [
                "Regra 1: sem percurso e sem argumento -> Grupo C.",
                "Regra 2: com percurso e sem argumento -> Grupo B.",
                "Regra 3: com percurso e com argumento -> Grupo D por defeito.",
                "Regra 4: sinais de plausibilidade, heterogeneidade, associação fraca, divergência estrutural ou mais de 2 argumentos -> Grupo A.",
                "Regra 5: na dúvida, revisão conservadora, sem inventar justificação factual.",
            ],
            "criterios_deteccao_inflacao_argumentativa": [
                "mais_de_2_argumentos_associados_ao_mesmo_ramo",
                "avisos_textuais_de_heterogeneidade_excessiva",
                "avisos_textuais_de_associacao_fraca",
                "avisos_textuais_de_plausibilidade",
                "divergencia_entre_estrutura_da_arvore_e_relatorios_de_geracao",
            ],
            "politica_de_prudencia": "Na dúvida, preferir revisão, mas apenas com base em factos extraídos ou inferências prudentes explicitadas.",
        },
        "extracao_relatorios": extraction_summary,
        "grupos": grupos,
        "fila_operacional": fila_operacional,
        "resumo": resumo,
        "observacoes_finais": {
            "triagem_fechada_para_script_seguinte": triagem_fechada,
            "ramos_com_revisao_manual_recomendada": manual_review,
            "nota": (
                "A triagem fica operacionalmente fechada se todos os ramos foram classificados exatamente num grupo. "
                "O script seguinte de revisão de percursos superiores deve começar pela fila 'rever_percurso_primeiro'."
            ),
        },
    }


def build_human_report(payload: Dict[str, Any], ramos_path_location: str, percursos_path_location: Optional[str], argumentos_path_location: Optional[str]) -> str:
    metadata = payload["metadata"]
    grupos = payload["grupos"]
    resumo = payload["resumo"]
    extracao = payload["extracao_relatorios"]

    lines: List[str] = []
    lines.append("RELATÓRIO DE TRIAGEM DO FECHO SUPERIOR V1")
    lines.append("=" * 72)
    lines.append(f"Data/hora UTC: {metadata['timestamp_utc']}")
    lines.append(f"Script: {metadata['script']}")
    lines.append(f"Bloco de ramos localizado em: {ramos_path_location}")
    lines.append(f"Bloco de percursos localizado em: {percursos_path_location or 'não localizado / não usado'}")
    lines.append(f"Bloco de argumentos localizado em: {argumentos_path_location or 'não localizado / não usado'}")
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
    lines.append(f"Número total de ramos: {metadata['total_ramos']}")
    lines.append(f"Grupo A — rever argumento: {resumo['A']}")
    lines.append(f"Grupo B — rever percurso e depois argumento: {resumo['B']}")
    lines.append(f"Grupo C — sem subida nesta ronda: {resumo['C']}")
    lines.append(f"Grupo D — fora do âmbito desta ronda: {resumo['D']}")
    lines.append("")

    lines.append("Critérios aplicados")
    lines.append("-" * 72)
    for rule in payload["criterios_aplicados"]["regras_classificacao"]:
        lines.append(f"- {rule}")
    lines.append("")
    lines.append("Critérios de deteção de inflação argumentativa")
    lines.append("-" * 72)
    for item in payload["criterios_aplicados"]["criterios_deteccao_inflacao_argumentativa"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("Extração dos relatórios")
    lines.append("-" * 72)
    for report_name, report_data in extracao.items():
        if report_name == "limitacoes_globais":
            continue
        lines.append(report_name)
        for key, value in report_data.items():
            if key == "limitacoes":
                continue
            lines.append(f"  - {key}: {value}")
        if report_data.get("limitacoes"):
            lines.append("  - limitações:")
            for item in report_data["limitacoes"]:
                lines.append(f"      * {item}")
    if extracao.get("limitacoes_globais"):
        lines.append("")
        lines.append("Limitações globais da extração")
        lines.append("-" * 72)
        for item in extracao["limitacoes_globais"]:
            lines.append(f"- {item}")
    lines.append("")

    group_titles = {
        "A_rever_argumento": "Grupo A — rever argumento",
        "B_rever_percurso_e_depois_argumento": "Grupo B — rever percurso e depois argumento",
        "C_sem_subida_nesta_ronda": "Grupo C — sem subida nesta ronda",
        "D_fora_do_ambito_desta_ronda": "Grupo D — fora do âmbito desta ronda",
    }

    for group_key in (
        "A_rever_argumento",
        "B_rever_percurso_e_depois_argumento",
        "C_sem_subida_nesta_ronda",
        "D_fora_do_ambito_desta_ronda",
    ):
        lines.append(group_titles[group_key])
        lines.append("-" * 72)
        items = grupos[group_key]
        if not items:
            lines.append("Nenhum ramo neste grupo.")
            lines.append("")
            continue

        for item in items:
            lines.append(
                f"{item['ramo_id']} | microlinhas={item['n_microlinhas']} | "
                f"percursos={item['n_percursos']} | argumentos={item['n_argumentos']} | "
                f"motivos={', '.join(item['motivos'])}"
            )
            lines.append(
                f"  percurso_ids: {', '.join(item['associacoes']['percurso_ids']) if item['associacoes']['percurso_ids'] else '∅'}"
            )
            lines.append(
                f"  argumento_ids: {', '.join(item['associacoes']['argumento_ids']) if item['associacoes']['argumento_ids'] else '∅'}"
            )
            if item["evidencias"]["factos_relatorios"]:
                lines.append(
                    "  factos_relatorios: " + ", ".join(item["evidencias"]["factos_relatorios"])
                )
            if item["evidencias"]["inferencias_prudentes"]:
                lines.append(
                    "  inferencias_prudentes: " + " | ".join(item["evidencias"]["inferencias_prudentes"])
                )
        lines.append("")

    lines.append("Observações finais")
    lines.append("-" * 72)
    triagem_fechada = payload["observacoes_finais"]["triagem_fechada_para_script_seguinte"]
    lines.append(
        "A triagem ficou suficientemente fechada para alimentar o script seguinte: "
        + ("sim" if triagem_fechada else "não")
    )
    manual = payload["observacoes_finais"]["ramos_com_revisao_manual_recomendada"]
    lines.append(
        "Ramos com revisão manual recomendada: "
        + (", ".join(manual) if manual else "nenhum")
    )
    lines.append(
        "Fila inicial para o script seguinte (revisão de percursos superiores): "
        + (
            ", ".join(payload["fila_operacional"]["rever_percurso_primeiro"])
            if payload["fila_operacional"]["rever_percurso_primeiro"]
            else "nenhuma"
        )
    )
    lines.append(
        "Casos ainda potencialmente manuais: divergências entre árvore e relatórios, anomalias argumento sem percurso, ou avisos extraídos parcialmente dos relatórios."
    )
    lines.append("")

    return "\n".join(lines)


def terminal_summary(payload: Dict[str, Any], output_json: Path, output_report: Path) -> str:
    resumo = payload["resumo"]
    lines = [
        f"Ramos triados: {payload['metadata']['total_ramos']}",
        f"Grupo A: {resumo['A']}",
        f"Grupo B: {resumo['B']}",
        f"Grupo C: {resumo['C']}",
        f"Grupo D: {resumo['D']}",
        f"JSON escrito em: {output_json}",
        f"Relatório escrito em: {output_report}",
    ]
    return "\n".join(lines)


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    paths = build_paths(script_dir)
    ensure_required_files(paths)

    tree = load_json(paths["input_tree"])
    if not isinstance(tree, dict):
        raise TriagemFechoSuperiorError("O ficheiro da árvore tem de ser um objeto JSON no topo.")

    ramos, ramos_location = locate_ramos(tree)
    if not ramos:
        raise TriagemFechoSuperiorError(
            "O bloco de ramos foi localizado, mas está vazio. Gere primeiro a camada de ramos."
        )

    percursos, percursos_location = locate_optional_section(tree, ("percursos",), id_prefix="P_")
    argumentos, argumentos_location = locate_optional_section(tree, ("argumentos",), id_prefix="ARG_")

    geracao_percursos_text = load_text(paths["report_geracao_percursos"])
    validacao_percursos_text = load_text(paths["report_validacao_percursos"])
    geracao_argumentos_text = load_text(paths["report_geracao_argumentos"])
    validacao_argumentos_text = load_text(paths["report_validacao_argumentos"])

    geracao_percursos = parse_generation_association_report(geracao_percursos_text, target="percurso")
    geracao_argumentos = parse_generation_association_report(geracao_argumentos_text, target="argumento")
    validacao_argumentos = parse_validation_argumentos_report(validacao_argumentos_text)
    extraction_summary = build_report_extraction_summary(
        geracao_percursos=geracao_percursos,
        validacao_percursos_text=validacao_percursos_text,
        geracao_argumentos=geracao_argumentos,
        validacao_argumentos=validacao_argumentos,
    )

    profiles = build_ramo_profiles(
        tree=tree,
        ramos=ramos,
        percursos=percursos,
        argumentos=argumentos,
        geracao_percursos=geracao_percursos,
        geracao_argumentos=geracao_argumentos,
        validacao_argumentos=validacao_argumentos,
    )
    classifications = [classify_ramo(profile) for profile in profiles]

    payload = build_triagem_payload(
        classifications=classifications,
        paths=paths,
        extraction_summary=extraction_summary,
    )
    report_text = build_human_report(
        payload=payload,
        ramos_path_location=ramos_location,
        percursos_path_location=percursos_location,
        argumentos_path_location=argumentos_location,
    )

    save_json_atomic(paths["output_json"], payload)
    write_text(paths["output_report"], report_text)

    print(terminal_summary(payload, paths["output_json"], paths["output_report"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TriagemFechoSuperiorError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)