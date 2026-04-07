#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import re
from typing import Any


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

OUTPUT_MAIN = "CONTEXTO_ESTRUTURAL_COMPACTO_DO_REAL__V2.md"
OUTPUT_ANNEX = "ANEXOS_TECNICOS_RESUMIDOS_DO_REAL__V2.md"

PATHS = {
    "meta_indice": PROJECT_ROOT / "13_Meta_Indice" / "meta" / "meta_indice.json",
    "meta_ref_percurso": PROJECT_ROOT / "13_Meta_Indice" / "meta" / "meta_referencia_do_percurso.json",
    "indice_sequencial": PROJECT_ROOT / "13_Meta_Indice" / "indice" / "indice_sequencial.json",
    "mapa_integral_indice": PROJECT_ROOT / "13_Meta_Indice" / "indice" / "01_mapa_integral_indice" / "mapa_integral_do_indice.json",
    "argumentos_unificados": PROJECT_ROOT / "13_Meta_Indice" / "indice" / "argumentos" / "argumentos_unificados.json",
    "todos_os_conceitos": PROJECT_ROOT / "13_Meta_Indice" / "dados_base" / "todos_os_conceitos.json",
    "operacoes": PROJECT_ROOT / "13_Meta_Indice" / "dados_base" / "operacoes.json",
    "mapa_dedutivo_final": PROJECT_ROOT / "14_mapa_dedutivo" / "02_fecho_canonico_mapa" / "outputs" / "versoes_finais" / "mapa_dedutivo_canonico_final__vfinal_corrente.json",
    "decisoes_canonicas": PROJECT_ROOT / "14_mapa_dedutivo" / "02_fecho_canonico_mapa" / "consolidacao" / "decisoes_canonicas_intermedias_consolidado_candidato.json",
    "arvore_fecho_superior": PROJECT_ROOT / "15_arvore_do_pensamento" / "01_dados" / "arvore_do_pensamento_v1_fecho_superior.json",
    "adjudicacao_argumentos": PROJECT_ROOT / "15_arvore_do_pensamento" / "01_dados" / "adjudicacao_argumentos_api_v1.json",
    "proposicoes_nucleares_enriquecidas": PROJECT_ROOT / "16_validacao_integral" / "01_dados" / "proposicoes_nucleares_enriquecidas_v1.json",
    "matriz_confronto": PROJECT_ROOT / "16_validacao_integral" / "01_dados" / "matriz_confronto_filosofico_v1.json",
    "adjudicacao_confrontos": PROJECT_ROOT / "16_validacao_integral" / "01_dados" / "adjudicacao_confrontos_filosoficos_restrita_v2.json",
    "grafo_resumo": PROJECT_ROOT / "10_grafo_dependencias" / "data" / "grafo" / "grafo_resumo.txt",
    "relatorio_revisao_argumentos": PROJECT_ROOT / "15_arvore_do_pensamento" / "01_dados" / "relatorio_revisao_argumentos_restritiva_v1.txt",
    "conteudo_completo_percursos": PROJECT_ROOT / "13_Meta_Indice" / "percursos" / "conteudo_completo_percursos.txt",
}

CORE_CONCEPTS = [
    "D_REAL", "D_SER", "D_RELACAO", "D_ESTRUTURA", "D_LIMITE",
    "D_ATUALIZACAO", "D_CAMPO", "D_LOCALIDADE", "D_APREENSAO",
    "D_SER_HUMANO", "D_MEMORIA", "D_REPRESENTACAO", "D_LINGUAGEM",
    "D_MEDIACAO", "D_CONSCIENCIA_REFLEXIVA", "D_ADEQUACAO",
    "D_CRITERIO", "D_VERDADE", "D_ERRO_ONTOLOGICO", "D_CORRECAO",
    "D_BEM", "D_MAL", "D_DEVER_SER", "D_SISTEMA", "D_CULTURA",
    "D_INSTITUICAO", "D_TECNOLOGIA",
]

