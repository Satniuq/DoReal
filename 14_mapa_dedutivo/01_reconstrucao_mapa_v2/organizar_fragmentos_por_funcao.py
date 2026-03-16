#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
04_organizar_fragmentos_por_funcao.py

Objetivo
--------
Ler os ficheiros de corredor extraídos a partir da revisão estrutural e organizar,
para cada proposição, os fragmentos relacionados segundo função reconstrutiva:

- fragmentos_justificativos
- fragmentos_mediacionais
- fragmentos_de_bloqueio
- fragmentos_ilustrativos

O script usa duas fontes:
1) o próprio ficheiro do corredor (materiais_de_reconstrucao)
2) tratamento_filosofico_fragmentos.json

Saídas
------
Para cada corredor de entrada, gera:
- <nome>_organizado.json

E também:
- resumo_organizacao_fragmentos_por_funcao.json

Notas metodológicas
-------------------
Este script NÃO pretende decidir filosofia por ti. Ele faz uma pré-organização
operativa do material para a reconstrução v2.

As regras são heurísticas, mas transparentes:
- justificativo: fragmento com vocação argumentativa/reconstrutiva forte
- mediacional: fragmento que faz ponte, transição, clarificação de mediação
- bloqueio: fragmento que critica, nega, recusa ou bloqueia objeções recorrentes
- ilustrativo: material expositivo, setorial, lateral, redacional, intuitivo,
  ou material útil mas ainda pouco estabilizado inferencialmente
