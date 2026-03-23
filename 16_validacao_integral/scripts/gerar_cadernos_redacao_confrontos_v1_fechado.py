#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gerar_cadernos_redacao_confrontos_v1.py

Gera os cadernos de redação por confronto a partir da adjudicação filosófica
restringida e dos artefactos auxiliares já produzidos na fase
16_validacao_integral.

Objetivos:
- transformar cada confronto adjudicado numa unidade autónoma de redação em Markdown;
- gerar um índice JSON auditável dos cadernos produzidos;
- preservar rastreabilidade para proposições, pontes entre níveis, ancoragens
  científicas e campos do real;
- produzir relatório textual de geração e validação.

Inputs esperados:
- 16_validacao_integral/01_dados/adjudicacao_confrontos_filosoficos_restrita_v2.json
- 16_validacao_integral/01_dados/matriz_confronto_filosofico_v1.json
- 16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json
- 16_validacao_integral/01_dados/matriz_pontes_entre_niveis_v1.json
- 16_validacao_integral/01_dados/matriz_ancoragem_cientifica_v1.json
- 16_validacao_integral/01_dados/mapa_campos_do_real_v1.json

Outputs:
- 16_validacao_integral/03_cadernos_confrontos/indice_cadernos_confrontos.json
- 16_validacao_integral/03_cadernos_confrontos/CFxx_dossier_confronto.md
- 16_validacao_integral/02_outputs/relatorio_geracao_cadernos_confrontos_v1.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


# =============================================================================
# CONFIGURAÇÃO CANÓNICA
# =============================================================================

DEFAULT_INPUT_ADJUDICACAO_RELATIVE = Path(
    "16_validacao_integral/01_dados/adjudicacao_confrontos_filosoficos_restrita_v2.json"
)
DEFAULT_INPUT_CONFRONTO_RELATIVE = Path(
    "16_validacao_integral/01_dados/matriz_confronto_filosofico_v1.json"
)
DEFAULT_INPUT_PROPOSICOES_RELATIVE = Path(
    "16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json"
)
DEFAULT_INPUT_PONTES_RELATIVE = Path(
    "16_validacao_integral/01_dados/matriz_pontes_entre_niveis_v1.json"
)
DEFAULT_INPUT_ANCORAGEM_RELATIVE = Path(
    "16_validacao_integral/01_dados/matriz_ancoragem_cientifica_v1.json"
)
DEFAULT_INPUT_CAMPOS_RELATIVE = Path(
    "16_validacao_integral/01_dados/mapa_campos_do_real_v1.json"
)

DEFAULT_OUTPUT_DIR_RELATIVE = Path(
    "16_validacao_integral/03_cadernos_confrontos"
)
DEFAULT_OUTPUT_INDEX_RELATIVE = Path(
    "16_validacao_integral/03_cadernos_confrontos/indice_cadernos_confrontos.json"
)
DEFAULT_REPORT_RELATIVE = Path(
    "16_validacao_integral/02_outputs/relatorio_geracao_cadernos_confrontos_v1.txt"
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
    "restringido",
    "gerado",
}

VALID_ESTADO_ITEM = {
    "por_preencher",
    "preenchido",
    "revisto",
    "validado",
    "integrado",
}

VALID_GRAU_RISCO = {"baixo", "medio", "alto", "critico"}
VALID_GRAU_PRIORIDADE = {"baixa", "media", "alta", "estrutural", "critica"}

SECOES_MINIMAS_DOSSIER = {
    "1. Identificação",
    "2. Pergunta central",
    "3. Descrição do confronto",
    "4. Síntese adjudicada",
    "5. Tese canónica provisória",
    "6. Teses de sustentação",
    "7. Proposições envolvidas",
    "8. Pontes entre níveis associadas",
    "9. Ancoragens científicas associadas",
    "10. Campos do real relacionados",
    "12. Distinções conceptuais mínimas",
    "13. Objeções priorizadas",
    "22. Sequência de redação canónica",
    "23. Checklist de fecho",
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
    path.write_text(text, encoding="utf-8", newline="\n")



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



def unique_preserve(values: Iterable[Any]) -> List[Any]:
    out: List[Any] = []
    seen: Set[str] = set()
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out



def relpath_str(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve())).replace("\\", "/")
    except Exception:
        return str(path.resolve())



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
        if (cand / DEFAULT_INPUT_ADJUDICACAO_RELATIVE).exists():
            return cand.resolve()

    return script_path.parent.parent.parent



