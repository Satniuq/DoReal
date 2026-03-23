#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
atribuir_regimes_de_validacao_v1.py

Lê o ficheiro-mãe de proposições nucleares enriquecidas e atribui, de forma
determinística, auditável e conservadora, os regimes iniciais de validação
pós-árvore para cada proposição.

Objetivos:
- preencher os campos de validação integral ainda genéricos;
- marcar necessidades de confronto filosófico, ancoragem científica,
  ponte entre níveis e cartografia de campo;
- atribuir grau de risco de salto e prioridade operacional;
- sugerir temas de confronto, domínios científicos, campos do real
  e pontes entre níveis;
- gerar relatório de atribuição.

Outputs:
- 16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json
  (atualizado in place, salvo se for indicado output alternativo)
- 16_validacao_integral/02_outputs/relatorio_atribuicao_regimes_v1.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


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

DEFAULT_INPUT_JSON_RELATIVE = Path(
    "16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json"
)
DEFAULT_OUTPUT_JSON_RELATIVE = Path(
    "16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json"
)
DEFAULT_REPORT_RELATIVE = Path(
    "16_validacao_integral/02_outputs/relatorio_atribuicao_regimes_v1.txt"
)


# =============================================================================
# ENUMS E CONSTANTES
# =============================================================================

VALID_TIPO_DE_PROPOSICAO = {
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
}

VALID_REGIME = {
    "coerencia_dedutiva_interna",
    "rastreabilidade_arquitetural",
    "confronto_filosofico",
    "compatibilidade_cientifica",
    "ancoragem_cientifica_forte",
    "justificacao_de_ponte",
    "cartografia_de_campo",
    "reformulacao_conceitual",
    "validacao_integrativa",
}

VALID_GRAU_RISCO = {"baixo", "medio", "alto", "critico"}
VALID_GRAU_PRIORIDADE = {"baixa", "media", "alta", "estrutural"}
VALID_ESTADO_TRABALHO = {
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
}
VALID_CAMPOS = {
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
}
VALID_ESCALAS = {
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
}
VALID_NIVEIS_REALIDADE = {
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
}
VALID_NIVEL_PONTE = {
    "ontologia_geral",
    "ontologia_estrutural",
    "ontologia_dinamica",
    "biologia_do_organismo",
    "ciencia_cognitiva",
    "linguagem_simbolica",
    "vida_social",
    "acao_pratica",
    "normatividade_etica",
}
VALID_TIPO_PONTE = {
    "determinacao_material",
    "instanciacao_regional",
    "emergencia",
    "condicao_de_possibilidade",
    "traducao_operativa",
    "derivacao_normativa",
    "articulacao_multinivel",
}
VALID_DOMINIOS_CIENTIFICOS = {
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
}
VALID_TIPO_DEP_CIENTIFICA = {
    "nao_aplicavel",
    "compatibilidade_geral",
    "compatibilidade_forte",
    "suporte_empirico_relevante",
    "determinacao_material_necessaria",
    "exemplificacao_regional",
    "restricao_cientifica_importante",
}

# temas de confronto: strings livres, sem enum fechado
# autores/tradições: strings livres


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


