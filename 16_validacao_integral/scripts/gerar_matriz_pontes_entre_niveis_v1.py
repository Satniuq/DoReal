#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gerar_matriz_pontes_entre_niveis_v1.py

Gera a matriz derivada de pontes entre níveis a partir do ficheiro
proposicoes_nucleares_enriquecidas_v1.json.

Objetivos:
- extrair e consolidar as pontes entre níveis já atribuídas por proposição;
- gerar uma matriz autónoma, auditável e pronta para revisão humana;
- preservar rastreabilidade para proposições e blocos relacionados;
- produzir relatório de geração.

Outputs:
- 16_validacao_integral/01_dados/matriz_pontes_entre_niveis_v1.json
- 16_validacao_integral/02_outputs/relatorio_geracao_matriz_pontes_entre_niveis_v1.txt
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

DEFAULT_INPUT_PROPOSICOES_RELATIVE = Path(
    "16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json"
)
DEFAULT_OUTPUT_JSON_RELATIVE = Path(
    "16_validacao_integral/01_dados/matriz_pontes_entre_niveis_v1.json"
)
DEFAULT_REPORT_RELATIVE = Path(
    "16_validacao_integral/02_outputs/relatorio_geracao_matriz_pontes_entre_niveis_v1.txt"
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

VALID_GRAU_RISCO = {"baixo", "medio", "alto", "critico"}

VALID_ESTADO_ITEM = {
    "por_preencher",
    "preenchido",
    "revisto",
    "validado",
    "integrado",
}

VALID_CAMPOS_REAL = {
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
    order = ["baixo", "medio", "alto", "critico"]
    cur = current if current in order else "baixo"
    cand = candidate if candidate in order else "baixo"
    return order[max(order.index(cur), order.index(cand))]


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
# HEURÍSTICAS DE APOIO
# =============================================================================

def infer_problem_description(
    nivel_origem: str,
    nivel_destino: str,
    tipo_ponte: str,
    proposicoes: Sequence[Dict[str, Any]],
) -> str:
    textos = " ".join(
        normalize_spaces(p.get("texto", "")).lower()
        for p in proposicoes
    )

    if tipo_ponte == "determinacao_material":
        return (
            "Trata-se de explicitar como uma determinação ontológica ou antropológica "
            "ganha inscrição material concreta sem colapso reducionista."
        )

    if tipo_ponte == "emergencia":
        return (
            "Trata-se de justificar a passagem entre organização material/viva e níveis "
            "cognitivos ou reflexivos sem salto ilegítimo."
        )

    if tipo_ponte == "derivacao_normativa":
        return (
            "Trata-se de justificar a passagem do real, da ação situada ou da estrutura "
            "ontológica para normatividade, dever-ser, dignidade ou vida boa."
        )

    if tipo_ponte == "instanciacao_regional":
        return (
            "Trata-se de mostrar como categorias ontológicas gerais se instanciam em "
            "domínios regionais ou campos específicos do real."
        )

    if tipo_ponte == "articulacao_multinivel":
        return (
            "Trata-se de articular níveis distintos sem confusão nem isolamento, "
            "preservando a especificidade funcional de cada um."
        )

    if tipo_ponte == "condicao_de_possibilidade":
        return (
            "Trata-se de mostrar que um nível funciona como condição de possibilidade "
            "ou suporte estrutural de outro."
        )

    if tipo_ponte == "traducao_operativa":
        return (
            "Trata-se de converter uma estrutura abstrata em critério operável ou forma "
            "de orientação situada."
        )

    if "linguagem" in textos or "símbolo" in textos or "simbolo" in textos:
        return (
            "Trata-se de articular mediação, cognição e linguagem como níveis distintos "
            "mas conectados."
        )

    return (
        "Trata-se de justificar uma transição entre níveis do sistema sem salto "
        "ilícito e com explicitação do nexo intermédio."
    )


def infer_preliminary_justification(
    nivel_origem: str,
    nivel_destino: str,
    tipo_ponte: str,
    proposicoes: Sequence[Dict[str, Any]],
) -> str:
    ids = [p.get("proposicao_id", "") for p in proposicoes if p.get("proposicao_id")]
    joined_ids = ", ".join(ids)

    if tipo_ponte == "determinacao_material":
        return (
            f"As proposições {joined_ids} sugerem que o nível de origem não pode permanecer "
            f"abstrato e exige determinação material mais concreta."
        )

    if tipo_ponte == "emergencia":
        return (
            f"As proposições {joined_ids} colocam um problema clássico de emergência ou "
            f"passagem para níveis cognitivos/reflexivos."
        )

    if tipo_ponte == "derivacao_normativa":
        return (
            f"As proposições {joined_ids} exigem explicitação adicional da passagem do ser, "
            f"da ação ou da estrutura para a normatividade."
        )

    if tipo_ponte == "instanciacao_regional":
        return (
            f"As proposições {joined_ids} apontam para a necessidade de regionalizar categorias "
            f"gerais em campos concretos do real."
        )

    if tipo_ponte == "articulacao_multinivel":
        return (
            f"As proposições {joined_ids} exigem articulação entre níveis heterogéneos "
            f"sem redução de um ao outro."
        )

    return (
        f"As proposições {joined_ids} indicam uma passagem relevante entre "
        f"{nivel_origem} e {nivel_destino} que requer elaboração posterior."
    )


def infer_riscos_identificados(
    nivel_origem: str,
    nivel_destino: str,
    tipo_ponte: str,
    grau_risco: str,
    proposicoes: Sequence[Dict[str, Any]],
) -> List[str]:
    riscos: List[str] = []

    if tipo_ponte == "derivacao_normativa":
        riscos += [
            "Salto ilegítimo entre descrição do real e normatividade.",
            "Insuficiência de mediação entre ação situada e dever-ser.",
        ]
    elif tipo_ponte == "emergencia":
        riscos += [
            "Reducionismo materialista ou biologicista.",
            "Dualismo implícito na passagem para cognição ou reflexividade.",
        ]
    elif tipo_ponte == "determinacao_material":
        riscos += [
            "Subdeterminação material do conceito filosófico.",
            "Confusão entre determinação ontológica e descrição empírica imediata.",
        ]
    elif tipo_ponte == "instanciacao_regional":
        riscos += [
            "Abstração excessiva sem concretização regional.",
            "Multiplicação de campos sem critério de individuação suficiente.",
        ]
    elif tipo_ponte == "articulacao_multinivel":
        riscos += [
            "Confusão entre níveis heterogéneos.",
            "Falta de critério para passagem entre mediação, cognição e linguagem.",
        ]
    elif tipo_ponte == "condicao_de_possibilidade":
        riscos += [
            "Passagem demasiado rápida entre condição formal e realização concreta.",
        ]
    elif tipo_ponte == "traducao_operativa":
        riscos += [
            "Transformação insuficientemente justificada de estrutura em orientação prática.",
        ]

    if grau_risco == "critico":
        riscos.append("Elevado risco estrutural na arquitetura global do sistema.")
    elif grau_risco == "alto":
        riscos.append("Elevado risco de mediação insuficiente entre níveis.")

    return unique_preserve(riscos)


def infer_needs_from_propositions(proposicoes: Sequence[Dict[str, Any]]) -> Dict[str, bool]:
    precisa_confronto = False
    precisa_ancoragem = False
    precisa_reformulacao = False

    for p in proposicoes:
        val = safe_dict(p.get("validacao_integral"))
        precisa_confronto = precisa_confronto or bool(val.get("precisa_confronto_filosofico"))
        precisa_ancoragem = precisa_ancoragem or bool(val.get("precisa_ancoragem_cientifica"))
        precisa_reformulacao = precisa_reformulacao or bool(val.get("precisa_reformulacao_conceitual"))

    return {
        "precisa_confronto_filosofico": precisa_confronto,
        "precisa_ancoragem_cientifica": precisa_ancoragem,
        "precisa_reformulacao_conceitual": precisa_reformulacao,
    }


def infer_campos_relacionados(proposicoes: Sequence[Dict[str, Any]]) -> List[str]:
    campos: List[str] = []
    for p in proposicoes:
        c = safe_dict(p.get("campos_do_real"))
        campos.extend(str(x) for x in safe_list(c.get("campos_principais")) if isinstance(x, str))
        campos.extend(str(x) for x in safe_list(c.get("campos_secundarios")) if isinstance(x, str))
    return unique_preserve([c for c in campos if c in VALID_CAMPOS_REAL])


def infer_requires_human_review(
    grau_risco: str,
    proposicoes: Sequence[Dict[str, Any]],
    tipo_ponte: str,
) -> Tuple[bool, str]:
    flagged = [
        p for p in proposicoes
        if bool(safe_dict(p.get("estado_trabalho")).get("necessita_revisao_humana"))
    ]

    if grau_risco == "critico":
        return True, "Ponte de risco crítico exige revisão humana."
    if flagged:
        ids = ", ".join(p.get("proposicao_id", "") for p in flagged)
        return True, f"A ponte agrega proposições já marcadas para revisão humana: {ids}."
    if tipo_ponte == "derivacao_normativa" and grau_risco in {"alto", "critico"}:
        return True, "A derivação normativa é estruturalmente sensível e exige revisão humana."
    return False, ""


def infer_entry_state(
    grau_risco: str,
    proposicoes: Sequence[Dict[str, Any]],
) -> str:
    if grau_risco == "critico":
        return "por_preencher"
    if any(bool(safe_dict(p.get("estado_trabalho")).get("necessita_revisao_humana")) for p in proposicoes):
        return "por_preencher"
    return "preenchido"


# =============================================================================
# GERAÇÃO DA MATRIZ
# =============================================================================

def build_bridge_groups(proposicoes: Sequence[Dict[str, Any]]) -> Dict[Tuple[str, str, str], List[Dict[str, Any]]]:
    groups: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)

    for prop in proposicoes:
        pontes = safe_list(prop.get("pontes_entre_niveis"))
        for ponte in pontes:
            pd = safe_dict(ponte)
            origem = str(pd.get("nivel_origem", "")).strip()
            destino = str(pd.get("nivel_destino", "")).strip()
            tipo = str(pd.get("tipo_ponte", "")).strip()

            if origem not in VALID_NIVEL_PONTE:
                continue
            if destino not in VALID_NIVEL_PONTE:
                continue
            if tipo not in VALID_TIPO_PONTE:
                continue

            groups[(origem, destino, tipo)].append(prop)

    return groups


def build_matrix_document(
    proposicoes_doc: Dict[str, Any],
    input_path: Path,
    output_path: Path,
) -> Dict[str, Any]:
    proposicoes = safe_list(proposicoes_doc.get("proposicoes"))
    groups = build_bridge_groups(proposicoes)

    entries: List[Dict[str, Any]] = []
    bridge_counter = 1

    for (origem, destino, tipo), props_group in sorted(
        groups.items(),
        key=lambda item: (item[0][0], item[0][1], item[0][2]),
    ):
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

        grau_risco = "baixo"
        descricoes: List[str] = []
        for p in props_group:
            for ponte in safe_list(p.get("pontes_entre_niveis")):
                pd = safe_dict(ponte)
                if (
                    str(pd.get("nivel_origem", "")).strip() == origem
                    and str(pd.get("nivel_destino", "")).strip() == destino
                    and str(pd.get("tipo_ponte", "")).strip() == tipo
                ):
                    grau_risco = max_risco(grau_risco, str(pd.get("risco", "baixo")).strip())
                    desc = normalize_spaces(pd.get("descricao", ""))
                    if desc:
                        descricoes.append(desc)

        problem_desc = infer_problem_description(origem, destino, tipo, props_group)
        justificacao = infer_preliminary_justification(origem, destino, tipo, props_group)
        riscos = infer_riscos_identificados(origem, destino, tipo, grau_risco, props_group)
        campos_rel = infer_campos_relacionados(props_group)
        needs = infer_needs_from_propositions(props_group)
        needs["precisa_reformulacao_conceitual"] = (
            needs["precisa_reformulacao_conceitual"]
            or tipo in {"derivacao_normativa", "articulacao_multinivel", "emergencia"}
        )

        necessita_revisao_humana, motivo_revisao = infer_requires_human_review(
            grau_risco, props_group, tipo
        )
        estado_item = infer_entry_state(grau_risco, props_group)

        entry = {
            "ponte_id": f"PN{bridge_counter:02d}",
            "proposicao_ids": proposicao_ids,
            "blocos_relacionados": blocos_relacionados,
            "nivel_origem": origem,
            "nivel_destino": destino,
            "tipo_ponte": tipo,
            "descricao": " | ".join(unique_preserve(descricoes)) or problem_desc,
            "problema_da_transicao": problem_desc,
            "justificacao_provisoria": justificacao,
            "riscos_identificados": riscos,
            "campos_relacionados": campos_rel,
            "necessidades_de_trabalho": needs,
            "grau_risco": grau_risco,
            "estado_item": estado_item,
            "necessita_revisao_humana": necessita_revisao_humana,
            "motivo_revisao_humana": motivo_revisao,
        }
        entries.append(entry)
        bridge_counter += 1

    total_pontes_por_nivel: Dict[str, int] = Counter()
    for e in entries:
        key = f"{e['nivel_origem']}__{e['nivel_destino']}"
        total_pontes_por_nivel[key] += 1

    doc = {
        "metadata": {
            "schema_nome": "matriz_pontes_entre_niveis_v1",
            "schema_versao": "1.0",
            "data_geracao": utc_now_iso(),
            "gerado_por_script": Path(__file__).name,
            "descricao": (
                "Matriz de pontes entre níveis para controlo dos saltos e transições "
                "entre níveis da fase pós-árvore."
            ),
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
            "total_pontes": len(entries),
            "total_proposicoes_mapeadas": len(
                {
                    pid
                    for e in entries
                    for pid in safe_list(e.get("proposicao_ids"))
                    if isinstance(pid, str) and pid.strip()
                }
            ),
            "total_pontes_por_nivel": dict(sorted(total_pontes_por_nivel.items())),
            "total_pontes_de_risco_alto_ou_critico": sum(
                1 for e in entries if e.get("grau_risco") in {"alto", "critico"}
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
            "grau_risco": [
                "baixo",
                "medio",
                "alto",
                "critico",
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
                    "descricao": "Cada ponte deve ter nível de origem e nível de destino.",
                },
                {
                    "id": "RG02",
                    "descricao": (
                        "Uma ponte não deve ter nível de origem igual ao nível de destino, "
                        "salvo justificação explícita."
                    ),
                },
                {
                    "id": "RG03",
                    "descricao": (
                        "Pontes com risco alto ou critico devem ter explicitação do problema."
                    ),
                },
            ]
        },
        "pontes": entries,
    }

    return doc


# =============================================================================
# VALIDAÇÃO
# =============================================================================

def validate_matrix_document(doc: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    if "pontes" not in doc:
        errors.append("Falta o bloco 'pontes'.")
        return errors

    entries = safe_list(doc.get("pontes"))
    ids_seen: Set[str] = set()

    for entry in entries:
        e = safe_dict(entry)
        pid = str(e.get("ponte_id", "")).strip() or "<sem_ponte_id>"

        if pid in ids_seen:
            errors.append(f"{pid}: ponte_id repetido.")
        ids_seen.add(pid)

        origem = str(e.get("nivel_origem", "")).strip()
        destino = str(e.get("nivel_destino", "")).strip()
        tipo = str(e.get("tipo_ponte", "")).strip()
        risco = str(e.get("grau_risco", "")).strip()
        estado_item = str(e.get("estado_item", "")).strip()

        if origem not in VALID_NIVEL_PONTE:
            errors.append(f"{pid}: nivel_origem inválido: {origem}")
        if destino not in VALID_NIVEL_PONTE:
            errors.append(f"{pid}: nivel_destino inválido: {destino}")
        if tipo not in VALID_TIPO_PONTE:
            errors.append(f"{pid}: tipo_ponte inválido: {tipo}")
        if risco not in VALID_GRAU_RISCO:
            errors.append(f"{pid}: grau_risco inválido: {risco}")
        if estado_item not in VALID_ESTADO_ITEM:
            errors.append(f"{pid}: estado_item inválido: {estado_item}")

        if origem == destino:
            errors.append(f"{pid}: nivel_origem e nivel_destino são iguais.")

        if not safe_list(e.get("proposicao_ids")):
            errors.append(f"{pid}: proposicao_ids vazio.")
        if not normalize_spaces(e.get("descricao", "")):
            errors.append(f"{pid}: descricao vazia.")
        if not normalize_spaces(e.get("problema_da_transicao", "")):
            errors.append(f"{pid}: problema_da_transicao vazio.")
        if not normalize_spaces(e.get("justificacao_provisoria", "")):
            errors.append(f"{pid}: justificacao_provisoria vazia.")

        for campo in safe_list(e.get("campos_relacionados")):
            if campo not in VALID_CAMPOS_REAL:
                errors.append(f"{pid}: campo_relacionado inválido: {campo}")

        needs = safe_dict(e.get("necessidades_de_trabalho"))
        for key in [
            "precisa_confronto_filosofico",
            "precisa_ancoragem_cientifica",
            "precisa_reformulacao_conceitual",
        ]:
            if key not in needs:
                errors.append(f"{pid}: falta necessidade de trabalho obrigatória: {key}")

        if bool(e.get("necessita_revisao_humana")) and not normalize_spaces(e.get("motivo_revisao_humana", "")):
            errors.append(f"{pid}: necessita_revisao_humana=true mas motivo_revisao_humana vazio.")

        if risco in {"alto", "critico"} and not safe_list(e.get("riscos_identificados")):
            errors.append(f"{pid}: risco alto/crítico mas riscos_identificados vazio.")

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
    entries = safe_list(doc.get("pontes"))

    risco_counter = Counter(str(safe_dict(e).get("grau_risco", "")) for e in entries)
    tipo_counter = Counter(str(safe_dict(e).get("tipo_ponte", "")) for e in entries)
    origem_destino_counter = Counter(
        f"{safe_dict(e).get('nivel_origem', '')} -> {safe_dict(e).get('nivel_destino', '')}"
        for e in entries
    )
    estado_counter = Counter(str(safe_dict(e).get("estado_item", "")) for e in entries)

    lines: List[str] = []
    lines.append("RELATÓRIO — GERAÇÃO DA MATRIZ DE PONTES ENTRE NÍVEIS V1")
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
    lines.append(f"Total de pontes: {stats.get('total_pontes', 0)}")
    lines.append(f"Total de proposições mapeadas: {stats.get('total_proposicoes_mapeadas', 0)}")
    lines.append(f"Pontes de risco alto/crítico: {stats.get('total_pontes_de_risco_alto_ou_critico', 0)}")
    lines.append("")
    lines.append("DISTRIBUIÇÕES")
    lines.append("-" * 78)
    lines.append(f"Por tipo de ponte: {json.dumps(dict(sorted(tipo_counter.items())), ensure_ascii=False)}")
    lines.append(f"Por grau de risco: {json.dumps(dict(sorted(risco_counter.items())), ensure_ascii=False)}")
    lines.append(f"Por transição origem->destino: {json.dumps(dict(sorted(origem_destino_counter.items())), ensure_ascii=False)}")
    lines.append(f"Por estado_item: {json.dumps(dict(sorted(estado_counter.items())), ensure_ascii=False)}")
    lines.append("")
    lines.append("PONTES MARCADAS PARA REVISÃO HUMANA")
    lines.append("-" * 78)
    flagged = [
        (
            str(safe_dict(e).get("ponte_id", "")),
            normalize_spaces(safe_dict(e).get("motivo_revisao_humana", "")),
        )
        for e in entries
        if bool(safe_dict(e).get("necessita_revisao_humana"))
    ]
    if flagged:
        for ponte_id, motivo in flagged:
            lines.append(f"- {ponte_id}: {motivo}")
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
        "A matriz de pontes entre níveis não resolve ainda os problemas de transição; "
        "ela identifica, agrupa e torna auditáveis os pontos em que o sistema exige "
        "elaboração intermédia mais forte."
    )
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# ARGPARSE
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera a matriz de pontes entre níveis a partir das proposições nucleares enriquecidas."
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
        help="Caminho do output matriz_pontes_entre_niveis_v1.json.",
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
            output_path=output_json_path,
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