"""

from __future__ import annotations

import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# CONFIGURAÇÃO DE PATHS
# ============================================================

NOME_FICHEIRO_TRATAMENTO = "tratamento_filosofico_fragmentos.json"
NOMES_CORREDOR_DEFAULT = [
    "corredor_P25_P30.json",
    "corredor_P33_P37.json",
    "corredor_P42_P48.json",
    "corredor_P50.json",
]


# ============================================================
# UTILITÁRIOS GERAIS
# ============================================================


def carregar_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)



def guardar_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



def agora_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()



def normalizar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor.strip()
    return str(valor).strip()



def normalizar_lista_strings(valor: Any) -> List[str]:
    if valor is None:
        return []
    if isinstance(valor, list):
        return [normalizar_texto(v) for v in valor if normalizar_texto(v)]
    texto = normalizar_texto(valor)
    return [texto] if texto else []



def procurar_ficheiro(nome: str, bases: List[Path]) -> Optional[Path]:
    for base in bases:
        candidato = (base / nome).resolve()
        if candidato.exists():
            return candidato
    return None



def slug_saida_corredor(path: Path) -> str:
    return path.stem + "_organizado.json"


# ============================================================
# ÍNDICE DO TRATAMENTO FILOSÓFICO
# ============================================================


def construir_indice_tratamento(tratamento: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    indice: Dict[str, Dict[str, Any]] = {}

    for item in tratamento:
        fragment_id = normalizar_texto(item.get("fragment_id"))
        if not fragment_id:
            continue
        indice[fragment_id] = item

    return indice


# ============================================================
# HEURÍSTICAS DE CLASSIFICAÇÃO
# ============================================================

PALAVRAS_BLOQUEIO = [
    "bloque",
    "critica",
    "critica_",
    "criticar",
    "nega",
    "negar",
    "nega_",
    "recusa",
    "recusar",
    "combate",
    "opoe",
    "corrige",
    "erro",
    "desfaz",
    "diagnostica",
    "fechamento",
    "autorreferencial",
    "substituicao_do_real",
]

PALAVRAS_MEDIACAO = [
    "transicao",
    "faz_ponte",
    "ponte",
    "media",
    "mediac",
    "clarifica_mediacao",
    "prepara_argumento_seguinte",
    "identifica_dependencia_estrutural",
    "identifica_campo_de_validade",
]

PALAVRAS_JUSTIFICACAO = [
    "subordina",
    "fixa_criterio",
    "mostra_condicao",
    "identifica_dependencia_estrutural",
    "reinscreve",
    "submete",
    "reconduz",
    "descreve_dinamica",
    "distingue_apreensao_de_representacao",
    "derivacao",
    "reconducao_estrutural",
    "dedutiva",
    "abductiva",
    "distincao_analitica",
]

PAPEIS_ILUSTRATIVOS = {
    "aplicacao_setorial",
    "nota_lateral_aproveitavel",
    "arquivo_de_intuicoes",
}

PAPEIS_MEDIACIONAIS = {
    "ponte_de_transicao",
}

PAPEIS_JUSTIFICATIVOS = {
    "apoio_argumentativo",
}

ESTADOS_ARGUMENTATIVOS_FRACOS = {
    "exploracao_pre_conceptual",
    "intuicao_bruta",
    "distincao_util_sem_argumento",
}

ESTADOS_ARGUMENTATIVOS_FORTES = {
    "argumento_em_esboco",
    "aplicacao_de_argumento",
    "formulacao_pre_argumentativa",
}

FORMAS_INFERENCIA_JUSTIFICATIVAS = {
    "reconducao_estrutural",
    "derivacao_normativa",
    "distincao_analitica",
    "dedutiva",
    "abductiva",
    "mista",
    "descricao_estrutural",
    "critica_por_contradicao",
    "exclusao_por_impossibilidade",
}



def contem_palavra_chave(texto: str, palavras: List[str]) -> bool:
    t = normalizar_texto(texto).lower()
    return any(p in t for p in palavras)



def classificar_fragmento(
    fragment_id: str,
    tratamento_item: Optional[Dict[str, Any]],
    proposicao: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Devolve um registo enriquecido com:
    - categoria_primaria
    - categorias_secundarias
    - pontuacoes
    - justificacao_classificacao
    - metadados úteis do tratamento
    """

    materiais = proposicao.get("materiais_de_reconstrucao", {}) or {}
    tf = (tratamento_item or {}).get("tratamento_filosofico_fragmento", {}) or {}
    destino = tf.get("destino_editorial", {}) or {}
    potencial = tf.get("potencial_argumentativo", {}) or {}
    avaliacao = tf.get("avaliacao_global", {}) or {}

    trabalho = normalizar_texto(tf.get("trabalho_no_sistema"))
    trabalho2 = normalizar_texto(tf.get("trabalho_no_sistema_secundario"))
    explicacao = normalizar_texto(tf.get("explicacao_textual_do_que_o_fragmento_tenta_fazer"))
    descricao_funcional = normalizar_texto(tf.get("descricao_funcional_curta"))
    problema = normalizar_texto(tf.get("problema_filosofico_central"))

    papel_prim = normalizar_texto(destino.get("papel_editorial_primario"))
    papel_sec = normalizar_texto(destino.get("papel_editorial_secundario"))
    destino_fino = normalizar_texto(destino.get("destino_editorial_fino"))
    prioridade_aproveitamento = normalizar_texto(destino.get("prioridade_de_aproveitamento"))
    prioridade_revisao = normalizar_texto(destino.get("prioridade_de_revisao"))
    requer_reescrita = bool(destino.get("requer_reescrita"))
    requer_densificacao = bool(destino.get("requer_densificacao"))
    requer_formalizacao = bool(destino.get("requer_formalizacao_logica"))

    estado_argumentativo = normalizar_texto(potencial.get("estado_argumentativo"))
    forma_inferencia = normalizar_texto(potencial.get("forma_de_inferencia"))
    argumento_reconstruivel = bool(potencial.get("argumento_reconstruivel"))
    necessita_reconstrucao_forte = bool(potencial.get("necessita_reconstrucao_forte"))
    forca_logica = normalizar_texto(potencial.get("forca_logica_estimada"))

    clareza = normalizar_texto(avaliacao.get("clareza_atual"))
    estabilizacao = normalizar_texto(avaliacao.get("grau_de_estabilizacao"))
    risco_ma_interpretacao = normalizar_texto(avaliacao.get("risco_de_ma_interpretacao"))

    texto_agregado = " | ".join(
        [
            trabalho,
            trabalho2,
            explicacao,
            descricao_funcional,
            problema,
            papel_prim,
            papel_sec,
            destino_fino,
            forma_inferencia,
        ]
    ).lower()

    score = {
        "justificativo": 0,
        "mediacional": 0,
        "bloqueio": 0,
        "ilustrativo": 0,
    }
    razoes: List[str] = []

    # --------------------------------------------------------
    # Justificativo
    # --------------------------------------------------------
    if argumento_reconstruivel:
        score["justificativo"] += 3
        razoes.append("argumento_reconstruivel=true")

    if estado_argumentativo in ESTADOS_ARGUMENTATIVOS_FORTES:
        score["justificativo"] += 2
        razoes.append(f"estado_argumentativo={estado_argumentativo}")

    if forma_inferencia in FORMAS_INFERENCIA_JUSTIFICATIVAS:
        score["justificativo"] += 2
        razoes.append(f"forma_de_inferencia={forma_inferencia}")

    if papel_prim in PAPEIS_JUSTIFICATIVOS or papel_sec in PAPEIS_JUSTIFICATIVOS:
        score["justificativo"] += 2
        razoes.append("papel_editorial com apoio_argumentativo")

    if contem_palavra_chave(texto_agregado, PALAVRAS_JUSTIFICACAO):
        score["justificativo"] += 2
        razoes.append("texto com sinais de justificação/recondução/subordinação")

    if prioridade_aproveitamento == "alta":
        score["justificativo"] += 1
        razoes.append("prioridade_de_aproveitamento=alta")

    if forca_logica in {"alta", "media"}:
        score["justificativo"] += 1
        razoes.append(f"forca_logica_estimada={forca_logica}")

    # --------------------------------------------------------
    # Mediacional
    # --------------------------------------------------------
    if papel_prim in PAPEIS_MEDIACIONAIS or papel_sec in PAPEIS_MEDIACIONAIS:
        score["mediacional"] += 3
        razoes.append("papel_editorial com ponte_de_transicao")

    if trabalho == "faz_transicao_de_percurso" or trabalho2 == "faz_transicao_de_percurso":
        score["mediacional"] += 3
        razoes.append("trabalho_no_sistema indica transição")

    if contem_palavra_chave(texto_agregado, PALAVRAS_MEDIACAO):
        score["mediacional"] += 2
        razoes.append("texto com sinais de ponte/mediação")

    if requer_densificacao and (papel_prim == "material_a_retrabalhar" or papel_sec == "ponte_de_transicao"):
        score["mediacional"] += 1
        razoes.append("material a retrabalhar com necessidade de densificação")

    # --------------------------------------------------------
    # Bloqueio
    # --------------------------------------------------------
    if contem_palavra_chave(texto_agregado, PALAVRAS_BLOQUEIO):
        score["bloqueio"] += 3
        razoes.append("texto com sinais de crítica/negação/bloqueio")

    if forma_inferencia == "critica_por_contradicao":
        score["bloqueio"] += 3
        razoes.append("forma_de_inferencia=critica_por_contradicao")

    if "diagnostica" in trabalho or "diagnostica" in trabalho2:
        score["bloqueio"] += 1
        razoes.append("trabalho_no_sistema com diagnóstico crítico")

    # --------------------------------------------------------
    # Ilustrativo
    # --------------------------------------------------------
    if papel_prim in PAPEIS_ILUSTRATIVOS or papel_sec in PAPEIS_ILUSTRATIVOS:
        score["ilustrativo"] += 3
        razoes.append("papel_editorial lateral/setorial/arquivo")

    if estado_argumentativo in ESTADOS_ARGUMENTATIVOS_FRACOS:
        score["ilustrativo"] += 2
        razoes.append(f"estado_argumentativo fraco: {estado_argumentativo}")

    if prioridade_aproveitamento == "baixa":
        score["ilustrativo"] += 1
        razoes.append("prioridade_de_aproveitamento=baixa")

    if clareza in {"muito_instavel", "instavel"}:
        score["ilustrativo"] += 1
        razoes.append(f"clareza_atual={clareza}")

    if estabilizacao in {"muito_provisorio", "provisorio"}:
        score["ilustrativo"] += 1
        razoes.append(f"grau_de_estabilizacao={estabilizacao}")

    if risco_ma_interpretacao == "alto":
        score["ilustrativo"] += 1
        razoes.append("risco_de_ma_interpretacao=alto")

    if requer_reescrita and necessita_reconstrucao_forte:
        score["ilustrativo"] += 1
        razoes.append("requer reescrita e reconstrução forte")

    # Ajustes finos
    # Material muito frágil não deve dominar como justificativo, mesmo que tenha tema central afim.
    if score["justificativo"] > 0 and score["ilustrativo"] >= 4 and not argumento_reconstruivel:
        score["justificativo"] -= 1
        razoes.append("redução de justificação por instabilidade alta sem argumento reconstruível")

    # Se há forte ponte, manter mediação competitiva.
    if score["mediacional"] >= 4 and score["justificativo"] >= 4:
        razoes.append("fragmento com dupla vocação: justificativa e mediacional")

    categoria_primaria = max(score.items(), key=lambda kv: (kv[1], kv[0]))[0]
    categorias_secundarias = [k for k, v in sorted(score.items(), key=lambda kv: (-kv[1], kv[0])) if k != categoria_primaria and v > 0]

    # Resumos curtos disponíveis no corredor
    idx_local = None
    fragmentos_rel = normalizar_lista_strings(materiais.get("fragmentos_relacionados"))
    try:
        idx_local = fragmentos_rel.index(fragment_id)
    except ValueError:
        idx_local = None

    resumo_local = None
    if idx_local is not None:
        resumos = materiais.get("resumos_de_fragmento") or []
        if idx_local < len(resumos):
            resumo_local = resumos[idx_local]

    justificacao_local = None
    if idx_local is not None:
        justs = materiais.get("justificacoes_da_associacao") or []
        if idx_local < len(justs):
            justificacao_local = justs[idx_local]

    return {
        "fragment_id": fragment_id,
        "origem_id": normalizar_texto((tratamento_item or {}).get("origem_id")),
        "categoria_primaria": categoria_primaria,
        "categorias_secundarias": categorias_secundarias,
        "pontuacoes": score,
        "justificacao_classificacao": razoes,
        "resumo_local_no_corredor": resumo_local,
        "justificacao_local_no_corredor": justificacao_local,
        "tratamento_filosofico": {
            "trabalho_no_sistema": trabalho,
            "trabalho_no_sistema_secundario": trabalho2,
            "descricao_funcional_curta": descricao_funcional,
            "problema_filosofico_central": problema,
            "papel_editorial_primario": papel_prim,
            "papel_editorial_secundario": papel_sec,
            "destino_editorial_fino": destino_fino,
            "prioridade_de_aproveitamento": prioridade_aproveitamento,
            "prioridade_de_revisao": prioridade_revisao,
            "requer_reescrita": requer_reescrita,
            "requer_densificacao": requer_densificacao,
            "requer_formalizacao_logica": requer_formalizacao,
            "estado_argumentativo": estado_argumentativo,
            "forma_de_inferencia": forma_inferencia,
            "forca_logica_estimada": forca_logica,
            "argumento_reconstruivel": argumento_reconstruivel,
            "necessita_reconstrucao_forte": necessita_reconstrucao_forte,
            "clareza_atual": clareza,
            "grau_de_estabilizacao": estabilizacao,
            "risco_de_ma_interpretacao": risco_ma_interpretacao,
        },
    }