CORE_ARGUMENTS = [
    "ARG_DISTINCAO_MINIMA",
    "ARG_RELACIONALIDADE_MINIMA",
    "ARG_ESTRUTURA_COMO_CONDICAO_DE_DETERMINABILIDADE",
    "ARG_LIMITE_COMO_CONDICAO_DE_EXISTENCIA_DETERMINADA",
    "ARG_REAL_COMO_CONTINUIDADE_ESTRUTURADA",
    "ARG_SER_COMO_MODO_DE_ESTAR_NO_REAL",
    "ARG_PODER_SER_COMO_DIMENSAO_REAL_DA_ESTRUTURA",
    "ARG_APREENSAO_COMO_CONTATO_SITUADO_COM_O_REAL",
    "ARG_SER_HUMANO_COMO_NODO_REFLEXIVO_LOCALIZADO",
    "ARG_MEMORIA_COMO_ESTABILIZACAO_TEMPORAL_INTERNA",
    "ARG_REPRESENTACAO_COMO_FIXACAO_MEDIADA_DA_APREENSAO",
    "ARG_MEDIACAO_COMO_TRANSFORMACAO_DA_APREENSAO_EM_REPRESENTACAO_OPERAVEL",
    "ARG_CRITERIO_COMO_FIXACAO_OPERATIVA_SOB_LIMITE",
    "ARG_VERDADE_COMO_ADEQUACAO_SOB_CRITERIO",
    "ARG_ERRO_COMO_DESALINHAMENTO_OPERATIVO",
    "ARG_CORRECAO_COMO_REINSCRICAO_NO_REAL",
    "ARG_BEM_COMO_ADEQUACAO_DA_ATUALIZACAO_AO_REAL",
    "ARG_DEVER_SER_COMO_SUBORDINACAO_AO_REAL",
    "ARG_SISTEMA_COMO_CRISTALIZACAO_SISTEMICA_DE_MEDIACOES",
    "ARG_CULTURA_COMO_SISTEMA_SIMBOLICO_ESTABILIZADO",
    "ARG_DIREITO_COMO_DESCRICAO_OPERATIVA_DO_REAL",
]

MAX_DECISOES = 15
MAX_RAMOS = 15
MAX_CONFRONTOS = 18


# ============================================================
# UTILITÁRIOS
# ============================================================

def exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def short(text: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) <= limit:
        return text
    return text[:limit - 1].rstrip() + "…"


def section(title: str) -> str:
    return f"\n## {title}\n\n"


def subsection(title: str) -> str:
    return f"\n### {title}\n\n"


def bullet(items: list[str]) -> str:
    if not items:
        return "- ∅\n"
    return "".join(f"- {x}\n" for x in items)


def kv(d: dict[str, Any]) -> str:
    if not d:
        return "- ∅\n"
    return "".join(f"- **{k}**: {v}\n" for k, v in d.items())


def code_block(text: str) -> str:
    return f"```text\n{text.strip()}\n```\n"


def sorted_keys(d: dict[str, Any]) -> list[str]:
    return sorted(d.keys(), key=lambda x: x.lower())


# ============================================================
# EXTRATORES NÚCLEO
# ============================================================

def build_sources_status() -> str:
    out = []
    for key, path in PATHS.items():
        out.append(f"- **{key}**: `{path}` — {'ok' if exists(path) else 'em falta'}\n")
    return "".join(out)


def compact_meta_indice_core(data: dict[str, Any]) -> str:
    meta = data.get("meta_indice", data)
    regimes = meta.get("regimes", {})
    mods = meta.get("modulos_meta_justificativos", {})

    out = []
    out.append(kv({
        "descrição": meta.get("descricao", ""),
        "critério_último": meta.get("criterio_ultimo", ""),
    }))

    out.append(subsection("Regimes"))
    for regime_id in sorted_keys(regimes):
        r = regimes[regime_id]
        out.append(f"#### {regime_id}\n\n")
        out.append(kv({
            "estatuto": r.get("estatuto", ""),
            "função": r.get("funcao", ""),
            "descrição": r.get("descricao", ""),
        }))
        out.append("Operações:\n")
        out.append(bullet([f"`{x}`" for x in r.get("operacoes", [])]))

    if mods:
        out.append(subsection("Módulos meta-justificativos"))
        for mod_id in sorted_keys(mods):
            m = mods[mod_id]
            out.append(f"#### {mod_id}\n\n")
            out.append(kv({
                "fundamenta_regime": m.get("fundamenta_regime", ""),
                "fundamenta_percurso": m.get("fundamenta_percurso", ""),
                "natureza": m.get("natureza", ""),
                "descrição": m.get("descricao", ""),
            }))
            out.append("Implicações:\n")
            out.append(bullet([short(x, 180) for x in m.get("implicacoes", [])]))

    return "".join(out)


