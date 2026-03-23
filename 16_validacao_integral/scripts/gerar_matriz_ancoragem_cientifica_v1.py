#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gerar_matriz_ancoragem_cientifica_v1.py

Gera a matriz derivada de ancoragem científica a partir do ficheiro
proposicoes_nucleares_enriquecidas_v1.json.

Objetivos:
- extrair e consolidar as necessidades de ancoragem científica já atribuídas;
- agrupar proposições por tema científico-material relevante;
- gerar uma matriz autónoma, auditável e pronta para revisão humana;
- preservar rastreabilidade para proposições e blocos relacionados;
- produzir relatório de geração.

Outputs:
- 16_validacao_integral/01_dados/matriz_ancoragem_cientifica_v1.json
- 16_validacao_integral/02_outputs/relatorio_geracao_matriz_ancoragem_cientifica_v1.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
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

DEFAULT_INPUT_PROPOSICOES_RELATIVE = Path(
    "16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json"
)
DEFAULT_OUTPUT_JSON_RELATIVE = Path(
    "16_validacao_integral/01_dados/matriz_ancoragem_cientifica_v1.json"
)
DEFAULT_REPORT_RELATIVE = Path(
    "16_validacao_integral/02_outputs/relatorio_geracao_matriz_ancoragem_cientifica_v1.txt"
)


# =============================================================================
# ENUMS / CONSTANTES
# =============================================================================

VALID_ESTADO_GLOBAL = {
    "em_construcao",
    "extraido",
    "enriquecido",
    "validado",
    "integrado",
}

