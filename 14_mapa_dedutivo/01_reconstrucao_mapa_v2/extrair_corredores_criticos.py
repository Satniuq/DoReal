from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ============================================================
# CONFIGURAÇÃO DE PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
MAPA_DEDUTIVO_DIR = SCRIPT_DIR.parent
ROOT_DIR = MAPA_DEDUTIVO_DIR.parent
META_INDICE_DIR = ROOT_DIR / "13_Meta_Indice"
CADENCIA_DIR = META_INDICE_DIR / "cadência"


def resolver_ficheiro(*candidatos: Path) -> Path:
    """Devolve o primeiro ficheiro existente entre os candidatos."""
    for candidato in candidatos:
        if candidato.exists():
            return candidato
    return candidatos[0]


FICHEIRO_REVISAO = resolver_ficheiro(
    SCRIPT_DIR / "revisao_estrutural_do_mapa.json",
    MAPA_DEDUTIVO_DIR / "revisao_estrutural_do_mapa.json",
    META_INDICE_DIR / "indice" / "revisao_estrutural_do_mapa.json",
)

FICHEIRO_MAPA_BASE = resolver_ficheiro(
    SCRIPT_DIR / "02_mapa_dedutivo_arquitetura_fragmentos.json",
    SCRIPT_DIR / "mapa_dedutivo_arquitetura_fragmentos.json",
    MAPA_DEDUTIVO_DIR / "02_mapa_dedutivo_arquitetura_fragmentos.json",
    META_INDICE_DIR / "indice" / "02_mapa_dedutivo_arquitetura_fragmentos.json",
)

FICHEIRO_TRATAMENTO_FILOSOFICO = resolver_ficheiro(
    SCRIPT_DIR / "tratamento_filosofico_fragmentos.json",
    CADENCIA_DIR / "04_extrator_q_faz_no_sistema" / "tratamento_filosofico_fragmentos.json",
)

PASTA_SAIDA = SCRIPT_DIR

NOME_SAIDA_CORREDOR_A = "corredor_P25_P30.json"
NOME_SAIDA_CORREDOR_B = "corredor_P33_P37.json"
NOME_SAIDA_CORREDOR_C = "corredor_P42_P48.json"
NOME_SAIDA_CORREDOR_D = "corredor_P50.json"
NOME_SAIDA_RESUMO = "resumo_extracao_corredores_criticos.json"

VERSAO_SCRIPT = "extrair_corredores_criticos_v1"

# ============================================================
# DEFINIÇÃO DOS CORREDORES
# ============================================================

CORREDORES: List[Dict[str, Any]] = [
    {
        "corredor_id": "A",
        "nome_ficheiro": NOME_SAIDA_CORREDOR_A,
        "titulo": "Corredor A — Localidade, apreensão, representação, consciência e liberdade situada",
        "descricao": (
            "Fecha a passagem entre estrutura do real, emergência da apreensão, "
            "mediação representacional, inscrição da consciência e liberdade situada."
        ),
        "proposicoes": ["P25", "P26", "P27", "P28", "P29", "P30"],
    },
    {
        "corredor_id": "B",
        "nome_ficheiro": NOME_SAIDA_CORREDOR_B,
        "titulo": "Corredor B — Critério, verdade, erro, correção e submissão ao real",
        "descricao": (
            "Fecha o corredor epistemológico central: critério, verdade, erro, "
            "correção e submissão do juízo ao real."
        ),
        "proposicoes": ["P33", "P34", "P35", "P36", "P37"],
    },
    {
        "corredor_id": "C",
        "nome_ficheiro": NOME_SAIDA_CORREDOR_C,
        "titulo": "Corredor C — Direção prática, normatividade, bem, correção prática e dever-ser",
        "descricao": (
            "Fecha a derivação ética do sistema a partir da estrutura de inserção, "
            "orientação e correção prática no real."
        ),
        "proposicoes": ["P42", "P43", "P44", "P45", "P46", "P47", "P48"],
    },
    {
        "corredor_id": "D",
        "nome_ficheiro": NOME_SAIDA_CORREDOR_D,
        "titulo": "Corredor D — Dignidade",
        "descricao": (
            "Trata o fecho ético da dignidade, a trabalhar preferencialmente depois "
            "de os corredores anteriores estarem estabilizados."
        ),
        "proposicoes": ["P50"],
    },
]

# ============================================================
# UTILITÁRIOS
# ============================================================


def carregar_json(caminho: Path) -> Any:
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)



def guardar_json(caminho: Path, dados: Any) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")



def utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()



def normalizar_lista(valor: Any) -> List[Any]:
    if isinstance(valor, list):
        return valor
    if valor is None:
        return []
    return [valor]