def resolve_relative(project_root: Path, relative_path: Path) -> Path:
    path = (project_root / relative_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {path}")
    return path



def order_from_id(value: str, prefix: str) -> int:
    value = str(value or "")
    if value.startswith(prefix):
        suffix = value[len(prefix):]
        if suffix.isdigit():
            return int(suffix)
    return 0



def sim_nao(value: Any) -> str:
    return "Sim" if bool(value) else "Não"



def to_text_list(value: Any) -> List[str]:
    return [normalize_spaces(str(x)) for x in safe_list(value) if normalize_spaces(str(x))]



def bullet_list(items: Iterable[str], fallback: str = "—") -> str:
    vals = [normalize_spaces(str(x)) for x in items if normalize_spaces(str(x))]
    if not vals:
        return f"- {fallback}"
    return "\n".join(f"- {v}" for v in vals)



def ordered_list(items: Iterable[str], fallback: str = "Sem sequência registada.") -> str:
    vals = [normalize_spaces(str(x)) for x in items if normalize_spaces(str(x))]
    if not vals:
        vals = [fallback]
    return "\n".join(f"{i}. {v}" for i, v in enumerate(vals, start=1))



def checklist_list(items: Iterable[str], fallback: str = "Sem itens registados.") -> str:
    vals = [normalize_spaces(str(x)) for x in items if normalize_spaces(str(x))]
    if not vals:
        vals = [fallback]
    return "\n".join(f"- [ ] {v}" for v in vals)


# =============================================================================
# LOOKUPS
# =============================================================================


def build_lookup(entries: List[Dict[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        value = str(entry.get(key, "")).strip()
        if value:
            out[value] = entry
    return out



def filter_by_ids(lookup: Dict[str, Dict[str, Any]], ids: Iterable[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for raw_id in ids:
        item_id = str(raw_id).strip()
        if not item_id or item_id in seen:
            continue
        if item_id in lookup:
            out.append(lookup[item_id])
            seen.add(item_id)
    return out


# =============================================================================
# EXTRAÇÃO PREFERENCIAL DE CAMPOS
# =============================================================================


def get_adj_restrita(conf: Dict[str, Any]) -> Dict[str, Any]:
    return safe_dict(conf.get("adjudicacao_filosofica_restrita"))



def get_adj_normal(conf: Dict[str, Any]) -> Dict[str, Any]:
    return safe_dict(conf.get("adjudicacao_filosofica"))



def prefer(conf: Dict[str, Any], *path_options: Tuple[str, ...], fallback: Any = None) -> Any:
    for path in path_options:
        cur: Any = conf
        ok = True
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                ok = False
                break
            cur = cur.get(key)
        if ok and cur not in (None, "", []):
            return cur
    return fallback



def extrair_teses_de_sustentacao(conf: Dict[str, Any]) -> List[str]:
    return to_text_list(
        prefer(
            conf,
            ("adjudicacao_filosofica_restrita", "teses_de_sustentacao_restritas"),
            ("adjudicacao_filosofica", "teses_de_sustentacao"),
            fallback=[],
        )
    )



def extrair_distincoes(conf: Dict[str, Any]) -> List[str]:
    return to_text_list(
        prefer(
            conf,
            ("adjudicacao_filosofica_restrita", "distincoes_conceituais_minimas_restritas"),
            ("adjudicacao_filosofica", "distincoes_conceituais_minimas"),
            fallback=[],
        )
    )



def extrair_objecoes_priorizadas(conf: Dict[str, Any]) -> List[str]:
    raw = prefer(
        conf,
        ("adjudicacao_filosofica_restrita", "objecoes_priorizadas_restritas"),
        ("adjudicacao_filosofica", "objecoes_priorizadas"),
        fallback=[],
    )
    out: List[str] = []
    for item in safe_list(raw):
        if isinstance(item, dict):
            ordem = item.get("ordem")
            obj = normalize_spaces(str(item.get("objecao", "")))
            resposta = normalize_spaces(str(item.get("resposta_curta", "")))
            estrategia = normalize_spaces(str(item.get("estrategia", "")))
            if not obj and not resposta and not estrategia:
                continue
            prefix = f"[{ordem}] " if isinstance(ordem, int) else ""
            text = prefix + obj if obj else prefix + "Objeção não descrita"
            if estrategia:
                text += f" (estratégia: {estrategia})"
            if resposta:
                text += f" — resposta curta: {resposta}"
            out.append(text)
        else:
            text = normalize_spaces(str(item))
            if text:
                out.append(text)
    return out



def extrair_plano_redacao(conf: Dict[str, Any]) -> List[str]:
    return to_text_list(
        prefer(
            conf,
            ("adjudicacao_filosofica_restrita", "plano_de_redacao_restrito", "sequencia_minima_restrita"),
            ("adjudicacao_filosofica", "plano_de_redacao_canonica", "sequencia_minima"),
            fallback=[],
        )
    )



def extrair_checklist(conf: Dict[str, Any]) -> List[str]:
    return to_text_list(
        prefer(
            conf,
            ("adjudicacao_filosofica_restrita", "checklist_de_fecho_restrito"),
            ("adjudicacao_filosofica", "checklist_de_fecho"),
            fallback=[],
        )
    )



def extrair_decisao(conf: Dict[str, Any]) -> str:
    data = prefer(
        conf,
        ("adjudicacao_filosofica_restrita", "decisao_de_adjudicacao_restrita"),
        ("adjudicacao_filosofica", "decisao_de_adjudicacao"),
        fallback={},
    )
    if isinstance(data, dict):
        decisao = normalize_spaces(str(data.get("decisao_principal", "")))
        justificacao = normalize_spaces(str(data.get("justificacao", "")))
        if decisao and justificacao:
            return f"{decisao} — {justificacao}"
        return decisao or justificacao or "—"
    return normalize_spaces(str(data)) or "—"



def extrair_articulacao_textual(conf: Dict[str, Any]) -> str:
    art = prefer(
        conf,
        ("adjudicacao_filosofica_restrita", "articulacao_estrutural_restrita"),
        ("adjudicacao_filosofica", "articulacao_estrutural"),
        fallback={},
    )
    if not isinstance(art, dict):
        return normalize_spaces(str(art)) or "—"

    partes: List[str] = []
    props = [str(x.get("proposicao_id", "")).strip() for x in safe_list(art.get("proposicoes_nucleares")) if isinstance(x, dict)]
    pontes = [str(x.get("ponte_id", "")).strip() for x in safe_list(art.get("pontes_entre_niveis")) if isinstance(x, dict)]
    ancs = [str(x.get("entrada_id", "")).strip() for x in safe_list(art.get("ancoragens_cientificas")) if isinstance(x, dict)]
    campos = [str(x.get("campo_id", "")).strip() for x in safe_list(art.get("campos_do_real")) if isinstance(x, dict)]

    if props:
        partes.append("proposições nucleares: " + ", ".join([x for x in props if x]))
    if pontes:
        partes.append("pontes entre níveis: " + ", ".join([x for x in pontes if x]))
    if ancs:
        partes.append("ancoragens científicas: " + ", ".join([x for x in ancs if x]))
    if campos:
        partes.append("campos do real: " + ", ".join([x for x in campos if x]))

    return "; ".join(partes) if partes else "—"


# =============================================================================
# RESUMOS
# =============================================================================


def resumir_proposicao(prop: Dict[str, Any]) -> str:
    pid = str(prop.get("proposicao_id", "?")).strip() or "?"
    bloco = str(prop.get("bloco_id", "?")).strip() or "?"
    texto = normalize_spaces(str(prop.get("texto_curto") or prop.get("texto") or ""))
    return f"**{pid}** ({bloco}) — {texto}" if texto else f"**{pid}** ({bloco})"



def resumir_ponte(ponte: Dict[str, Any]) -> str:
    pid = str(ponte.get("ponte_id", "?")).strip() or "?"
    origem = str(ponte.get("nivel_origem", "?")).strip() or "?"
    destino = str(ponte.get("nivel_destino", "?")).strip() or "?"
    tipo = str(ponte.get("tipo_ponte", "?")).strip() or "?"
    risco = str(ponte.get("grau_risco", "?")).strip() or "?"
    desc = normalize_spaces(str(ponte.get("problema_da_transicao") or ponte.get("descricao") or ""))
    if desc:
        return f"**{pid}** — {origem} → {destino} | tipo: {tipo} | risco: {risco}. {desc}"
    return f"**{pid}** — {origem} → {destino} | tipo: {tipo} | risco: {risco}."



def resumir_ancoragem(anc: Dict[str, Any]) -> str:
    aid = str(anc.get("entrada_id", "?")).strip() or "?"
    tema = normalize_spaces(str(anc.get("tema_cientifico", ""))) or "sem_tema"
    tipos = ", ".join(to_text_list(anc.get("tipo_dependencia_cientifica"))) or "—"
    estado = normalize_spaces(str(anc.get("estado_item", ""))) or "—"
    desc = normalize_spaces(str(anc.get("descricao_do_tema", "")))
    if desc:
        return f"**{aid}** — {tema} | dependência: {tipos} | estado: {estado}. {desc}"
    return f"**{aid}** — {tema} | dependência: {tipos} | estado: {estado}."



def resumir_campo(campo: Dict[str, Any]) -> str:
    cid = str(campo.get("campo_id", "?")).strip() or "?"
    nome = normalize_spaces(str(campo.get("nome_campo", ""))) or "sem_nome"
    tipo = normalize_spaces(str(campo.get("tipo_campo", ""))) or "—"
    risco = normalize_spaces(str(campo.get("grau_risco", ""))) or "—"
    desc = normalize_spaces(str(campo.get("descricao_do_campo", "")))
    if desc:
        return f"**{cid}** — {nome} | tipo: {tipo} | risco: {risco}. {desc}"
    return f"**{cid}** — {nome} | tipo: {tipo} | risco: {risco}."


# =============================================================================
# GERAÇÃO DE DOSSIER
# =============================================================================


def build_markdown_dossier(
    conf: Dict[str, Any],
    proposicoes_lookup: Dict[str, Dict[str, Any]],
    pontes_lookup: Dict[str, Dict[str, Any]],
    ancoragem_lookup: Dict[str, Dict[str, Any]],
    campos_lookup: Dict[str, Dict[str, Any]],
) -> str:
    cf_id = str(conf.get("confronto_id", "CF??")).strip() or "CF??"
    titulo = normalize_spaces(str(conf.get("titulo_curto", "Sem título"))) or "Sem título"

    proposicoes = filter_by_ids(proposicoes_lookup, safe_list(conf.get("proposicao_ids")))
    ponte_ids = prefer(conf, ("ponte_ids_relacionadas_restritas",), ("ponte_ids_relacionadas",), fallback=[])
    anc_ids = prefer(conf, ("ancoragem_ids_relacionadas_restritas",), ("ancoragem_ids_relacionadas",), fallback=[])
    campo_ids = prefer(conf, ("campo_ids_relacionados_restritos",), ("campo_ids_relacionados",), fallback=[])

    pontes = filter_by_ids(pontes_lookup, safe_list(ponte_ids))
    ancoragens = filter_by_ids(ancoragem_lookup, safe_list(anc_ids))
    campos = filter_by_ids(campos_lookup, safe_list(campo_ids))

    sintese = normalize_spaces(str(
        prefer(
            conf,
            ("adjudicacao_filosofica_restrita", "sintese_adjudicada_restrita"),
            ("adjudicacao_filosofica", "sintese_adjudicada"),
            fallback="",
        )
    ))
    tese = normalize_spaces(str(
        prefer(
            conf,
            ("adjudicacao_filosofica_restrita", "tese_central_restrita"),
            ("adjudicacao_filosofica", "tese_central_adjudicada"),
            ("resposta_provavel_do_sistema",),
            fallback="",
        )
    ))

    conteudo = f"""# {cf_id} — {titulo}

## 1. Identificação
- confronto_id: `{cf_id}`
- problema_id: `{conf.get('problema_id', '')}`
- tipo_de_problema: `{conf.get('tipo_de_problema', '')}`
- nivel_arquitetonico: `{conf.get('nivel_arquitetonico', '')}`
- grau_de_prioridade: `{conf.get('grau_de_prioridade', '')}`
- grau_de_risco: `{conf.get('grau_de_risco', '')}`
- grau_de_centralidade: `{conf.get('grau_de_centralidade', '')}`
- grau_de_cobertura_no_projeto: `{conf.get('grau_de_cobertura_no_projeto', '')}`
- estado_item: `{conf.get('estado_item', '')}`
- exige_resposta_canonica: **{sim_nao(conf.get('exige_resposta_canonica'))}**
- precisa_capitulo_proprio: **{sim_nao(conf.get('precisa_capitulo_proprio'))}**
- precisa_subcapitulo: **{sim_nao(conf.get('precisa_subcapitulo'))}**
- precisa_argumento_canonico: **{sim_nao(conf.get('precisa_argumento_canonico'))}**
- necessita_revisao_humana: **{sim_nao(conf.get('necessita_revisao_humana'))}**
- confiança_heurística: `{prefer(conf, ('adjudicacao_filosofica_restrita', 'confianca_heuristica_herdada'), ('adjudicacao_filosofica', 'confianca_heuristica'), fallback='')}`

## 2. Pergunta central
{normalize_spaces(str(conf.get('pergunta_central', ''))) or '—'}

## 3. Descrição do confronto
{normalize_spaces(str(conf.get('descricao_do_confronto', ''))) or '—'}

## 4. Síntese adjudicada
{sintese or '—'}

## 5. Tese canónica provisória
{tese or '—'}

## 6. Teses de sustentação
{bullet_list(extrair_teses_de_sustentacao(conf))}

## 7. Proposições envolvidas
{bullet_list([resumir_proposicao(x) for x in proposicoes], fallback='Sem proposições resolvidas no índice.')}

## 8. Pontes entre níveis associadas
{bullet_list([resumir_ponte(x) for x in pontes], fallback='Sem pontes associadas.')}

## 9. Ancoragens científicas associadas
{bullet_list([resumir_ancoragem(x) for x in ancoragens], fallback='Sem ancoragens associadas.')}

## 10. Campos do real relacionados
{bullet_list([resumir_campo(x) for x in campos], fallback='Sem campos relacionados.')}

## 11. Subproblemas
{bullet_list(to_text_list(conf.get('subproblemas')))}

## 12. Distinções conceptuais mínimas
{bullet_list(extrair_distincoes(conf))}

## 13. Objeções priorizadas
{bullet_list(extrair_objecoes_priorizadas(conf))}

## 14. Insuficiências típicas identificadas
{bullet_list(to_text_list(prefer(conf, ('insuficiencias_tipicas_identificadas_restritas',), ('insuficiencias_tipicas_identificadas',), fallback=[])))}

## 15. Autores e tradições a mobilizar
### Autores prioritários
{bullet_list(to_text_list(prefer(conf, ('autores_prioritarios_restritos',), ('autores_prioritarios',), fallback=[])))}

### Tradições prioritárias
{bullet_list(to_text_list(prefer(conf, ('tradicoes_prioritarias_restritas',), ('tradicoes_prioritarias',), fallback=[])))}

## 16. Conceitos, teses em tensão e adversários filosóficos
### Conceitos clássicos associados
{bullet_list(to_text_list(prefer(conf, ('conceitos_classicos_associados_restritos',), ('conceitos_classicos_associados',), fallback=[])))}

### Teses clássicas em tensão
{bullet_list(to_text_list(prefer(conf, ('teses_classicas_em_tensao_restritas',), ('teses_classicas_em_tensao',), fallback=[])))}

### Tipos de adversário filosófico
{bullet_list(to_text_list(prefer(conf, ('tipos_de_adversario_filosofico_restritos',), ('tipos_de_adversario_filosofico',), fallback=[])))}

## 17. Temas agregados e focos restritos
### Temas agregados
{bullet_list(to_text_list(prefer(conf, ('temas_agregados_restritos',), ('temas_agregados',), fallback=[])))}

### Focos restritos
{bullet_list(to_text_list(conf.get('focos_restritos')))}

## 18. Linhas de tratamento
{bullet_list(to_text_list(prefer(conf, ('linhas_de_tratamento_restritas',), ('linhas_de_tratamento',), fallback=[])))}

## 19. Tipo de resposta exigida, tensão e veredito provisório
### Tipo de resposta exigida
{bullet_list(to_text_list(prefer(conf, ('tipo_de_resposta_exigida_restrita',), ('tipo_de_resposta_exigida',), fallback=[])))}

### Tipo de tensão com o sistema
{bullet_list(to_text_list(prefer(conf, ('tipo_de_tensao_com_o_sistema_restrita',), ('tipo_de_tensao_com_o_sistema',), fallback=[])))}

### Veredito provisório
{bullet_list(to_text_list(prefer(conf, ('veredito_provisorio_restrito',), ('veredito_provisorio',), fallback=[])))}

## 20. Articulação estrutural
{extrair_articulacao_textual(conf)}

## 21. Decisão de adjudicação
{extrair_decisao(conf)}

## 22. Sequência de redação canónica
{ordered_list(extrair_plano_redacao(conf))}

## 23. Checklist de fecho
{checklist_list(extrair_checklist(conf))}

## 24. Necessidades de trabalho
- precisa_reconstrucao_argumentativa: **{sim_nao(safe_dict(conf.get('necessidades_de_trabalho')).get('precisa_reconstrucao_argumentativa'))}**
- precisa_distincao_conceitual: **{sim_nao(safe_dict(conf.get('necessidades_de_trabalho')).get('precisa_distincao_conceitual'))}**
- precisa_resposta_a_objecoes: **{sim_nao(safe_dict(conf.get('necessidades_de_trabalho')).get('precisa_resposta_a_objecoes'))}**
- precisa_articulacao_com_pontes: **{sim_nao(safe_dict(conf.get('necessidades_de_trabalho')).get('precisa_articulacao_com_pontes'))}**
- precisa_articulacao_com_ciencia: **{sim_nao(safe_dict(conf.get('necessidades_de_trabalho')).get('precisa_articulacao_com_ciencia'))}**
- precisa_revisao_humana: **{sim_nao(safe_dict(conf.get('necessidades_de_trabalho')).get('precisa_revisao_humana'))}**

## 25. Lacunas identificadas
{bullet_list(to_text_list(conf.get('lacunas_identificadas')))}

## 26. Notas de revisão humana
{normalize_spaces(str(conf.get('motivo_revisao_humana', ''))) or 'Sem motivo específico registado.'}

## 27. Observações adicionais
{normalize_spaces(str(conf.get('observacoes', ''))) or '—'}
"""
    return conteudo.strip() + "\n"


# =============================================================================
# ÍNDICE JSON
# =============================================================================


def build_index_document(
    project_root: Path,
    output_dir: Path,
    adjudicacao_path: Path,
    matriz_path: Path,
    proposicoes_path: Path,
    pontes_path: Path,
    ancoragem_path: Path,
    campos_path: Path,
    confrontos: List[Dict[str, Any]],
    proposicoes_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for conf in sorted(confrontos, key=lambda x: order_from_id(str(x.get("confronto_id", "")), "CF")):
        cf_id = str(conf.get("confronto_id", "CF??")).strip() or "CF??"
        md_name = f"{cf_id}_dossier_confronto.md"
        props = filter_by_ids(proposicoes_lookup, safe_list(conf.get("proposicao_ids")))
        items.append(
            {
                "confronto_id": cf_id,
                "titulo_curto": conf.get("titulo_curto", ""),
                "tipo_de_problema": conf.get("tipo_de_problema", ""),
                "nivel_arquitetonico": conf.get("nivel_arquitetonico", ""),
                "grau_de_prioridade": conf.get("grau_de_prioridade", ""),
                "grau_de_risco": conf.get("grau_de_risco", ""),
                "estado_item": conf.get("estado_item", ""),
                "necessita_revisao_humana": bool(conf.get("necessita_revisao_humana", False)),
                "motivo_revisao_humana": conf.get("motivo_revisao_humana", ""),
                "proposicao_ids": safe_list(conf.get("proposicao_ids")),
                "blocos_relacionados": safe_list(conf.get("blocos_relacionados")),
                "ponte_ids_relacionadas": safe_list(prefer(conf, ("ponte_ids_relacionadas_restritas",), ("ponte_ids_relacionadas",), fallback=[])),
                "ancoragem_ids_relacionadas": safe_list(prefer(conf, ("ancoragem_ids_relacionadas_restritas",), ("ancoragem_ids_relacionadas",), fallback=[])),
                "campo_ids_relacionados": safe_list(prefer(conf, ("campo_ids_relacionados_restritos",), ("campo_ids_relacionados",), fallback=[])),
                "proposicoes_resumidas": [resumir_proposicao(p) for p in props],
                "ficheiro_markdown": relpath_str(output_dir / md_name, project_root),
            }
        )

    return {
        "metadata": {
            "schema_nome": "indice_cadernos_confrontos_v1",
            "schema_versao": "1.0",
            "data_geracao": utc_now_iso(),
            "gerado_por_script": "gerar_cadernos_redacao_confrontos_v1.py",
            "descricao": "Índice operacional dos cadernos de redação por confronto.",
            "idioma": "pt-PT",
            "projeto": "DoReal / 16_validacao_integral",
            "estado_global": "gerado",
        },
        "fontes": {
            "fonte_adjudicacao_restrita": relpath_str(adjudicacao_path, project_root),
            "fonte_matriz_confronto": relpath_str(matriz_path, project_root),
            "fonte_proposicoes_enriquecidas": relpath_str(proposicoes_path, project_root),
            "fonte_matriz_pontes": relpath_str(pontes_path, project_root),
            "fonte_matriz_ancoragem": relpath_str(ancoragem_path, project_root),
            "fonte_mapa_campos": relpath_str(campos_path, project_root),
        },
        "estatisticas": {
            "total_cadernos": len(items),
            "total_com_revisao_humana": sum(1 for x in items if x["necessita_revisao_humana"]),
            "total_prioridade_estrutural_ou_critica": sum(1 for x in items if x["grau_de_prioridade"] in {"estrutural", "critica"}),
            "total_risco_alto_ou_critico": sum(1 for x in items if x["grau_de_risco"] in {"alto", "critico"}),
        },
        "cadernos": items,
    }


# =============================================================================
# VALIDAÇÃO
# =============================================================================


def validate_index_document(index_doc: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    metadata = safe_dict(index_doc.get("metadata"))
    if metadata.get("estado_global") not in VALID_ESTADO_GLOBAL:
        errors.append("metadata.estado_global inválido no índice")

    items = safe_list(index_doc.get("cadernos"))
    if not items:
        errors.append("O índice não contém cadernos.")
        return errors

    seen: Set[str] = set()
    for item in items:
        cid = str(item.get("confronto_id", "")).strip()
        if not cid:
            errors.append("Índice com caderno sem confronto_id")
            continue
        if cid in seen:
            errors.append(f"confronto_id duplicado no índice: {cid}")
        seen.add(cid)

        risco = str(item.get("grau_de_risco", "")).strip()
        if risco and risco not in VALID_GRAU_RISCO:
            errors.append(f"{cid}: grau_de_risco inválido no índice: {risco}")

        prioridade = str(item.get("grau_de_prioridade", "")).strip()
        if prioridade and prioridade not in VALID_GRAU_PRIORIDADE:
            errors.append(f"{cid}: grau_de_prioridade inválido no índice: {prioridade}")

        estado_item = str(item.get("estado_item", "")).strip()
        if estado_item and estado_item not in VALID_ESTADO_ITEM:
            errors.append(f"{cid}: estado_item inválido no índice: {estado_item}")

        ficheiro = str(item.get("ficheiro_markdown", "")).strip()
        if not ficheiro.endswith(".md"):
            errors.append(f"{cid}: ficheiro_markdown inválido: {ficheiro}")

    return errors



def validate_markdown_file(path: Path, expected_conf_id: str) -> List[str]:
    errors: List[str] = []
    if not path.exists():
        return [f"Ficheiro Markdown não encontrado: {path}"]

    text = path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0].strip() if text.splitlines() else ""
    if not first_line.startswith(f"# {expected_conf_id} —"):
        errors.append(f"{expected_conf_id}: cabeçalho inicial inválido no Markdown.")

    for sec in SECOES_MINIMAS_DOSSIER:
        if f"## {sec}" not in text:
            errors.append(f"{expected_conf_id}: falta a secção obrigatória '{sec}'.")

    return errors


# =============================================================================
# RELATÓRIO
# =============================================================================


def build_report(
    project_root: Path,
    input_paths: Dict[str, Path],
    output_dir: Path,
    output_index_path: Path,
    output_report_path: Path,
    index_doc: Dict[str, Any],
    generated_count: int,
    preserved_count: int,
    validation_errors: List[str],
) -> str:
    stats = safe_dict(index_doc.get("estatisticas"))
    items = safe_list(index_doc.get("cadernos"))

    prioridade_counter = Counter(str(x.get("grau_de_prioridade", "")) for x in items)
    risco_counter = Counter(str(x.get("grau_de_risco", "")) for x in items)
    estado_counter = Counter(str(x.get("estado_item", "")) for x in items)

    lines: List[str] = []
    lines.append("RELATÓRIO — GERAÇÃO DOS CADERNOS DE REDAÇÃO DOS CONFRONTOS V1")
    lines.append("=" * 78)
    lines.append(f"Data de geração: {safe_dict(index_doc.get('metadata')).get('data_geracao', '')}")
    lines.append(f"Estado global: {safe_dict(index_doc.get('metadata')).get('estado_global', '')}")
    lines.append("")
    lines.append("Ficheiros lidos:")
    lines.append("-" * 78)
    for key, path in input_paths.items():
        lines.append(f"- {key}: {relpath_str(path, project_root)}")
    lines.append("")
    lines.append("Ficheiros escritos:")
    lines.append("-" * 78)
    lines.append(f"- pasta_cadernos: {relpath_str(output_dir, project_root)}")
    lines.append(f"- indice_json: {relpath_str(output_index_path, project_root)}")
    lines.append(f"- relatorio_txt: {relpath_str(output_report_path, project_root)}")
    lines.append("")
    lines.append("Resumo quantitativo:")
    lines.append("-" * 78)
    lines.append(f"- total_cadernos: {stats.get('total_cadernos', 0)}")
    lines.append(f"- gerados_ou_atualizados_nesta_execucao: {generated_count}")
    lines.append(f"- preservados_sem_reescrita: {preserved_count}")
    lines.append(f"- total_com_revisao_humana: {stats.get('total_com_revisao_humana', 0)}")
    lines.append(f"- total_prioridade_estrutural_ou_critica: {stats.get('total_prioridade_estrutural_ou_critica', 0)}")
    lines.append(f"- total_risco_alto_ou_critico: {stats.get('total_risco_alto_ou_critico', 0)}")
    lines.append("")
    lines.append("Distribuições:")
    lines.append("-" * 78)
    lines.append(f"- por_prioridade: {json.dumps(dict(sorted(prioridade_counter.items())), ensure_ascii=False)}")
    lines.append(f"- por_risco: {json.dumps(dict(sorted(risco_counter.items())), ensure_ascii=False)}")
    lines.append(f"- por_estado_item: {json.dumps(dict(sorted(estado_counter.items())), ensure_ascii=False)}")
    lines.append("")
    lines.append("Listagem dos cadernos:")
    lines.append("-" * 78)
    for item in items:
        lines.append(
            f"- {item.get('confronto_id','')} | prioridade={item.get('grau_de_prioridade','')} | risco={item.get('grau_de_risco','')} | revisão_humana={'sim' if item.get('necessita_revisao_humana') else 'não'} | {item.get('titulo_curto','')}"
        )
    lines.append("")
    if validation_errors:
        lines.append("Erros de validação:")
        lines.append("-" * 78)
        for err in validation_errors:
            lines.append(f"- {err}")
    else:
        lines.append("Concluído sem erros de validação.")
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# MAIN
# =============================================================================


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Gerar os cadernos de redação por confronto v1.")
    parser.add_argument("--project-root", type=Path, default=None, help="Raiz explícita do projeto DoReal")
    parser.add_argument("--input-adjudicacao", type=Path, default=None, help="Caminho explícito da adjudicação restrita")
    parser.add_argument("--input-confronto", type=Path, default=None, help="Caminho explícito da matriz de confronto")
    parser.add_argument("--input-proposicoes", type=Path, default=None, help="Caminho explícito das proposições enriquecidas")
    parser.add_argument("--input-pontes", type=Path, default=None, help="Caminho explícito da matriz de pontes")
    parser.add_argument("--input-ancoragem", type=Path, default=None, help="Caminho explícito da matriz de ancoragem")
    parser.add_argument("--input-campos", type=Path, default=None, help="Caminho explícito do mapa de campos")
    parser.add_argument("--output-dir", type=Path, default=None, help="Pasta explícita para os cadernos Markdown")
    parser.add_argument("--output-index", type=Path, default=None, help="Caminho explícito do índice JSON")
    parser.add_argument("--output-relatorio", type=Path, default=None, help="Caminho explícito do relatório TXT")
    parser.add_argument("--overwrite-md", action="store_true", help="Reescreve os dossiers Markdown já existentes")
    args = parser.parse_args(argv)

    try:
        project_root = project_root_from_explicit_or_cwd(args.project_root)

        adjudicacao_path = args.input_adjudicacao.resolve() if args.input_adjudicacao else resolve_relative(project_root, DEFAULT_INPUT_ADJUDICACAO_RELATIVE)
        confronto_path = args.input_confronto.resolve() if args.input_confronto else resolve_relative(project_root, DEFAULT_INPUT_CONFRONTO_RELATIVE)
        proposicoes_path = args.input_proposicoes.resolve() if args.input_proposicoes else resolve_relative(project_root, DEFAULT_INPUT_PROPOSICOES_RELATIVE)
        pontes_path = args.input_pontes.resolve() if args.input_pontes else resolve_relative(project_root, DEFAULT_INPUT_PONTES_RELATIVE)
        ancoragem_path = args.input_ancoragem.resolve() if args.input_ancoragem else resolve_relative(project_root, DEFAULT_INPUT_ANCORAGEM_RELATIVE)
        campos_path = args.input_campos.resolve() if args.input_campos else resolve_relative(project_root, DEFAULT_INPUT_CAMPOS_RELATIVE)

        output_dir = args.output_dir.resolve() if args.output_dir else (project_root / DEFAULT_OUTPUT_DIR_RELATIVE).resolve()
        output_index_path = args.output_index.resolve() if args.output_index else (project_root / DEFAULT_OUTPUT_INDEX_RELATIVE).resolve()
        output_report_path = args.output_relatorio.resolve() if args.output_relatorio else (project_root / DEFAULT_REPORT_RELATIVE).resolve()

        adjudicacao_doc = safe_dict(read_json(adjudicacao_path))
        _confronto_doc = safe_dict(read_json(confronto_path))
        proposicoes_doc = safe_dict(read_json(proposicoes_path))
        pontes_doc = safe_dict(read_json(pontes_path))
        ancoragem_doc = safe_dict(read_json(ancoragem_path))
        campos_doc = safe_dict(read_json(campos_path))

        confrontos = safe_list(adjudicacao_doc.get("confrontos"))
        if not confrontos:
            raise ValueError("O ficheiro de adjudicação restrita não contém a lista 'confrontos'.")

        proposicoes_lookup = build_lookup(safe_list(proposicoes_doc.get("proposicoes")), "proposicao_id")
        pontes_lookup = build_lookup(safe_list(pontes_doc.get("pontes")), "ponte_id")
        ancoragem_lookup = build_lookup(safe_list(ancoragem_doc.get("entradas")), "entrada_id")
        campos_lookup = build_lookup(safe_list(campos_doc.get("campos")), "campo_id")

        output_dir.mkdir(parents=True, exist_ok=True)

        generated_count = 0
        preserved_count = 0
        validation_errors: List[str] = []

        for conf in sorted(confrontos, key=lambda x: order_from_id(str(x.get("confronto_id", "")), "CF")):
            cf_id = str(conf.get("confronto_id", "CF??")).strip() or "CF??"
            md_path = output_dir / f"{cf_id}_dossier_confronto.md"

            if md_path.exists() and not args.overwrite_md:
                preserved_count += 1
            else:
                md_text = build_markdown_dossier(
                    conf=conf,
                    proposicoes_lookup=proposicoes_lookup,
                    pontes_lookup=pontes_lookup,
                    ancoragem_lookup=ancoragem_lookup,
                    campos_lookup=campos_lookup,
                )
                write_text(md_path, md_text)
                generated_count += 1

            validation_errors.extend(validate_markdown_file(md_path, cf_id))

        index_doc = build_index_document(
            project_root=project_root,
            output_dir=output_dir,
            adjudicacao_path=adjudicacao_path,
            matriz_path=confronto_path,
            proposicoes_path=proposicoes_path,
            pontes_path=pontes_path,
            ancoragem_path=ancoragem_path,
            campos_path=campos_path,
            confrontos=confrontos,
            proposicoes_lookup=proposicoes_lookup,
        )
        validation_errors.extend(validate_index_document(index_doc))
        write_json(output_index_path, index_doc)

        report_text = build_report(
            project_root=project_root,
            input_paths={
                "adjudicacao_restrita": adjudicacao_path,
                "matriz_confronto": confronto_path,
                "proposicoes": proposicoes_path,
                "pontes": pontes_path,
                "ancoragem": ancoragem_path,
                "campos": campos_path,
            },
            output_dir=output_dir,
            output_index_path=output_index_path,
            output_report_path=output_report_path,
            index_doc=index_doc,
            generated_count=generated_count,
            preserved_count=preserved_count,
            validation_errors=validation_errors,
        )
        write_text(output_report_path, report_text)

        print(f"Cadernos gerados em: {output_dir}")
        print(f"Índice gerado em: {output_index_path}")
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
