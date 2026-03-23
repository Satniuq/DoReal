#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gerar_mapa_campos_do_real_v1.py

Gera o mapa derivado de campos do real a partir do ficheiro
proposicoes_nucleares_enriquecidas_v1.json.

Objetivos:
- consolidar a cartografia regional já sugerida por proposição;
- agrupar proposições por campos estruturais do real relevantes para a fase pós-árvore;
- explicitar escalas, níveis, propriedades, dinâmicas e limites próprios de cada campo;
- preservar rastreabilidade para proposições e blocos relacionados;
- produzir um artefacto autónomo, auditável e pronto para revisão humana.

Outputs:
- 16_validacao_integral/01_dados/mapa_campos_do_real_v1.json
- 16_validacao_integral/02_outputs/relatorio_geracao_mapa_campos_do_real_v1.txt
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
    "16_validacao_integral/01_dados/mapa_campos_do_real_v1.json"
)
DEFAULT_REPORT_RELATIVE = Path(
    "16_validacao_integral/02_outputs/relatorio_geracao_mapa_campos_do_real_v1.txt"
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

VALID_CAMPO_REAL = {
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

VALID_ESCALA_ONTOLOGICA = {
    "particula",
    "objeto",
    "organismo",
    "sujeito_encarnado",
    "agente",
    "grupo_social",
    "instituicao",
    "cultura",
    "escala_multinivel",
}

VALID_NIVEL_REALIDADE = {
    "estrutura",
    "vida",
    "cognicao",
    "representacao",
    "linguagem",
    "coexistencia",
    "acao",
    "normatividade",
    "valor",
}

VALID_TIPO_CAMPO = {
    "campo_estrutural",
    "campo_regional",
    "campo_de_articulacao",
    "campo_pratico_normativo",
    "campo_historico_cultural",
}

VALID_GRAU_DELIMITACAO = {"baixo", "medio", "alto"}
VALID_GRAU_PRIORIDADE = {"baixa", "media", "alta", "estrutural"}
VALID_ESTADO_ITEM = {
    "por_preencher",
    "preenchido",
    "revisto",
    "validado",
    "integrado",
}

RISK_ORDER = ["baixo", "medio", "alto", "critico"]
PRIORITY_ORDER = ["baixa", "media", "alta", "estrutural"]


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



def max_risco(current: str, candidate: str) -> str:
    cur = current if current in RISK_ORDER else "baixo"
    cand = candidate if candidate in RISK_ORDER else "baixo"
    return RISK_ORDER[max(RISK_ORDER.index(cur), RISK_ORDER.index(cand))]



def max_prioridade(current: str, candidate: str) -> str:
    cur = current if current in PRIORITY_ORDER else "baixa"
    cand = candidate if candidate in PRIORITY_ORDER else "baixa"
    return PRIORITY_ORDER[max(PRIORITY_ORDER.index(cur), PRIORITY_ORDER.index(cand))]



def text_contains_any(text: str, needles: Sequence[str]) -> bool:
    return any(n in text for n in needles)



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


# =============================================================================
# HEURÍSTICAS DE AGRUPAMENTO E DESCRIÇÃO
# =============================================================================


def classify_field_cluster(proposicao: Dict[str, Any]) -> str:
    texto = normalize_spaces(proposicao.get("texto", "")).lower()
    ordem = int(proposicao.get("ordem_global") or 0)
    classificacao = safe_dict(proposicao.get("classificacao_filosofica_inicial"))
    dominio = str(classificacao.get("dominio_principal", "")).strip()

    campos = safe_dict(proposicao.get("campos_do_real"))
    principais = set(str(x) for x in safe_list(campos.get("campos_principais")))
    secundarios = set(str(x) for x in safe_list(campos.get("campos_secundarios")))
    niveis = set(str(x) for x in safe_list(campos.get("nivel_de_realidade_implicado")))

    if (
        "pratico_normativo" in principais
        or "normatividade" in niveis
        or "valor" in niveis
        or dominio == "etica"
        or text_contains_any(texto, ["normativ", "dignidade", "vida boa", "bem", "mal", "dever", "dano"])
    ):
        if "historico_cultural" in secundarios or "cultura" in texto or "institui" in texto:
            return "pratica_normatividade_e_formas_historicas"
        return "acao_normatividade_e_formas_sociais"

    if (
        "simbolico_linguistico" in principais
        or "simbolico_linguistico" in secundarios
        or "linguagem" in niveis
        or dominio == "filosofia_da_linguagem"
        or text_contains_any(texto, ["símbolo", "simbolo", "linguagem", "mediação", "mediacao"])
    ):
        return "simbolo_linguagem_e_partilha_social"

    if (
        "cognitivo_representacional" in principais
        or "cognitivo_representacional" in secundarios
        or {"cognicao", "representacao"} & niveis
        or dominio in {"filosofia_da_mente", "epistemologia", "antropologia_filosofica"}
        or 24 <= ordem <= 30
        or text_contains_any(texto, ["consci", "memória", "memoria", "representa", "critério", "criterio"])
    ):
        return "cognicao_representacao_e_reflexividade"

    if (
        "biologico" in principais
        or "biologico" in secundarios
        or "vida" in niveis
        or text_contains_any(texto, ["vida", "organismo", "corpo", "metabol", "vulner", "homeost"])
    ):
        return "vida_corporeidade_e_organismo"

    if (
        "historico_cultural" in principais
        or "historico_cultural" in secundarios
        or text_contains_any(texto, ["históric", "historic", "cultural", "institui", "tradição", "tradicao"])
    ):
        return "regionalizacao_historico_cultural"

    if "integral_multicampo" in principais or "estrutura" in niveis or dominio == "ontologia":
        return "estrutura_integral_e_regionalizacao_do_real"

    return "estrutura_integral_e_regionalizacao_do_real"



def cluster_metadata(cluster: str) -> Dict[str, Any]:
    mapping: Dict[str, Dict[str, Any]] = {
        "estrutura_integral_e_regionalizacao_do_real": {
            "tipo_campo": "campo_estrutural",
            "nome_campo": "estrutura_integral_e_regionalizacao_do_real",
            "descricao": (
                "Campo em que o sistema trata categorias gerais do real, limite, relação, diferença, unidade, "
                "potencialidade e atualização, antes da sua concretização regional mais fina."
            ),
            "campos_principais": ["integral_multicampo"],
            "campos_secundarios": ["fisico", "biologico", "historico_cultural"],
            "propriedades": [
                "estrutura",
                "relação",
                "diferença",
                "limite",
                "unidade",
                "potencialidade",
                "atualização",
                "regionalização",
            ],
            "dinamicas": [
                "passagem do plano ontológico geral para campos regionais",
                "distribuição de categorias transversais por níveis do real",
                "articulação entre estrutura fixa e dinamismo de atualização",
            ],
            "limites": [
                "Não confundir categoria ontológica geral com descrição empírica suficiente.",
                "Não tratar o campo integral como se abolisse a especificidade dos campos regionais.",
                "Exige controlo forte da instanciação regional para evitar abstração vazia.",
            ],
            "perguntas": [
                "Como se regionalizam categorias gerais sem perda de coerência?",
                "Que propriedades são verdadeiramente transversais e quais já pertencem a campos concretos?",
            ],
        },
        "vida_corporeidade_e_organismo": {
            "tipo_campo": "campo_regional",
            "nome_campo": "vida_corporeidade_e_organismo",
            "descricao": (
                "Campo da vida, do corpo, do organismo e da vulnerabilidade material, no qual o sistema precisa de "
                "mostrar como o ente situado se determina como vivente encarnado."
            ),
            "campos_principais": ["biologico"],
            "campos_secundarios": ["ecologico", "sensorio_motor", "integral_multicampo"],
            "propriedades": [
                "corporeidade",
                "organização viva",
                "autorregulação",
                "vulnerabilidade",
                "inscrição ecológica",
                "dependência material",
            ],
            "dinamicas": [
                "autoconservação e regulação interna",
                "acoplamento organismo-meio",
                "condicionamento material de cognição e ação",
            ],
            "limites": [
                "Não reduzir vida e ação a mero mecanismo físico-químico.",
                "Não abstrair a corporeidade ao descrever o agente ou o sujeito.",
                "Exige distinguir determinação material de reducionismo biologicista.",
            ],
            "perguntas": [
                "Como se passa do organismo ao sujeito encarnado sem salto?",
                "Que peso ontológico tem a vulnerabilidade na arquitetura do sistema?",
            ],
        },
        "cognicao_representacao_e_reflexividade": {
            "tipo_campo": "campo_de_articulacao",
            "nome_campo": "cognicao_representacao_e_reflexividade",
            "descricao": (
                "Campo em que aparecem memória, representação, critério, correção, reflexividade e mediações "
                "epistémicas do sujeito encarnado."
            ),
            "campos_principais": ["cognitivo_representacional"],
            "campos_secundarios": ["sensorio_motor", "simbolico_linguistico", "intersubjetivo_social"],
            "propriedades": [
                "memória",
                "representação",
                "atenção",
                "critério",
                "correção",
                "reflexividade",
                "mediação",
            ],
            "dinamicas": [
                "estabilização do apreendido em forma operável",
                "passagem da incorporação à representação",
                "formação de critérios submetidos ao real",
            ],
            "limites": [
                "Não dualizar mente e corpo.",
                "Não confundir representação com espelhamento passivo do real.",
                "Exige explicitar como verdade e erro são possíveis em agente encarnado.",
            ],
            "perguntas": [
                "Como emerge a reflexividade a partir de condições materiais e corporais?",
                "Que estatuto têm memória e representação no sistema: descritivo, funcional ou ontológico?",
            ],
        },
        "simbolo_linguagem_e_partilha_social": {
            "tipo_campo": "campo_de_articulacao",
            "nome_campo": "simbolo_linguagem_e_partilha_social",
            "descricao": (
                "Campo em que símbolo, linguagem e mediação tornam a representação partilhável, transmissível e socialmente estabilizada."
            ),
            "campos_principais": ["simbolico_linguistico", "intersubjetivo_social"],
            "campos_secundarios": ["cognitivo_representacional", "historico_cultural"],
            "propriedades": [
                "simbolização",
                "linguagem",
                "transmissibilidade",
                "partilha",
                "estabilização intersubjetiva",
                "mediação social",
            ],
            "dinamicas": [
                "fixação simbólica do representado",
                "circulação intersubjetiva de sentido",
                "formação de práticas linguísticas e gramáticas de uso",
            ],
            "limites": [
                "Não tratar linguagem como camada puramente formal desligada da incorporação.",
                "Não dissolver o símbolo em convenção arbitrária sem suporte prático e social.",
                "Exige distinguir mediação simbólica de mera codificação técnica.",
            ],
            "perguntas": [
                "Como passa a representação a ser transmissível sem perder referência ao real?",
                "Qual o nexo entre símbolo, prática e comunidade de uso?",
            ],
        },
        "acao_normatividade_e_formas_sociais": {
            "tipo_campo": "campo_pratico_normativo",
            "nome_campo": "acao_normatividade_e_formas_sociais",
            "descricao": (
                "Campo em que ação, dano, bem, mal, coexistência, responsabilidade e vida boa se articulam com práticas e instituições."
            ),
            "campos_principais": ["pratico_normativo", "intersubjetivo_social"],
            "campos_secundarios": ["biologico", "historico_cultural"],
            "propriedades": [
                "ação situada",
                "responsabilidade",
                "dano",
                "dever-ser",
                "dignidade",
                "vida boa",
                "institucionalidade",
            ],
            "dinamicas": [
                "passagem da ação à avaliação normativa",
                "coordenação intersubjetiva de expectativas e obrigações",
                "formação de critérios práticos e restrições éticas",
            ],
            "limites": [
                "Não derivar normatividade diretamente de factos sem mediação suficiente.",
                "Não ignorar vulnerabilidade, contexto e práticas sociais reais.",
                "Exige distinguir fundamento ontológico, justificação prática e institucionalização histórica.",
            ],
            "perguntas": [
                "Como justificar a derivação normativa sem salto ilegítimo?",
                "Que papel têm instituições e formas de vida na estabilização do bem e do dano?",
            ],
        },
        "pratica_normatividade_e_formas_historicas": {
            "tipo_campo": "campo_historico_cultural",
            "nome_campo": "pratica_normatividade_e_formas_historicas",
            "descricao": (
                "Campo em que normatividade, dignidade, instituições, cultura e sedimentação histórica se cruzam, "
                "mostrando a regionalização histórico-cultural das categorias práticas."
            ),
            "campos_principais": ["pratico_normativo", "historico_cultural", "intersubjetivo_social"],
            "campos_secundarios": ["simbolico_linguistico", "biologico"],
            "propriedades": [
                "sedimentação histórica",
                "cultura",
                "instituições",
                "tradições práticas",
                "legitimação",
                "variação contextual",
            ],
            "dinamicas": [
                "estabilização histórica de formas de vida",
                "transmissão cultural de critérios e práticas",
                "reformulação institucional da normatividade",
            ],
            "limites": [
                "Não relativizar completamente a normatividade a cada contexto histórico.",
                "Não abstrair a historicidade real de instituições e práticas.",
                "Exige articular universalidade pretendida e concretização histórica situada.",
            ],
            "perguntas": [
                "Como compatibilizar dignidade e vida boa com pluralidade histórico-cultural?",
                "Que parte da normatividade depende de instituições e que parte as limita?",
            ],
        },
        "regionalizacao_historico_cultural": {
            "tipo_campo": "campo_historico_cultural",
            "nome_campo": "regionalizacao_historico_cultural",
            "descricao": (
                "Campo dedicado à inscrição histórica e cultural das categorias do sistema, sobretudo quando práticas, linguagem ou instituições "
                "exigem regionalização mais concreta."
            ),
            "campos_principais": ["historico_cultural"],
            "campos_secundarios": ["intersubjetivo_social", "simbolico_linguistico"],
            "propriedades": [
                "historicidade",
                "cultura",
                "instituição",
                "sedimentação",
                "variação contextual",
                "transmissão",
            ],
            "dinamicas": [
                "sedimentação de práticas e significados",
                "herança e transformação institucional",
                "variação histórica de formas de organização e sentido",
            ],
            "limites": [
                "Não confundir historicidade com pura contingência sem estrutura.",
                "Não reduzir cultura a sobreposição superficial sobre o real material.",
                "Exige ligação explícita ao campo prático, simbólico ou social relevante.",
            ],
            "perguntas": [
                "Onde a categoria é estrutural e onde já depende de sedimentação histórica?",
                "Que limites materiais travam a plasticidade cultural?",
            ],
        },
    }
    return mapping[cluster]



def infer_delimitacao_cluster(cluster: str, proposicoes: Sequence[Dict[str, Any]]) -> str:
    total = len(proposicoes)
    if cluster in {"estrutura_integral_e_regionalizacao_do_real", "acao_normatividade_e_formas_sociais"}:
        return "alto"
    if total >= 8:
        return "alto"
    if total >= 4:
        return "medio"
    return "baixo"



def infer_prioridade_cluster(cluster: str, proposicoes: Sequence[Dict[str, Any]]) -> str:
    prioridade = "baixa"
    for p in proposicoes:
        vi = safe_dict(p.get("validacao_integral"))
        prioridade = max_prioridade(prioridade, str(vi.get("grau_prioridade", "baixa")))

    if cluster in {
        "estrutura_integral_e_regionalizacao_do_real",
        "acao_normatividade_e_formas_sociais",
        "pratica_normatividade_e_formas_historicas",
    }:
        return max_prioridade(prioridade, "estrutural")

    return prioridade



def infer_risco_cluster(cluster: str, proposicoes: Sequence[Dict[str, Any]]) -> str:
    risco = "baixo"
    for p in proposicoes:
        vi = safe_dict(p.get("validacao_integral"))
        risco = max_risco(risco, str(vi.get("grau_risco_salto", "baixo")))
        for ponte in safe_list(p.get("pontes_entre_niveis")):
            risco = max_risco(risco, str(safe_dict(ponte).get("risco", "baixo")))

    if cluster in {"acao_normatividade_e_formas_sociais", "pratica_normatividade_e_formas_historicas"}:
        risco = max_risco(risco, "alto")
    return risco



def infer_requires_human_review(cluster: str, proposicoes: Sequence[Dict[str, Any]], grau_risco: str) -> Tuple[bool, str]:
    flagged = [
        str(p.get("proposicao_id", "")).strip()
        for p in proposicoes
        if bool(safe_dict(p.get("estado_trabalho")).get("necessita_revisao_humana"))
    ]
    flagged = [x for x in flagged if x]

    if flagged:
        return True, f"O campo agrega proposições já marcadas para revisão humana: {', '.join(flagged)}."

    if grau_risco == "critico":
        return True, "Campo com risco crítico de regionalização ou derivação intercampos exige revisão humana."

    if cluster == "estrutura_integral_e_regionalizacao_do_real" and len(proposicoes) >= 10:
        return True, "Campo estrutural de grande amplitude exige revisão humana para evitar mistura de níveis."

    return False, ""



def infer_estado_item(proposicoes: Sequence[Dict[str, Any]], grau_risco: str, necessita_revisao: bool) -> str:
    if necessita_revisao or grau_risco in {"alto", "critico"}:
        return "por_preencher"

    estados = [
        str(safe_dict(p.get("estado_trabalho")).get("estado_atual", "")).strip()
        for p in proposicoes
    ]
    if any(e == "concluido" for e in estados):
        return "preenchido"
    return "por_preencher"



def aggregate_field_lists(proposicoes: Sequence[Dict[str, Any]]) -> Tuple[List[str], List[str], List[str], List[str]]:
    principais: List[str] = []
    secundarios: List[str] = []
    escalas: List[str] = []
    niveis: List[str] = []

    for p in proposicoes:
        campos = safe_dict(p.get("campos_do_real"))
        principais.extend(str(x) for x in safe_list(campos.get("campos_principais")))
        secundarios.extend(str(x) for x in safe_list(campos.get("campos_secundarios")))
        escalas.extend(str(x) for x in safe_list(campos.get("escala_ontologica")))
        niveis.extend(str(x) for x in safe_list(campos.get("nivel_de_realidade_implicado")))

    return (
        unique_preserve(principais),
        unique_preserve(secundarios),
        unique_preserve(escalas),
        unique_preserve(niveis),
    )



def infer_campos_transversais(cluster: str, proposicoes: Sequence[Dict[str, Any]]) -> List[str]:
    principais, secundarios, _, _ = aggregate_field_lists(proposicoes)
    out = unique_preserve(principais + secundarios)

    if cluster == "estrutura_integral_e_regionalizacao_do_real" and "integral_multicampo" not in out:
        out.insert(0, "integral_multicampo")
    if cluster == "acao_normatividade_e_formas_sociais" and "pratico_normativo" not in out:
        out.insert(0, "pratico_normativo")
    return out



def infer_exemplos_de_manifestacao(cluster: str, proposicoes: Sequence[Dict[str, Any]]) -> List[str]:
    exemplos: List[str] = []
    _, _, escalas, niveis = aggregate_field_lists(proposicoes)
    escalas_set = set(escalas)
    niveis_set = set(niveis)

    if cluster == "estrutura_integral_e_regionalizacao_do_real":
        exemplos += [
            "categorias estruturais transversais do sistema",
            "passagens de potencialidade a atualização",
            "regionalização de propriedades gerais por domínios do real",
        ]
    if cluster == "vida_corporeidade_e_organismo":
        exemplos += [
            "organismos vivos",
            "corpos vulneráveis",
            "autorregulação e homeostase",
            "acoplamento organismo-meio",
        ]
    if cluster == "cognicao_representacao_e_reflexividade":
        exemplos += [
            "memória incorporada",
            "representação operável",
            "atenção e aprendizagem",
            "correção e erro em agente situado",
        ]
    if cluster == "simbolo_linguagem_e_partilha_social":
        exemplos += [
            "símbolos partilháveis",
            "linguagem estabilizada",
            "circulação intersubjetiva de sentido",
            "práticas discursivas",
        ]
    if cluster == "acao_normatividade_e_formas_sociais":
        exemplos += [
            "ação situada",
            "dano e responsabilidade",
            "coordenação prática",
            "instituições e obrigações",
        ]
    if cluster in {"pratica_normatividade_e_formas_historicas", "regionalizacao_historico_cultural"}:
        exemplos += [
            "formas de vida históricas",
            "instituições sedimentadas",
            "tradições e práticas culturais",
            "variação contextual da normatividade",
        ]

    if "agente" in escalas_set and "acao" in niveis_set:
        exemplos.append("agentes situados em práticas concretas")
    if "grupo_social" in escalas_set and "coexistencia" in niveis_set:
        exemplos.append("grupos sociais e coordenação de coexistência")
    if "cultura" in escalas_set:
        exemplos.append("formas culturais de estabilização")

    return unique_preserve(exemplos)



def infer_questoes_de_regionalizacao(cluster: str, proposicoes: Sequence[Dict[str, Any]]) -> List[str]:
    base = list(cluster_metadata(cluster)["perguntas"])
    _, _, escalas, niveis = aggregate_field_lists(proposicoes)

    if "escala_multinivel" in escalas:
        base.append("Como preservar continuidade entre escalas sem colapsar diferenças de nível?")
    if "normatividade" in niveis:
        base.append("Que mediações separam descrição do campo e justificação normativa?")
    if "linguagem" in niveis:
        base.append("Como se articula a linguagem com cognição e vida social sem isolamento formalista?")
    return unique_preserve(base)



def infer_observacoes(cluster: str, proposicoes: Sequence[Dict[str, Any]]) -> str:
    ids = [str(p.get("proposicao_id", "")).strip() for p in proposicoes if p.get("proposicao_id")]
    if not ids:
        return ""

    if cluster == "estrutura_integral_e_regionalizacao_do_real":
        return (
            f"Campo estruturante agregado a partir de {len(ids)} proposições ({', '.join(ids[:8])}"
            f"{'...' if len(ids) > 8 else ''}) com forte incidência ontológica e multiescalar."
        )
    if cluster in {"acao_normatividade_e_formas_sociais", "pratica_normatividade_e_formas_historicas"}:
        return (
            f"Campo sensível porque agrega proposições práticas/normativas ({', '.join(ids[:8])}"
            f"{'...' if len(ids) > 8 else ''}) e exige mediação forte entre ação, coexistência e valor."
        )
    return f"Campo agregado a partir de {len(ids)} proposições relacionadas: {', '.join(ids[:10])}{'...' if len(ids) > 10 else ''}."



def build_field_groups(proposicoes: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for proposicao in proposicoes:
        vi = safe_dict(proposicao.get("validacao_integral"))
        if not bool(vi.get("precisa_cartografia_de_campo")):
            continue
        cluster = classify_field_cluster(proposicao)
        groups[cluster].append(proposicao)
    return dict(groups)


# =============================================================================
# CONSTRUÇÃO DO DOCUMENTO
# =============================================================================


def build_map_document(input_path: Path, proposicoes_doc: Dict[str, Any]) -> Dict[str, Any]:
    proposicoes = safe_list(proposicoes_doc.get("proposicoes"))
    groups = build_field_groups(proposicoes)

    campos: List[Dict[str, Any]] = []
    field_counter = 1

    for cluster, props_group in sorted(groups.items(), key=lambda x: x[0]):
        meta = cluster_metadata(cluster)
        proposicao_ids = unique_preserve(
            str(p.get("proposicao_id", "")).strip()
            for p in props_group
            if p.get("proposicao_id")
        )
        blocos_relacionados = unique_preserve(
            str(p.get("bloco_id", "")).strip()
            for p in props_group
            if p.get("bloco_id")
        )
        campos_principais_ag, campos_secundarios_ag, escalas_ag, niveis_ag = aggregate_field_lists(props_group)

        campos_principais = unique_preserve(list(meta["campos_principais"]) + campos_principais_ag)
        campos_secundarios = unique_preserve(list(meta["campos_secundarios"]) + campos_secundarios_ag)
        campos_transversais = infer_campos_transversais(cluster, props_group)
        exemplos = infer_exemplos_de_manifestacao(cluster, props_group)
        questoes = infer_questoes_de_regionalizacao(cluster, props_group)
        grau_delimitacao = infer_delimitacao_cluster(cluster, props_group)
        prioridade = infer_prioridade_cluster(cluster, props_group)
        grau_risco = infer_risco_cluster(cluster, props_group)
        necessita_revisao, motivo_revisao = infer_requires_human_review(cluster, props_group, grau_risco)
        estado_item = infer_estado_item(props_group, grau_risco, necessita_revisao)

        campo = {
            "campo_id": f"CR{field_counter:02d}",
            "proposicao_ids": proposicao_ids,
            "blocos_relacionados": blocos_relacionados,
            "tipo_campo": meta["tipo_campo"],
            "nome_campo": meta["nome_campo"],
            "descricao_do_campo": meta["descricao"],
            "campos_principais": campos_principais,
            "campos_secundarios": campos_secundarios,
            "campos_transversais": campos_transversais,
            "escalas_ontologicas_implicadas": escalas_ag,
            "niveis_de_realidade_implicados": niveis_ag,
            "propriedades_em_foco": unique_preserve(meta["propriedades"]),
            "dinamicas_relevantes": unique_preserve(meta["dinamicas"]),
            "limites_e_cuidados": unique_preserve(meta["limites"]),
            "questoes_de_regionalizacao": questoes,
            "exemplos_de_manifestacao": exemplos,
            "grau_de_delimitacao": grau_delimitacao,
            "grau_prioridade": prioridade,
            "grau_risco": grau_risco,
            "observacoes": infer_observacoes(cluster, props_group),
            "estado_item": estado_item,
            "necessita_revisao_humana": necessita_revisao,
            "motivo_revisao_humana": motivo_revisao,
        }
        campos.append(campo)
        field_counter += 1

    campo_counter = Counter()
    escala_counter = Counter()
    nivel_counter = Counter()

    for c in campos:
        for x in safe_list(c.get("campos_principais")):
            campo_counter[str(x)] += 1
        for x in safe_list(c.get("escalas_ontologicas_implicadas")):
            escala_counter[str(x)] += 1
        for x in safe_list(c.get("niveis_de_realidade_implicados")):
            nivel_counter[str(x)] += 1

    doc = {
        "metadata": {
            "schema_nome": "mapa_campos_do_real_v1",
            "schema_versao": "1.0",
            "data_geracao": utc_now_iso(),
            "gerado_por_script": Path(__file__).name,
            "descricao": "Mapa de campos do real das proposições nucleares da fase pós-árvore.",
            "idioma": "pt-PT",
            "projeto": "arvore_do_pensamento",
            "estado_global": "enriquecido",
        },
        "fontes": {
            "fonte_proposicoes_enriquecidas": {
                "caminho": str(input_path.parent),
                "ficheiro": input_path.name,
                "hash_opcional": "",
            }
        },
        "estatisticas": {
            "total_campos": len(campos),
            "total_proposicoes_mapeadas": len(
                {
                    pid
                    for c in campos
                    for pid in safe_list(c.get("proposicao_ids"))
                    if isinstance(pid, str) and pid.strip()
                }
            ),
            "total_campos_com_revisao_humana": sum(1 for c in campos if bool(c.get("necessita_revisao_humana"))),
            "total_campos_com_incidencia_normativa": sum(
                1 for c in campos if "normatividade" in safe_list(c.get("niveis_de_realidade_implicados"))
            ),
            "total_campos_multiescala": sum(
                1 for c in campos if len(safe_list(c.get("escalas_ontologicas_implicadas"))) >= 3
            ),
            "total_campos_por_tipo": dict(
                sorted(Counter(str(c.get("tipo_campo", "")) for c in campos).items())
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
                "particula",
                "objeto",
                "organismo",
                "sujeito_encarnado",
                "agente",
                "grupo_social",
                "instituicao",
                "cultura",
                "escala_multinivel",
            ],
            "nivel_de_realidade": [
                "estrutura",
                "vida",
                "cognicao",
                "representacao",
                "linguagem",
                "coexistencia",
                "acao",
                "normatividade",
                "valor",
            ],
            "tipo_campo": [
                "campo_estrutural",
                "campo_regional",
                "campo_de_articulacao",
                "campo_pratico_normativo",
                "campo_historico_cultural",
            ],
            "grau_de_delimitacao": ["baixo", "medio", "alto"],
            "grau_prioridade": ["baixa", "media", "alta", "estrutural"],
            "grau_risco": ["baixo", "medio", "alto", "critico"],
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
                    "descricao": "Cada campo deve referir pelo menos uma proposição.",
                },
                {
                    "id": "RG02",
                    "descricao": "Cada campo deve indicar pelo menos um campo principal ou transversal do real.",
                },
                {
                    "id": "RG03",
                    "descricao": "Escalas, níveis, tipos e estados têm de pertencer aos enums documentados.",
                },
                {
                    "id": "RG04",
                    "descricao": "Se necessita_revisao_humana=true, o motivo deve estar preenchido.",
                },
            ]
        },
        "campos": campos,
    }

    return doc


# =============================================================================
# VALIDAÇÃO
# =============================================================================


def validate_map_document(doc: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    campos = safe_list(doc.get("campos"))

    if not campos:
        errors.append("A lista 'campos' está vazia.")
        return errors

    estado_global = str(safe_dict(doc.get("metadata")).get("estado_global", "")).strip()
    if estado_global not in VALID_ESTADO_GLOBAL:
        errors.append(f"metadata.estado_global inválido: {estado_global}")

    ids_seen: Set[str] = set()

    for campo in campos:
        c = safe_dict(campo)
        cid = str(c.get("campo_id", "")).strip() or "<sem_campo_id>"

        if cid in ids_seen:
            errors.append(f"{cid}: campo_id repetido.")
        ids_seen.add(cid)

        if not safe_list(c.get("proposicao_ids")):
            errors.append(f"{cid}: proposicao_ids vazio.")

        if not normalize_spaces(c.get("nome_campo", "")):
            errors.append(f"{cid}: nome_campo vazio.")

        if not normalize_spaces(c.get("descricao_do_campo", "")):
            errors.append(f"{cid}: descricao_do_campo vazia.")

        tipo_campo = str(c.get("tipo_campo", "")).strip()
        if tipo_campo not in VALID_TIPO_CAMPO:
            errors.append(f"{cid}: tipo_campo inválido: {tipo_campo}")

        if not safe_list(c.get("campos_principais")) and not safe_list(c.get("campos_transversais")):
            errors.append(f"{cid}: campos_principais e campos_transversais ambos vazios.")

        for x in safe_list(c.get("campos_principais")) + safe_list(c.get("campos_secundarios")) + safe_list(c.get("campos_transversais")):
            if x not in VALID_CAMPO_REAL:
                errors.append(f"{cid}: campo_do_real inválido: {x}")

        for x in safe_list(c.get("escalas_ontologicas_implicadas")):
            if x not in VALID_ESCALA_ONTOLOGICA:
                errors.append(f"{cid}: escala_ontologica inválida: {x}")

        for x in safe_list(c.get("niveis_de_realidade_implicados")):
            if x not in VALID_NIVEL_REALIDADE:
                errors.append(f"{cid}: nivel_de_realidade inválido: {x}")

        delimitacao = str(c.get("grau_de_delimitacao", "")).strip()
        if delimitacao not in VALID_GRAU_DELIMITACAO:
            errors.append(f"{cid}: grau_de_delimitacao inválido: {delimitacao}")

        prioridade = str(c.get("grau_prioridade", "")).strip()
        if prioridade not in VALID_GRAU_PRIORIDADE:
            errors.append(f"{cid}: grau_prioridade inválido: {prioridade}")

        risco = str(c.get("grau_risco", "")).strip()
        if risco not in set(RISK_ORDER):
            errors.append(f"{cid}: grau_risco inválido: {risco}")

        estado_item = str(c.get("estado_item", "")).strip()
        if estado_item not in VALID_ESTADO_ITEM:
            errors.append(f"{cid}: estado_item inválido: {estado_item}")

        if not safe_list(c.get("propriedades_em_foco")):
            errors.append(f"{cid}: propriedades_em_foco vazio.")
        if not safe_list(c.get("dinamicas_relevantes")):
            errors.append(f"{cid}: dinamicas_relevantes vazio.")
        if not safe_list(c.get("limites_e_cuidados")):
            errors.append(f"{cid}: limites_e_cuidados vazio.")
        if not safe_list(c.get("questoes_de_regionalizacao")):
            errors.append(f"{cid}: questoes_de_regionalizacao vazio.")

        if bool(c.get("necessita_revisao_humana")) and not normalize_spaces(c.get("motivo_revisao_humana", "")):
            errors.append(f"{cid}: necessita_revisao_humana=true mas motivo vazio.")

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
    campos = safe_list(doc.get("campos"))

    tipo_counter = Counter(str(safe_dict(c).get("tipo_campo", "")) for c in campos)
    risco_counter = Counter(str(safe_dict(c).get("grau_risco", "")) for c in campos)
    prioridade_counter = Counter(str(safe_dict(c).get("grau_prioridade", "")) for c in campos)
    estado_counter = Counter(str(safe_dict(c).get("estado_item", "")) for c in campos)
    campo_principal_counter = Counter()

    for c in campos:
        cd = safe_dict(c)
        for cp in safe_list(cd.get("campos_principais")):
            campo_principal_counter[str(cp)] += 1

    lines: List[str] = []
    lines.append("RELATÓRIO — GERAÇÃO DO MAPA DE CAMPOS DO REAL V1")
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
    lines.append(f"Total de campos: {stats.get('total_campos', 0)}")
    lines.append(f"Total de proposições mapeadas: {stats.get('total_proposicoes_mapeadas', 0)}")
    lines.append(f"Campos com revisão humana: {stats.get('total_campos_com_revisao_humana', 0)}")
    lines.append(f"Campos com incidência normativa: {stats.get('total_campos_com_incidencia_normativa', 0)}")
    lines.append(f"Campos multiescala: {stats.get('total_campos_multiescala', 0)}")
    lines.append("")
    lines.append("DISTRIBUIÇÕES")
    lines.append("-" * 78)
    lines.append(f"Por tipo de campo: {json.dumps(dict(sorted(tipo_counter.items())), ensure_ascii=False)}")
    lines.append(f"Por grau de risco: {json.dumps(dict(sorted(risco_counter.items())), ensure_ascii=False)}")
    lines.append(f"Por grau de prioridade: {json.dumps(dict(sorted(prioridade_counter.items())), ensure_ascii=False)}")
    lines.append(f"Por estado_item: {json.dumps(dict(sorted(estado_counter.items())), ensure_ascii=False)}")
    lines.append(f"Por campo principal: {json.dumps(dict(sorted(campo_principal_counter.items())), ensure_ascii=False)}")
    lines.append("")
    lines.append("CAMPOS MARCADOS PARA REVISÃO HUMANA")
    lines.append("-" * 78)
    flagged = [
        (
            str(safe_dict(c).get("campo_id", "")),
            normalize_spaces(safe_dict(c).get("motivo_revisao_humana", "")),
        )
        for c in campos
        if bool(safe_dict(c).get("necessita_revisao_humana"))
    ]
    if flagged:
        for campo_id, motivo in flagged:
            lines.append(f"- {campo_id}: {motivo}")
    else:
        lines.append("Nenhum.")

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
        "O mapa de campos do real não substitui ainda a investigação filosófica nem a ancoragem científica. "
        "Ele regionaliza onde as proposições se mostram, em que escalas e níveis operam, e onde os limites "
        "de instância, historicidade ou normatividade exigem trabalho adicional."
    )
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# ARGPARSE
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera o mapa de campos do real a partir das proposições nucleares enriquecidas."
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
        help="Caminho do output mapa_campos_do_real_v1.json.",
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
        map_doc = build_map_document(input_json_path, proposicoes_doc)
        validation_errors = validate_map_document(map_doc)
        report_text = build_report(
            input_json_path,
            output_json_path,
            output_report_path,
            map_doc,
            validation_errors,
        )

        write_json(output_json_path, map_doc)
        write_text(output_report_path, report_text)

        print(f"JSON gerado em: {output_json_path}")
        print(f"Relatório gerado em: {output_report_path}")
        if validation_errors:
            print(f"Atenção: foram detetados {len(validation_errors)} erro(s) de validação.")
            return 2

        print("Concluído sem erros de validação.")
        return 0

    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