def compact_percursos_core(data: dict[str, Any]) -> str:
    out = []
    for percurso_id in sorted_keys(data):
        p = data[percurso_id]
        out.append(f"#### {percurso_id}\n\n")
        out.append(kv({
            "tipo_instância": p.get("tipo_instancia", ""),
            "observação": p.get("observacao", ""),
        }))
        out.append("Pressupõe:\n")
        out.append(bullet([f"`{x}`" for x in p.get("pressupoe_percursos", [])]))
    return "".join(out)


def compact_indice_core(data: dict[str, Any]) -> str:
    capitulos = data.get("capitulos", [])
    partes = data.get("partes", [])

    out = []
    out.append(subsection("Capítulos"))
    for cap in capitulos:
        out.append(f"#### {cap.get('id', '')}\n\n")
        out.append(kv({
            "título": cap.get("titulo", ""),
            "parte": cap.get("parte", ""),
            "nível": cap.get("nivel", ""),
            "percurso_axial": cap.get("percurso_axial", ""),
            "estado_instalação": cap.get("estado_instalacao", ""),
        }))
        out.append("Campos:\n")
        out.append(bullet([f"`{x}`" for x in cap.get("campos", [])]))

    out.append(subsection("Partes"))
    for parte in partes:
        out.append(f"#### {parte.get('parte_id', '')}\n\n")
        out.append(kv({"ordem": parte.get("ordem", "")}))
        out.append("Capítulos:\n")
        out.append(bullet([f"`{x}`" for x in parte.get("capitulos_ids", [])]))

    return "".join(out)


def compact_mapa_integral_core(data: dict[str, Any]) -> str:
    estrutura = data.get("estrutura_global", {})
    resumo = data.get("resumo_cobertura", {})

    out = []
    out.append(kv({
        "total_capítulos": estrutura.get("total_capitulos", ""),
        "total_argumentos": estrutura.get("total_argumentos", ""),
        "total_fragmentos_tratados": estrutura.get("total_fragmentos_tratados", ""),
        "total_fragmentos_fortes": estrutura.get("total_fragmentos_fortes", ""),
        "total_fragmentos_prováveis": estrutura.get("total_fragmentos_provaveis", ""),
    }))

    for key in [
        "capitulos_sem_argumentos",
        "capitulos_sem_fragmentos",
        "capitulos_com_cobertura_forte",
        "capitulos_com_cobertura_apenas_provavel",
    ]:
        out.append(subsection(key))
        out.append(bullet([f"`{x}`" for x in resumo.get(key, [])]))

    return "".join(out)


def compact_concepts_core(data: dict[str, Any]) -> str:
    out = []
    for cid in CORE_CONCEPTS:
        if cid not in data:
            continue
        c = data[cid]
        definicao = c.get("definicao", {})
        deps = c.get("dependencias", {})
        out.append(f"#### {cid}\n\n")
        out.append(kv({
            "nome": c.get("nome", ""),
            "nível": c.get("nivel", ""),
            "domínio": c.get("dominio", ""),
            "definição": definicao.get("texto", ""),
        }))
        out.append("Depende de:\n")
        out.append(bullet([f"`{x}`" for x in deps.get("depende_de", [])]))
        out.append("Implica:\n")
        out.append(bullet([f"`{x}`" for x in deps.get("implica", [])]))
    return "".join(out)


def compact_operations_core(data: dict[str, Any]) -> str:
    out = []
    for op_id in sorted_keys(data):
        op = data[op_id]
        out.append(f"#### {op_id}\n\n")
        out.append(kv({
            "tipo": op.get("tipo", ""),
            "descrição": op.get("descricao", ""),
            "critério_último": op.get("criterio_ultimo", ""),
        }))
    return "".join(out)


