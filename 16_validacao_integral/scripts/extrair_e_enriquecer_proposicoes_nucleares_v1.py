#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
extrair_e_enriquecer_proposicoes_nucleares_v1.py

Extrai as proposições nucleares do mapa dedutivo final e enriquece cada
proposição com dependências dedutivas, rastreabilidade arquitetural e
estrutura-base para a fase pós-árvore.

Outputs:
- 16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json
- 16_validacao_integral/02_outputs/relatorio_extracao_e_enriquecimento_proposicoes_v1.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict, deque
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


# =============================================================================
# CONFIGURAÇÃO CANÓNICA
# =============================================================================

DEFAULT_MAP_RELATIVE = Path(
    "14_mapa_dedutivo/02_fecho_canonico_mapa/outputs/versoes_finais/mapa_dedutivo_canonico_final__vfinal_corrente.json"
)
DEFAULT_TREE_RELATIVE = Path(
    "15_arvore_do_pensamento/01_dados/arvore_do_pensamento_v1_fecho_superior.json"
)
DEFAULT_IMPACT_RELATIVE = Path(
    "14_mapa_dedutivo/impacto_fragmentos_no_mapa.json"
)
DEFAULT_ARCH_RELATIVE = Path(
    "14_mapa_dedutivo/02_mapa_dedutivo_arquitetura_fragmentos.json"
)
DEFAULT_ARGUMENTOS_RELATIVE = Path(
    "13_Meta_Indice/indice/argumentos/argumentos_unificados.json"
)
DEFAULT_INDICE_PERCURSOS_RELATIVE = Path(
    "13_Meta_Indice/indice/indice_por_percurso.json"
)

OUTPUT_JSON_RELATIVE = Path(
    "16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json"
)
OUTPUT_REPORT_RELATIVE = Path(
    "16_validacao_integral/02_outputs/relatorio_extracao_e_enriquecimento_proposicoes_v1.txt"
)

ENUMS_DOCUMENTADOS: Dict[str, List[str]] = {
    "estado_global": [
        "em_construcao",
        "extraido",
        "enriquecido",
        "atribuido",
        "validado",
        "integrado",
    ],
    "tipo_fonte_auxiliar": [
        "impacto_no_mapa",
        "indice_percursos",
        "argumentos_unificados",
        "convergencias",
        "relacoes",
        "relatorio_validacao",
        "outro",
    ],
    "estado_proposicao": [
        "ativa",
        "reformulada",
        "desdobrada",
        "suspensa",
    ],
    "grau_rastreabilidade": [
        "baixo",
        "medio",
        "alto",
        "muito_alto",
    ],
    "dominio_principal": [
        "ontologia",
        "metafisica",
        "epistemologia",
        "filosofia_da_mente",
        "filosofia_da_linguagem",
        "antropologia_filosofica",
        "etica",
        "axiologia",
        "filosofia_da_ciencia",
        "filosofia_da_biologia",
        "filosofia_social",
        "integrativo",
    ],
    "tipo_formulacao": [
        "proposicao_fundacional",
        "proposicao_derivada",
        "proposicao_transicional",
        "proposicao_definicional",
        "proposicao_criteriologica",
        "proposicao_normativa",
        "proposicao_integrativa",
    ],
    "funcao_no_mapa": [
        "fundamento",
        "articulacao",
        "transicao",
        "definicao",
        "criterio",
        "derivacao",
        "fecho",
        "integracao",
    ],
    "tipo_de_proposicao": [
        "ontologica_fundacional",
        "ontologica_estrutural",
        "ontologica_dinamica",
        "fenomenologico_descritiva",
        "transcendental_operativa",
        "antropologica_estrutural",
        "epistemologica_criteriologica",
        "epistemologica_corretiva",
        "etica_derivada",
        "normativa_derivada",
        "integrativa_entre_niveis",
        "cientifico_material_dependente",
    ],
    "regime_de_validacao": [
        "coerencia_dedutiva_interna",
        "rastreabilidade_arquitetural",
        "confronto_filosofico",
        "compatibilidade_cientifica",
        "ancoragem_cientifica_forte",
        "justificacao_de_ponte",
        "cartografia_de_campo",
        "reformulacao_conceitual",
        "validacao_integrativa",
    ],
    "grau_risco_salto": [
        "baixo",
        "medio",
        "alto",
        "critico",
    ],
    "grau_prioridade": [
        "baixa",
        "media",
        "alta",
        "estrutural",
    ],
    "campo_do_real": [
        "fisico",
        "quimico",
        "biologico",
        "ecologico",
        "sensorio_motor",
        "cognitivo_representacional",
        "simbolico_linguistico",
        "intersubjetivo_social",
        "tecnico",
        "pratico_normativo",
        "historico_cultural",
        "integral_multicampo",
    ],
    "escala_ontologica": [
        "microfisica",
        "fisica_mesoscopica",
        "quimica_molecular",
        "celular",
        "organismo",
        "ecossistema",
        "agente",
        "sujeito_encarnado",
        "grupo_social",
        "instituicao",
        "cultura",
        "escala_multinivel",
    ],
    "nivel_de_realidade_implicado": [
        "materia",
        "estrutura",
        "vida",
        "sensibilidade",
        "cognicao",
        "representacao",
        "linguagem",
        "acao",
        "normatividade",
        "valor",
        "coexistencia",
    ],
    "nivel_ponte": [
        "ontologia_geral",
        "ontologia_estrutural",
        "ontologia_dinamica",
        "biologia_do_organismo",
        "ciencia_cognitiva",
        "linguagem_simbolica",
        "vida_social",
        "acao_pratica",
        "normatividade_etica",
    ],
    "tipo_ponte": [
        "determinacao_material",
        "instanciacao_regional",
        "emergencia",
        "condicao_de_possibilidade",
        "traducao_operativa",
        "derivacao_normativa",
        "articulacao_multinivel",
    ],
    "dominio_cientifico": [
        "fisica",
        "quimica",
        "biologia",
        "ecologia",
        "neurociencia",
        "ciencia_cognitiva",
        "linguistica",
        "antropologia",
        "psicologia",
        "sociologia",
        "ciencias_da_complexidade",
        "teoria_de_sistemas",
    ],
    "tipo_dependencia_cientifica": [
        "nao_aplicavel",
        "compatibilidade_geral",
        "compatibilidade_forte",
        "suporte_empirico_relevante",
        "determinacao_material_necessaria",
        "exemplificacao_regional",
        "restricao_cientifica_importante",
    ],
    "estado_trabalho": [
        "por_classificar",
        "classificada",
        "validada_internamente",
        "pendente_confronto_filosofico",
        "pendente_ancoragem_cientifica",
        "pendente_ponte_entre_niveis",
        "pendente_cartografia_de_campo",
        "pendente_revisao_humana",
        "reformulada",
        "integrada",
    ],
}