# ============================================================
# PROCESSAMENTO DE UM CORREDOR
# ============================================================


def organizar_corredor(
    corredor_data: Dict[str, Any],
    indice_tratamento: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    proposicoes = corredor_data.get("proposicoes") or []

    resumo_corredor = {
        "total_proposicoes": 0,
        "total_fragmentos_processados": 0,
        "total_fragmentos_sem_tratamento": 0,
        "distribuicao_categorias_primarias": Counter(),
        "por_proposicao": [],
    }

    for proposicao in proposicoes:
        resumo_corredor["total_proposicoes"] += 1

        materiais = proposicao.get("materiais_de_reconstrucao") or {}
        fragmentos = normalizar_lista_strings(materiais.get("fragmentos_relacionados"))
        classificados: List[Dict[str, Any]] = []

        for fragment_id in fragmentos:
            item_trat = indice_tratamento.get(fragment_id)
            if item_trat is None:
                resumo_corredor["total_fragmentos_sem_tratamento"] += 1

            registo = classificar_fragmento(fragment_id, item_trat, proposicao)
            classificados.append(registo)
            resumo_corredor["total_fragmentos_processados"] += 1
            resumo_corredor["distribuicao_categorias_primarias"][registo["categoria_primaria"]] += 1

        # Ordenação: primeiro por categoria, depois por força heurística dentro da categoria.
        classificados.sort(
            key=lambda x: (
                x["categoria_primaria"],
                -x["pontuacoes"].get(x["categoria_primaria"], 0),
                x["fragment_id"],
            )
        )

        justificativos = [x for x in classificados if x["categoria_primaria"] == "justificativo"]
        mediacionais = [x for x in classificados if x["categoria_primaria"] == "mediacional"]
        bloqueio = [x for x in classificados if x["categoria_primaria"] == "bloqueio"]
        ilustrativos = [x for x in classificados if x["categoria_primaria"] == "ilustrativo"]

        recon = proposicao.setdefault("reconstrucao_v2", {})
        recon["fragmentos_justificativos"] = justificativos
        recon["fragmentos_mediacionais"] = mediacionais
        recon["fragmentos_de_bloqueio"] = bloqueio
        recon["fragmentos_ilustrativos"] = ilustrativos
        recon["criterio_organizacao_fragmentos"] = (
            "Classificação heurística baseada no tratamento filosófico do fragmento,"
            " no papel editorial, no potencial argumentativo e nos materiais de reconstrução do corredor."
        )

        proposicao["organizacao_fragmentos_por_funcao"] = {
            "total_fragmentos_relacionados": len(fragmentos),
            "distribuicao_categorias_primarias": {
                "justificativo": len(justificativos),
                "mediacional": len(mediacionais),
                "bloqueio": len(bloqueio),
                "ilustrativo": len(ilustrativos),
            },
            "fragmentos_sem_tratamento_filosofico": [
                frag for frag in fragmentos if frag not in indice_tratamento
            ],
        }

        resumo_corredor["por_proposicao"].append(
            {
                "proposicao_id": proposicao.get("proposicao_id"),
                "numero": proposicao.get("numero"),
                "total_fragmentos_relacionados": len(fragmentos),
                "justificativos": len(justificativos),
                "mediacionais": len(mediacionais),
                "bloqueio": len(bloqueio),
                "ilustrativos": len(ilustrativos),
                "fragmentos_sem_tratamento": len(
                    [frag for frag in fragmentos if frag not in indice_tratamento]
                ),
            }
        )

    resumo_corredor["distribuicao_categorias_primarias"] = dict(
        resumo_corredor["distribuicao_categorias_primarias"]
    )
    return corredor_data, resumo_corredor


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    pasta_script = Path(__file__).resolve().parent
    pasta_mapa_dedutivo = pasta_script.parent
    raiz_projeto = pasta_mapa_dedutivo.parent

    pasta_tratamento = (
        raiz_projeto
        / "13_Meta_Indice"
        / "cadência"
        / "04_extrator_q_faz_no_sistema"
    )

    bases_procura = [
        pasta_script,
        pasta_tratamento,
        Path.cwd(),
    ]

    path_tratamento = procurar_ficheiro(NOME_FICHEIRO_TRATAMENTO, bases_procura)
    if path_tratamento is None:
        raise FileNotFoundError(
            f"Não encontrei {NOME_FICHEIRO_TRATAMENTO}."
        )

    tratamento = carregar_json(path_tratamento)
    if not isinstance(tratamento, list):
        raise ValueError(f"{path_tratamento.name} deve ser uma lista de fragmentos.")

    indice_tratamento = construir_indice_tratamento(tratamento)

    paths_corredor: List[Path] = []
    for nome in NOMES_CORREDOR_DEFAULT:
        p = procurar_ficheiro(nome, bases_procura)
        if p is not None:
            paths_corredor.append(p)

    if not paths_corredor:
        raise FileNotFoundError("Não encontrei nenhum ficheiro de corredor.")

    resumo_global = {
        "meta": {
            "gerado_em_utc": agora_utc_iso(),
            "versao_script": "organizar_fragmentos_por_funcao_v1",
            "ficheiro_tratamento_origem": str(path_tratamento),
            "corredores_processados": [],
            "observacao": (
                "Pré-organização heurística de fragmentos por função reconstrutiva. "
                "Serve para preparar as fichas v2; não substitui revisão filosófica humana."
            ),
        },
        "resumo_por_corredor": [],
    }

    for path_corredor in paths_corredor:
        corredor_data = carregar_json(path_corredor)
        if not isinstance(corredor_data, dict):
            raise ValueError(f"{path_corredor.name} deve ser um objeto JSON.")

        organizado, resumo_corredor = organizar_corredor(corredor_data, indice_tratamento)

        meta = organizado.setdefault("meta", {})
        meta["versao_organizacao_fragmentos"] = "organizar_fragmentos_por_funcao_v1"
        meta["ficheiro_tratamento_utilizado"] = str(path_tratamento)

        organizado["resumo_organizacao_fragmentos_por_funcao"] = resumo_corredor

        path_saida = path_corredor.with_name(slug_saida_corredor(path_corredor))
        guardar_json(path_saida, organizado)

        resumo_global["meta"]["corredores_processados"].append(
            {
                "entrada": str(path_corredor),
                "saida": str(path_saida),
            }
        )
        resumo_global["resumo_por_corredor"].append(
            {
                "corredor": path_corredor.name,
                "saida": path_saida.name,
                **resumo_corredor,
            }
        )

    guardar_json(
        pasta_script / "resumo_organizacao_fragmentos_por_funcao.json",
        resumo_global,
    )

    print("Organização por função concluída.")
    for item in resumo_global["meta"]["corredores_processados"]:
        print(f"- {Path(item['entrada']).name} -> {Path(item['saida']).name}")


if __name__ == "__main__":
    main()