def compact_arguments_core(data: list[dict[str, Any]]) -> str:
    index = {a.get("id"): a for a in data}
    out = []
    for aid in CORE_ARGUMENTS:
        a = index.get(aid)
        if not a:
            continue
        concl = a.get("estrutura_logica", {}).get("conclusao", "")
        out.append(f"#### {aid}\n\n")
        out.append(kv({
            "capítulo": a.get("capitulo", ""),
            "parte": a.get("parte", ""),
            "conceito_alvo": a.get("conceito_alvo", ""),
            "tipo_de_necessidade": a.get("tipo_de_necessidade", ""),
            "nível_de_operação": a.get("nivel_de_operacao", ""),
            "natureza": a.get("natureza", ""),
            "critério_último": a.get("criterio_ultimo", ""),
            "conclusão": short(concl, 260),
        }))
    return "".join(out)


def compact_mapa_dedutivo_core(data: dict[str, Any]) -> str:
    resumo = data.get("resumo_de_consolidacao", {})
    arbitragens = data.get("arbitragens_de_corredor", [])

    out = []
    out.append(kv({
        "total_passos_no_mapa": resumo.get("total_passos_no_mapa", ""),
        "passos_substituídos_pelo_agregador": resumo.get("passos_substituidos_pelo_agregador", ""),
        "passos_preservados_do_precanónico": resumo.get("passos_preservados_do_precanonico", ""),
    }))
    out.append("Corredores fechados por arbitragem:\n")
    out.append(bullet([f"`{x}`" for x in resumo.get("corredores_fechados_por_arbitragem", [])]))

    out.append(subsection("Arbitragens"))
    for a in arbitragens:
        out.append(f"#### {a.get('corredor', '')}\n\n")
        out.append(kv({
            "estado_final": a.get("estado_final_do_corredor", ""),
            "sequência_mínima_fechada": a.get("sequencia_minima_ficou_fechada", ""),
            "critério_de_fecho": short(a.get("criterio_de_fecho_aplicado", ""), 240),
        }))
        out.append("Passos fechados:\n")
        out.append(bullet([f"`{x}`" for x in a.get("passos_fechados", [])]))
    return "".join(out)


def compact_decisoes_core(data: dict[str, Any]) -> str:
    ordem = data.get("ordem_de_execucao", [])
    decisoes = data.get("decisoes_por_passo", [])

    out = []
    out.append("Ordem de execução:\n")
    out.append(bullet([f"`{x}`" for x in ordem]))

    out.append(subsection("Passos exemplares"))
    for d in decisoes[:MAX_DECISOES]:
        out.append(f"#### {d.get('passo_id', '')}\n\n")
        out.append(kv({
            "corredor": d.get("corredor", ""),
            "decisão_editorial": d.get("decisao_editorial", ""),
            "estado_final": d.get("estado_final_do_passo", ""),
            "formulação_final": d.get("formulacao_canonica_final", ""),
        }))
    return "".join(out)


def compact_arvore_core(data: dict[str, Any]) -> str:
    m = data.get("manifesto_cobertura", {})
    out = []
    out.append(kv({
        "arranque_permitido": m.get("arranque_permitido", ""),
        "total_fragmentos_base": m.get("total_fragmentos_base", ""),
        "total_fragmentos_com_cadencia": m.get("total_fragmentos_com_cadencia", ""),
        "total_fragmentos_com_tratamento": m.get("total_fragmentos_com_tratamento", ""),
        "total_fragmentos_com_impacto": m.get("total_fragmentos_com_impacto", ""),
    }))
    out.append("Fragmentos sem tratamento:\n")
    out.append(bullet([f"`{x}`" for x in m.get("fragmentos_sem_tratamento_ids", [])]))
    out.append("Fragmentos com validação problemática:\n")
    out.append(bullet([f"`{x}`" for x in m.get("fragmentos_com_validacao_base_problemática_ids", [])]))
    return "".join(out)