def indexar_revisao_por_id(revisao: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    itens = revisao.get("revisao_por_proposicao", [])
    indice: Dict[str, Dict[str, Any]] = {}

    if isinstance(itens, list):
        for item in itens:
            if isinstance(item, dict) and item.get("proposicao_id"):
                indice[str(item["proposicao_id"])] = item
    elif isinstance(itens, dict):
        for chave, item in itens.items():
            if isinstance(item, dict):
                pid = str(item.get("proposicao_id") or chave)
                indice[pid] = item

    return indice



def indexar_mapa_base_por_id(mapa_base: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    indice: Dict[str, Dict[str, Any]] = {}
    blocos = mapa_base.get("blocos", [])
    if not isinstance(blocos, list):
        return indice

    for bloco in blocos:
        if not isinstance(bloco, dict):
            continue
        proposicoes = bloco.get("proposicoes", [])
        if not isinstance(proposicoes, list):
            continue
        for prop in proposicoes:
            if isinstance(prop, dict) and prop.get("id"):
                indice[str(prop["id"])] = prop
    return indice



def indexar_tratamento_filosofico(tratamento: Any) -> Dict[str, Dict[str, Any]]:
    """
    Tenta indexar o tratamento filosófico por id de fragmento, tolerando
    estruturas diferentes entre versões do ficheiro.
    """
    indice: Dict[str, Dict[str, Any]] = {}

    candidatos: List[Dict[str, Any]] = []

    if isinstance(tratamento, list):
        candidatos = [x for x in tratamento if isinstance(x, dict)]
    elif isinstance(tratamento, dict):
        for chave in (
            "fragmentos",
            "itens",
            "resultados",
            "tratamento_filosofico_fragmentos",
            "dados",
        ):
            valor = tratamento.get(chave)
            if isinstance(valor, list):
                candidatos = [x for x in valor if isinstance(x, dict)]
                break
        else:
            candidatos = [v for v in tratamento.values() if isinstance(v, dict)]

    for item in candidatos:
        possiveis_ids = [
            item.get("fragmento_id"),
            item.get("id_fragmento"),
            item.get("id"),
            item.get("origem_id"),
        ]
        for pid in possiveis_ids:
            if isinstance(pid, str) and pid.strip():
                indice[pid.strip()] = item
                break

    return indice



def recolher_campos_reconstrucao_v2() -> Dict[str, Any]:
    return {
        "funcao_no_percurso": None,
        "nucleo_que_se_mantem": None,
        "defice_principal": None,
        "mediacoes_em_falta_v2": [],
        "objecoes_a_bloquear_v2": [],
        "fragmentos_justificativos": [],
        "fragmentos_mediacionais": [],
        "fragmentos_de_bloqueio": [],
        "fragmentos_ilustrativos": [],
        "ponte_com_passo_anterior": None,
        "ponte_com_passo_seguinte": None,
        "decisao_editorial_v2": None,
        "nova_formulacao_v2_provisoria": None,
        "observacoes_de_trabalho": [],
    }



def resumo_tratamento_fragmento(registo: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(registo, dict):
        return {}

    campos_relevantes = [
        "fragmento_id",
        "id_fragmento",
        "argumento_reconstruivel",
        "necessita_reconstrucao_forte",
        "destino_editorial",
        "papel_editorial_primario",
        "requer_densificacao",
        "requer_formalizacao_logica",
        "problemas_filosoficos",
        "funcao_argumentativa",
        "potencial_argumentativo",
        "posicao_provavel_no_percurso",
        "relevancia_para_o_indice",
    ]

    saida: Dict[str, Any] = {}
    for campo in campos_relevantes:
        if campo in registo:
            saida[campo] = registo[campo]
    return saida



def montar_registo_proposicao(
    proposicao_id: str,
    revisao_item: Dict[str, Any],
    mapa_item: Optional[Dict[str, Any]],
    tratamento_idx: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    registo = deepcopy(revisao_item)

    registo["mapa_base_origem"] = mapa_item or {}
    registo["reconstrucao_v2"] = recolher_campos_reconstrucao_v2()

    materiais = registo.get("materiais_de_reconstrucao", {})
    fragmentos_relacionados = normalizar_lista(materiais.get("fragmentos_relacionados")) if isinstance(materiais, dict) else []

    registo["apoio_tratamento_filosofico"] = {}
    for fragmento_id in fragmentos_relacionados:
        if not isinstance(fragmento_id, str):
            continue

        candidatos_ids = [fragmento_id]
        # Também tenta a origem, caso o tratamento filosófico esteja indexado por origem.
        if "_SEG_" in fragmento_id:
            candidatos_ids.append(fragmento_id.split("_SEG_", 1)[0])

        apoio: Dict[str, Any] = {}
        for candidato in candidatos_ids:
            apoio = resumo_tratamento_fragmento(tratamento_idx.get(candidato))
            if apoio:
                break

        if apoio:
            registo["apoio_tratamento_filosofico"][fragmento_id] = apoio

    # Harmonização útil para trabalho futuro.
    registo.setdefault("numero", None)
    registo.setdefault("bloco_id", None)
    registo.setdefault("bloco_titulo", None)
    registo.setdefault("proposicao", None)
    registo.setdefault("descricao_curta", None)
    registo.setdefault("depende_de", [])
    registo.setdefault("prepara", [])

    return registo



def extrair_corredor(
    definicao_corredor: Dict[str, Any],
    revisao_idx: Dict[str, Dict[str, Any]],
    mapa_idx: Dict[str, Dict[str, Any]],
    tratamento_idx: Dict[str, Dict[str, Any]],
    meta_global: Dict[str, Any],
    resumo_global: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[str]]:
    proposicoes = definicao_corredor["proposicoes"]
    itens: List[Dict[str, Any]] = []
    em_falta: List[str] = []

    for proposicao_id in proposicoes:
        revisao_item = revisao_idx.get(proposicao_id)
        if not revisao_item:
            em_falta.append(proposicao_id)
            continue

        mapa_item = mapa_idx.get(proposicao_id)
        itens.append(
            montar_registo_proposicao(
                proposicao_id=proposicao_id,
                revisao_item=revisao_item,
                mapa_item=mapa_item,
                tratamento_idx=tratamento_idx,
            )
        )

    itens.sort(key=lambda x: (x.get("numero") is None, x.get("numero") or 0, x.get("proposicao_id") or ""))

    distribuicao_estabilidade: Dict[str, int] = {}
    distribuicao_necessidade: Dict[str, int] = {}
    distribuicao_acao: Dict[str, int] = {}
    top_pressao: List[Dict[str, Any]] = []

    for item in itens:
        diagnostico = item.get("diagnostico_estrutural", {}) if isinstance(item.get("diagnostico_estrutural"), dict) else {}
        pressao = item.get("pressao_dos_fragmentos", {}) if isinstance(item.get("pressao_dos_fragmentos"), dict) else {}

        estabilidade = diagnostico.get("estabilidade") or "desconhecida"
        necessidade = diagnostico.get("necessidade_principal") or "desconhecida"
        acao = diagnostico.get("acao_estrutural_recomendada") or "desconhecida"

        distribuicao_estabilidade[estabilidade] = distribuicao_estabilidade.get(estabilidade, 0) + 1
        distribuicao_necessidade[necessidade] = distribuicao_necessidade.get(necessidade, 0) + 1
        distribuicao_acao[acao] = distribuicao_acao.get(acao, 0) + 1

        top_pressao.append(
            {
                "proposicao_id": item.get("proposicao_id"),
                "numero": item.get("numero"),
                "total_fragmentos_que_tocam": pressao.get("total_fragmentos_que_tocam", 0),
                "acao_recomendada_dominante": pressao.get("acao_recomendada_dominante"),
                "efeito_principal_dominante": pressao.get("efeito_principal_dominante"),
                "necessidade_principal": diagnostico.get("necessidade_principal"),
                "estabilidade": diagnostico.get("estabilidade"),
            }
        )

    top_pressao.sort(
        key=lambda x: (
            -(x.get("total_fragmentos_que_tocam") or 0),
            x.get("numero") or 0,
            x.get("proposicao_id") or "",
        )
    )

    saida = {
        "meta": {
            "gerado_em_utc": utc_iso(),
            "versao_script": VERSAO_SCRIPT,
            "corredor_id": definicao_corredor["corredor_id"],
            "titulo": definicao_corredor["titulo"],
            "descricao": definicao_corredor["descricao"],
            "ficheiro_revisao_origem": str(FICHEIRO_REVISAO),
            "ficheiro_mapa_base_origem": str(FICHEIRO_MAPA_BASE),
            "ficheiro_tratamento_filosofico_origem": str(FICHEIRO_TRATAMENTO_FILOSOFICO),
            "proposicoes_pedidas": proposicoes,
            "proposicoes_extraidas": [item.get("proposicao_id") for item in itens],
            "proposicoes_em_falta": em_falta,
            "total_proposicoes_extraidas": len(itens),
            "objetivo": (
                "Isolar o corredor crítico como dossiê de reconstrução local, "
                "preservando o diagnóstico estrutural da revisão e acrescentando "
                "campos próprios de trabalho para o mapa dedutivo reconstruído v2."
            ),
        },
        "contexto_global": {
            "meta_revisao": meta_global,
            "resumo_global_revisao": {
                "distribuicao_estabilidade": resumo_global.get("distribuicao_estabilidade", {}),
                "distribuicao_necessidade_principal": resumo_global.get("distribuicao_necessidade_principal", {}),
                "distribuicao_acao_estrutural_recomendada": resumo_global.get("distribuicao_acao_estrutural_recomendada", {}),
                "top_proposicoes_por_pressao": resumo_global.get("top_proposicoes_por_pressao", []),
            },
        },
        "resumo_do_corredor": {
            "distribuicao_estabilidade": distribuicao_estabilidade,
            "distribuicao_necessidade_principal": distribuicao_necessidade,
            "distribuicao_acao_estrutural_recomendada": distribuicao_acao,
            "top_proposicoes_por_pressao_no_corredor": top_pressao,
        },
        "proposicoes": itens,
    }

    return saida, em_falta



def validar_precondicoes() -> None:
    faltas = []
    for caminho in (FICHEIRO_REVISAO, FICHEIRO_MAPA_BASE):
        if not caminho.exists():
            faltas.append(str(caminho))

    if faltas:
        raise FileNotFoundError(
            "Não foi possível encontrar os ficheiros obrigatórios:\n- " + "\n- ".join(faltas)
        )



def main() -> None:
    validar_precondicoes()

    revisao = carregar_json(FICHEIRO_REVISAO)
    mapa_base = carregar_json(FICHEIRO_MAPA_BASE)
    tratamento = carregar_json(FICHEIRO_TRATAMENTO_FILOSOFICO) if FICHEIRO_TRATAMENTO_FILOSOFICO.exists() else {}

    revisao_idx = indexar_revisao_por_id(revisao)
    mapa_idx = indexar_mapa_base_por_id(mapa_base)
    tratamento_idx = indexar_tratamento_filosofico(tratamento)

    meta_global = revisao.get("meta", {}) if isinstance(revisao, dict) else {}
    resumo_global = revisao.get("resumo_global", {}) if isinstance(revisao, dict) else {}

    resumo_execucao = {
        "meta": {
            "gerado_em_utc": utc_iso(),
            "versao_script": VERSAO_SCRIPT,
            "ficheiro_revisao_origem": str(FICHEIRO_REVISAO),
            "ficheiro_mapa_base_origem": str(FICHEIRO_MAPA_BASE),
            "ficheiro_tratamento_filosofico_origem": str(FICHEIRO_TRATAMENTO_FILOSOFICO),
        },
        "corredores_gerados": [],
        "faltas": [],
    }

    for definicao_corredor in CORREDORES:
        dados_corredor, em_falta = extrair_corredor(
            definicao_corredor=definicao_corredor,
            revisao_idx=revisao_idx,
            mapa_idx=mapa_idx,
            tratamento_idx=tratamento_idx,
            meta_global=meta_global,
            resumo_global=resumo_global,
        )

        caminho_saida = PASTA_SAIDA / definicao_corredor["nome_ficheiro"]
        guardar_json(caminho_saida, dados_corredor)

        resumo_execucao["corredores_gerados"].append(
            {
                "corredor_id": definicao_corredor["corredor_id"],
                "titulo": definicao_corredor["titulo"],
                "ficheiro_saida": str(caminho_saida),
                "total_proposicoes_extraidas": dados_corredor["meta"]["total_proposicoes_extraidas"],
                "proposicoes_extraidas": dados_corredor["meta"]["proposicoes_extraidas"],
                "proposicoes_em_falta": em_falta,
            }
        )

        if em_falta:
            resumo_execucao["faltas"].append(
                {
                    "corredor_id": definicao_corredor["corredor_id"],
                    "proposicoes_em_falta": em_falta,
                }
            )

    guardar_json(PASTA_SAIDA / NOME_SAIDA_RESUMO, resumo_execucao)

    print("=" * 72)
    print("EXTRAÇÃO DE CORREDORES CRÍTICOS CONCLUÍDA")
    print("=" * 72)
    print(f"Revisão estrutural: {FICHEIRO_REVISAO}")
    print(f"Mapa base:         {FICHEIRO_MAPA_BASE}")
    print(f"Tratamento filos.: {FICHEIRO_TRATAMENTO_FILOSOFICO} -> {FICHEIRO_TRATAMENTO_FILOSOFICO.exists()}")
    print("-" * 72)
    for item in resumo_execucao["corredores_gerados"]:
        print(
            f"[{item['corredor_id']}] {item['titulo']} -> "
            f"{item['total_proposicoes_extraidas']} proposição(ões) -> {item['ficheiro_saida']}"
        )
        if item["proposicoes_em_falta"]:
            print(f"    EM FALTA: {', '.join(item['proposicoes_em_falta'])}")
    print("-" * 72)
    print(f"Resumo: {PASTA_SAIDA / NOME_SAIDA_RESUMO}")


if __name__ == "__main__":
    main()