def normalize_spaces(text: str) -> str:
    return " ".join((text or "").strip().split())


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def unique_preserve(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    for v in values:
        if not isinstance(v, str):
            continue
        vv = v.strip()
        if not vv or vv in seen:
            continue
        seen.add(vv)
        out.append(vv)
    return out


def project_root_from_explicit_or_cwd(explicit_root: Optional[Path]) -> Path:
    if explicit_root:
        return explicit_root.resolve()

    script_path = Path(__file__).resolve()
    candidates = [
        script_path.parent.parent.parent,
        script_path.parent.parent,
        Path.cwd(),
        Path.cwd().parent,
        Path.cwd().parent.parent,
    ]
    for cand in candidates:
        if (cand / DEFAULT_INPUT_JSON_RELATIVE).exists():
            return cand.resolve()
    return script_path.parent.parent.parent


def resolve_relative(project_root: Path, relative_path: Path) -> Path:
    path = (project_root / relative_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {path}")
    return path


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def add_regime(regimes: Set[str], *values: str) -> None:
    for value in values:
        if value in VALID_REGIME:
            regimes.add(value)


def text_contains_any(text: str, needles: Sequence[str]) -> bool:
    return any(n in text for n in needles)


def bool_count(items: Iterable[bool]) -> int:
    return sum(1 for x in items if x)


# =============================================================================
# HEURÍSTICAS SEMÂNTICAS
# =============================================================================

def classify_phase(
    proposicao: Dict[str, Any]
) -> Dict[str, Any]:
    texto = normalize_spaces(proposicao.get("texto", "")).lower()
    texto_curto = normalize_spaces(proposicao.get("texto_curto", "")).lower()
    bloco_id = str(proposicao.get("bloco_id", "")).strip()
    ordem = int(proposicao.get("ordem_global") or 0)

    classif = safe_dict(proposicao.get("classificacao_filosofica_inicial"))
    dominio = str(classif.get("dominio_principal", "")).strip()
    tipo_prop = str(safe_dict(proposicao.get("validacao_integral")).get("tipo_de_proposicao", "")).strip()

    flags = {
        "is_ontologia": dominio in {"ontologia", "metafisica"} or tipo_prop.startswith("ontologica_"),
        "is_antropologia": dominio == "antropologia_filosofica" or tipo_prop == "antropologica_estrutural",
        "is_mente": dominio == "filosofia_da_mente" or "conscien" in texto or "representa" in texto,
        "is_linguagem": dominio == "filosofia_da_linguagem" or text_contains_any(texto, ["linguagem", "símbolo", "simbolo", "mediação", "mediacao"]),
        "is_epistemologia": dominio == "epistemologia" or tipo_prop.startswith("epistemologica_"),
        "is_etica": dominio == "etica" or tipo_prop in {"etica_derivada", "normativa_derivada"},
        "is_normatividade": text_contains_any(texto, ["dever-ser", "normatividade", "dignidade", "vida boa", "bem", "mal"]),
        "mentions_field": text_contains_any(texto, ["campo", "campos"]),
        "mentions_potentiality": text_contains_any(texto, ["potencialidade", "potencialidades", "atualização", "actualização", "atualiz", "actualiz"]),
        "mentions_biology": text_contains_any(texto, ["biológ", "biolog", "organismo", "corpo", "corpó", "encarn", "vida", "metabol", "autorreg", "reprodu", "ecolog"]),
        "mentions_truth_error": text_contains_any(texto, ["verdade", "erro", "critério", "criterio", "adequação", "adequacao", "desadequação", "desadequacao"]),
        "mentions_action_damage": text_contains_any(texto, ["ação", "acao", "agir", "dano", "preservação", "preservacao", "correção", "correcao", "não-dano", "nao-dano"]),
    }

    return {
        "texto": texto,
        "texto_curto": texto_curto,
        "bloco_id": bloco_id,
        "ordem": ordem,
        "dominio": dominio,
        "tipo_prop": tipo_prop,
        "flags": flags,
    }


def infer_regimes_and_needs(proposicao: Dict[str, Any]) -> Dict[str, Any]:
    info = classify_phase(proposicao)
    texto = info["texto"]
    ordem = info["ordem"]
    bloco_id = info["bloco_id"]
    tipo_prop = info["tipo_prop"]
    flags = info["flags"]

    regimes: Set[str] = {"coerencia_dedutiva_interna", "rastreabilidade_arquitetural"}
    precisa_confronto = False
    precisa_ancoragem = False
    precisa_ponte = False
    precisa_campo = False
    precisa_reformulacao = False
    grau_risco = "baixo"
    grau_prioridade = safe_dict(proposicao.get("validacao_integral")).get("grau_prioridade", "media")
    grau_confianca = 0.82
    justificacoes: List[str] = []

    # Ontologia fundacional / estrutural / dinâmica
    if flags["is_ontologia"]:
        add_regime(regimes, "confronto_filosofico")
        precisa_confronto = True
        justificacoes.append("Proposição ontológica exige confronto filosófico estrutural.")
        grau_confianca = min(grau_confianca, 0.86)

        if tipo_prop == "ontologica_dinamica" or flags["mentions_field"] or flags["mentions_potentiality"]:
            add_regime(regimes, "cartografia_de_campo")
            precisa_campo = True
            justificacoes.append("Categoria dinâmica/campo beneficia de cartografia de campos do real.")
            grau_risco = max_risco(grau_risco, "medio")

        if flags["mentions_biology"]:
            add_regime(regimes, "compatibilidade_cientifica", "justificacao_de_ponte")
            precisa_ancoragem = True
            precisa_ponte = True
            justificacoes.append("Há inscrição material/biológica dentro de proposição ontológica.")
            grau_risco = max_risco(grau_risco, "alto")

    # Antropologia / mente / linguagem
    if flags["is_antropologia"] or flags["is_mente"] or flags["is_linguagem"]:
        add_regime(regimes, "confronto_filosofico", "justificacao_de_ponte")
        precisa_confronto = True
        precisa_ponte = True
        justificacoes.append("Zona antropológica/mente/linguagem exige ponte entre níveis e confronto filosófico.")
        grau_risco = max_risco(grau_risco, "alto")
        grau_confianca = min(grau_confianca, 0.79)

        if flags["is_mente"] or flags["mentions_biology"] or text_contains_any(texto, ["memória", "memoria", "consciên", "conscien", "cogni", "símbolo", "simbolo", "linguagem"]):
            add_regime(regimes, "compatibilidade_cientifica")
            precisa_ancoragem = True
            justificacoes.append("Tema cognitivo/encarnado pede ancoragem científica compatível.")
            grau_risco = max_risco(grau_risco, "alto")

        if flags["mentions_biology"]:
            add_regime(regimes, "ancoragem_cientifica_forte")
            justificacoes.append("Traço biológico/material torna a ancoragem científica mais forte.")

        if flags["mentions_field"] or bloco_id == "B4":
            add_regime(regimes, "cartografia_de_campo")
            precisa_campo = True
            justificacoes.append("A emergência do humano situado beneficia de cartografia de campos.")

    # Epistemologia
    if flags["is_epistemologia"] or flags["mentions_truth_error"]:
        add_regime(regimes, "confronto_filosofico")
        precisa_confronto = True
        justificacoes.append("Problema epistemológico requer confronto filosófico forte.")
        grau_risco = max_risco(grau_risco, "medio")
        grau_confianca = min(grau_confianca, 0.85)

        if text_contains_any(texto, ["representação", "representacao", "consciên", "conscien", "linguagem"]):
            add_regime(regimes, "justificacao_de_ponte")
            precisa_ponte = True
            justificacoes.append("Há mediação entre níveis cognitivos/representacionais.")
            grau_risco = max_risco(grau_risco, "alto")

    # Ética / normatividade
    if flags["is_etica"] or flags["is_normatividade"] or flags["mentions_action_damage"]:
        add_regime(regimes, "confronto_filosofico", "justificacao_de_ponte")
        precisa_confronto = True
        precisa_ponte = True
        justificacoes.append("Passagem à ética e normatividade exige ponte e confronto filosófico.")
        grau_risco = max_risco(grau_risco, "alto")
        grau_confianca = min(grau_confianca, 0.78)

        if text_contains_any(texto, ["ação", "acao", "dano", "preservação", "preservacao", "vulner", "corpo", "vida"]):
            add_regime(regimes, "compatibilidade_cientifica")
            precisa_ancoragem = True
            justificacoes.append("Ação, dano e vulnerabilidade beneficiam de compatibilidade científica/material.")
            grau_risco = max_risco(grau_risco, "alto")

        if text_contains_any(texto, ["campo", "co-exist", "coexist", "situad", "real"]):
            add_regime(regimes, "cartografia_de_campo")
            precisa_campo = True
            justificacoes.append("Normatividade situada beneficia de cartografia de campo.")
            grau_risco = max_risco(grau_risco, "alto")

    # Ajustes por ordem estrutural
    if ordem in {1, 11, 23, 30, 34, 38, 44, 46, 50, 51}:
        grau_prioridade = "estrutural"
    elif ordem <= 10 or 31 <= ordem <= 37:
        grau_prioridade = max_prioridade(grau_prioridade, "alta")
    else:
        grau_prioridade = max_prioridade(grau_prioridade, "media")

    # Pontos normalmente delicados
    if ordem in {24, 25, 26, 27, 28, 29, 30, 38, 42, 44, 45, 46, 47, 48, 49, 50, 51}:
        grau_risco = max_risco(grau_risco, "alto")
    if ordem in {30, 44, 46, 47, 50, 51}:
        grau_risco = max_risco(grau_risco, "critico")

    # Se nada ficou marcado além do mínimo, ontologia fundacional continua com confronto
    if regimes == {"coerencia_dedutiva_interna", "rastreabilidade_arquitetural"}:
        add_regime(regimes, "confronto_filosofico")
        precisa_confronto = True
        justificacoes.append("Fallback conservador: toda proposição nuclear deve entrar em confronto filosófico.")
        grau_risco = max_risco(grau_risco, "medio")

    return {
        "regimes": sorted(regimes),
        "precisa_confronto_filosofico": precisa_confronto,
        "precisa_ancoragem_cientifica": precisa_ancoragem,
        "precisa_ponte_entre_niveis": precisa_ponte,
        "precisa_cartografia_de_campo": precisa_campo,
        "precisa_reformulacao_conceitual": precisa_reformulacao,
        "grau_risco_salto": grau_risco,
        "grau_prioridade": grau_prioridade,
        "grau_confianca_atribuicao": round(grau_confianca, 2),
        "justificacao_atribuicao": " ".join(unique_preserve(justificacoes)),
    }


def max_risco(current: str, candidate: str) -> str:
    order = ["baixo", "medio", "alto", "critico"]
    return order[max(order.index(current), order.index(candidate))]


def max_prioridade(current: str, candidate: str) -> str:
    order = ["baixa", "media", "alta", "estrutural"]
    cur = current if current in order else "media"
    cand = candidate if candidate in order else "media"
    return order[max(order.index(cur), order.index(cand))]


def infer_temas_confronto(proposicao: Dict[str, Any]) -> Tuple[List[str], List[str], List[str], List[str]]:
    info = classify_phase(proposicao)
    texto = info["texto"]
    ordem = info["ordem"]
    flags = info["flags"]

    temas: List[str] = []
    autores: List[str] = []
    tradicoes: List[str] = []
    questoes: List[str] = []

    if flags["is_ontologia"]:
        temas += ["real", "ser", "diferença", "relação", "estrutura", "limite"]
        autores += ["Aristóteles", "Kant", "Heidegger"]
        tradicoes += ["metafisica_classica", "fenomenologia", "realismo_critico"]
        questoes += ["Como se distingue a estrutura do real de uma mera coerência conceptual?"]

        if flags["mentions_potentiality"]:
            temas += ["potencialidade", "mudança", "atualização"]
            autores += ["Aristóteles", "Whitehead"]
            tradicoes += ["metafisica_classica", "filosofia_do_processo"]

        if flags["mentions_field"]:
            temas += ["campo", "escala", "regionalização_do_real"]
            autores += ["Hartmann"]
            tradicoes += ["ontologia_estratificada"]

    if flags["is_antropologia"] or flags["is_mente"]:
        temas += ["humano_situado", "corporeidade", "consciência", "memória", "representação"]
        autores += ["Merleau-Ponty", "Jonas", "Plessner"]
        tradicoes += ["fenomenologia", "antropologia_filosofica", "filosofia_da_biologia"]
        questoes += ["Como justificar a especificidade do ser reflexivo sem dualismo nem reducionismo?"]

    if flags["is_linguagem"]:
        temas += ["símbolo", "linguagem", "mediação"]
        autores += ["Cassirer", "Wittgenstein", "Ricoeur"]
        tradicoes += ["filosofia_da_linguagem", "hermeneutica"]

    if flags["is_epistemologia"] or flags["mentions_truth_error"]:
        temas += ["verdade", "erro", "critério", "correção"]
        autores += ["Aristóteles", "Kant", "Peirce"]
        tradicoes += ["epistemologia", "pragmatismo", "realismo_critico"]
        questoes += ["Como assegurar um critério submetido ao real e não apenas ao sistema?"]

    if flags["is_etica"] or flags["is_normatividade"] or flags["mentions_action_damage"]:
        temas += ["ação", "dano", "bem", "mal", "normatividade", "dignidade", "vida_boa"]
        autores += ["Aristóteles", "Kant", "Hans Jonas", "MacIntyre"]
        tradicoes += ["etica_das_virtudes", "deontologia", "etica_da_responsabilidade"]
        questoes += ["Como passar do real e da ação situada à normatividade sem salto ilegítimo?"]

    if ordem in {46, 47, 48, 49, 50, 51}:
        questoes += ["Qual é o estatuto da derivação normativa a partir da estrutura do real?"]

    return (
        unique_preserve(temas),
        unique_preserve(autores),
        unique_preserve(tradicoes),
        unique_preserve(questoes),
    )


def infer_ancoragem_cientifica(proposicao: Dict[str, Any]) -> Tuple[List[str], List[str], List[str], str]:
    info = classify_phase(proposicao)
    texto = info["texto"]
    flags = info["flags"]
    ordem = info["ordem"]

    dominios: List[str] = []
    subdominios: List[str] = []
    tipos: List[str] = []
    observacoes: List[str] = []

    if not (
        safe_dict(proposicao.get("validacao_integral")).get("precisa_ancoragem_cientifica", False)
    ):
        return [], [], [], ""

    if flags["mentions_biology"] or flags["is_antropologia"]:
        dominios += ["biologia", "ecologia", "teoria_de_sistemas"]
        subdominios += ["biologia_dos_organismos", "autorregulacao", "homeostase", "corpo_situado"]
        tipos += ["compatibilidade_forte"]

    if flags["is_mente"] or flags["is_linguagem"]:
        dominios += ["neurociencia", "ciencia_cognitiva", "psicologia"]
        subdominios += ["memoria", "cognicao_incorporada", "representacao", "linguagem"]
        tipos += ["suporte_empirico_relevante"]

    if flags["mentions_field"] or flags["mentions_potentiality"]:
        dominios += ["ciencias_da_complexidade", "teoria_de_sistemas"]
        subdominios += ["dinamica_de_sistemas", "organizacao_multinivel", "emergencia"]
        tipos += ["compatibilidade_geral"]

    if flags["is_etica"] or flags["mentions_action_damage"]:
        dominios += ["biologia", "psicologia", "antropologia", "sociologia"]
        subdominios += ["vulnerabilidade", "acao_situada", "coexistencia", "cooperacao"]
        tipos += ["compatibilidade_geral"]

    if ordem in {24, 25, 26, 27, 28, 29, 30}:
        tipos += ["determinacao_material_necessaria"]
        observacoes.append("A zona da emergência do ser reflexivo pede determinação material mais forte.")

    if ordem in {44, 45, 46, 47, 48, 49, 50, 51}:
        observacoes.append("A ciência aqui funciona sobretudo como restrição e compatibilidade, não como substituição da derivação filosófica.")

    return (
        unique_preserve([d for d in dominios if d in VALID_DOMINIOS_CIENTIFICOS]),
        unique_preserve(subdominios),
        unique_preserve([t for t in tipos if t in VALID_TIPO_DEP_CIENTIFICA]),
        " ".join(unique_preserve(observacoes)),
    )


def infer_campos_do_real(proposicao: Dict[str, Any]) -> Tuple[List[str], List[str], List[str], List[str], str]:
    info = classify_phase(proposicao)
    texto = info["texto"]
    flags = info["flags"]
    ordem = info["ordem"]

    campos_p: List[str] = []
    campos_s: List[str] = []
    escalas: List[str] = []
    niveis: List[str] = []
    obs: List[str] = []

    if flags["is_ontologia"]:
        campos_p += ["integral_multicampo"]
        escalas += ["escala_multinivel"]
        niveis += ["estrutura"]

        if flags["mentions_field"] or flags["mentions_potentiality"]:
            obs += ["A proposição exige instanciação regional dos campos do real."]
            campos_s += ["fisico", "biologico", "historico_cultural"]

    if flags["mentions_biology"] or flags["is_antropologia"]:
        campos_p += ["biologico"]
        escalas += ["organismo", "sujeito_encarnado"]
        niveis += ["vida", "acao"]

    if flags["is_mente"]:
        campos_s += ["cognitivo_representacional", "sensorio_motor"]
        escalas += ["agente", "sujeito_encarnado"]
        niveis += ["cognicao", "representacao"]

    if flags["is_linguagem"]:
        campos_s += ["simbolico_linguistico", "intersubjetivo_social"]
        escalas += ["grupo_social", "cultura"]
        niveis += ["linguagem", "coexistencia"]

    if flags["is_epistemologia"]:
        campos_p += ["cognitivo_representacional"]
        escalas += ["agente"]
        niveis += ["representacao", "cognicao"]

    if flags["is_etica"] or flags["is_normatividade"]:
        campos_p += ["pratico_normativo", "intersubjetivo_social"]
        escalas += ["agente", "grupo_social", "instituicao"]
        niveis += ["acao", "normatividade", "valor", "coexistencia"]

    if ordem in {50, 51}:
        campos_s += ["historico_cultural"]
        escalas += ["cultura"]
        obs += ["Dignidade e vida boa implicam também regionalização histórico-cultural."]

    return (
        unique_preserve([x for x in campos_p if x in VALID_CAMPOS]),
        unique_preserve([x for x in campos_s if x in VALID_CAMPOS and x not in campos_p]),
        unique_preserve([x for x in escalas if x in VALID_ESCALAS]),
        unique_preserve([x for x in niveis if x in VALID_NIVEIS_REALIDADE]),
        " ".join(unique_preserve(obs)),
    )


def infer_pontes_entre_niveis(proposicao: Dict[str, Any]) -> List[Dict[str, Any]]:
    info = classify_phase(proposicao)
    texto = info["texto"]
    flags = info["flags"]
    ordem = info["ordem"]

    pontes: List[Dict[str, Any]] = []

    def add_ponte(
        origem: str,
        destino: str,
        tipo: str,
        descricao: str,
        risco: str,
    ) -> None:
        if origem not in VALID_NIVEL_PONTE or destino not in VALID_NIVEL_PONTE:
            return
        if tipo not in VALID_TIPO_PONTE or risco not in VALID_GRAU_RISCO:
            return
        pontes.append(
            {
                "nivel_origem": origem,
                "nivel_destino": destino,
                "tipo_ponte": tipo,
                "descricao": descricao,
                "risco": risco,
            }
        )

    if flags["is_antropologia"] or flags["mentions_biology"]:
        add_ponte(
            "ontologia_geral",
            "biologia_do_organismo",
            "determinacao_material",
            "Passagem do ente situado à sua determinação material como organismo vivo.",
            "alto",
        )

    if flags["is_mente"] or text_contains_any(texto, ["consciên", "conscien", "representa", "memória", "memoria"]):
        add_ponte(
            "biologia_do_organismo",
            "ciencia_cognitiva",
            "emergencia",
            "Passagem da organização viva/corporal à cognição, memória, representação e reflexividade.",
            "alto",
        )

    if flags["is_linguagem"]:
        add_ponte(
            "ciencia_cognitiva",
            "linguagem_simbolica",
            "articulacao_multinivel",
            "Passagem da cognição e mediação à linguagem/símbolo enquanto sistema partilhável.",
            "alto",
        )

    if flags["is_etica"] or flags["is_normatividade"]:
        add_ponte(
            "ontologia_dinamica" if flags["is_ontologia"] else "acao_pratica",
            "normatividade_etica",
            "derivacao_normativa",
            "Passagem do real e da ação situada à normatividade, dever-ser, dignidade ou vida boa.",
            "critico" if ordem in {46, 47, 50, 51} else "alto",
        )

    if flags["mentions_field"] or flags["mentions_potentiality"]:
        add_ponte(
            "ontologia_estrutural",
            "ontologia_dinamica",
            "instanciacao_regional",
            "Passagem de estrutura/limite para campos de potencialidade e atualização.",
            "medio",
        )

    return dedup_pontes(pontes)


def dedup_pontes(pontes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Set[Tuple[str, str, str, str, str]] = set()
    out: List[Dict[str, Any]] = []
    for p in pontes:
        key = (
            p.get("nivel_origem", ""),
            p.get("nivel_destino", ""),
            p.get("tipo_ponte", ""),
            p.get("descricao", ""),
            p.get("risco", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def infer_estado_trabalho(proposicao: Dict[str, Any]) -> Tuple[str, bool, str]:
    val = safe_dict(proposicao.get("validacao_integral"))
    precisa_confronto = bool(val.get("precisa_confronto_filosofico"))
    precisa_ancoragem = bool(val.get("precisa_ancoragem_cientifica"))
    precisa_ponte = bool(val.get("precisa_ponte_entre_niveis"))
    precisa_campo = bool(val.get("precisa_cartografia_de_campo"))
    risco = str(val.get("grau_risco_salto", "baixo"))
    ordem = int(proposicao.get("ordem_global") or 0)

    necessita_revisao = False
    motivo = ""
    estado = "classificada"

    if risco == "critico":
        necessita_revisao = True
        motivo = "Risco crítico de salto entre níveis ou de derivação normativa."
        estado = "pendente_revisao_humana"
        return estado, necessita_revisao, motivo

    if precisa_ponte:
        estado = "pendente_ponte_entre_niveis"
    elif precisa_ancoragem:
        estado = "pendente_ancoragem_cientifica"
    elif precisa_campo:
        estado = "pendente_cartografia_de_campo"
    elif precisa_confronto:
        estado = "pendente_confronto_filosofico"
    else:
        estado = "validada_internamente"

    if risco == "alto" and ordem in {30, 44, 46, 47, 50, 51}:
        necessita_revisao = True
        motivo = "Passo estruturalmente sensível com elevado risco de salto."
        estado = "pendente_revisao_humana"

    return estado, necessita_revisao, motivo


# =============================================================================
# ATRIBUIÇÃO
# =============================================================================

def atribuir_regimes(documento: Dict[str, Any]) -> Dict[str, Any]:
    doc = deepcopy(documento)
    props = safe_list(doc.get("proposicoes"))

    for prop in props:
        val = safe_dict(prop.get("validacao_integral"))
        confronto = safe_dict(prop.get("confronto_filosofico"))
        ancoragem = safe_dict(prop.get("ancoragem_cientifica"))
        campos = safe_dict(prop.get("campos_do_real"))
        estado = safe_dict(prop.get("estado_trabalho"))

        inferred = infer_regimes_and_needs(prop)
        val["regime_de_validacao"] = inferred["regimes"]
        val["precisa_confronto_filosofico"] = inferred["precisa_confronto_filosofico"]
        val["precisa_ancoragem_cientifica"] = inferred["precisa_ancoragem_cientifica"]
        val["precisa_ponte_entre_niveis"] = inferred["precisa_ponte_entre_niveis"]
        val["precisa_cartografia_de_campo"] = inferred["precisa_cartografia_de_campo"]
        val["precisa_reformulacao_conceitual"] = inferred["precisa_reformulacao_conceitual"]
        val["grau_risco_salto"] = inferred["grau_risco_salto"]
        val["grau_prioridade"] = inferred["grau_prioridade"]
        val["grau_confianca_atribuicao"] = inferred["grau_confianca_atribuicao"]
        val["justificacao_atribuicao"] = inferred["justificacao_atribuicao"]
        prop["validacao_integral"] = val

        temas, autores, tradicoes, questoes = infer_temas_confronto(prop)
        confronto["temas_de_confronto"] = temas
        confronto["autores_prioritarios"] = autores
        confronto["tradicoes_prioritarias"] = tradicoes
        confronto["questoes_abertas"] = questoes
        prop["confronto_filosofico"] = confronto

        dominios, subdominios, tipos_dep, obs_anc = infer_ancoragem_cientifica(prop)
        ancoragem["dominios_cientificos"] = dominios
        ancoragem["subdominios_cientificos"] = subdominios
        ancoragem["tipo_dependencia_cientifica"] = tipos_dep
        ancoragem["observacoes"] = obs_anc
        prop["ancoragem_cientifica"] = ancoragem

        campos_p, campos_s, escalas, niveis, obs_campos = infer_campos_do_real(prop)
        campos["campos_principais"] = campos_p
        campos["campos_secundarios"] = campos_s
        campos["escala_ontologica"] = escalas
        campos["nivel_de_realidade_implicado"] = niveis
        campos["observacoes"] = obs_campos
        prop["campos_do_real"] = campos

        prop["pontes_entre_niveis"] = infer_pontes_entre_niveis(prop)

        # Reconciliação entre necessidade de ponte e pontes efetivamente geradas.
        # Se a heurística marcou necessidade de ponte mas não foi gerada nenhuma
        # ponte concreta, corrigimos de forma conservadora para evitar falso positivo.
        if val.get("precisa_ponte_entre_niveis") and not prop["pontes_entre_niveis"]:
            val["precisa_ponte_entre_niveis"] = False
            if "justificacao_de_ponte" in val.get("regime_de_validacao", []):
                val["regime_de_validacao"] = [
                    r for r in val["regime_de_validacao"]
                    if r != "justificacao_de_ponte"
                ]
            justificacao = str(val.get("justificacao_atribuicao", "")).strip()
            nota = (
                " A marcação inicial de ponte entre níveis foi removida por não ter "
                "sido gerada nenhuma ponte concreta nesta fase heurística."
            )
            val["justificacao_atribuicao"] = (justificacao + nota).strip()

        prop["validacao_integral"] = val

        est, rev, motivo = infer_estado_trabalho(prop)
        estado["estado_atual"] = est
        estado["necessita_revisao_humana"] = rev
        estado["motivo_revisao_humana"] = motivo
        prop["estado_trabalho"] = estado

    # atualizar metadata/estatísticas
    metadata = safe_dict(doc.get("metadata"))
    metadata["data_geracao"] = utc_now_iso()
    metadata["gerado_por_script"] = Path(__file__).name
    metadata["estado_global"] = "atribuido"
    doc["metadata"] = metadata

    doc["estatisticas"] = recompute_statistics(doc)
    return doc


def recompute_statistics(doc: Dict[str, Any]) -> Dict[str, Any]:
    props = safe_list(doc.get("proposicoes"))
    blocos = Counter(str(p.get("bloco_id", "")).strip() for p in props)

    return {
        "total_proposicoes": len(props),
        "total_blocos": len(blocos),
        "proposicoes_por_bloco": dict(sorted(blocos.items())),
        "proposicoes_com_fragmentos": sum(1 for p in props if safe_dict(p.get("suporte_estrutural")).get("tem_fragmentos_rastreaveis")),
        "proposicoes_com_microlinhas": sum(1 for p in props if safe_dict(p.get("suporte_estrutural")).get("tem_microlinhas_rastreaveis")),
        "proposicoes_com_ramos": sum(1 for p in props if safe_dict(p.get("suporte_estrutural")).get("tem_ramos_rastreaveis")),
        "proposicoes_com_percursos": sum(1 for p in props if safe_dict(p.get("suporte_estrutural")).get("tem_percursos_rastreaveis")),
        "proposicoes_com_argumentos": sum(1 for p in props if safe_dict(p.get("suporte_estrutural")).get("tem_argumentos_rastreaveis")),
        "proposicoes_que_precisam_confronto_filosofico": sum(1 for p in props if safe_dict(p.get("validacao_integral")).get("precisa_confronto_filosofico")),
        "proposicoes_que_precisam_ancoragem_cientifica": sum(1 for p in props if safe_dict(p.get("validacao_integral")).get("precisa_ancoragem_cientifica")),
        "proposicoes_que_precisam_ponte_entre_niveis": sum(1 for p in props if safe_dict(p.get("validacao_integral")).get("precisa_ponte_entre_niveis")),
        "proposicoes_que_precisam_cartografia_de_campo": sum(1 for p in props if safe_dict(p.get("validacao_integral")).get("precisa_cartografia_de_campo")),
        "proposicoes_com_revisao_humana": sum(1 for p in props if safe_dict(p.get("estado_trabalho")).get("necessita_revisao_humana")),
    }


# =============================================================================
# VALIDAÇÃO
# =============================================================================

def validate_document(doc: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    props = safe_list(doc.get("proposicoes"))
    if not props:
        errors.append("A lista 'proposicoes' está vazia.")
        return errors

    ids = {p.get("proposicao_id") for p in props}

    for p in props:
        pid = str(p.get("proposicao_id", "<sem_id>"))
        val = safe_dict(p.get("validacao_integral"))
        confronto = safe_dict(p.get("confronto_filosofico"))
        ancoragem = safe_dict(p.get("ancoragem_cientifica"))
        campos = safe_dict(p.get("campos_do_real"))
        pontes = safe_list(p.get("pontes_entre_niveis"))
        estado = safe_dict(p.get("estado_trabalho"))
        deps = safe_dict(p.get("dependencias"))

        tipo_prop = str(val.get("tipo_de_proposicao", ""))
        if tipo_prop and tipo_prop not in VALID_TIPO_DE_PROPOSICAO:
            errors.append(f"{pid}: tipo_de_proposicao inválido: {tipo_prop}")

        for regime in safe_list(val.get("regime_de_validacao")):
            if regime not in VALID_REGIME:
                errors.append(f"{pid}: regime_de_validacao inválido: {regime}")

        risco = str(val.get("grau_risco_salto", ""))
        if risco and risco not in VALID_GRAU_RISCO:
            errors.append(f"{pid}: grau_risco_salto inválido: {risco}")

        prioridade = str(val.get("grau_prioridade", ""))
        if prioridade and prioridade not in VALID_GRAU_PRIORIDADE:
            errors.append(f"{pid}: grau_prioridade inválido: {prioridade}")

        try:
            gc = float(val.get("grau_confianca_atribuicao", 0.0))
            if not (0.0 <= gc <= 1.0):
                errors.append(f"{pid}: grau_confianca_atribuicao fora do intervalo [0,1].")
        except Exception:
            errors.append(f"{pid}: grau_confianca_atribuicao inválido.")

        if bool(val.get("precisa_confronto_filosofico")) and not safe_list(confronto.get("temas_de_confronto")):
            errors.append(f"{pid}: precisa_confronto_filosofico=true mas temas_de_confronto vazio.")

        if bool(val.get("precisa_ancoragem_cientifica")) and not safe_list(ancoragem.get("dominios_cientificos")):
            errors.append(f"{pid}: precisa_ancoragem_cientifica=true mas dominios_cientificos vazio.")

        if bool(val.get("precisa_ponte_entre_niveis")) and not pontes:
            errors.append(f"{pid}: precisa_ponte_entre_niveis=true mas pontes_entre_niveis vazio.")

        if bool(val.get("precisa_cartografia_de_campo")):
            campos_p = safe_list(campos.get("campos_principais"))
            campos_s = safe_list(campos.get("campos_secundarios"))
            if not campos_p and not campos_s:
                errors.append(f"{pid}: precisa_cartografia_de_campo=true mas campos_do_real vazio.")

        for campo in safe_list(campos.get("campos_principais")) + safe_list(campos.get("campos_secundarios")):
            if campo not in VALID_CAMPOS:
                errors.append(f"{pid}: campo_do_real inválido: {campo}")

        for esc in safe_list(campos.get("escala_ontologica")):
            if esc not in VALID_ESCALAS:
                errors.append(f"{pid}: escala_ontologica inválida: {esc}")

        for nivel in safe_list(campos.get("nivel_de_realidade_implicado")):
            if nivel not in VALID_NIVEIS_REALIDADE:
                errors.append(f"{pid}: nivel_de_realidade_implicado inválido: {nivel}")

        for dom in safe_list(ancoragem.get("dominios_cientificos")):
            if dom not in VALID_DOMINIOS_CIENTIFICOS:
                errors.append(f"{pid}: dominio_cientifico inválido: {dom}")

        for td in safe_list(ancoragem.get("tipo_dependencia_cientifica")):
            if td not in VALID_TIPO_DEP_CIENTIFICA:
                errors.append(f"{pid}: tipo_dependencia_cientifica inválido: {td}")

        for ponte in pontes:
            ponte = safe_dict(ponte)
            no = str(ponte.get("nivel_origem", ""))
            nd = str(ponte.get("nivel_destino", ""))
            tp = str(ponte.get("tipo_ponte", ""))
            rr = str(ponte.get("risco", ""))
            if no not in VALID_NIVEL_PONTE:
                errors.append(f"{pid}: nivel_origem inválido: {no}")
            if nd not in VALID_NIVEL_PONTE:
                errors.append(f"{pid}: nivel_destino inválido: {nd}")
            if tp not in VALID_TIPO_PONTE:
                errors.append(f"{pid}: tipo_ponte inválido: {tp}")
            if rr not in VALID_GRAU_RISCO:
                errors.append(f"{pid}: risco de ponte inválido: {rr}")

        est = str(estado.get("estado_atual", ""))
        if est not in VALID_ESTADO_TRABALHO:
            errors.append(f"{pid}: estado_atual inválido: {est}")

        if bool(estado.get("necessita_revisao_humana")) and not normalize_spaces(estado.get("motivo_revisao_humana", "")):
            errors.append(f"{pid}: necessita_revisao_humana=true mas motivo vazio.")

        anteriores = set(safe_list(deps.get("dependencias_anteriores")))
        imediatas = set(safe_list(deps.get("dependencias_imediatas")))
        distais = set(safe_list(deps.get("dependencias_distais")))
        posteriores = set(safe_list(deps.get("dependencias_posteriores")))
        if pid in anteriores or pid in imediatas or pid in distais or pid in posteriores:
            errors.append(f"{pid}: auto-dependência detetada.")
        if not imediatas.issubset(anteriores):
            errors.append(f"{pid}: dependencias_imediatas não são subconjunto de dependencias_anteriores.")
        if not distais.issubset(anteriores):
            errors.append(f"{pid}: dependencias_distais não são subconjunto de dependencias_anteriores.")
        for ref in anteriores | posteriores:
            if ref not in ids:
                errors.append(f"{pid}: dependência refere proposição inexistente: {ref}")

    return errors


# =============================================================================
# RELATÓRIO
# =============================================================================

def build_report(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    doc: Dict[str, Any],
    validation_errors: List[str],
) -> str:
    props = safe_list(doc.get("proposicoes"))
    stats = safe_dict(doc.get("estatisticas"))

    regimes_counter: Counter[str] = Counter()
    risco_counter: Counter[str] = Counter()
    prioridade_counter: Counter[str] = Counter()
    estado_counter: Counter[str] = Counter()

    for p in props:
        val = safe_dict(p.get("validacao_integral"))
        estado = safe_dict(p.get("estado_trabalho"))
        for rg in safe_list(val.get("regime_de_validacao")):
            regimes_counter[str(rg)] += 1
        risco_counter[str(val.get("grau_risco_salto", ""))] += 1
        prioridade_counter[str(val.get("grau_prioridade", ""))] += 1
        estado_counter[str(estado.get("estado_atual", ""))] += 1

    lines: List[str] = []
    lines.append("RELATÓRIO — ATRIBUIÇÃO DE REGIMES DE VALIDAÇÃO V1")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"Data UTC: {safe_dict(doc.get('metadata')).get('data_geracao', '')}")
    lines.append(f"Script: {safe_dict(doc.get('metadata')).get('gerado_por_script', '')}")
    lines.append("")
    lines.append("FICHEIROS")
    lines.append("-" * 78)
    lines.append(f"Input JSON: {input_path}")
    lines.append(f"Output JSON: {output_path}")
    lines.append(f"Relatório: {report_path}")
    lines.append("")
    lines.append("ESTATÍSTICAS GERAIS")
    lines.append("-" * 78)
    lines.append(f"Total de proposições: {stats.get('total_proposicoes', 0)}")
    lines.append(f"Precisam de confronto filosófico: {stats.get('proposicoes_que_precisam_confronto_filosofico', 0)}")
    lines.append(f"Precisam de ancoragem científica: {stats.get('proposicoes_que_precisam_ancoragem_cientifica', 0)}")
    lines.append(f"Precisam de ponte entre níveis: {stats.get('proposicoes_que_precisam_ponte_entre_niveis', 0)}")
    lines.append(f"Precisam de cartografia de campo: {stats.get('proposicoes_que_precisam_cartografia_de_campo', 0)}")
    lines.append(f"Com revisão humana: {stats.get('proposicoes_com_revisao_humana', 0)}")
    lines.append("")
    lines.append("DISTRIBUIÇÕES")
    lines.append("-" * 78)
    lines.append(f"Regimes de validação: {json.dumps(dict(sorted(regimes_counter.items())), ensure_ascii=False)}")
    lines.append(f"Grau de risco: {json.dumps(dict(sorted(risco_counter.items())), ensure_ascii=False)}")
    lines.append(f"Grau de prioridade: {json.dumps(dict(sorted(prioridade_counter.items())), ensure_ascii=False)}")
    lines.append(f"Estado de trabalho: {json.dumps(dict(sorted(estado_counter.items())), ensure_ascii=False)}")
    lines.append("")
    lines.append("PROPOSIÇÕES COM REVISÃO HUMANA")
    lines.append("-" * 78)
    flagged = [
        (
            p.get("proposicao_id", ""),
            safe_dict(p.get("estado_trabalho")).get("motivo_revisao_humana", ""),
        )
        for p in props
        if safe_dict(p.get("estado_trabalho")).get("necessita_revisao_humana")
    ]
    if flagged:
        for pid, motivo in flagged:
            lines.append(f"- {pid}: {motivo}")
    else:
        lines.append("Nenhuma.")

    lines.append("")
    lines.append("VALIDAÇÃO")
    lines.append("-" * 78)
    if validation_errors:
        lines.append(f"Foram encontrados {len(validation_errors)} erro(s):")
        for err in validation_errors:
            lines.append(f"- {err}")
    else:
        lines.append("Sem erros de validação.")

    lines.append("")
    lines.append("OBSERVAÇÃO")
    lines.append("-" * 78)
    lines.append(
        "Este script produz uma atribuição inicial, conservadora e auditável. "
        "Ele não substitui a fase posterior de confronto filosófico substantivo, "
        "ancoragem científica detalhada, elaboração de pontes entre níveis "
        "e cartografia aprofundada dos campos do real."
    )
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# ARGPARSE
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Atribui regimes de validação ao ficheiro de proposições nucleares enriquecidas."
    )
    parser.add_argument(
        "--project-root",
        help="Raiz do projeto. Se omitida, será inferida automaticamente.",
    )
    parser.add_argument(
        "--input-json",
        help="Caminho do ficheiro proposicoes_nucleares_enriquecidas_v1.json. "
             "Se omitido, usa 16_validacao_integral/01_dados/...",
    )
    parser.add_argument(
        "--output-json",
        help="Caminho do output JSON. Se omitido, sobrescreve o ficheiro de input.",
    )
    parser.add_argument(
        "--output-relatorio",
        help="Caminho do relatório TXT.",
    )
    return parser


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        project_root = project_root_from_explicit_or_cwd(
            Path(args.project_root) if args.project_root else None
        )

        input_json_path = (
            Path(args.input_json).resolve()
            if args.input_json
            else resolve_relative(project_root, DEFAULT_INPUT_JSON_RELATIVE)
        )
        output_json_path = (
            Path(args.output_json).resolve()
            if args.output_json
            else (project_root / DEFAULT_OUTPUT_JSON_RELATIVE).resolve()
        )
        output_report_path = (
            Path(args.output_relatorio).resolve()
            if args.output_relatorio
            else (project_root / DEFAULT_REPORT_RELATIVE).resolve()
        )

        doc = read_json(input_json_path)
        doc = atribuir_regimes(doc)

        validation_errors = validate_document(doc)

        ensure_parent(output_json_path)
        ensure_parent(output_report_path)

        write_json(output_json_path, doc)
        report = build_report(
            input_path=input_json_path,
            output_path=output_json_path,
            report_path=output_report_path,
            doc=doc,
            validation_errors=validation_errors,
        )
        write_text(output_report_path, report)

        print(f"JSON atualizado em: {output_json_path}")
        print(f"Relatório gerado em: {output_report_path}")

        if validation_errors:
            print(f"Atenção: foram detetados {len(validation_errors)} erro(s) de validação.")
            return 2

        print("Concluído sem erros de validação.")
        return 0

    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())