def compact_adjudicacao_argumentos_core(data: dict[str, Any]) -> str:
    resumo = data.get("resumo", {})
    ramos = data.get("ramos_adjudicados", [])

    out = []
    out.append(kv({
        "total_ramos_considerados": resumo.get("total_ramos_considerados", ""),
        "total_processados": resumo.get("total_processados_nesta_execucao", ""),
        "total_adjudicado_sem_revisão_humana": resumo.get("total_adjudicado_sem_revisao_humana", ""),
        "total_manter_1": resumo.get("total_manter_1", ""),
        "total_manter_2_excecional": resumo.get("total_manter_2_excecional", ""),
        "total_manter_0": resumo.get("total_manter_0", ""),
        "total_revisão_humana": resumo.get("total_revisao_humana_necessaria", ""),
    }))

    out.append(subsection("Ramos exemplares"))
    for ramo in ramos[:MAX_RAMOS]:
        out.append(f"#### {ramo.get('ramo_id', '')}\n\n")
        out.append(kv({
            "decisão_final": ramo.get("decisao_final", ""),
            "argumento_dominante": ramo.get("argumento_dominante", ""),
            "confiança": ramo.get("confianca_decisao", ""),
            "justificação_curta": short(ramo.get("justificacao_curta", ""), 220),
        }))
    return "".join(out)


def compact_proposicoes_core(data: dict[str, Any]) -> str:
    stats = data.get("estatisticas", {})
    return kv({
        "total_proposições": stats.get("total_proposicoes", ""),
        "proposições_com_fragmentos": stats.get("proposicoes_com_fragmentos", ""),
        "proposições_com_microlinhas": stats.get("proposicoes_com_microlinhas", ""),
        "proposições_com_ramos": stats.get("proposicoes_com_ramos", ""),
        "proposições_com_percursos": stats.get("proposicoes_com_percursos", ""),
        "proposições_com_argumentos": stats.get("proposicoes_com_argumentos", ""),
        "proposições_que_precisam_confronto_filosófico": stats.get("proposicoes_que_precisam_confronto_filosofico", ""),
    })


def compact_matriz_confronto_core(data: dict[str, Any]) -> str:
    stats = data.get("estatisticas", {})
    confrontos = data.get("confrontos", [])

    out = []
    out.append(kv({
        "total_confrontos": stats.get("total_confrontos", ""),
        "total_problemas_inventariados": stats.get("total_problemas_inventariados", ""),
        "total_confrontos_com_revisão_humana": stats.get("total_confrontos_com_revisao_humana", ""),
        "total_confrontos_com_resposta_canónica": stats.get("total_confrontos_com_resposta_canonica", ""),
        "total_confrontos_com_capítulo_próprio": stats.get("total_confrontos_com_capitulo_proprio", ""),
    }))

    out.append(subsection("Confrontos"))
    for cf in confrontos[:MAX_CONFRONTOS]:
        out.append(f"#### {cf.get('confronto_id', '')}\n\n")
        out.append(kv({
            "título_curto": cf.get("titulo_curto", ""),
            "tipo_de_problema": cf.get("tipo_de_problema", ""),
            "nível_arquitetónico": cf.get("nivel_arquitetonico", ""),
            "grau_de_centralidade": cf.get("grau_de_centralidade", ""),
            "grau_de_prioridade": cf.get("grau_de_prioridade", ""),
            "grau_de_risco": cf.get("grau_de_risco", ""),
            "pergunta_central": cf.get("pergunta_central", ""),
        }))
    return "".join(out)


def compact_adjudicacao_confrontos_core(data: dict[str, Any]) -> str:
    stats = data.get("estatisticas", {})
    return kv({
        "total_confrontos_restritos": stats.get("total_confrontos_restritos", ""),
        "total_revistos_herdados": stats.get("total_revistos_herdados", ""),
        "total_com_revisão_humana_herdados": stats.get("total_com_revisao_humana_herdados", ""),
        "média_confiança_heurística": stats.get("media_confianca_heuristica_herdada", ""),
    })


# ============================================================
# ANEXOS
# ============================================================