REGRAS_DE_VALIDACAO: Dict[str, List[Dict[str, str]]] = {
    "regras_gerais": [
        {"id": "RG01", "descricao": "O ficheiro raiz tem de conter todos os blocos obrigatórios."},
        {"id": "RG02", "descricao": "Cada proposição tem de ter um proposicao_id único."},
        {"id": "RG03", "descricao": "ordem_global tem de ser inteira, positiva, única e sequencial sem repetições."},
        {"id": "RG04", "descricao": "ordem_no_bloco tem de ser inteira, positiva e coerente com bloco_id."},
        {"id": "RG05", "descricao": "texto não pode estar vazio."},
        {"id": "RG06", "descricao": "texto_curto não pode estar vazio."},
        {"id": "RG07", "descricao": "Todos os valores enumerados têm de pertencer aos enums documentados."},
        {"id": "RG08", "descricao": "grau_confianca_atribuicao tem de estar entre 0.0 e 1.0."},
    ],
    "regras_de_consistencia_estrutural": [
        {"id": "RC01", "descricao": "Se tem_fragmentos_rastreaveis for true, fragmento_ids não pode estar vazio."},
        {"id": "RC02", "descricao": "Se tem_microlinhas_rastreaveis for true, microlinha_ids não pode estar vazio."},
        {"id": "RC03", "descricao": "Se tem_ramos_rastreaveis for true, ramo_ids não pode estar vazio."},
        {"id": "RC04", "descricao": "Se tem_percursos_rastreaveis for true, percurso_ids não pode estar vazio."},
        {"id": "RC05", "descricao": "Se tem_argumentos_rastreaveis for true, argumento_ids não pode estar vazio."},
    ],
    "regras_de_consistencia_validacao": [
        {"id": "RV01", "descricao": "Se precisa_confronto_filosofico for true, temas_de_confronto não pode estar vazio."},
        {"id": "RV02", "descricao": "Se precisa_ancoragem_cientifica for true, dominios_cientificos não pode estar vazio."},
        {"id": "RV03", "descricao": "Se precisa_ponte_entre_niveis for true, pontes_entre_niveis não pode estar vazio."},
        {
            "id": "RV04",
            "descricao": "Se precisa_cartografia_de_campo for true, campos_principais e/ou campos_secundarios não pode estar totalmente vazio.",
        },
        {"id": "RV05", "descricao": "Se necessita_revisao_humana for true, motivo_revisao_humana não pode estar vazio."},
    ],
    "regras_de_consistencia_dedutiva": [
        {"id": "RD01", "descricao": "Uma proposição não pode depender de si mesma."},
        {"id": "RD02", "descricao": "dependencias_imediatas e dependencias_distais têm de ser subconjuntos de dependencias_anteriores."},
        {"id": "RD03", "descricao": "Dependências referidas têm de existir em proposicoes[].proposicao_id."},
    ],
    "regras_de_qualidade_recomendadas": [
        {"id": "RQ01", "descricao": "justificacao_atribuicao deve ser curta, específica e auditável."},
        {"id": "RQ02", "descricao": "autores_prioritarios deve privilegiar nomes realmente relevantes para a proposição."},
        {"id": "RQ03", "descricao": "subdominios_cientificos deve evitar excesso de granularidade irrelevante."},
        {"id": "RQ04", "descricao": "campos_do_real deve refletir domínios efetivamente implicados pela proposição, não listas genéricas."},
    ],
}


# =============================================================================
# UTILITÁRIOS
# =============================================================================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def unique_sorted(values: Iterable[str]) -> List[str]:
    return sorted({v for v in values if isinstance(v, str) and v.strip()})


def safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def normalize_spaces(text: str) -> str:
    return " ".join((text or "").strip().split())


def normalize_block_id(raw: str) -> str:
    raw = (raw or "").strip().upper()
    mapping = {
        "BLOCO_I": "B1",
        "BLOCO_II": "B2",
        "BLOCO_III": "B3",
        "BLOCO_IV": "B4",
        "BLOCO_V": "B5",
        "BLOCO_VI": "B6",
        "BLOCO_VII": "B7",
    }
    return mapping.get(raw, raw or "B?")


def score_to_traceability(has_frag: bool, has_ml: bool, has_ramo: bool, has_perc: bool, has_arg: bool) -> str:
    n = sum([has_frag, has_ml, has_ramo, has_perc, has_arg])
    if n <= 1:
        return "baixo"
    if n == 2:
        return "medio"
    if n in (3, 4):
        return "alto"
    return "muito_alto"