VALID_DOMINIO_CIENTIFICO = {
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

VALID_TIPO_DEPENDENCIA = {
    "nao_aplicavel",
    "compatibilidade_geral",
    "compatibilidade_forte",
    "suporte_empirico_relevante",
    "determinacao_material_necessaria",
    "exemplificacao_regional",
    "restricao_cientifica_importante",
}

VALID_GRAU_SOLIDEZ = {
    "baixo",
    "medio",
    "alto",
    "muito_alto",
}

VALID_ESTADO_ITEM = {
    "por_preencher",
    "preenchido",
    "revisto",
    "validado",
    "integrado",
}


# =============================================================================
# UTILITÁRIOS GERAIS
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


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_spaces(text: str) -> str:
    return " ".join((text or "").strip().split())


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
        if (cand / DEFAULT_INPUT_PROPOSICOES_RELATIVE).exists():
            return cand.resolve()

    return script_path.parent.parent.parent


def resolve_relative(project_root: Path, relative_path: Path) -> Path:
    path = (project_root / relative_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {path}")
    return path


def text_contains_any(text: str, needles: Sequence[str]) -> bool:
    return any(n in text for n in needles)


# =============================================================================
# HEURÍSTICAS DE AGRUPAMENTO
# =============================================================================

def classify_scientific_cluster(proposicao: Dict[str, Any]) -> str:
    texto = normalize_spaces(proposicao.get("texto", "")).lower()
    ancoragem = safe_dict(proposicao.get("ancoragem_cientifica"))
    dominios = set(str(x) for x in safe_list(ancoragem.get("dominios_cientificos")))
    subdominios = set(str(x).lower() for x in safe_list(ancoragem.get("subdominios_cientificos")))
    ordem = int(proposicao.get("ordem_global") or 0)

    if (
        {"biologia", "ecologia", "teoria_de_sistemas"} & dominios
        and {"neurociencia", "ciencia_cognitiva"} & dominios
    ):
        return "vida_corporeidade_e_emergencia_cognitiva"

    if {"biologia", "ecologia", "teoria_de_sistemas"} & dominios:
        if text_contains_any(texto, ["organismo", "corpo", "vida", "autorreg", "reprodu", "metabol", "vulner"]):
            return "vida_corporeidade_e_organizacao"
        return "organizacao_biologica_e_sistemica"

    if {"neurociencia", "ciencia_cognitiva", "psicologia"} & dominios:
        if text_contains_any(texto, ["linguagem", "símbolo", "simbolo", "mediação", "mediacao"]):
            return "cognicao_mediação_e_linguagem"
        return "cognicao_memoria_representacao_e_reflexividade"

    if {"ciencias_da_complexidade", "teoria_de_sistemas"} & dominios:
        return "campos_potencialidade_e_dinamica_multinivel"

    if {"antropologia", "sociologia"} & dominios:
        return "acao_situada_coexistencia_e_formas_sociais"

    if text_contains_any(texto, ["dano", "ação", "acao", "bem", "mal", "normatividade", "dignidade", "vida boa"]):
        return "vulnerabilidade_acao_e_restricoes_materialmente_relevantes"

    if ordem in {24, 25, 26, 27, 28, 29, 30}:
        return "vida_corporeidade_e_emergencia_cognitiva"

    return "compatibilidade_cientifica_geral_do_sistema"


def theme_description(cluster: str) -> str:
    mapping = {
        "vida_corporeidade_e_emergencia_cognitiva":
            "Articulação entre vida, corpo, organização viva e emergência de cognição, memória, representação ou reflexividade.",
        "vida_corporeidade_e_organizacao":
            "Determinação material do ser vivo, do corpo e da organização autorregulada enquanto base do ente situado.",
        "organizacao_biologica_e_sistemica":
            "Compatibilidade do sistema com descrição biológica, ecológica e sistémica de entidades e processos vivos.",
        "cognicao_memoria_representacao_e_reflexividade":
            "Ancoragem científica de fenómenos cognitivos, memoriais, representacionais e reflexivos.",
        "cognicao_mediação_e_linguagem":
            "Articulação entre cognição, mediação, simbolização e linguagem em termos cientificamente compatíveis.",
        "campos_potencialidade_e_dinamica_multinivel":
            "Compatibilidade entre categorias de campo, potencialidade, atualização e modelos dinâmicos/multinível.",
        "acao_situada_coexistencia_e_formas_sociais":
            "Inscrição material e social da ação situada, coexistência e formas coletivas.",
        "vulnerabilidade_acao_e_restricoes_materialmente_relevantes":
            "Restrições materialmente relevantes para dano, vulnerabilidade, ação e formas práticas.",
        "compatibilidade_cientifica_geral_do_sistema":
            "Compatibilidade científica geral do sistema em zonas que não exigem uma determinação material tão específica.",
    }
    return mapping.get(cluster, "Tema científico-material a especificar.")


def infer_tipo_evidencia_necessaria(
    dominios: Sequence[str],
    tipos_dependencia: Sequence[str],
    proposicoes: Sequence[Dict[str, Any]],
) -> List[str]:
    evidencias: List[str] = []

    doms = set(dominios)
    deps = set(tipos_dependencia)
    textos = " ".join(
        normalize_spaces(p.get("texto", "")).lower()
        for p in proposicoes
    )

    if "determinacao_material_necessaria" in deps:
        evidencias.append("explicitação material forte do tipo de ente ou processo em causa")

    if "suporte_empirico_relevante" in deps:
        evidencias.append("suporte empírico relevante sobre processos ou capacidades implicadas")

    if "compatibilidade_forte" in deps:
        evidencias.append("compatibilidade forte com resultados científicos consolidados")

    if "compatibilidade_geral" in deps:
        evidencias.append("compatibilidade geral com o melhor conhecimento científico disponível")

    if "restricao_cientifica_importante" in deps:
        evidencias.append("restrições científicas negativas a usos filosóficos excessivos")

    if {"biologia", "ecologia"} & doms:
        evidencias.append("descrição de organismos, vulnerabilidade, autorregulação e inserção ecológica")

    if {"neurociencia", "ciencia_cognitiva", "psicologia"} & doms:
        evidencias.append("descrição de memória, cognição, representação, incorporação e linguagem")

    if {"ciencias_da_complexidade", "teoria_de_sistemas"} & doms:
        evidencias.append("modelos de organização, dinâmica, emergência e níveis")

    if {"sociologia", "antropologia"} & doms:
        evidencias.append("descrição situada de formas sociais, ação coletiva e coexistência")

    if text_contains_any(textos, ["bem", "mal", "normatividade", "dever-ser", "dignidade", "vida boa"]):
        evidencias.append("função da ciência como restrição e não como substituição da derivação normativa")

    return unique_preserve(evidencias)


def infer_estado_atual_ancoragem(
    tipos_dependencia: Sequence[str],
    dominios: Sequence[str],
    proposicoes: Sequence[Dict[str, Any]],
) -> str:
    deps = set(tipos_dependencia)

    if "determinacao_material_necessaria" in deps:
        return "carece de elaboração material robusta"
    if "suporte_empirico_relevante" in deps:
        return "carece de suporte empírico relevante"
    if "compatibilidade_forte" in deps:
        return "carece de compatibilização científica forte"
    if "compatibilidade_geral" in deps:
        return "carece de verificação de compatibilidade geral"
    if dominios:
        return "carece de recorte científico temático"
    return "não suficientemente determinado"


def infer_restricoes_ou_alertas(
    dominios: Sequence[str],
    tipos_dependencia: Sequence[str],
    cluster: str,
    proposicoes: Sequence[Dict[str, Any]],
) -> List[str]:
    alerts: List[str] = []
    doms = set(dominios)
    deps = set(tipos_dependencia)
    textos = " ".join(
        normalize_spaces(p.get("texto", "")).lower()
        for p in proposicoes
    )

    if "determinacao_material_necessaria" in deps:
        alerts.append("Evitar deixar a determinação material do ente ou processo em branco.")

    if {"biologia", "ecologia"} & doms:
        alerts.append("Evitar reducionismo biologicista e evitar também abstração desencarnada.")

    if {"neurociencia", "ciencia_cognitiva"} & doms:
        alerts.append("Evitar inferências excessivas da ciência empírica para teses ontológicas fortes.")
        alerts.append("Distinguir correlação empírica, condição material e identidade ontológica.")

    if {"ciencias_da_complexidade", "teoria_de_sistemas"} & doms:
        alerts.append("Não confundir modelos dinâmicos com prova imediata de categorias ontológicas.")

    if text_contains_any(textos, ["normatividade", "dever-ser", "dignidade", "vida boa", "bem", "mal"]):
        alerts.append("A ciência aqui opera sobretudo como restrição e compatibilidade, não como fundamento normativo suficiente.")

    if cluster == "cognicao_mediação_e_linguagem":
        alerts.append("Distinguir linguagem enquanto sistema simbólico de base neurocognitiva sem reduzi-la a ela.")

    if cluster == "vida_corporeidade_e_emergencia_cognitiva":
        alerts.append("Explicitar melhor a passagem entre corpo vivo e reflexividade, evitando dualismo implícito.")

    return unique_preserve(alerts)


def infer_perguntas_de_investigacao(
    cluster: str,
    dominios: Sequence[str],
    proposicoes: Sequence[Dict[str, Any]],
) -> List[str]:
    perguntas: List[str] = []

    if cluster == "vida_corporeidade_e_emergencia_cognitiva":
        perguntas += [
            "Que condições biológicas mínimas suportam cognição, memória e reflexividade?",
            "Como justificar a continuidade entre vida organizada e emergência de representação sem colapso reducionista?",
        ]
    elif cluster == "vida_corporeidade_e_organizacao":
        perguntas += [
            "Que traços biológicos são indispensáveis para pensar o ente situado como organismo vivo?",
            "Como descrever autorregulação, vulnerabilidade e corporeidade de forma filosoficamente integrada?",
        ]
    elif cluster == "cognicao_memoria_representacao_e_reflexividade":
        perguntas += [
            "Que suporte empírico é relevante para memória, representação e consciência reflexiva?",
            "Como distinguir níveis de cognição, representação e reflexividade de forma não simplista?",
        ]
    elif cluster == "cognicao_mediação_e_linguagem":
        perguntas += [
            "Que relações cientificamente sustentáveis existem entre cognição incorporada, simbolização e linguagem?",
            "Como evitar reduzir linguagem a mera função neurocognitiva mantendo ancoragem material?",
        ]
    elif cluster == "campos_potencialidade_e_dinamica_multinivel":
        perguntas += [
            "Que modelos científicos ajudam a pensar campos, dinâmica, emergência e níveis?",
            "Como distinguir analogia útil, compatibilidade científica e prova ontológica propriamente dita?",
        ]
    elif cluster == "acao_situada_coexistencia_e_formas_sociais":
        perguntas += [
            "Que ciências ajudam a descrever ação situada, coexistência e formas sociais relevantes?",
            "Como articular dimensão biográfica, social e institucional sem perder a escala ontológica?",
        ]
    elif cluster == "vulnerabilidade_acao_e_restricoes_materialmente_relevantes":
        perguntas += [
            "Que dados científicos restringem o uso de categorias como dano, vulnerabilidade e preservação?",
            "Que papel material tem o corpo vulnerável na assimetria prática das ações?",
        ]
    else:
        perguntas += [
            "Que tipo de ciência é realmente necessária aqui: compatibilidade geral, suporte empírico ou determinação material?",
            "Onde termina a utilidade científica e começa o trabalho propriamente filosófico de integração?",
        ]

    return unique_preserve(perguntas)


def infer_exemplos_de_fenomenos(
    dominios: Sequence[str],
    cluster: str,
    proposicoes: Sequence[Dict[str, Any]],
) -> List[str]:
    exemplos: List[str] = []
    doms = set(dominios)

    if {"biologia", "ecologia"} & doms:
        exemplos += ["organismos vivos", "autorregulação", "homeostase", "vulnerabilidade corporal", "inserção ecológica"]
    if {"neurociencia", "ciencia_cognitiva"} & doms:
        exemplos += ["memória", "cognição incorporada", "atenção", "representação", "aprendizagem"]
    if {"linguistica"} & doms:
        exemplos += ["sistemas simbólicos", "linguagem", "produção e compreensão linguística"]
    if {"ciencias_da_complexidade", "teoria_de_sistemas"} & doms:
        exemplos += ["dinâmica de sistemas", "organização multinível", "emergência", "estabilidade e transição"]
    if {"sociologia", "antropologia"} & doms:
        exemplos += ["cooperação", "formas sociais", "instituições", "práticas coletivas"]

    if cluster == "vulnerabilidade_acao_e_restricoes_materialmente_relevantes":
        exemplos += ["dano real", "preservação de condições de vida", "estreitamento do poder-ser"]

    return unique_preserve(exemplos)


def infer_grau_solidez(
    tipos_dependencia: Sequence[str],
    dominios: Sequence[str],
    proposicoes: Sequence[Dict[str, Any]],
) -> str:
    deps = set(tipos_dependencia)

    if "determinacao_material_necessaria" in deps:
        return "medio"
    if "suporte_empirico_relevante" in deps and "compatibilidade_forte" in deps:
        return "medio"
    if "compatibilidade_forte" in deps:
        return "alto"
    if "compatibilidade_geral" in deps:
        return "medio"
    if dominios:
        return "medio"
    return "baixo"


def infer_requires_human_review(
    cluster: str,
    tipos_dependencia: Sequence[str],
    proposicoes: Sequence[Dict[str, Any]],
) -> Tuple[bool, str]:
    deps = set(tipos_dependencia)
    flagged = [
        p for p in proposicoes
        if bool(safe_dict(p.get("estado_trabalho")).get("necessita_revisao_humana"))
    ]
    flagged_ids = ", ".join(
        p.get("proposicao_id", "") for p in flagged if p.get("proposicao_id")
    )

    if "determinacao_material_necessaria" in deps:
        return True, "O tema exige determinação material necessária e revisão humana."
    if flagged:
        return True, f"O tema agrega proposições já marcadas para revisão humana: {flagged_ids}."
    if cluster in {
        "vida_corporeidade_e_emergencia_cognitiva",
        "cognicao_mediação_e_linguagem",
        "vulnerabilidade_acao_e_restricoes_materialmente_relevantes",
    }:
        return True, "Tema sensível, com risco de extrapolação entre níveis, exige revisão humana."
    return False, ""


def infer_estado_item(
    tipos_dependencia: Sequence[str],
    proposicoes: Sequence[Dict[str, Any]],
) -> str:
    deps = set(tipos_dependencia)
    if "determinacao_material_necessaria" in deps:
        return "por_preencher"
    if any(bool(safe_dict(p.get("estado_trabalho")).get("necessita_revisao_humana")) for p in proposicoes):
        return "por_preencher"
    return "preenchido"


# =============================================================================
# GERAÇÃO DA MATRIZ
# =============================================================================

def build_science_groups(proposicoes: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for prop in proposicoes:
        val = safe_dict(prop.get("validacao_integral"))
        if not bool(val.get("precisa_ancoragem_cientifica")):
            continue

        cluster = classify_scientific_cluster(prop)
        groups[cluster].append(prop)

    return groups


def aggregate_domains(proposicoes: Sequence[Dict[str, Any]]) -> Tuple[List[str], List[str], List[str]]:
    dominios: List[str] = []
    subdominios: List[str] = []
    tipos_dep: List[str] = []

    for p in proposicoes:
        anc = safe_dict(p.get("ancoragem_cientifica"))
        dominios.extend(
            str(x) for x in safe_list(anc.get("dominios_cientificos"))
            if isinstance(x, str) and x in VALID_DOMINIO_CIENTIFICO
        )
        subdominios.extend(
            str(x) for x in safe_list(anc.get("subdominios_cientificos"))
            if isinstance(x, str)
        )
        tipos_dep.extend(
            str(x) for x in safe_list(anc.get("tipo_dependencia_cientifica"))
            if isinstance(x, str) and x in VALID_TIPO_DEPENDENCIA
        )

    return unique_preserve(dominios), unique_preserve(subdominios), unique_preserve(tipos_dep)


def build_matrix_document(
    proposicoes_doc: Dict[str, Any],
    input_path: Path,
) -> Dict[str, Any]:
    proposicoes = safe_list(proposicoes_doc.get("proposicoes"))
    groups = build_science_groups(proposicoes)

    entradas: List[Dict[str, Any]] = []
    entry_counter = 1

    for cluster, props_group in sorted(groups.items(), key=lambda x: x[0]):
        proposicao_ids = unique_preserve(
            p.get("proposicao_id", "")
            for p in props_group
            if p.get("proposicao_id")
        )
        blocos_relacionados = unique_preserve(
            str(p.get("bloco_id", "")).strip()
            for p in props_group
            if p.get("bloco_id")
        )

        dominios, subdominios, tipos_dep = aggregate_domains(props_group)
        tema = cluster
        descricao = theme_description(cluster)
        tipo_evidencia = infer_tipo_evidencia_necessaria(dominios, tipos_dep, props_group)
        estado_ancoragem = infer_estado_atual_ancoragem(tipos_dep, dominios, props_group)
        alertas = infer_restricoes_ou_alertas(dominios, tipos_dep, cluster, props_group)
        perguntas = infer_perguntas_de_investigacao(cluster, dominios, props_group)
        exemplos = infer_exemplos_de_fenomenos(dominios, cluster, props_group)
        grau_solidez = infer_grau_solidez(tipos_dep, dominios, props_group)
        necessita_revisao, motivo_revisao = infer_requires_human_review(cluster, tipos_dep, props_group)
        estado_item = infer_estado_item(tipos_dep, props_group)

        entrada = {
            "entrada_id": f"AC{entry_counter:02d}",
            "proposicao_ids": proposicao_ids,
            "blocos_relacionados": blocos_relacionados,
            "tema_cientifico": tema,
            "descricao_do_tema": descricao,
            "dominios_cientificos": dominios,
            "subdominios_cientificos": subdominios,
            "tipo_dependencia_cientifica": tipos_dep,
            "tipo_de_evidencia_necessaria": tipo_evidencia,
            "estado_atual_da_ancoragem": estado_ancoragem,
            "restricoes_ou_alertas": alertas,
            "perguntas_de_investigacao": perguntas,
            "exemplos_de_fenomenos_ou_processos": exemplos,
            "grau_solidez": grau_solidez,
            "notas": "",
            "estado_item": estado_item,
            "necessita_revisao_humana": necessita_revisao,
            "motivo_revisao_humana": motivo_revisao,
        }
        entradas.append(entrada)
        entry_counter += 1

    total_dominios = Counter()
    for e in entradas:
        for dom in safe_list(e.get("dominios_cientificos")):
            total_dominios[str(dom)] += 1

    doc = {
        "metadata": {
            "schema_nome": "matriz_ancoragem_cientifica_v1",
            "schema_versao": "1.0",
            "data_geracao": utc_now_iso(),
            "gerado_por_script": Path(__file__).name,
            "descricao": "Matriz de ancoragem científica das proposições nucleares da fase pós-árvore.",
            "idioma": "pt-PT",
            "projeto": "arvore_do_pensamento",
            "estado_global": "enriquecido",
        },
        "fontes": {
            "fonte_proposicoes_enriquecidas": {
                "caminho": str(input_path.parent),
                "ficheiro": input_path.name,
                "hash_opcional": "",
            },
            "fontes_cientificas_iniciais": [],
        },
        "estatisticas": {
            "total_proposicoes_mapeadas": len(
                {
                    pid
                    for e in entradas
                    for pid in safe_list(e.get("proposicao_ids"))
                    if isinstance(pid, str) and pid.strip()
                }
            ),
            "total_dominios_cientificos": len(total_dominios),
            "total_itens_com_suporte_empirico": sum(
                1 for e in entradas if "suporte_empirico_relevante" in safe_list(e.get("tipo_dependencia_cientifica"))
            ),
            "total_itens_com_determinacao_material": sum(
                1 for e in entradas if "determinacao_material_necessaria" in safe_list(e.get("tipo_dependencia_cientifica"))
            ),
            "total_itens_com_restricao_cientifica": sum(
                1 for e in entradas if "restricao_cientifica_importante" in safe_list(e.get("tipo_dependencia_cientifica"))
            ),
        },
        "enums_documentados": {
            "estado_global": [
                "em_construcao",
                "extraido",
                "enriquecido",
                "validado",
                "integrado",
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
            "grau_solidez": [
                "baixo",
                "medio",
                "alto",
                "muito_alto",
            ],
            "estado_item": [
                "por_preencher",
                "preenchido",
                "revisto",
                "validado",
                "integrado",
            ],
        },
        "regras_de_validacao": {
            "regras_gerais": [
                {
                    "id": "RG01",
                    "descricao": "Cada entrada deve referir pelo menos uma proposição.",
                },
                {
                    "id": "RG02",
                    "descricao": "Cada entrada deve ter pelo menos um domínio científico quando a dependência não for nao_aplicavel.",
                },
                {
                    "id": "RG03",
                    "descricao": "tipo_dependencia_cientifica tem de pertencer ao enum documentado.",
                },
            ]
        },
        "entradas": entradas,
    }

    return doc


# =============================================================================
# VALIDAÇÃO
# =============================================================================

def validate_matrix_document(doc: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    entradas = safe_list(doc.get("entradas"))

    if not entradas:
        errors.append("A lista 'entradas' está vazia.")
        return errors

    ids_seen: Set[str] = set()

    for entrada in entradas:
        e = safe_dict(entrada)
        eid = str(e.get("entrada_id", "")).strip() or "<sem_entrada_id>"

        if eid in ids_seen:
            errors.append(f"{eid}: entrada_id repetido.")
        ids_seen.add(eid)

        if not safe_list(e.get("proposicao_ids")):
            errors.append(f"{eid}: proposicao_ids vazio.")

        if not normalize_spaces(e.get("tema_cientifico", "")):
            errors.append(f"{eid}: tema_cientifico vazio.")

        if not normalize_spaces(e.get("descricao_do_tema", "")):
            errors.append(f"{eid}: descricao_do_tema vazia.")

        dominios = safe_list(e.get("dominios_cientificos"))
        tipos_dep = safe_list(e.get("tipo_dependencia_cientifica"))

        for dom in dominios:
            if dom not in VALID_DOMINIO_CIENTIFICO:
                errors.append(f"{eid}: dominio_cientifico inválido: {dom}")

        for td in tipos_dep:
            if td not in VALID_TIPO_DEPENDENCIA:
                errors.append(f"{eid}: tipo_dependencia_cientifica inválido: {td}")

        if tipos_dep and any(td != "nao_aplicavel" for td in tipos_dep) and not dominios:
            errors.append(f"{eid}: há dependência científica mas dominios_cientificos está vazio.")

        grau_solidez = str(e.get("grau_solidez", "")).strip()
        if grau_solidez not in VALID_GRAU_SOLIDEZ:
            errors.append(f"{eid}: grau_solidez inválido: {grau_solidez}")

        estado_item = str(e.get("estado_item", "")).strip()
        if estado_item not in VALID_ESTADO_ITEM:
            errors.append(f"{eid}: estado_item inválido: {estado_item}")

        if bool(e.get("necessita_revisao_humana")) and not normalize_spaces(e.get("motivo_revisao_humana", "")):
            errors.append(f"{eid}: necessita_revisao_humana=true mas motivo vazio.")

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
    stats = safe_dict(doc.get("estatisticas"))
    entradas = safe_list(doc.get("entradas"))

    dominio_counter = Counter()
    tipo_dep_counter = Counter()
    solidez_counter = Counter()
    estado_counter = Counter()

    for e in entradas:
        ed = safe_dict(e)
        for dom in safe_list(ed.get("dominios_cientificos")):
            dominio_counter[str(dom)] += 1
        for td in safe_list(ed.get("tipo_dependencia_cientifica")):
            tipo_dep_counter[str(td)] += 1
        solidez_counter[str(ed.get("grau_solidez", ""))] += 1
        estado_counter[str(ed.get("estado_item", ""))] += 1

    lines: List[str] = []
    lines.append("RELATÓRIO — GERAÇÃO DA MATRIZ DE ANCORAGEM CIENTÍFICA V1")
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
    lines.append(f"Total de proposições mapeadas: {stats.get('total_proposicoes_mapeadas', 0)}")
    lines.append(f"Total de domínios científicos: {stats.get('total_dominios_cientificos', 0)}")
    lines.append(f"Itens com suporte empírico: {stats.get('total_itens_com_suporte_empirico', 0)}")
    lines.append(f"Itens com determinação material: {stats.get('total_itens_com_determinacao_material', 0)}")
    lines.append(f"Itens com restrição científica: {stats.get('total_itens_com_restricao_cientifica', 0)}")
    lines.append("")
    lines.append("DISTRIBUIÇÕES")
    lines.append("-" * 78)
    lines.append(f"Por domínio científico: {json.dumps(dict(sorted(dominio_counter.items())), ensure_ascii=False)}")
    lines.append(f"Por tipo de dependência: {json.dumps(dict(sorted(tipo_dep_counter.items())), ensure_ascii=False)}")
    lines.append(f"Por grau de solidez: {json.dumps(dict(sorted(solidez_counter.items())), ensure_ascii=False)}")
    lines.append(f"Por estado_item: {json.dumps(dict(sorted(estado_counter.items())), ensure_ascii=False)}")
    lines.append("")
    lines.append("ENTRADAS MARCADAS PARA REVISÃO HUMANA")
    lines.append("-" * 78)
    flagged = [
        (
            str(safe_dict(e).get("entrada_id", "")),
            normalize_spaces(safe_dict(e).get("motivo_revisao_humana", "")),
        )
        for e in entradas
        if bool(safe_dict(e).get("necessita_revisao_humana"))
    ]
    if flagged:
        for entrada_id, motivo in flagged:
            lines.append(f"- {entrada_id}: {motivo}")
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
        "A matriz de ancoragem científica não prova ainda as proposições. "
        "Ela recorta onde a ciência entra, com que tipo de função e com que "
        "grau de exigência material, empírica ou restritiva."
    )
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# ARGPARSE
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera a matriz de ancoragem científica a partir das proposições nucleares enriquecidas."
    )
    parser.add_argument(
        "--project-root",
        help="Raiz do projeto. Se omitida, será inferida automaticamente.",
    )
    parser.add_argument(
        "--input-json",
        help="Caminho do ficheiro proposicoes_nucleares_enriquecidas_v1.json.",
    )
    parser.add_argument(
        "--output-json",
        help="Caminho do output matriz_ancoragem_cientifica_v1.json.",
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
            else resolve_relative(project_root, DEFAULT_INPUT_PROPOSICOES_RELATIVE)
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

        proposicoes_doc = read_json(input_json_path)
        matrix_doc = build_matrix_document(
            proposicoes_doc=proposicoes_doc,
            input_path=input_json_path,
        )

        validation_errors = validate_matrix_document(matrix_doc)

        write_json(output_json_path, matrix_doc)
        report = build_report(
            input_path=input_json_path,
            output_path=output_json_path,
            report_path=output_report_path,
            doc=matrix_doc,
            validation_errors=validation_errors,
        )
        write_text(output_report_path, report)

        print(f"JSON gerado em: {output_json_path}")
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