def compact_text_annex(title: str, path: Path, limit: int = 5000) -> str:
    out = []
    out.append(section(title))
    if not exists(path):
        out.append(f"**Fonte em falta:** `{path}`\n")
        return "".join(out)
    try:
        txt = read_text(path)
        out.append(code_block(short(txt, limit)))
    except Exception as e:
        out.append(f"**Erro ao ler:** `{e}`\n")
    return "".join(out)


# ============================================================
# BUILDERS
# ============================================================

def build_main_document() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out = []

    out.append("# CONTEXTO ESTRUTURAL COMPACTO DO REAL — V2\n\n")
    out.append(f"- Gerado em: `{now}`\n")
    out.append(f"- Base: `{BASE_DIR}`\n")
    out.append(f"- Projeto raiz: `{PROJECT_ROOT}`\n\n")
    out.append("Este ficheiro é o núcleo estrutural compacto para contexto de trabalho no projeto GPT. ")
    out.append("Substitui razoavelmente bem vários ficheiros estruturais estáveis como contexto transversal, ")
    out.append("mas não substitui as fontes canónicas do repositório.\n")

    out.append(section("Fontes verificadas"))
    out.append(build_sources_status())

    tasks = [
        ("Meta-índice", "meta_indice", compact_meta_indice_core),
        ("Percursos", "meta_ref_percurso", compact_percursos_core),
        ("Índice sequencial", "indice_sequencial", compact_indice_core),
        ("Mapa integral do índice", "mapa_integral_indice", compact_mapa_integral_core),
        ("Conceitos centrais", "todos_os_conceitos", compact_concepts_core),
        ("Operações", "operacoes", compact_operations_core),
        ("Argumentos centrais", "argumentos_unificados", compact_arguments_core),
        ("Mapa dedutivo canónico final", "mapa_dedutivo_final", compact_mapa_dedutivo_core),
        ("Decisões canónicas", "decisoes_canonicas", compact_decisoes_core),
        ("Árvore do pensamento", "arvore_fecho_superior", compact_arvore_core),
        ("Adjudicação de argumentos", "adjudicacao_argumentos", compact_adjudicacao_argumentos_core),
        ("Proposições nucleares enriquecidas", "proposicoes_nucleares_enriquecidas", compact_proposicoes_core),
        ("Matriz de confronto", "matriz_confronto", compact_matriz_confronto_core),
        ("Adjudicação de confrontos", "adjudicacao_confrontos", compact_adjudicacao_confrontos_core),
    ]

    out.append(section("Índice"))
    for title, _, _ in tasks:
        out.append(f"- {title}\n")

    for title, key, fn in tasks:
        out.append(section(title))
        path = PATHS[key]
        if not exists(path):
            out.append(f"**Fonte em falta:** `{path}`\n")
            continue
        try:
            data = read_json(path)
            out.append(fn(data))
        except Exception as e:
            out.append(f"**Erro ao processar `{path.name}`:** `{e}`\n")

    return "".join(out)


def build_annex_document() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out = []

    out.append("# ANEXOS TÉCNICOS RESUMIDOS DO REAL — V2\n\n")
    out.append(f"- Gerado em: `{now}`\n")
    out.append("Este ficheiro contém anexos resumidos que podem ajudar como contexto suplementar, ")
    out.append("mas não devem ocupar o lugar do núcleo estrutural compacto.\n")

    out.append(compact_text_annex("Grafo resumo", PATHS["grafo_resumo"], 5000))
    out.append(compact_text_annex("Relatório de revisão restritiva de argumentos", PATHS["relatorio_revisao_argumentos"], 6000))
    out.append(compact_text_annex("Conteúdo completo dos percursos", PATHS["conteudo_completo_percursos"], 7000))

    return "".join(out)


def main():
    main_path = BASE_DIR / OUTPUT_MAIN
    annex_path = BASE_DIR / OUTPUT_ANNEX

    main_path.write_text(build_main_document(), encoding="utf-8")
    annex_path.write_text(build_annex_document(), encoding="utf-8")

    print(f"[ok] Núcleo criado: {main_path}")
    print(f"[ok] Anexos criados: {annex_path}")


if __name__ == "__main__":
    main()