def deep_get(obj: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return cur if cur is not None else default


def infer_project_root(explicit_root: Optional[Path] = None) -> Path:
    if explicit_root:
        return explicit_root.resolve()

    script_path = Path(__file__).resolve()
    candidates = [
        script_path.parent.parent.parent,   # sobe de 16_validacao_integral/scripts para DoReal
        script_path.parent.parent,
        Path.cwd(),
        Path.cwd().parent,
    ]
    for cand in candidates:
        if (cand / DEFAULT_MAP_RELATIVE).exists() and (cand / DEFAULT_TREE_RELATIVE).exists():
            return cand.resolve()

    return script_path.parent.parent.parent.resolve()

def resolve_input_path(
    explicit: Optional[Path],
    project_root: Path,
    relative_default: Path,
) -> Path:
    if explicit:
        p = explicit.resolve()
        if not p.exists():
            raise FileNotFoundError(f"Ficheiro não encontrado: {p}")
        return p

    p = (project_root / relative_default).resolve()
    if p.exists():
        return p

    raise FileNotFoundError(
        f"Não foi possível localizar automaticamente o ficheiro '{relative_default}'."
    )


def output_path(project_root: Path, explicit: Optional[Path], relative_default: Path) -> Path:
    if explicit:
        return explicit.resolve()
    return (project_root / relative_default).resolve()


def as_bool(v: Any) -> bool:
    return bool(v)


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class LoadedSources:
    project_root: Path
    mapa_path: Path
    arvore_path: Path
    impacto_path: Optional[Path]
    arquitetura_path: Optional[Path]
    argumentos_path: Optional[Path]
    indice_percursos_path: Optional[Path]


# =============================================================================
# CARGA DE FONTES
# =============================================================================

def load_sources(args: argparse.Namespace) -> LoadedSources:
    project_root = infer_project_root(Path(args.project_root) if args.project_root else None)

    mapa_path = resolve_input_path(Path(args.mapa) if args.mapa else None, project_root, DEFAULT_MAP_RELATIVE)
    arvore_path = resolve_input_path(Path(args.arvore) if args.arvore else None, project_root, DEFAULT_TREE_RELATIVE)

    def try_resolve(user_value: Optional[str], relative_default: Path) -> Optional[Path]:
        if user_value == "":
            return None
        try:
            return resolve_input_path(
                Path(user_value) if user_value else None,
                project_root,
                relative_default,
            )
        except FileNotFoundError:
            return None

    impacto_path = try_resolve(args.impacto, DEFAULT_IMPACT_RELATIVE)
    arquitetura_path = try_resolve(args.arquitetura, DEFAULT_ARCH_RELATIVE)
    argumentos_path = try_resolve(args.argumentos, DEFAULT_ARGUMENTOS_RELATIVE)
    indice_percursos_path = try_resolve(args.indice_percursos, DEFAULT_INDICE_PERCURSOS_RELATIVE)

    return LoadedSources(
        project_root=project_root,
        mapa_path=mapa_path,
        arvore_path=arvore_path,
        impacto_path=impacto_path,
        arquitetura_path=arquitetura_path,
        argumentos_path=argumentos_path,
        indice_percursos_path=indice_percursos_path,
    )


# =============================================================================
# ÍNDICES E RELAÇÕES
# =============================================================================

def build_graph(passos: List[Dict[str, Any]]) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    deps: Dict[str, Set[str]] = {}
    forward: Dict[str, Set[str]] = {}
    for p in passos:
        pid = p.get("id")
        anteriores = {x for x in safe_list(p.get("depende_de")) if isinstance(x, str)}
        deps[pid] = anteriores
        forward.setdefault(pid, set())
        for dep in anteriores:
            forward.setdefault(dep, set()).add(pid)
    return deps, forward


def transitive_ancestors(node: str, deps: Dict[str, Set[str]]) -> Set[str]:
    visited: Set[str] = set()
    stack = list(deps.get(node, set()))
    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        stack.extend(deps.get(cur, set()))
    return visited


def transitive_descendants(node: str, forward: Dict[str, Set[str]]) -> Set[str]:
    visited: Set[str] = set()
    stack = list(forward.get(node, set()))
    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        stack.extend(forward.get(cur, set()))
    return visited


def build_tree_indexes(arvore: Dict[str, Any]) -> Dict[str, Any]:
    fragmentos = safe_list(arvore.get("fragmentos"))
    microlinhas = safe_list(arvore.get("microlinhas"))
    ramos = safe_list(arvore.get("ramos"))
    percursos = safe_list(arvore.get("percursos"))
    argumentos = safe_list(arvore.get("argumentos"))
    convergencias = safe_list(arvore.get("convergencias"))
    relacoes = safe_list(arvore.get("relacoes"))

    fragment_by_id = {x.get("id"): x for x in fragmentos if isinstance(x, dict) and x.get("id")}
    microlinha_by_id = {x.get("id"): x for x in microlinhas if isinstance(x, dict) and x.get("id")}
    ramo_by_id = {x.get("id"): x for x in ramos if isinstance(x, dict) and x.get("id")}
    percurso_by_id = {x.get("id"): x for x in percursos if isinstance(x, dict) and x.get("id")}
    argumento_by_id = {x.get("id"): x for x in argumentos if isinstance(x, dict) and x.get("id")}
    convergencia_by_id = {x.get("id"): x for x in convergencias if isinstance(x, dict) and x.get("id")}
    relacao_by_id = {x.get("id"): x for x in relacoes if isinstance(x, dict) and x.get("id")}

    passo_to_ramos: Dict[str, Set[str]] = defaultdict(set)
    ramo_to_microlinhas: Dict[str, Set[str]] = defaultdict(set)
    microlinha_to_fragmentos: Dict[str, Set[str]] = defaultdict(set)
    fragment_to_ligacoes: Dict[str, Dict[str, Set[str]]] = {}
    microlinha_to_percursos: Dict[str, Set[str]] = defaultdict(set)
    microlinha_to_argumentos: Dict[str, Set[str]] = defaultdict(set)

    for ramo in ramos:
        rid = ramo.get("id")
        for pid in safe_list(ramo.get("passo_ids_alvo")):
            if isinstance(pid, str):
                passo_to_ramos[pid].add(rid)
        for mlid in safe_list(ramo.get("microlinha_ids")):
            if isinstance(mlid, str):
                ramo_to_microlinhas[rid].add(mlid)

    for ml in microlinhas:
        mlid = ml.get("id")
        for fid in safe_list(ml.get("fragmento_ids")):
            if isinstance(fid, str):
                microlinha_to_fragmentos[mlid].add(fid)
        for pid in safe_list(ml.get("percurso_ids_sugeridos")):
            if isinstance(pid, str):
                microlinha_to_percursos[mlid].add(pid)
        for aid in safe_list(ml.get("argumento_ids_sugeridos")):
            if isinstance(aid, str):
                microlinha_to_argumentos[mlid].add(aid)

    for frag in fragmentos:
        fid = frag.get("id")
        lig = safe_dict(frag.get("ligacoes_arvore"))
        fragment_to_ligacoes[fid] = {
            "microlinha_ids": {x for x in safe_list(lig.get("microlinha_ids")) if isinstance(x, str)},
            "ramo_ids": {x for x in safe_list(lig.get("ramo_ids")) if isinstance(x, str)},
            "percurso_ids": {x for x in safe_list(lig.get("percurso_ids")) if isinstance(x, str)},
            "argumento_ids": {x for x in safe_list(lig.get("argumento_ids")) if isinstance(x, str)},
            "relacao_ids": {x for x in safe_list(lig.get("relacao_ids")) if isinstance(x, str)},
            "convergencia_ids": {x for x in safe_list(lig.get("convergencia_ids")) if isinstance(x, str)},
        }

    return {
        "fragment_by_id": fragment_by_id,
        "microlinha_by_id": microlinha_by_id,
        "ramo_by_id": ramo_by_id,
        "percurso_by_id": percurso_by_id,
        "argumento_by_id": argumento_by_id,
        "convergencia_by_id": convergencia_by_id,
        "relacao_by_id": relacao_by_id,
        "passo_to_ramos": passo_to_ramos,
        "ramo_to_microlinhas": ramo_to_microlinhas,
        "microlinha_to_fragmentos": microlinha_to_fragmentos,
        "fragment_to_ligacoes": fragment_to_ligacoes,
        "microlinha_to_percursos": microlinha_to_percursos,
        "microlinha_to_argumentos": microlinha_to_argumentos,
    }


def build_impact_index(impacto: Optional[List[Dict[str, Any]]]) -> Dict[str, Set[str]]:
    passo_to_fragmentos: Dict[str, Set[str]] = defaultdict(set)
    if not impacto:
        return passo_to_fragmentos

    for item in impacto:
        if not isinstance(item, dict):
            continue
        fid = item.get("id")
        impacto_mapa = safe_dict(item.get("impacto_mapa"))
        touched = safe_list(impacto_mapa.get("proposicoes_do_mapa_tocadas"))
        for t in touched:
            if not isinstance(t, dict):
                continue
            pid = t.get("proposicao_id")
            if isinstance(pid, str) and isinstance(fid, str):
                passo_to_fragmentos[pid].add(fid)
    return passo_to_fragmentos


def build_argument_index(argumentos: Optional[List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    if not argumentos:
        return {}
    return {
        x.get("id"): x
        for x in argumentos
        if isinstance(x, dict) and isinstance(x.get("id"), str)
    }


def build_indice_percursos_index(indice: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not indice:
        return {}
    percursos = safe_dict(indice.get("percursos"))
    out: Dict[str, Dict[str, Any]] = {}
    for pid, payload in percursos.items():
        if isinstance(pid, str) and isinstance(payload, dict):
            out[pid] = payload
    return out


# =============================================================================
# HEURÍSTICAS DE CLASSIFICAÇÃO INICIAL
# =============================================================================

def infer_dominio_principal(passo: Dict[str, Any]) -> str:
    ordem = int(passo.get("numero_final") or passo.get("numero_original") or 0)
    bloco_raw = passo.get("bloco_id", "")
    bloco = normalize_block_id(bloco_raw)
    texto = normalize_spaces(
        f"{passo.get('proposicao_final', '')} {passo.get('proposicao_original', '')} {passo.get('descricao_curta', '')}"
    ).lower()

    if bloco in {"B1", "B2", "B3"}:
        return "ontologia"
    if bloco == "B4":
        if any(k in texto for k in ["linguagem", "símbolo", "simbolo"]):
            return "filosofia_da_linguagem"
        if any(k in texto for k in ["consciência", "consciencia", "representação", "representacao"]):
            return "filosofia_da_mente"
        return "antropologia_filosofica"
    if bloco == "B5":
        return "epistemologia"
    if bloco in {"B6", "B7"}:
        return "etica"
    if ordem <= 22:
        return "ontologia"
    if 23 <= ordem <= 30:
        return "antropologia_filosofica"
    if 31 <= ordem <= 37:
        return "epistemologia"
    return "etica"


def infer_subdominios(dominio: str, passo: Dict[str, Any]) -> List[str]:
    texto = normalize_spaces(
        f"{passo.get('proposicao_final', '')} {passo.get('descricao_curta', '')}"
    ).lower()
    subs: Set[str] = set()

    if dominio == "ontologia":
        if any(k in texto for k in ["real", "ser", "não-ser", "nao-ser", "estrutura", "limite"]):
            subs.add("estrutura_do_real")
        if any(k in texto for k in ["potencialidade", "mudança", "mudanca", "tempo", "campo"]):
            subs.add("dinamica_ontologica")

    if dominio == "antropologia_filosofica":
        if any(k in texto for k in ["consciência", "consciencia", "reflexiva", "memória", "memoria"]):
            subs.add("filosofia_da_mente")
        if any(k in texto for k in ["linguagem", "símbolo", "simbolo", "mediação", "mediacao"]):
            subs.add("filosofia_da_linguagem")

    if dominio == "epistemologia":
        if any(k in texto for k in ["verdade", "erro", "critério", "criterio", "adequação", "adequacao"]):
            subs.add("teoria_do_conhecimento")

    if dominio == "etica":
        if any(k in texto for k in ["bem", "mal", "dano", "dever-ser", "normatividade", "dignidade", "vida boa"]):
            subs.add("etica_fundamental")

    return sorted(subs)


def infer_tipo_formulacao(passo: Dict[str, Any]) -> str:
    ordem = int(passo.get("numero_final") or passo.get("numero_original") or 0)
    texto = normalize_spaces(passo.get("proposicao_final", "")).lower()

    if ordem in {1, 2, 3}:
        return "proposicao_fundacional"
    if any(k in texto for k in ["consiste", "designa", "é a", "é o", "deve ser definido"]):
        return "proposicao_definicional"
    if any(k in texto for k in ["verdade", "erro", "critério", "criterio"]):
        return "proposicao_criteriologica"
    if any(k in texto for k in ["deve", "bem", "mal", "dever-ser", "normatividade", "dignidade", "vida boa"]):
        return "proposicao_normativa"
    if any(k in texto for k in ["passagem", "transição", "transicao", "emergência", "emergencia"]):
        return "proposicao_transicional"
    return "proposicao_derivada"


def infer_funcao_no_mapa(passo: Dict[str, Any]) -> str:
    ordem = int(passo.get("numero_final") or passo.get("numero_original") or 0)
    bloco = normalize_block_id(passo.get("bloco_id", ""))

    if ordem == 1:
        return "fundamento"
    if bloco in {"B1", "B2"}:
        return "derivacao"
    if bloco in {"B3", "B4"}:
        return "transicao"
    if bloco == "B5":
        return "criterio"
    if bloco in {"B6", "B7"}:
        return "fecho"
    return "articulacao"


def infer_tipo_de_proposicao(passo: Dict[str, Any], dominio: str) -> str:
    ordem = int(passo.get("numero_final") or passo.get("numero_original") or 0)
    texto = normalize_spaces(passo.get("proposicao_final", "")).lower()

    if dominio == "ontologia":
        if ordem <= 10:
            return "ontologica_fundacional"
        if any(k in texto for k in ["mudança", "mudanca", "potencialidade", "campo", "tempo", "dinâmica", "dinamica"]):
            return "ontologica_dinamica"
        return "ontologica_estrutural"

    if dominio == "antropologia_filosofica":
        return "antropologica_estrutural"

    if dominio == "filosofia_da_mente":
        return "transcendental_operativa"

    if dominio == "filosofia_da_linguagem":
        return "integrativa_entre_niveis"

    if dominio == "epistemologia":
        if any(k in texto for k in ["verdade", "critério", "criterio", "adequação", "adequacao"]):
            return "epistemologica_criteriologica"
        return "epistemologica_corretiva"

    if dominio == "etica":
        if any(k in texto for k in ["dever-ser", "normatividade", "dignidade", "vida boa"]):
            return "normativa_derivada"
        return "etica_derivada"

    return "integrativa_entre_niveis"


def infer_grau_prioridade(passo: Dict[str, Any]) -> str:
    ordem = int(passo.get("numero_final") or passo.get("numero_original") or 0)
    if ordem in {1, 11, 23, 30, 34, 38, 44, 46, 50, 51}:
        return "estrutural"
    if ordem <= 10 or 31 <= ordem <= 37:
        return "alta"
    return "media"


# =============================================================================
# ENRIQUECIMENTO
# =============================================================================

def collect_links_for_step(
    passo: Dict[str, Any],
    tree_idx: Dict[str, Any],
    impact_idx: Dict[str, Set[str]],
) -> Dict[str, List[str]]:
    pid = passo.get("id")
    fragment_ids: Set[str] = set()

    # 1) fragmentos explicitamente apoiados no mapa final
    fragment_ids.update(x for x in safe_list(passo.get("fragmentos_de_apoio_final")) if isinstance(x, str))

    # 2) impacto por proposição
    fragment_ids.update(impact_idx.get(pid, set()))

    # 3) ramos ligados diretamente ao passo
    ramo_ids: Set[str] = set(tree_idx["passo_to_ramos"].get(pid, set()))

    # 4) percursos / argumentos explicitamente mencionados no mapa
    apoio_arg = safe_dict(passo.get("apoio_argumentativo"))
    percurso_ids: Set[str] = {x for x in safe_list(apoio_arg.get("percursos_ids")) if isinstance(x, str)}
    argumento_ids: Set[str] = {x for x in safe_list(apoio_arg.get("argumentos_ids")) if isinstance(x, str)}

    # 5) microlinhas a partir dos ramos
    microlinha_ids: Set[str] = set()
    for rid in ramo_ids:
        microlinha_ids.update(tree_idx["ramo_to_microlinhas"].get(rid, set()))

    # 6) fragmentos a partir das microlinhas
    for mlid in microlinha_ids:
        fragment_ids.update(tree_idx["microlinha_to_fragmentos"].get(mlid, set()))
        percurso_ids.update(tree_idx["microlinha_to_percursos"].get(mlid, set()))
        argumento_ids.update(tree_idx["microlinha_to_argumentos"].get(mlid, set()))

    # 7) completar ligações a partir dos próprios fragmentos
    relacao_ids: Set[str] = set()
    convergencia_ids: Set[str] = set()
    for fid in list(fragment_ids):
        lig = tree_idx["fragment_to_ligacoes"].get(fid, {})
        microlinha_ids.update(lig.get("microlinha_ids", set()))
        ramo_ids.update(lig.get("ramo_ids", set()))
        percurso_ids.update(lig.get("percurso_ids", set()))
        argumento_ids.update(lig.get("argumento_ids", set()))
        relacao_ids.update(lig.get("relacao_ids", set()))
        convergencia_ids.update(lig.get("convergencia_ids", set()))

    # 8) completar de novo microlinhas vindas agora dos fragmentos
    for mlid in list(microlinha_ids):
        fragment_ids.update(tree_idx["microlinha_to_fragmentos"].get(mlid, set()))
        percurso_ids.update(tree_idx["microlinha_to_percursos"].get(mlid, set()))
        argumento_ids.update(tree_idx["microlinha_to_argumentos"].get(mlid, set()))

    # 9) percursos/argumentos a partir dos ramos
    for rid in list(ramo_ids):
        ramo = tree_idx["ramo_by_id"].get(rid, {})
        percurso_ids.update(x for x in safe_list(ramo.get("percurso_ids_associados")) if isinstance(x, str))
        argumento_ids.update(x for x in safe_list(ramo.get("argumento_ids_associados")) if isinstance(x, str))
        convergencia_ids.update(x for x in safe_list(ramo.get("convergencia_ids")) if isinstance(x, str))

    return {
        "fragmento_ids": unique_sorted(fragment_ids),
        "microlinha_ids": unique_sorted(microlinha_ids),
        "ramo_ids": unique_sorted(ramo_ids),
        "percurso_ids": unique_sorted(percurso_ids),
        "argumento_ids": unique_sorted(argumento_ids),
        "convergencia_ids": unique_sorted(convergencia_ids),
        "relacao_ids": unique_sorted(relacao_ids),
    }


def build_base_proposition_template() -> Dict[str, Any]:
    return {
        "proposicao_id": "",
        "texto": "",
        "texto_curto": "",
        "bloco_id": "",
        "bloco_titulo": "",
        "ordem_global": 0,
        "ordem_no_bloco": 0,
        "estado_proposicao": "ativa",
        "dependencias": {
            "dependencias_anteriores": [],
            "dependencias_posteriores": [],
            "dependencias_imediatas": [],
            "dependencias_distais": [],
        },
        "arquitetura_origem": {
            "fragmento_ids": [],
            "microlinha_ids": [],
            "ramo_ids": [],
            "percurso_ids": [],
            "argumento_ids": [],
            "convergencia_ids": [],
            "relacao_ids": [],
        },
        "suporte_estrutural": {
            "tem_fragmentos_rastreaveis": False,
            "tem_microlinhas_rastreaveis": False,
            "tem_ramos_rastreaveis": False,
            "tem_percursos_rastreaveis": False,
            "tem_argumentos_rastreaveis": False,
            "grau_rastreabilidade": "baixo",
        },
        "classificacao_filosofica_inicial": {
            "dominio_principal": "integrativo",
            "subdominios": [],
            "tipo_formulacao": "proposicao_derivada",
            "funcao_no_mapa": "articulacao",
        },
        "validacao_integral": {
            "tipo_de_proposicao": "integrativa_entre_niveis",
            "regime_de_validacao": [
                "coerencia_dedutiva_interna",
                "rastreabilidade_arquitetural",
            ],
            "precisa_confronto_filosofico": False,
            "precisa_ancoragem_cientifica": False,
            "precisa_ponte_entre_niveis": False,
            "precisa_cartografia_de_campo": False,
            "precisa_reformulacao_conceitual": False,
            "grau_risco_salto": "baixo",
            "grau_prioridade": "media",
            "grau_confianca_atribuicao": 0.0,
            "justificacao_atribuicao": "A preencher por script posterior de atribuição de regimes de validação.",
        },
        "campos_do_real": {
            "campos_principais": [],
            "campos_secundarios": [],
            "escala_ontologica": [],
            "nivel_de_realidade_implicado": [],
            "observacoes": "",
        },
        "pontes_entre_niveis": [],
        "confronto_filosofico": {
            "temas_de_confronto": [],
            "autores_prioritarios": [],
            "tradicoes_prioritarias": [],
            "questoes_abertas": [],
        },
        "ancoragem_cientifica": {
            "dominios_cientificos": [],
            "subdominios_cientificos": [],
            "tipo_dependencia_cientifica": [],
            "observacoes": "",
        },
        "estado_trabalho": {
            "estado_atual": "por_classificar",
            "necessita_revisao_humana": False,
            "motivo_revisao_humana": "",
            "notas_internas": "",
        },
    }


def enrich_propositions(
    mapa: Dict[str, Any],
    arvore: Dict[str, Any],
    impacto: Optional[List[Dict[str, Any]]],
    argumentos_unificados: Optional[List[Dict[str, Any]]] = None,
    indice_percursos: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    passos = safe_list(mapa.get("passos"))
    if not passos:
        raise ValueError("O mapa dedutivo não contém a lista 'passos'.")

    deps, forward = build_graph(passos)
    tree_idx = build_tree_indexes(arvore)
    impact_idx = build_impact_index(impacto)
    argumentos_idx = build_argument_index(argumentos_unificados)
    percursos_idx = build_indice_percursos_index(indice_percursos)

    # ordem por bloco
    passos_ordenados = sorted(
        passos,
        key=lambda p: (
            int(p.get("numero_final") or p.get("numero_original") or 10**9),
            p.get("id", ""),
        ),
    )

    bloco_counts: Dict[str, int] = defaultdict(int)
    proposicoes: List[Dict[str, Any]] = []

    coverage_info = {
        "mapa_total_passos": len(passos),
        "passos_com_fragmentos": 0,
        "passos_com_microlinhas": 0,
        "passos_com_ramos": 0,
        "passos_com_percursos": 0,
        "passos_com_argumentos": 0,
        "passos_com_convergencias": 0,
        "passos_com_relacoes": 0,
        "argumentos_externos_indexados": len(argumentos_idx),
        "percursos_externos_indexados": len(percursos_idx),
    }

    for passo in passos_ordenados:
        pid = passo.get("id")
        bloco_id = normalize_block_id(passo.get("bloco_id", ""))
        bloco_counts[bloco_id] += 1
        ordem_bloco = bloco_counts[bloco_id]

        item = build_base_proposition_template()
        item["proposicao_id"] = pid
        item["texto"] = normalize_spaces(
            passo.get("proposicao_final")
            or passo.get("tratamento_academico", {}).get("formulacao_filosofico_academica")
            or passo.get("proposicao")
            or passo.get("proposicao_original")
            or ""
        )
        item["texto_curto"] = normalize_spaces(
            passo.get("descricao_curta")
            or passo.get("tese_minima")
            or passo.get("proposicao_original")
            or item["texto"]
        )
        item["bloco_id"] = bloco_id
        item["bloco_titulo"] = passo.get("bloco_titulo", "") or ""
        item["ordem_global"] = int(passo.get("numero_final") or passo.get("numero_original") or 0)
        item["ordem_no_bloco"] = ordem_bloco
        item["estado_proposicao"] = "ativa"

        # dependências
        imediatas = unique_sorted(deps.get(pid, set()))
        anteriores = unique_sorted(transitive_ancestors(pid, deps))
        distais = unique_sorted(set(anteriores) - set(imediatas))
        posteriores = unique_sorted(transitive_descendants(pid, forward))

        item["dependencias"]["dependencias_imediatas"] = imediatas
        item["dependencias"]["dependencias_anteriores"] = anteriores
        item["dependencias"]["dependencias_distais"] = distais
        item["dependencias"]["dependencias_posteriores"] = posteriores

        # arquitetura
        lig = collect_links_for_step(passo, tree_idx, impact_idx)
        item["arquitetura_origem"] = lig

        has_frag = bool(lig["fragmento_ids"])
        has_ml = bool(lig["microlinha_ids"])
        has_ramo = bool(lig["ramo_ids"])
        has_perc = bool(lig["percurso_ids"])
        has_arg = bool(lig["argumento_ids"])

        item["suporte_estrutural"]["tem_fragmentos_rastreaveis"] = has_frag
        item["suporte_estrutural"]["tem_microlinhas_rastreaveis"] = has_ml
        item["suporte_estrutural"]["tem_ramos_rastreaveis"] = has_ramo
        item["suporte_estrutural"]["tem_percursos_rastreaveis"] = has_perc
        item["suporte_estrutural"]["tem_argumentos_rastreaveis"] = has_arg
        item["suporte_estrutural"]["grau_rastreabilidade"] = score_to_traceability(
            has_frag, has_ml, has_ramo, has_perc, has_arg
        )

        if has_frag:
            coverage_info["passos_com_fragmentos"] += 1
        if has_ml:
            coverage_info["passos_com_microlinhas"] += 1
        if has_ramo:
            coverage_info["passos_com_ramos"] += 1
        if has_perc:
            coverage_info["passos_com_percursos"] += 1
        if has_arg:
            coverage_info["passos_com_argumentos"] += 1
        if lig["convergencia_ids"]:
            coverage_info["passos_com_convergencias"] += 1
        if lig["relacao_ids"]:
            coverage_info["passos_com_relacoes"] += 1

        # classificação inicial
        dominio = infer_dominio_principal(passo)
        subdominios = infer_subdominios(dominio, passo)
        tipo_formulacao = infer_tipo_formulacao(passo)
        funcao = infer_funcao_no_mapa(passo)
        tipo_prop = infer_tipo_de_proposicao(passo, dominio)

        item["classificacao_filosofica_inicial"]["dominio_principal"] = dominio
        item["classificacao_filosofica_inicial"]["subdominios"] = subdominios
        item["classificacao_filosofica_inicial"]["tipo_formulacao"] = tipo_formulacao
        item["classificacao_filosofica_inicial"]["funcao_no_mapa"] = funcao

        item["validacao_integral"]["tipo_de_proposicao"] = tipo_prop
        item["validacao_integral"]["grau_prioridade"] = infer_grau_prioridade(passo)

        # notas internas úteis para pipeline seguinte
        notas = []
        if passo.get("requer_arbitragem_humana") is True:
            notas.append("O mapa final assinala requer_arbitragem_humana=true neste passo.")
        if safe_list(passo.get("tipos_de_fragilidade")):
            notas.append(
                "Fragilidades no mapa final: "
                + ", ".join(str(x) for x in safe_list(passo.get("tipos_de_fragilidade")))
            )
        if safe_list(passo.get("mediacao_necessaria")):
            notas.append(
                "Mediações ainda assinaladas no mapa: "
                + " | ".join(str(x) for x in safe_list(passo.get("mediacao_necessaria")))
            )
        item["estado_trabalho"]["notas_internas"] = " ".join(notas)

        proposicoes.append(item)

    return proposicoes, coverage_info


# =============================================================================
# MONTAGEM DO FICHEIRO-MÃE
# =============================================================================

def build_output_document(
    sources: LoadedSources,
    mapa: Dict[str, Any],
    proposicoes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    bloco_counter = Counter(p["bloco_id"] for p in proposicoes)

    total_com_fragmentos = sum(1 for p in proposicoes if p["suporte_estrutural"]["tem_fragmentos_rastreaveis"])
    total_com_microlinhas = sum(1 for p in proposicoes if p["suporte_estrutural"]["tem_microlinhas_rastreaveis"])
    total_com_ramos = sum(1 for p in proposicoes if p["suporte_estrutural"]["tem_ramos_rastreaveis"])
    total_com_percursos = sum(1 for p in proposicoes if p["suporte_estrutural"]["tem_percursos_rastreaveis"])
    total_com_argumentos = sum(1 for p in proposicoes if p["suporte_estrutural"]["tem_argumentos_rastreaveis"])

    document = {
        "metadata": {
            "schema_nome": "proposicoes_nucleares_enriquecidas_v1",
            "schema_versao": "1.0",
            "data_geracao": utc_now_iso(),
            "gerado_por_script": Path(__file__).name,
            "descricao": (
                "Proposições nucleares do mapa dedutivo enriquecidas com dependências dedutivas, "
                "rastreabilidade arquitetural e atributos de validação integral pós-árvore."
            ),
            "idioma": "pt-PT",
            "projeto": "arvore_do_pensamento",
            "estado_global": "enriquecido",
        },
        "fontes": {
            "fonte_mapa_dedutivo": {
                "caminho": str(sources.mapa_path.parent),
                "ficheiro": sources.mapa_path.name,
                "hash_opcional": "",
            },
            "fonte_arvore": {
                "caminho": str(sources.arvore_path.parent),
                "ficheiro": sources.arvore_path.name,
                "hash_opcional": "",
            },
            "fontes_auxiliares": [],
        },
        "estatisticas": {
            "total_proposicoes": len(proposicoes),
            "total_blocos": len(bloco_counter),
            "proposicoes_por_bloco": dict(sorted(bloco_counter.items())),
            "proposicoes_com_fragmentos": total_com_fragmentos,
            "proposicoes_com_microlinhas": total_com_microlinhas,
            "proposicoes_com_ramos": total_com_ramos,
            "proposicoes_com_percursos": total_com_percursos,
            "proposicoes_com_argumentos": total_com_argumentos,
            "proposicoes_que_precisam_confronto_filosofico": 0,
            "proposicoes_que_precisam_ancoragem_cientifica": 0,
            "proposicoes_que_precisam_ponte_entre_niveis": 0,
            "proposicoes_que_precisam_cartografia_de_campo": 0,
            "proposicoes_com_revisao_humana": 0,
        },
        "enums_documentados": deepcopy(ENUMS_DOCUMENTADOS),
        "regras_de_validacao": deepcopy(REGRAS_DE_VALIDACAO),
        "proposicoes": proposicoes,
    }

    if sources.impacto_path:
        document["fontes"]["fontes_auxiliares"].append(
            {
                "tipo": "impacto_no_mapa",
                "caminho": str(sources.impacto_path.parent),
                "ficheiro": sources.impacto_path.name,
                "descricao": "Indexação auxiliar de fragmentos por proposição tocada.",
            }
        )
    if sources.arquitetura_path:
        document["fontes"]["fontes_auxiliares"].append(
            {
                "tipo": "outro",
                "caminho": str(sources.arquitetura_path.parent),
                "ficheiro": sources.arquitetura_path.name,
                "descricao": "Arquitetura anterior do mapa usada apenas como referência contextual.",
            }
        )
    if sources.argumentos_path:
        document["fontes"]["fontes_auxiliares"].append(
            {
                "tipo": "argumentos_unificados",
                "caminho": str(sources.argumentos_path.parent),
                "ficheiro": sources.argumentos_path.name,
                "descricao": "Coleção auxiliar de argumentos unificados.",
            }
        )
    if sources.indice_percursos_path:
        document["fontes"]["fontes_auxiliares"].append(
            {
                "tipo": "indice_percursos",
                "caminho": str(sources.indice_percursos_path.parent),
                "ficheiro": sources.indice_percursos_path.name,
                "descricao": "Índice auxiliar por percurso.",
            }
        )

    return document


# =============================================================================
# VALIDAÇÃO BÁSICA
# =============================================================================

def validate_document(doc: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    required_root = [
        "metadata",
        "fontes",
        "estatisticas",
        "enums_documentados",
        "regras_de_validacao",
        "proposicoes",
    ]
    for key in required_root:
        if key not in doc:
            errors.append(f"Falta o bloco raiz obrigatório: {key}")

    proposicoes = safe_list(doc.get("proposicoes"))
    if not proposicoes:
        errors.append("A lista 'proposicoes' está vazia.")
        return errors

    ids = [p.get("proposicao_id") for p in proposicoes]
    if len(ids) != len(set(ids)):
        errors.append("Existem proposicao_id repetidos.")

    ordens = [p.get("ordem_global") for p in proposicoes]
    if sorted(ordens) != list(range(1, len(ordens) + 1)):
        errors.append("ordem_global não é sequencial contínua a partir de 1.")

    valid_ids = set(ids)
    for p in proposicoes:
        pid = p.get("proposicao_id", "<sem_id>")
        if not normalize_spaces(p.get("texto", "")):
            errors.append(f"{pid}: texto vazio.")
        if not normalize_spaces(p.get("texto_curto", "")):
            errors.append(f"{pid}: texto_curto vazio.")

        dep = safe_dict(p.get("dependencias"))
        anteriores = set(dep.get("dependencias_anteriores", []))
        imediatas = set(dep.get("dependencias_imediatas", []))
        distais = set(dep.get("dependencias_distais", []))

        if pid in anteriores or pid in imediatas or pid in distais:
            errors.append(f"{pid}: auto-dependência detetada.")

        if not imediatas.issubset(anteriores):
            errors.append(f"{pid}: dependencias_imediatas não são subconjunto de dependencias_anteriores.")

        if not distais.issubset(anteriores):
            errors.append(f"{pid}: dependencias_distais não são subconjunto de dependencias_anteriores.")

        for ref in anteriores.union(set(dep.get("dependencias_posteriores", []))):
            if ref not in valid_ids:
                errors.append(f"{pid}: dependência refere proposição inexistente: {ref}")

        sup = safe_dict(p.get("suporte_estrutural"))
        arq = safe_dict(p.get("arquitetura_origem"))

        consistency_checks = [
            ("tem_fragmentos_rastreaveis", "fragmento_ids"),
            ("tem_microlinhas_rastreaveis", "microlinha_ids"),
            ("tem_ramos_rastreaveis", "ramo_ids"),
            ("tem_percursos_rastreaveis", "percurso_ids"),
            ("tem_argumentos_rastreaveis", "argumento_ids"),
        ]
        for flag, field in consistency_checks:
            if as_bool(sup.get(flag)) and not safe_list(arq.get(field)):
                errors.append(f"{pid}: {flag}=true mas {field} está vazio.")

        val = safe_dict(p.get("validacao_integral"))
        gca = val.get("grau_confianca_atribuicao")
        try:
            gca_num = float(gca)
        except Exception:
            errors.append(f"{pid}: grau_confianca_atribuicao inválido.")
        else:
            if not (0.0 <= gca_num <= 1.0):
                errors.append(f"{pid}: grau_confianca_atribuicao fora do intervalo [0.0, 1.0].")

    return errors


# =============================================================================
# RELATÓRIO
# =============================================================================

def build_report(
    sources: LoadedSources,
    doc: Dict[str, Any],
    validation_errors: List[str],
) -> str:
    stats = safe_dict(doc.get("estatisticas"))
    props = safe_list(doc.get("proposicoes"))

    rastreabilidade_counter = Counter(
        safe_dict(p.get("suporte_estrutural")).get("grau_rastreabilidade", "baixo")
        for p in props
    )
    dominios_counter = Counter(
        safe_dict(safe_dict(p.get("classificacao_filosofica_inicial"))).get("dominio_principal", "integrativo")
        for p in props
    )
    tipos_counter = Counter(
        safe_dict(safe_dict(p.get("validacao_integral"))).get("tipo_de_proposicao", "integrativa_entre_niveis")
        for p in props
    )

    lines: List[str] = []
    lines.append("RELATÓRIO — EXTRAÇÃO E ENRIQUECIMENTO DE PROPOSIÇÕES NUCLEARES V1")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"Data UTC: {doc['metadata']['data_geracao']}")
    lines.append(f"Script: {doc['metadata']['gerado_por_script']}")
    lines.append("")
    lines.append("FONTES")
    lines.append("-" * 78)
    lines.append(f"Mapa dedutivo: {sources.mapa_path}")
    lines.append(f"Árvore: {sources.arvore_path}")
    lines.append(f"Impacto: {sources.impacto_path if sources.impacto_path else '[não usado]'}")
    lines.append(f"Arquitetura: {sources.arquitetura_path if sources.arquitetura_path else '[não usada]'}")
    lines.append(f"Argumentos unificados: {sources.argumentos_path if sources.argumentos_path else '[não usado]'}")
    lines.append(f"Índice por percurso: {sources.indice_percursos_path if sources.indice_percursos_path else '[não usado]'}")
    lines.append("")
    lines.append("ESTATÍSTICAS GERAIS")
    lines.append("-" * 78)
    lines.append(f"Total de proposições: {stats.get('total_proposicoes', 0)}")
    lines.append(f"Total de blocos: {stats.get('total_blocos', 0)}")
    lines.append(f"Proposições por bloco: {json.dumps(stats.get('proposicoes_por_bloco', {}), ensure_ascii=False)}")
    lines.append("")
    lines.append("COBERTURA DE RASTREABILIDADE")
    lines.append("-" * 78)
    lines.append(f"Com fragmentos: {stats.get('proposicoes_com_fragmentos', 0)}")
    lines.append(f"Com microlinhas: {stats.get('proposicoes_com_microlinhas', 0)}")
    lines.append(f"Com ramos: {stats.get('proposicoes_com_ramos', 0)}")
    lines.append(f"Com percursos: {stats.get('proposicoes_com_percursos', 0)}")
    lines.append(f"Com argumentos: {stats.get('proposicoes_com_argumentos', 0)}")
    lines.append(f"Distribuição do grau de rastreabilidade: {json.dumps(dict(sorted(rastreabilidade_counter.items())), ensure_ascii=False)}")
    lines.append("")
    lines.append("CLASSIFICAÇÃO INICIAL")
    lines.append("-" * 78)
    lines.append(f"Domínios principais: {json.dumps(dict(sorted(dominios_counter.items())), ensure_ascii=False)}")
    lines.append(f"Tipos de proposição: {json.dumps(dict(sorted(tipos_counter.items())), ensure_ascii=False)}")
    lines.append("")
    lines.append("VALIDAÇÃO BÁSICA")
    lines.append("-" * 78)
    if validation_errors:
        lines.append(f"Foram encontrados {len(validation_errors)} erro(s):")
        for err in validation_errors:
            lines.append(f"- {err}")
    else:
        lines.append("Sem erros de validação básica.")
    lines.append("")
    lines.append("OBSERVAÇÕES")
    lines.append("-" * 78)
    lines.append(
        "Este script apenas extrai e enriquece estruturalmente as proposições nucleares. "
        "A atribuição substantiva de regimes de validação, confronto filosófico, ancoragem científica, "
        "pontes entre níveis e cartografia de campo fica para script posterior."
    )
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# ARGPARSE
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extrai e enriquece as proposições nucleares do mapa dedutivo final."
    )
    parser.add_argument("--project-root", help="Raiz do projeto. Se omitido, é inferida automaticamente.")
    parser.add_argument("--mapa", help="Caminho do mapa dedutivo final.")
    parser.add_argument("--arvore", help="Caminho da árvore fechada.")
    parser.add_argument("--impacto", help="Caminho do ficheiro de impacto dos fragmentos no mapa.")
    parser.add_argument("--arquitetura", help="Caminho do ficheiro de arquitetura do mapa.")
    parser.add_argument("--argumentos", help="Caminho do ficheiro de argumentos unificados.")
    parser.add_argument("--indice-percursos", dest="indice_percursos", help="Caminho do índice por percurso.")
    parser.add_argument("--output-json", help="Caminho do output JSON.")
    parser.add_argument("--output-relatorio", help="Caminho do relatório TXT.")
    return parser


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        sources = load_sources(args)

        mapa = read_json(sources.mapa_path)
        arvore = read_json(sources.arvore_path)
        impacto = read_json(sources.impacto_path) if sources.impacto_path else None
        _arquitetura = read_json(sources.arquitetura_path) if sources.arquitetura_path else None
        argumentos = read_json(sources.argumentos_path) if sources.argumentos_path else None
        indice_percursos = read_json(sources.indice_percursos_path) if sources.indice_percursos_path else None

        proposicoes, _coverage = enrich_propositions(
            mapa=mapa,
            arvore=arvore,
            impacto=impacto,
            argumentos_unificados=argumentos,
            indice_percursos=indice_percursos,
        )

        document = build_output_document(
            sources=sources,
            mapa=mapa,
            proposicoes=proposicoes,
        )

        validation_errors = validate_document(document)

        output_json_path = output_path(
            sources.project_root,
            Path(args.output_json) if args.output_json else None,
            OUTPUT_JSON_RELATIVE,
        )
        output_report_path = output_path(
            sources.project_root,
            Path(args.output_relatorio) if args.output_relatorio else None,
            OUTPUT_REPORT_RELATIVE,
        )

        write_json(output_json_path, document)
        report = build_report(sources, document, validation_errors)
        write_text(output_report_path, report)

        print(f"JSON gerado em: {output_json_path}")
        print(f"Relatório gerado em: {output_report_path}")
        if validation_errors:
            print(f"Atenção: foram detetados {len(validation_errors)} erro(s) de validação básica.")
            return 2

        print("Concluído sem erros de validação básica.")
        return 0

    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())