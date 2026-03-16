from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonschema
from dotenv import load_dotenv
from openai import OpenAI

# ============================================================
# CONFIGURAÇÃO
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
META_INDICE_DIR = ROOT_DIR / "13_Meta_Indice"
CADENCIA_DIR = META_INDICE_DIR / "cadência"


def resolver_ficheiro(*candidatos: Path) -> Path:
    for c in candidatos:
        if c.exists():
            return c
    return candidatos[0]


FICHEIRO_FRAGMENTOS = resolver_ficheiro(
    CADENCIA_DIR / "01_segmentar_fragmentos" / "fragmentos_resegmentados.json",
    SCRIPT_DIR / "fragmentos_resegmentados.json",
)

FICHEIRO_CADENCIA = resolver_ficheiro(
    CADENCIA_DIR / "02_extrator_cadência" / "cadencia_extraida.json",
    SCRIPT_DIR / "cadencia_extraida.json",
)

FICHEIRO_META_PERCURSO = resolver_ficheiro(
    META_INDICE_DIR / "meta" / "meta_referencia_do_percurso.json",
    SCRIPT_DIR / "meta_referencia_do_percurso.json",
)

FICHEIRO_META_INDICE = resolver_ficheiro(
    META_INDICE_DIR / "meta" / "meta_indice.json",
    SCRIPT_DIR / "meta_indice.json",
)

FICHEIRO_INDICE_SEQUENCIAL = resolver_ficheiro(
    META_INDICE_DIR / "indice" / "indice_sequencial.json",
    SCRIPT_DIR / "indice_sequencial.json",
)

FICHEIRO_INDICE_ARGUMENTOS = resolver_ficheiro(
    META_INDICE_DIR / "indice" / "indice_argumentos.json",
    SCRIPT_DIR / "indice_argumentos.json",
)

FICHEIRO_ARGUMENTOS_UNIFICADOS = resolver_ficheiro(
    META_INDICE_DIR / "indice" / "argumentos" / "argumentos_unificados.json",
    SCRIPT_DIR / "argumentos_unificados.json",
)

FICHEIRO_CONCEITOS = resolver_ficheiro(
    META_INDICE_DIR / "dados_base" / "todos_os_conceitos.json",
    SCRIPT_DIR / "todos_os_conceitos.json",
)

FICHEIRO_OPERACOES = resolver_ficheiro(
    META_INDICE_DIR / "dados_base" / "operacoes.json",
    SCRIPT_DIR / "operacoes.json",
)

FICHEIRO_TRATAMENTO_FILOSOFICO = resolver_ficheiro(
    CADENCIA_DIR / "04_extrator_q_faz_no_sistema" / "tratamento_filosofico_fragmentos.json",
    SCRIPT_DIR / "tratamento_filosofico_fragmentos.json",
)

FICHEIRO_MAPA_DEDUTIVO = resolver_ficheiro(
    SCRIPT_DIR / "02_mapa_dedutivo_arquitetura_fragmentos.json",
    SCRIPT_DIR / "mapa_dedutivo_arquitetura_fragmentos.json",
)

FICHEIRO_SAIDA = SCRIPT_DIR / "impacto_fragmentos_no_mapa.json"
FICHEIRO_ESTADO = SCRIPT_DIR / "estado_impacto_fragmentos_no_mapa.json"
FICHEIRO_FALHAS = SCRIPT_DIR / "falhas_impacto_fragmentos_no_mapa.json"
FICHEIRO_LOGS = SCRIPT_DIR / "impacto_fragmentos_no_mapa_logs_execucao.json"
FICHEIRO_RELATORIO = SCRIPT_DIR / "impacto_fragmentos_no_mapa_relatorio_validacao.json"
FICHEIRO_AGREGADO = SCRIPT_DIR / "agregado_impacto_por_proposicao.json"

VERSAO_EXTRATOR = "extrator_impacto_fragmentos_no_mapa_v2_gpt54"
MODELO_PRINCIPAL = "gpt-5.4"
MODELO_ARBITRAGEM = "gpt-5.4"

FORCAR_REPROCESSAMENTO = False
REPROCESSAR_FALHAS = True
GUARDAR_PROMPTS = False

MAX_RETRIES_SCHEMA = 2
MAX_RETRIES_INTERPRETACAO = 1
MAX_RETRIES_FALLBACK = 1

LIMITE_FRAGMENTOS_TESTE = None

MAX_CHARS_FRAGMENTO = 4500
MAX_ITEMS_ZONAS = 20
MAX_ITEMS_ARGUMENTOS = 25
MAX_ITEMS_INDICE = 20
MAX_ITEMS_CONCEITOS = 40
MAX_ITEMS_OPERACOES = 40
MAX_PROPOSICOES_MAPA_RESUMO = 80
MAX_PROPOSICOES_TOCADAS = 5
MAX_OBJECOES = 5
MAX_CONCEITOS_NOVOS = 6

load_dotenv(ROOT_DIR / ".env")
load_dotenv(SCRIPT_DIR / ".env")

print("SCRIPT_DIR =", SCRIPT_DIR)
print("ROOT_DIR =", ROOT_DIR)
print("META_INDICE_DIR =", META_INDICE_DIR)
print("CADENCIA_DIR =", CADENCIA_DIR)

print("FICHEIRO_FRAGMENTOS =", FICHEIRO_FRAGMENTOS, FICHEIRO_FRAGMENTOS.exists())
print("FICHEIRO_CADENCIA =", FICHEIRO_CADENCIA, FICHEIRO_CADENCIA.exists())
print("FICHEIRO_META_PERCURSO =", FICHEIRO_META_PERCURSO, FICHEIRO_META_PERCURSO.exists())
print("FICHEIRO_META_INDICE =", FICHEIRO_META_INDICE, FICHEIRO_META_INDICE.exists())
print("FICHEIRO_INDICE_SEQUENCIAL =", FICHEIRO_INDICE_SEQUENCIAL, FICHEIRO_INDICE_SEQUENCIAL.exists())
print("FICHEIRO_INDICE_ARGUMENTOS =", FICHEIRO_INDICE_ARGUMENTOS, FICHEIRO_INDICE_ARGUMENTOS.exists())
print("FICHEIRO_ARGUMENTOS_UNIFICADOS =", FICHEIRO_ARGUMENTOS_UNIFICADOS, FICHEIRO_ARGUMENTOS_UNIFICADOS.exists())
print("FICHEIRO_CONCEITOS =", FICHEIRO_CONCEITOS, FICHEIRO_CONCEITOS.exists())
print("FICHEIRO_OPERACOES =", FICHEIRO_OPERACOES, FICHEIRO_OPERACOES.exists())
print("FICHEIRO_TRATAMENTO_FILOSOFICO =", FICHEIRO_TRATAMENTO_FILOSOFICO, FICHEIRO_TRATAMENTO_FILOSOFICO.exists())
print("FICHEIRO_MAPA_DEDUTIVO =", FICHEIRO_MAPA_DEDUTIVO, FICHEIRO_MAPA_DEDUTIVO.exists())
print("ENV ROOT =", (ROOT_DIR / ".env").exists())

CLIENT = OpenAI()


# ============================================================
# DADOS DERIVADOS
# ============================================================

@dataclass
class ResultadoValidacao:
    ok: bool
    erros: List[str]
    avisos: List[str]


@dataclass
class ResultadoCoerencia:
    ok: bool
    score_fragilidade: int
    motivos_reprompt: List[str]
    avisos: List[str]


# ============================================================
# IO BÁSICO
# ============================================================

def carregar_json(caminho: Path) -> Any:
    if not caminho.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {caminho}")
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def carregar_json_opcional(caminho: Path, default: Any) -> Any:
    if not caminho.exists():
        return default
    return carregar_json(caminho)


def gravar_json(caminho: Path, dados: Any) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def print_parcial(processados: int, ignorados: int, falhados: int) -> None:
    print(
        f"   📊 Parcial | processados={processados} | ignorados={ignorados} | falhados={falhados}",
        flush=True,
    )


# ============================================================
# SCHEMA EMBUTIDO
# ============================================================

def construir_schema_impacto_no_mapa() -> Dict[str, Any]:
    zonas = [
        "fundacao_ontologica",
        "dinamica_do_real",
        "organizacao_do_real",
        "localidade_e_consciencia",
        "epistemologia",
        "etica_ontologica",
        "fecho_etico",
        "metaestrutural",
        "mista",
    ]

    grau_relevancia = ["alto", "medio", "baixo"]
    tipo_relacao = [
        "toca_diretamente",
        "toca_indiretamente",
        "faz_ponte_entre",
        "corrige_formulacao",
        "introduz_distincao_nova",
        "apoia_justificacao",
        "bloqueia_objecao",
    ]

    efeitos = [
        "repete",
        "explicita",
        "corrige",
        "medeia",
        "cria_passo_novo",
        "sem_impacto_relevante",
    ]

    acoes = [
        "manter",
        "densificar",
        "reformular",
        "dividir",
        "criar_intermedio",
        "deslocar",
        "sem_acao",
    ]

    prioridade = ["imediata", "alta", "media", "baixa"]
    confianca = ["alta", "media", "baixa"]
    utilidade = [
        "estrutural",
        "justificativa",
        "mediacional",
        "redacional",
        "tematica",
        "nenhuma",
    ]

    tipo_densificacao = [
        "do_passo",
        "da_justificacao_do_passo",
        "da_exposicao",
        "nao_se_aplica",
    ]

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "impacto_fragmento_no_mapa.schema.json",
        "title": "Impacto do Fragmento no Mapa Dedutivo",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "fragment_id",
            "origem_id",
            "ordem_no_ficheiro",
            "impacto_no_mapa_fragmento",
        ],
        "properties": {
            "fragment_id": {"type": "string"},
            "origem_id": {"type": ["string", "null"]},
            "ordem_no_ficheiro": {"type": "integer"},
            "impacto_no_mapa_fragmento": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "resumo_do_fragmento_para_o_mapa",
                    "tese_principal_relevante",
                    "zona_filosofica_dominante",
                    "tipo_de_utilidade_principal",
                    "proposicoes_do_mapa_tocadas",
                    "efeito_principal_no_mapa",
                    "efeitos_secundarios",
                    "impacto_editorial_e_dedutivo",
                    "decisao_final",
                ],
                "properties": {
                    "resumo_do_fragmento_para_o_mapa": {"type": "string"},
                    "tese_principal_relevante": {"type": "string"},
                    "zona_filosofica_dominante": {
                        "type": "string",
                        "enum": zonas,
                    },
                    "tipo_de_utilidade_principal": {
                        "type": "string",
                        "enum": utilidade,
                    },
                    "proposicoes_do_mapa_tocadas": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "proposicao_id",
                                "numero",
                                "proposicao_resumida",
                                "grau_de_relevancia",
                                "tipo_de_relacao",
                                "justificacao_da_associacao",
                            ],
                            "properties": {
                                "proposicao_id": {"type": "string"},
                                "numero": {"type": "integer"},
                                "proposicao_resumida": {"type": "string"},
                                "grau_de_relevancia": {
                                    "type": "string",
                                    "enum": grau_relevancia,
                                },
                                "tipo_de_relacao": {
                                    "type": "string",
                                    "enum": tipo_relacao,
                                },
                                "justificacao_da_associacao": {"type": "string"},
                            },
                        },
                    },
                    "efeito_principal_no_mapa": {
                        "type": "string",
                        "enum": efeitos,
                    },
                    "efeitos_secundarios": {
                        "type": "array",
                        "items": {"type": "string", "enum": efeitos},
                        "uniqueItems": True,
                    },
                    "impacto_editorial_e_dedutivo": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "tipo_de_densificacao",
                            "o_que_o_fragmento_acrescenta_ao_mapa",
                            "justificacao_nova_que_fornece",
                            "objecoes_que_ajuda_a_bloquear",
                            "mediacao_que_fornece",
                            "conceitos_ou_distincoes_novas",
                            "obriga_a_reescrever_o_passo",
                            "obriga_a_dividir_o_passo",
                            "obriga_a_criar_passo_intermedio",
                            "proposta_de_nova_formulacao",
                            "proposta_de_novo_passo",
                            "entre_que_passos_deveria_entrar",
                        ],
                        "properties": {
                            "tipo_de_densificacao": {
                                "type": "string",
                                "enum": tipo_densificacao,
                            },
                            "o_que_o_fragmento_acrescenta_ao_mapa": {"type": "string"},
                            "justificacao_nova_que_fornece": {"type": "string"},
                            "objecoes_que_ajuda_a_bloquear": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "mediacao_que_fornece": {"type": "string"},
                            "conceitos_ou_distincoes_novas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "obriga_a_reescrever_o_passo": {"type": "boolean"},
                            "obriga_a_dividir_o_passo": {"type": "boolean"},
                            "obriga_a_criar_passo_intermedio": {"type": "boolean"},
                            "proposta_de_nova_formulacao": {"type": ["string", "null"]},
                            "proposta_de_novo_passo": {"type": ["string", "null"]},
                            "entre_que_passos_deveria_entrar": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                        },
                    },
                    "decisao_final": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "acao_recomendada_sobre_o_mapa",
                            "prioridade_editorial",
                            "confianca_da_analise",
                            "necessita_revisao_humana",
                            "observacao_final",
                        ],
                        "properties": {
                            "acao_recomendada_sobre_o_mapa": {
                                "type": "string",
                                "enum": acoes,
                            },
                            "prioridade_editorial": {
                                "type": "string",
                                "enum": prioridade,
                            },
                            "confianca_da_analise": {
                                "type": "string",
                                "enum": confianca,
                            },
                            "necessita_revisao_humana": {"type": "boolean"},
                            "observacao_final": {"type": "string"},
                        },
                    },
                },
            },
        },
    }


# ============================================================
# NORMALIZAÇÃO / RESUMOS
# ============================================================

def garantir_lista_fragmentos(dados: Any) -> List[Dict[str, Any]]:
    if isinstance(dados, list):
        return dados
    if isinstance(dados, dict) and isinstance(dados.get("fragmentos"), list):
        return dados["fragmentos"]
    raise ValueError("fragmentos_resegmentados.json não tem formato esperado")


def garantir_lista_cadencia(dados: Any) -> List[Dict[str, Any]]:
    if isinstance(dados, list):
        return dados
    if isinstance(dados, dict) and isinstance(dados.get("cadencias"), list):
        return dados["cadencias"]
    raise ValueError("cadencia_extraida.json não tem formato esperado")


def garantir_lista_tratamento(dados: Any) -> List[Dict[str, Any]]:
    if isinstance(dados, list):
        return dados
    if isinstance(dados, dict) and isinstance(dados.get("resultados"), list):
        return dados["resultados"]
    raise ValueError("tratamento_filosofico_fragmentos.json não tem formato esperado")


def normalizar_lista(valor: Any) -> List[Any]:
    if valor is None:
        return []
    if isinstance(valor, list):
        return valor
    return [valor]


def normalizar_dict(valor: Any) -> Dict[str, Any]:
    return valor if isinstance(valor, dict) else {}


def inferir_origem_id(fragmento: Dict[str, Any]) -> Optional[str]:
    origem = fragmento.get("origem")
    if isinstance(origem, dict) and origem.get("origem_id"):
        return origem.get("origem_id")

    for chave in ("origem_id", "fragmento_pai_id", "container_id"):
        valor = fragmento.get(chave)
        if valor:
            return valor

    fragment_id = (
        fragmento.get("fragment_id")
        or fragmento.get("fragmento_id")
        or fragmento.get("id_fragmento")
        or fragmento.get("id")
    )

    if isinstance(fragment_id, str) and "_SEG_" in fragment_id:
        return fragment_id.split("_SEG_")[0]

    return None


def extrair_ordem_no_ficheiro(fragmento: Dict[str, Any], fallback: int) -> int:
    origem = fragmento.get("origem")
    if isinstance(origem, dict):
        valor = origem.get("ordem_no_ficheiro")
        if isinstance(valor, int):
            return valor
    if isinstance(fragmento.get("ordem_no_ficheiro"), int):
        return fragmento["ordem_no_ficheiro"]
    return fallback


def bucket_comprimento(n_chars: int) -> str:
    if n_chars < 220:
        return "curto"
    if n_chars < 700:
        return "medio"
    return "longo"


def limitar_texto(texto: str, limite: int = MAX_CHARS_FRAGMENTO) -> str:
    texto = (texto or "").strip()
    if len(texto) <= limite:
        return texto
    return texto[:limite] + "\n\n[TRUNCADO]"


def indexar_por_fragment_id(lista: List[Dict[str, Any]], chave: str = "fragment_id") -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for item in lista:
        if not isinstance(item, dict):
            continue
        fid = item.get(chave)
        if isinstance(fid, str):
            out[fid] = item
    return out


def resumir_meta_indice(meta_indice: Any) -> Dict[str, Any]:
    if not isinstance(meta_indice, dict):
        return {}

    meta = meta_indice.get("meta_indice", {})
    if not isinstance(meta, dict):
        return {}

    regimes_resumo = []
    for regime_id, dados in (meta.get("regimes", {}) or {}).items():
        if not isinstance(dados, dict):
            continue
        regimes_resumo.append(
            {
                "id": regime_id,
                "descricao": dados.get("descricao"),
                "estatuto": dados.get("estatuto"),
                "funcao": dados.get("funcao"),
            }
        )

    return {
        "descricao": meta.get("descricao"),
        "criterio_ultimo": meta.get("criterio_ultimo"),
        "regimes": regimes_resumo[:MAX_ITEMS_ZONAS],
    }


def resumir_indice_argumentos(indice_argumentos: Any) -> Any:
    if isinstance(indice_argumentos, dict) and "lista_auxiliar_argumentos" in indice_argumentos:
        base = indice_argumentos["lista_auxiliar_argumentos"]
        if isinstance(base, list):
            return base[:MAX_ITEMS_INDICE]
        if isinstance(base, dict):
            resumo = {}
            for k, v in list(base.items())[:MAX_ITEMS_INDICE]:
                resumo[k] = v
            return resumo

    if isinstance(indice_argumentos, list):
        return indice_argumentos[:MAX_ITEMS_INDICE]

    if isinstance(indice_argumentos, dict):
        resumo = {}
        for k, v in list(indice_argumentos.items())[:MAX_ITEMS_INDICE]:
            resumo[k] = v
        return resumo

    return {}


def resumir_indice_sequencial(indice_sequencial: Any) -> Any:
    if isinstance(indice_sequencial, dict):
        for chave_candidata in ("indice_sequencial", "lista_auxiliar_indice", "capitulos", "sequencia"):
            if chave_candidata in indice_sequencial:
                base = indice_sequencial[chave_candidata]
                if isinstance(base, list):
                    return base[:MAX_ITEMS_INDICE]
                if isinstance(base, dict):
                    resumo = {}
                    for k, v in list(base.items())[:MAX_ITEMS_INDICE]:
                        resumo[k] = v
                    return resumo

    if isinstance(indice_sequencial, list):
        return indice_sequencial[:MAX_ITEMS_INDICE]

    if isinstance(indice_sequencial, dict):
        resumo = {}
        for k, v in list(indice_sequencial.items())[:MAX_ITEMS_INDICE]:
            resumo[k] = v
        return resumo

    return {}


def resumir_argumentos_unificados(argumentos_unificados: Any) -> List[Dict[str, Any]]:
    resumo = []
    if isinstance(argumentos_unificados, list):
        for item in argumentos_unificados[:MAX_ITEMS_ARGUMENTOS]:
            if not isinstance(item, dict):
                continue
            resumo.append(
                {
                    "id": item.get("id") or item.get("argumento_id"),
                    "capitulo": item.get("capitulo"),
                    "parte": item.get("parte"),
                    "titulo": item.get("titulo") or item.get("nome"),
                    "conceito_alvo": item.get("conceito_alvo"),
                    "descricao": item.get("descricao") or item.get("resumo"),
                    "operacoes_chave": item.get("operacoes_chave", []),
                    "pressupostos_ontologicos": item.get("pressupostos_ontologicos", []),
                    "ligacoes_narrativas": item.get("ligacoes_narrativas", []),
                }
            )
    return resumo


def resumir_meta_percurso(meta_percurso: Any) -> List[Dict[str, Any]]:
    zonas = []
    if isinstance(meta_percurso, dict):
        for zona_id, dados in list(meta_percurso.items())[:MAX_ITEMS_ZONAS]:
            if not isinstance(dados, dict):
                continue
            zonas.append(
                {
                    "id": zona_id,
                    "tipo_instancia": dados.get("tipo_instancia"),
                    "pressupoe_percursos": dados.get("pressupoe_percursos", []),
                    "observacao": dados.get("observacao"),
                }
            )
    return zonas


def resumir_conceitos(conceitos: Any) -> List[Dict[str, Any]]:
    out = []
    if isinstance(conceitos, dict):
        for cid, dados in list(conceitos.items())[:MAX_ITEMS_CONCEITOS]:
            if not isinstance(dados, dict):
                continue
            out.append(
                {
                    "id": dados.get("id", cid),
                    "nome": dados.get("nome"),
                    "dominio": dados.get("dominio"),
                    "definicao": dados.get("definicao"),
                    "dependencias": dados.get("dependencias", []),
                    "operacoes_ontologicas": dados.get("operacoes_ontologicas", []),
                }
            )
    return out


def resumir_operacoes(operacoes: Any) -> List[Dict[str, Any]]:
    out = []
    if isinstance(operacoes, dict):
        for oid, dados in list(operacoes.items())[:MAX_ITEMS_OPERACOES]:
            if not isinstance(dados, dict):
                continue
            out.append(
                {
                    "id": oid,
                    "tipo": dados.get("tipo"),
                    "descricao": dados.get("descricao"),
                    "criterio_ultimo": dados.get("criterio_ultimo"),
                }
            )
    return out


def resumir_mapa_dedutivo(mapa: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(mapa, dict):
        return out

    blocos = mapa.get("blocos")
    if not isinstance(blocos, list):
        return out

    for bloco in blocos:
        if not isinstance(bloco, dict):
            continue
        bloco_id = bloco.get("id")
        bloco_titulo = bloco.get("titulo")
        for prop in normalizar_lista(bloco.get("proposicoes")):
            if not isinstance(prop, dict):
                continue
            just = normalizar_dict(prop.get("justificacao"))
            trat = normalizar_dict(prop.get("tratamento_academico"))
            dec = normalizar_dict(prop.get("decisao_editorial"))
            out.append(
                {
                    "bloco_id": bloco_id,
                    "bloco_titulo": bloco_titulo,
                    "proposicao_id": prop.get("id"),
                    "numero": prop.get("numero"),
                    "proposicao": prop.get("proposicao"),
                    "descricao_curta": prop.get("descricao_curta"),
                    "depende_de": normalizar_lista(prop.get("depende_de")),
                    "prepara": normalizar_lista(prop.get("prepara")),
                    "tese_minima": just.get("tese_minima"),
                    "tipo_de_necessidade": just.get("tipo_de_necessidade"),
                    "estatuto_inferencial": just.get("estatuto_inferencial"),
                    "formulacao_filosofico_academica": trat.get("formulacao_filosofico_academica"),
                    "o_que_falta_provar_ou_explicitar": trat.get("o_que_falta_provar_ou_explicitar"),
                    "objecoes_tipicas_a_bloquear": normalizar_lista(trat.get("objecoes_tipicas_a_bloquear")),
                    "estado_atual": dec.get("estado_atual"),
                    "necessidade_de_tratamento": dec.get("necessidade_de_tratamento"),
                }
            )
            if len(out) >= MAX_PROPOSICOES_MAPA_RESUMO:
                return out
    return out


def resumir_tratamento_previo(item: Dict[str, Any]) -> Dict[str, Any]:
    raiz = normalizar_dict(item.get("tratamento_filosofico_fragmento"))
    pos = normalizar_dict(raiz.get("posicao_no_indice"))
    pot = normalizar_dict(raiz.get("potencial_argumentativo"))
    dest = normalizar_dict(raiz.get("destino_editorial"))

    return {
        "explicacao_textual_do_que_o_fragmento_tenta_fazer": raiz.get("explicacao_textual_do_que_o_fragmento_tenta_fazer"),
        "trabalho_no_sistema": raiz.get("trabalho_no_sistema"),
        "trabalho_no_sistema_secundario": raiz.get("trabalho_no_sistema_secundario"),
        "problema_filosofico_central": raiz.get("problema_filosofico_central"),
        "problemas_filosoficos_associados": normalizar_lista(raiz.get("problemas_filosoficos_associados")),
        "tipo_de_problema": raiz.get("tipo_de_problema"),
        "posicao_no_indice": {
            "parte_id": pos.get("parte_id"),
            "capitulo_id": pos.get("capitulo_id"),
            "capitulo_titulo": pos.get("capitulo_titulo"),
            "argumento_canonico_relacionado": pos.get("argumento_canonico_relacionado"),
            "argumentos_canonicos_associados": normalizar_lista(pos.get("argumentos_canonicos_associados")),
            "grau_de_pertenca_ao_indice": pos.get("grau_de_pertenca_ao_indice"),
            "modo_de_pertenca": pos.get("modo_de_pertenca"),
            "justificacao_de_posicao_no_indice": pos.get("justificacao_de_posicao_no_indice"),
        },
        "potencial_argumentativo": {
            "estado_argumentativo": pot.get("estado_argumentativo"),
            "premissa_central_reconstruida": pot.get("premissa_central_reconstruida"),
            "conclusao_visada": pot.get("conclusao_visada"),
            "forma_de_inferencia": pot.get("forma_de_inferencia"),
            "forca_logica_estimada": pot.get("forca_logica_estimada"),
            "argumento_reconstruivel": pot.get("argumento_reconstruivel"),
            "observacoes_argumentativas": pot.get("observacoes_argumentativas"),
        },
        "destino_editorial": {
            "destino_editorial_fino": dest.get("destino_editorial_fino"),
            "papel_editorial_primario": dest.get("papel_editorial_primario"),
            "prioridade_de_revisao": dest.get("prioridade_de_revisao"),
            "prioridade_de_aproveitamento": dest.get("prioridade_de_aproveitamento"),
            "requer_reescrita": dest.get("requer_reescrita"),
            "requer_densificacao": dest.get("requer_densificacao"),
            "requer_formalizacao_logica": dest.get("requer_formalizacao_logica"),
        },
    }


# ============================================================
# CONTEXTO MACRO REDUZIDO
# ============================================================

def construir_contexto_macro_minimo(
    meta_percurso: Dict[str, Any],
    meta_indice: Any,
    indice_sequencial: Any,
    indice_argumentos: Any,
    argumentos_unificados: Any,
    conceitos: Any,
    operacoes: Any,
    mapa_dedutivo: Any,
) -> Dict[str, Any]:
    return {
        "regras_gerais": [
            "texto_fragmento manda sobre os campos auxiliares",
            "nao confundir afinidade tematica com impacto estrutural no mapa",
            "nao classificar como cria_passo_novo sem necessidade dedutiva clara",
            "preferir explicita a corrige quando a diferenca for apenas de formulacao",
            "preferir medeia quando o fragmento liga dois passos ja existentes",
            "um fragmento pode ser util para a escrita sem mexer na arquitetura",
            "se houver duvida, usar classificacoes mais fracas e prudentes",
        ],
        "zonas_do_percurso": resumir_meta_percurso(meta_percurso),
        "meta_indice_resumo": resumir_meta_indice(meta_indice),
        "indice_sequencial_resumo": resumir_indice_sequencial(indice_sequencial),
        "indice_argumentos_resumo": resumir_indice_argumentos(indice_argumentos),
        "argumentos_unificados_resumo": resumir_argumentos_unificados(argumentos_unificados),
        "conceitos_resumo": resumir_conceitos(conceitos),
        "operacoes_resumo": resumir_operacoes(operacoes),
        "mapa_dedutivo_resumo": resumir_mapa_dedutivo(mapa_dedutivo),
    }


# ============================================================
# PREPARAÇÃO DO PAYLOAD
# ============================================================

def preparar_payload_fragmento(
    fragmento: Dict[str, Any],
    cadencia_item: Optional[Dict[str, Any]],
    tratamento_item: Optional[Dict[str, Any]],
    ordem_loop: int,
) -> Dict[str, Any]:
    relacoes = normalizar_dict(fragmento.get("relacoes_locais"))
    texto = (fragmento.get("texto_fragmento") or "").strip()
    n_chars = int(fragmento.get("n_chars_fragmento") or len(texto))
    segmentacao = normalizar_dict(fragmento.get("segmentacao"))
    origem = normalizar_dict(fragmento.get("origem"))
    cad = normalizar_dict((cadencia_item or {}).get("cadencia"))

    return {
        "fragment_id": (
            fragmento.get("fragment_id")
            or fragmento.get("fragmento_id")
            or fragmento.get("id_fragmento")
            or fragmento.get("id")
        ),
        "origem_id": inferir_origem_id(fragmento),
        "ordem_no_ficheiro": extrair_ordem_no_ficheiro(fragmento, ordem_loop),
        "ordem_no_container": fragmento.get("ordem_no_container"),
        "origem": {
            "ficheiro": origem.get("ficheiro"),
            "data": origem.get("data"),
            "titulo_container": origem.get("titulo_container"),
            "tem_header_formal": origem.get("tem_header_formal"),
            "header_original": origem.get("header_original"),
            "blocos_fonte": origem.get("blocos_fonte"),
        },
        "tipo_material_fonte": fragmento.get("tipo_material_fonte"),
        "texto_fragmento": limitar_texto(texto),
        "texto_normalizado": limitar_texto(fragmento.get("texto_normalizado") or texto),
        "texto_fonte_reconstituido": limitar_texto(fragmento.get("texto_fonte_reconstituido") or texto),
        "paragrafos_agregados": fragmento.get("paragrafos_agregados"),
        "frases_aproximadas": fragmento.get("frases_aproximadas"),
        "n_chars_fragmento": n_chars,
        "densidade_aprox": fragmento.get("densidade_aprox"),
        "comprimento_bucket": bucket_comprimento(n_chars),
        "funcao_textual_dominante": fragmento.get("funcao_textual_dominante"),
        "segmentacao": {
            "tipo_unidade": segmentacao.get("tipo_unidade"),
            "criterio_de_unidade": segmentacao.get("criterio_de_unidade"),
            "houve_fusao_de_paragrafos": segmentacao.get("houve_fusao_de_paragrafos"),
            "houve_corte_interno": segmentacao.get("houve_corte_interno"),
            "container_tipo_segmentacao": segmentacao.get("container_tipo_segmentacao"),
        },
        "relacoes_locais": relacoes,
        "tema_dominante_provisorio": fragmento.get("tema_dominante_provisorio"),
        "conceitos_relevantes_provisorios": normalizar_lista(fragmento.get("conceitos_relevantes_provisorios")),
        "integridade_semantica": fragmento.get("integridade_semantica"),
        "confianca_segmentacao": fragmento.get("confianca_segmentacao"),
        "estado_revisao": fragmento.get("estado_revisao"),
        "sinalizador_para_cadencia": fragmento.get("sinalizador_para_cadencia"),
        "cadencia_preexistente": cad,
        "tratamento_filosofico_previo": resumir_tratamento_previo(tratamento_item or {}),
        "sinais_automaticos": {
            "continua_anterior": bool(relacoes.get("continua_anterior")),
            "prepara_seguinte": bool(relacoes.get("prepara_seguinte")),
            "tem_fragmento_anterior": relacoes.get("fragmento_anterior") is not None,
            "tem_fragmento_seguinte": relacoes.get("fragmento_seguinte") is not None,
            "texto_muito_curto": n_chars < 120,
            "texto_muito_longo": n_chars > 900,
        },
    }


# ============================================================
# PROMPTS
# ============================================================

def construir_prompt_extracao(
    schema_json: Dict[str, Any],
    contexto_macro_minimo: Dict[str, Any],
    fragmento_payload: Dict[str, Any],
) -> str:
    return f"""
És um extrator de impacto de fragmentos no mapa dedutivo.

Objetivo:
avaliar rigorosamente como um fragmento mexe — ou não mexe — no mapa dedutivo já construído.

Tarefa:
preencher estritamente um objeto JSON conforme ao schema fornecido, identificando:
- a tese principal relevante do fragmento para o mapa;
- o tipo de utilidade principal do fragmento;
- as proposições do mapa tocadas, se tocar alguma;
- o efeito principal do fragmento sobre o mapa;
- o que o fragmento acrescenta em termos de justificação, mediação, objeções bloqueadas ou distinções novas;
- e a decisão editorial final sobre o mapa.

Regra central:
o texto_fragmento manda.
Os metadados e o tratamento filosófico prévio ajudam, mas não substituem a leitura do fragmento.

Não deves:
- confundir tema semelhante com impacto estrutural real no mapa;
- associar uma proposição só porque o fragmento fala vagamente do mesmo tema;
- dizer que o fragmento corrige quando ele apenas densifica ou explicita;
- dizer que cria passo novo sem necessidade dedutiva clara;
- associar o fragmento a demasiadas proposições do mapa;
- exagerar o impacto apenas porque o fragmento é interessante;
- produzir prosa interpretativa longa.

Usa por esta ordem:
1. texto_fragmento
2. texto_normalizado e texto_fonte_reconstituido
3. tratamento_filosofico_previo
4. relacoes_locais e cadencia_preexistente
5. contexto macro reduzido e resumo do mapa

Regras adicionais:
- usa exatamente os enums do schema;
- escreve de forma curta, seca e operacional;
- se houver dúvida entre "corrige" e "explicita", prefere "explicita";
- se houver dúvida entre "medeia" e "cria_passo_novo", prefere "medeia";
- "proposicoes_do_mapa_tocadas" deve ser curta e criteriosa; muitas vezes pode estar vazia;
- se o fragmento tocar apenas vagamente o mapa, usa "sem_impacto_relevante";
- se "efeito_principal_no_mapa" for "sem_impacto_relevante", então por defeito:
  - "proposicoes_do_mapa_tocadas" deve estar vazia ou quase vazia;
  - "efeitos_secundarios" deve vir vazio;
  - "objecoes_que_ajuda_a_bloquear" deve vir vazio salvo caso muito claro;
  - "conceitos_ou_distincoes_novas" deve vir vazio salvo caso muito claro;
  - "mediacao_que_fornece" deve dizer que nao fornece mediacao estrutural;
  - "acao_recomendada_sobre_o_mapa" deve ser "sem_acao" ou "manter";
- "tipo_de_utilidade_principal" deve distinguir:
  - "estrutural" quando mexe realmente na arquitetura;
  - "justificativa" quando reforça justificação de um passo;
  - "mediacional" quando liga passos;
  - "redacional" quando serve mais para exposição do que para a estrutura;
  - "tematica" quando só tem afinidade de tema;
  - "nenhuma" quando nem isso vale significativamente;
- "tipo_de_densificacao":
  - "do_passo" quando melhora a formulação do próprio passo;
  - "da_justificacao_do_passo" quando melhora a justificação;
  - "da_exposicao" quando ajuda mais a escrever o capítulo;
  - "nao_se_aplica" quando não há densificação relevante;
- "justificacao_da_associacao" deve dizer por que o fragmento toca esse passo;
- "justificacao_nova_que_fornece" deve focar a contribuição real;
- "mediacao_que_fornece" só quando o fragmento ajuda a ligar passos;
- "proposta_de_novo_passo" só se for realmente indispensável;
- se não houver nova formulação ou novo passo, usa null;
- "entre_que_passos_deveria_entrar" deve vir vazio quando não se aplica;
- se o fragmento for instável, sê prudente.

Critérios decisivos:
- "repete" = diz substancialmente o que o passo já dizia;
- "explicita" = melhora formulação, justificação ou distinção, sem alterar a arquitetura;
- "corrige" = mostra que a formulação atual de um passo está errada ou insuficiente;
- "medeia" = fornece a passagem entre dois passos existentes;
- "cria_passo_novo" = introduz distinção ou elo indispensável em falta;
- "sem_impacto_relevante" = não mexe realmente na arquitetura do mapa.

CONTEXTO_MACRO_MINIMO:
{json.dumps(contexto_macro_minimo, ensure_ascii=False)}

SCHEMA:
{json.dumps(schema_json, ensure_ascii=False)}

FRAGMENTO:
{json.dumps(fragmento_payload, ensure_ascii=False)}

DEVOLVE APENAS UM OBJETO JSON VÁLIDO.
""".strip()


def construir_prompt_correcao_schema(
    schema_json: Dict[str, Any],
    fragmento_payload: Dict[str, Any],
    resposta_anterior: Dict[str, Any],
    erros_validacao: List[str],
) -> str:
    return f"""
A resposta anterior falhou na validação do schema.

Tarefa:
corrigir a resposta anterior para que fique estritamente conforme ao schema fornecido.

Regras:
- não acrescentes comentários;
- não expliques o que fizeste;
- não mudes o conteúdo mais do que o necessário para cumprir o schema e manter prudência interpretativa;
- a resposta final deve ser apenas JSON válido;
- se um campo não puder ser sustentado, enfraquece-o em vez de forçar precisão;
- se o efeito principal for "sem_impacto_relevante", simplifica a resposta em vez de a embelezar.

SCHEMA:
{json.dumps(schema_json, ensure_ascii=False)}

FRAGMENTO:
{json.dumps(fragmento_payload, ensure_ascii=False)}

ERROS_DE_VALIDACAO:
{json.dumps(erros_validacao, ensure_ascii=False)}

RESPOSTA_ANTERIOR:
{json.dumps(resposta_anterior, ensure_ascii=False)}

DEVOLVE APENAS UM OBJETO JSON VÁLIDO.
""".strip()


def construir_prompt_arbitragem(
    schema_json: Dict[str, Any],
    fragmento_payload: Dict[str, Any],
    resposta_anterior: Dict[str, Any],
    motivos_reprompt: List[str],
) -> str:
    return f"""
A resposta anterior é estruturalmente frágil ou excessivamente forte.

Tarefa:
rever criticamente a resposta anterior e devolver uma versão mais prudente, mais coerente e menos especulativa.

Modo de trabalho obrigatório:
- não inferir mais do que o fragmento permite;
- não transformar afinidade temática em impacto estrutural;
- não classificar como cria_passo_novo sem lacuna dedutiva clara;
- não classificar como corrige se o fragmento apenas melhora formulação ou justificação;
- se o fragmento tocar a passagem entre dois passos, considerar medeia;
- se o fragmento não mexer realmente na arquitetura, preferir sem_impacto_relevante;
- se houver dúvida entre manter um valor forte e enfraquecê-lo, enfraquece-o;
- reduz a verbosidade;
- mantém-te estritamente conforme ao schema;
- a resposta final deve ser apenas JSON válido.

SCHEMA:
{json.dumps(schema_json, ensure_ascii=False)}

FRAGMENTO:
{json.dumps(fragmento_payload, ensure_ascii=False)}

RESPOSTA_ANTERIOR:
{json.dumps(resposta_anterior, ensure_ascii=False)}

MOTIVOS_DE_REAVALIACAO:
{json.dumps(motivos_reprompt, ensure_ascii=False)}

DEVOLVE APENAS UM OBJETO JSON VÁLIDO.
""".strip()


def construir_prompt_fallback_minimo(
    schema_json: Dict[str, Any],
    contexto_macro_minimo: Dict[str, Any],
    fragmento_payload: Dict[str, Any],
) -> str:
    return f"""
Receberás um fragmento difícil, oralizado, instável ou incompleto.

Objetivo:
preencher apenas o núcleo mínimo fiável do objeto conforme ao schema, deixando o resto em forma prudente e fraca.

Prioridades:
1. resumir a tese relevante para o mapa;
2. identificar se toca alguma proposição do mapa;
3. decidir o efeito principal provável no mapa;
4. indicar a ação editorial mínima recomendada.

Estratégia:
- não forçar impacto forte;
- se houver apenas contacto temático vago, usar "sem_impacto_relevante";
- se o valor for só de tema ou de escrita, usar "tematica" ou "redacional" em "tipo_de_utilidade_principal";
- se não houver base para nova formulação ou novo passo, usar null e listas vazias;
- preferir baixa confiança a falsa precisão.

CONTEXTO_MACRO_MINIMO:
{json.dumps(contexto_macro_minimo, ensure_ascii=False)}

SCHEMA:
{json.dumps(schema_json, ensure_ascii=False)}

FRAGMENTO:
{json.dumps(fragmento_payload, ensure_ascii=False)}

DEVOLVE APENAS UM OBJETO JSON VÁLIDO.
""".strip()


# ============================================================
# CHAMADA AO MODELO
# ============================================================

def _normalizar_schema_para_strict(schema: Any) -> Any:
    if isinstance(schema, list):
        return [_normalizar_schema_para_strict(x) for x in schema]

    if not isinstance(schema, dict):
        return schema

    schema = copy.deepcopy(schema)

    for k in [
        "$schema",
        "$id",
        "title",
        "description",
        "default",
        "examples",
        "uniqueItems",
        "minItems",
        "maxItems",
        "minLength",
        "maxLength",
        "pattern",
        "format",
    ]:
        schema.pop(k, None)

    if schema.get("type") == "object":
        schema.setdefault("additionalProperties", False)

    if "properties" in schema and isinstance(schema["properties"], dict):
        schema["properties"] = {
            k: _normalizar_schema_para_strict(v)
            for k, v in schema["properties"].items()
        }

    if "items" in schema:
        schema["items"] = _normalizar_schema_para_strict(schema["items"])

    if "anyOf" in schema and isinstance(schema["anyOf"], list):
        schema["anyOf"] = [_normalizar_schema_para_strict(x) for x in schema["anyOf"]]

    if "oneOf" in schema and isinstance(schema["oneOf"], list):
        schema["oneOf"] = [_normalizar_schema_para_strict(x) for x in schema["oneOf"]]

    if "allOf" in schema and isinstance(schema["allOf"], list):
        schema["allOf"] = [_normalizar_schema_para_strict(x) for x in schema["allOf"]]

    return schema


def _extrair_texto_output(response: Any) -> str:
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text

    partes: List[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text_value = getattr(content, "text", None)
            if text_value:
                partes.append(text_value)
    return "\n".join(partes).strip()


def chamar_modelo_json_schema(prompt: str, schema_obj: Dict[str, Any], model: str) -> Dict[str, Any]:
    schema_strict = _normalizar_schema_para_strict(copy.deepcopy(schema_obj))

    response = CLIENT.responses.create(
        model=model,
        input=prompt,
        store=False,
        text={
            "format": {
                "type": "json_schema",
                "name": "impacto_fragmento_no_mapa",
                "schema": schema_strict,
                "strict": True,
            }
        },
    )

    texto = _extrair_texto_output(response)
    if not texto:
        raise ValueError("resposta_vazia_do_modelo")

    try:
        return json.loads(texto)
    except json.JSONDecodeError as e:
        raise ValueError(f"json_invalido:{e}") from e


# ============================================================
# PÓS-PROCESSAMENTO LEVE
# ============================================================

def _dedupe_strings(itens: List[Any]) -> List[str]:
    vistos = set()
    out: List[str] = []
    for item in itens:
        if not isinstance(item, str):
            continue
        chave = item.strip()
        if not chave:
            continue
        if chave not in vistos:
            vistos.add(chave)
            out.append(chave)
    return out


def normalizar_resultado_impacto(resultado: Dict[str, Any]) -> Dict[str, Any]:
    raiz = normalizar_dict(resultado.get("impacto_no_mapa_fragmento"))
    imp = normalizar_dict(raiz.get("impacto_editorial_e_dedutivo"))
    dec = normalizar_dict(raiz.get("decisao_final"))

    props = []
    for prop in normalizar_lista(raiz.get("proposicoes_do_mapa_tocadas")):
        if not isinstance(prop, dict):
            continue
        props.append(
            {
                "proposicao_id": prop.get("proposicao_id"),
                "numero": prop.get("numero"),
                "proposicao_resumida": prop.get("proposicao_resumida"),
                "grau_de_relevancia": prop.get("grau_de_relevancia"),
                "tipo_de_relacao": prop.get("tipo_de_relacao"),
                "justificacao_da_associacao": (prop.get("justificacao_da_associacao") or "").strip(),
            }
        )
    raiz["proposicoes_do_mapa_tocadas"] = props[:MAX_PROPOSICOES_TOCADAS]

    raiz["efeitos_secundarios"] = _dedupe_strings(normalizar_lista(raiz.get("efeitos_secundarios")))
    imp["objecoes_que_ajuda_a_bloquear"] = _dedupe_strings(
        normalizar_lista(imp.get("objecoes_que_ajuda_a_bloquear"))
    )[:MAX_OBJECOES]
    imp["conceitos_ou_distincoes_novas"] = _dedupe_strings(
        normalizar_lista(imp.get("conceitos_ou_distincoes_novas"))
    )[:MAX_CONCEITOS_NOVOS]
    imp["entre_que_passos_deveria_entrar"] = _dedupe_strings(
        normalizar_lista(imp.get("entre_que_passos_deveria_entrar"))
    )

    efeito = raiz.get("efeito_principal_no_mapa")
    utilidade = raiz.get("tipo_de_utilidade_principal")

    if efeito == "sem_impacto_relevante":
        if len(raiz["proposicoes_do_mapa_tocadas"]) > 1:
            raiz["proposicoes_do_mapa_tocadas"] = raiz["proposicoes_do_mapa_tocadas"][:1]
        raiz["efeitos_secundarios"] = []
        if utilidade not in ("tematica", "redacional", "nenhuma"):
            raiz["tipo_de_utilidade_principal"] = "tematica"
        imp["tipo_de_densificacao"] = "nao_se_aplica"
        if not imp.get("mediacao_que_fornece"):
            imp["mediacao_que_fornece"] = "Nao fornece mediacao estrutural."
        imp["objecoes_que_ajuda_a_bloquear"] = imp["objecoes_que_ajuda_a_bloquear"][:1]
        imp["conceitos_ou_distincoes_novas"] = imp["conceitos_ou_distincoes_novas"][:1]
        imp["obriga_a_reescrever_o_passo"] = False
        imp["obriga_a_dividir_o_passo"] = False
        imp["obriga_a_criar_passo_intermedio"] = False
        imp["proposta_de_nova_formulacao"] = None
        imp["proposta_de_novo_passo"] = None
        imp["entre_que_passos_deveria_entrar"] = []
        if dec.get("acao_recomendada_sobre_o_mapa") not in ("sem_acao", "manter"):
            dec["acao_recomendada_sobre_o_mapa"] = "sem_acao"
        if dec.get("prioridade_editorial") in ("imediata", "alta"):
            dec["prioridade_editorial"] = "baixa"

    resultado["impacto_no_mapa_fragmento"] = raiz
    raiz["impacto_editorial_e_dedutivo"] = imp
    raiz["decisao_final"] = dec
    return resultado


# ============================================================
# VALIDAÇÃO
# ============================================================

def validar_resultado_schema(resultado: Dict[str, Any], schema_obj: Dict[str, Any]) -> ResultadoValidacao:
    erros: List[str] = []
    avisos: List[str] = []

    if not isinstance(resultado, dict):
        erros.append("resultado_nao_e_objeto")
        return ResultadoValidacao(False, erros, avisos)

    try:
        jsonschema.validate(instance=resultado, schema=schema_obj)
    except jsonschema.ValidationError as e:
        caminho = "/".join(str(x) for x in e.absolute_path)
        if caminho:
            erros.append(f"schema:{caminho}:{e.message}")
        else:
            erros.append(f"schema:{e.message}")
    except jsonschema.SchemaError as e:
        erros.append(f"schema_interno_invalido:{e}")

    return ResultadoValidacao(len(erros) == 0, erros, avisos)


def validar_coerencia_impacto_no_mapa(resultado: Dict[str, Any]) -> ResultadoCoerencia:
    avisos: List[str] = []
    motivos: List[str] = []
    score = 0

    raiz = normalizar_dict(resultado.get("impacto_no_mapa_fragmento"))
    props = normalizar_lista(raiz.get("proposicoes_do_mapa_tocadas"))
    efeito = raiz.get("efeito_principal_no_mapa")
    secundarios = normalizar_lista(raiz.get("efeitos_secundarios"))
    utilidade = raiz.get("tipo_de_utilidade_principal")
    imp = normalizar_dict(raiz.get("impacto_editorial_e_dedutivo"))
    dec = normalizar_dict(raiz.get("decisao_final"))

    if len(props) > MAX_PROPOSICOES_TOCADAS:
        motivos.append("demasiadas_proposicoes_tocadas")
        score += 2

    if len(normalizar_lista(imp.get("objecoes_que_ajuda_a_bloquear"))) > MAX_OBJECOES:
        avisos.append("muitas_objecoes_bloqueadas")
        score += 1

    if len(normalizar_lista(imp.get("conceitos_ou_distincoes_novas"))) > MAX_CONCEITOS_NOVOS:
        avisos.append("muitos_conceitos_novos")
        score += 1

    if efeito == "sem_impacto_relevante":
        if len(props) > 1:
            motivos.append("sem_impacto_com_demasiadas_proposicoes_associadas")
            score += 2
        elif len(props) == 1:
            avisos.append("sem_impacto_com_uma_proposicao_associada")
            score += 1
        if secundarios:
            avisos.append("sem_impacto_com_efeitos_secundarios")
            score += 1
        if dec.get("acao_recomendada_sobre_o_mapa") not in ("sem_acao", "manter"):
            motivos.append("sem_impacto_com_acao_forte")
            score += 2
        if dec.get("prioridade_editorial") in ("imediata", "alta"):
            avisos.append("sem_impacto_com_prioridade_alta")
            score += 1
        if utilidade not in ("tematica", "redacional", "nenhuma"):
            avisos.append("sem_impacto_com_utilidade_forte")
            score += 1
        if imp.get("obriga_a_reescrever_o_passo") is True:
            motivos.append("sem_impacto_com_reescrita")
            score += 2
        if imp.get("obriga_a_dividir_o_passo") is True:
            motivos.append("sem_impacto_com_divisao")
            score += 2
        if imp.get("obriga_a_criar_passo_intermedio") is True:
            motivos.append("sem_impacto_com_criacao_intermedio")
            score += 2

    if efeito == "repete":
        if dec.get("acao_recomendada_sobre_o_mapa") in ("reformular", "dividir", "criar_intermedio", "deslocar"):
            motivos.append("repete_com_acao_estrutural_forte")
            score += 2

    if efeito == "explicita":
        if dec.get("acao_recomendada_sobre_o_mapa") in ("dividir", "deslocar"):
            avisos.append("explicita_com_acao_potencialmente_forte_demais")
            score += 1

    if efeito == "corrige":
        if not imp.get("proposta_de_nova_formulacao"):
            motivos.append("corrige_sem_nova_formulacao")
            score += 2
        if dec.get("acao_recomendada_sobre_o_mapa") not in ("reformular", "densificar"):
            avisos.append("corrige_sem_acao_compativel")
            score += 1

    if efeito == "medeia":
        if len(props) < 2:
            motivos.append("medeia_com_menos_de_duas_proposicoes")
            score += 2
        if not (imp.get("mediacao_que_fornece") or "").strip():
            motivos.append("medeia_sem_descrever_mediacao")
            score += 2
        if utilidade != "mediacional":
            avisos.append("medeia_sem_utilidade_mediacional")
            score += 1
        if dec.get("acao_recomendada_sobre_o_mapa") not in ("densificar", "criar_intermedio", "dividir"):
            avisos.append("medeia_sem_acao_compativel")
            score += 1

    if efeito == "cria_passo_novo":
        if not imp.get("proposta_de_novo_passo"):
            motivos.append("cria_passo_novo_sem_proposta")
            score += 2
        if len(normalizar_lista(imp.get("entre_que_passos_deveria_entrar"))) < 2:
            motivos.append("cria_passo_novo_sem_localizacao")
            score += 2
        if imp.get("obriga_a_criar_passo_intermedio") is not True:
            avisos.append("cria_passo_novo_sem_flag_correspondente")
            score += 1
        if dec.get("acao_recomendada_sobre_o_mapa") not in ("criar_intermedio", "dividir", "reformular"):
            motivos.append("cria_passo_novo_sem_acao_compativel")
            score += 2

    if imp.get("obriga_a_dividir_o_passo") is True and dec.get("acao_recomendada_sobre_o_mapa") != "dividir":
        avisos.append("dividir_flag_sem_acao_dividir")
        score += 1

    if imp.get("obriga_a_reescrever_o_passo") is True and not imp.get("proposta_de_nova_formulacao"):
        avisos.append("reescrita_sem_nova_formulacao")
        score += 1

    if secundarios and efeito in secundarios:
        avisos.append("efeito_principal_repetido_nos_secundarios")
        score += 1

    if dec.get("confianca_da_analise") == "baixa" and dec.get("necessita_revisao_humana") is False:
        avisos.append("confianca_baixa_sem_revisao_humana")
        score += 1

    tipo_densificacao = imp.get("tipo_de_densificacao")
    if dec.get("acao_recomendada_sobre_o_mapa") == "densificar" and tipo_densificacao == "nao_se_aplica":
        avisos.append("acao_densificar_sem_tipo_de_densificacao")
        score += 1

    if utilidade == "nenhuma" and efeito != "sem_impacto_relevante":
        avisos.append("utilidade_nenhuma_com_efeito_mais_forte")
        score += 1

    ok = score < 2
    return ResultadoCoerencia(
        ok=ok,
        score_fragilidade=score,
        motivos_reprompt=motivos,
        avisos=avisos,
    )


def precisa_reprompt(valid_schema: ResultadoValidacao, valid_coerencia: ResultadoCoerencia) -> Tuple[bool, str]:
    if not valid_schema.ok:
        return True, "schema"
    if valid_coerencia.score_fragilidade >= 2:
        return True, "interpretacao"
    return False, ""


# ============================================================
# AUXILIARES DE LOG / FALHAS / ESTADO
# ============================================================

def carregar_estado() -> Dict[str, Any]:
    return carregar_json_opcional(FICHEIRO_ESTADO, {"fragmentos": {}})


def registar_falha(fragment_id: str, etapa: str, detalhe: Any) -> None:
    falhas = carregar_json_opcional(FICHEIRO_FALHAS, [])
    falhas.append(
        {
            "timestamp": timestamp_utc(),
            "fragment_id": fragment_id,
            "etapa": etapa,
            "detalhe": detalhe,
        }
    )
    gravar_json(FICHEIRO_FALHAS, falhas)


def anexar_log_execucao(log_entry: Dict[str, Any]) -> None:
    logs = carregar_json_opcional(FICHEIRO_LOGS, [])
    logs.append(log_entry)
    gravar_json(FICHEIRO_LOGS, logs)


# ============================================================
# PIPELINE POR FRAGMENTO
# ============================================================

def extrair_impacto_fragmento_no_mapa(
    fragmento_payload: Dict[str, Any],
    schema_obj: Dict[str, Any],
    contexto_macro_minimo: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    logs: Dict[str, Any] = {
        "fragment_id": fragmento_payload.get("fragment_id"),
        "etapas": [],
    }

    print("   🤖 Extração principal...", flush=True)

    prompt = construir_prompt_extracao(
        schema_json=schema_obj,
        contexto_macro_minimo=contexto_macro_minimo,
        fragmento_payload=fragmento_payload,
    )
    logs["etapas"].append({"tipo": "extracao_principal"})
    if GUARDAR_PROMPTS:
        logs["prompt_extracao"] = prompt

    resposta = chamar_modelo_json_schema(prompt, schema_obj, MODELO_PRINCIPAL)
    resposta = normalizar_resultado_impacto(resposta)
    valid_schema = validar_resultado_schema(resposta, schema_obj)

    if valid_schema.ok:
        valid_coerencia = validar_coerencia_impacto_no_mapa(resposta)
        logs["etapas"].append(
            {
                "tipo": "validacao_inicial",
                "score_fragilidade": valid_coerencia.score_fragilidade,
                "avisos": valid_coerencia.avisos,
            }
        )
    else:
        valid_coerencia = ResultadoCoerencia(False, 99, ["schema_invalido"], [])

    precisa, tipo = precisa_reprompt(valid_schema, valid_coerencia)
    if not precisa:
        return resposta, logs

    if tipo == "schema":
        print("   ⚠️ Schema inválido, a tentar correção...", flush=True)

        tentativa = 0
        resposta_corrente = resposta
        valid_corrente = valid_schema

        while tentativa < MAX_RETRIES_SCHEMA:
            tentativa += 1
            print(f"   🔧 Correção de schema tentativa {tentativa}/{MAX_RETRIES_SCHEMA}...", flush=True)

            prompt2 = construir_prompt_correcao_schema(
                schema_json=schema_obj,
                fragmento_payload=fragmento_payload,
                resposta_anterior=resposta_corrente,
                erros_validacao=valid_corrente.erros,
            )
            logs["etapas"].append(
                {
                    "tipo": "correcao_schema",
                    "tentativa": tentativa,
                    "erros": valid_corrente.erros,
                }
            )
            if GUARDAR_PROMPTS:
                logs[f"prompt_correcao_schema_{tentativa}"] = prompt2

            resposta2 = chamar_modelo_json_schema(prompt2, schema_obj, MODELO_PRINCIPAL)
            resposta2 = normalizar_resultado_impacto(resposta2)
            valid_schema2 = validar_resultado_schema(resposta2, schema_obj)

            if valid_schema2.ok:
                valid_coerencia2 = validar_coerencia_impacto_no_mapa(resposta2)
                logs["etapas"].append(
                    {
                        "tipo": "validacao_pos_correcao_schema",
                        "tentativa": tentativa,
                        "score_fragilidade": valid_coerencia2.score_fragilidade,
                        "avisos": valid_coerencia2.avisos,
                    }
                )

                precisa2, tipo2 = precisa_reprompt(valid_schema2, valid_coerencia2)
                if not precisa2:
                    return resposta2, logs

                resposta = resposta2
                valid_coerencia = valid_coerencia2
                tipo = tipo2
                break

            resposta_corrente = resposta2
            valid_corrente = valid_schema2
        else:
            return None, logs

    if tipo == "interpretacao":
        print("   ⚖️ A tentar arbitragem interpretativa...", flush=True)

        tentativa = 0
        resposta_corrente = resposta
        resposta_final = None

        while tentativa < MAX_RETRIES_INTERPRETACAO:
            tentativa += 1
            print(f"   🔁 Arbitragem tentativa {tentativa}/{MAX_RETRIES_INTERPRETACAO}...", flush=True)

            prompt3 = construir_prompt_arbitragem(
                schema_json=schema_obj,
                fragmento_payload=fragmento_payload,
                resposta_anterior=resposta_corrente,
                motivos_reprompt=valid_coerencia.motivos_reprompt,
            )
            logs["etapas"].append(
                {
                    "tipo": "arbitragem",
                    "tentativa": tentativa,
                    "motivos": valid_coerencia.motivos_reprompt,
                }
            )
            if GUARDAR_PROMPTS:
                logs[f"prompt_arbitragem_{tentativa}"] = prompt3

            resposta3 = chamar_modelo_json_schema(prompt3, schema_obj, MODELO_ARBITRAGEM)
            resposta3 = normalizar_resultado_impacto(resposta3)
            valid_schema3 = validar_resultado_schema(resposta3, schema_obj)

            if valid_schema3.ok:
                valid_coerencia3 = validar_coerencia_impacto_no_mapa(resposta3)
                logs["etapas"].append(
                    {
                        "tipo": "validacao_pos_arbitragem",
                        "tentativa": tentativa,
                        "score_fragilidade": valid_coerencia3.score_fragilidade,
                        "avisos": valid_coerencia3.avisos,
                    }
                )

                precisa3, _ = precisa_reprompt(valid_schema3, valid_coerencia3)
                if not precisa3:
                    resposta_final = resposta3
                    break

            resposta_corrente = resposta3

        if resposta_final is not None:
            return resposta_final, logs

    print("   🪂 A tentar fallback mínimo...", flush=True)

    tentativa = 0
    while tentativa < MAX_RETRIES_FALLBACK:
        tentativa += 1
        prompt4 = construir_prompt_fallback_minimo(
            schema_json=schema_obj,
            contexto_macro_minimo=contexto_macro_minimo,
            fragmento_payload=fragmento_payload,
        )
        logs["etapas"].append({"tipo": "fallback_minimo", "tentativa": tentativa})
        if GUARDAR_PROMPTS:
            logs[f"prompt_fallback_{tentativa}"] = prompt4

        try:
            resposta4 = chamar_modelo_json_schema(prompt4, schema_obj, MODELO_PRINCIPAL)
            resposta4 = normalizar_resultado_impacto(resposta4)
        except Exception as e:
            logs["etapas"].append({"tipo": "erro_fallback", "tentativa": tentativa, "erro": str(e)})
            continue

        valid_schema4 = validar_resultado_schema(resposta4, schema_obj)
        if valid_schema4.ok:
            valid_coerencia4 = validar_coerencia_impacto_no_mapa(resposta4)
            logs["etapas"].append(
                {
                    "tipo": "validacao_fallback",
                    "tentativa": tentativa,
                    "score_fragilidade": valid_coerencia4.score_fragilidade,
                    "avisos": valid_coerencia4.avisos,
                }
            )
            return resposta4, logs

    return None, logs


# ============================================================
# AGREGAÇÃO POR PROPOSIÇÃO
# ============================================================

def construir_agregado_por_proposicao(
    resultados: List[Dict[str, Any]],
    mapa_dedutivo: Dict[str, Any],
) -> Dict[str, Any]:
    props_mapa = {}
    for bloco in normalizar_lista(mapa_dedutivo.get("blocos")):
        if not isinstance(bloco, dict):
            continue
        for prop in normalizar_lista(bloco.get("proposicoes")):
            if not isinstance(prop, dict):
                continue
            pid = prop.get("id")
            if not isinstance(pid, str):
                continue
            props_mapa[pid] = {
                "proposicao_id": pid,
                "numero": prop.get("numero"),
                "proposicao": prop.get("proposicao"),
                "bloco_id": bloco.get("id"),
                "bloco_titulo": bloco.get("titulo"),
                "fragmentos_relacionados": [],
                "contagens": {
                    "total": 0,
                    "repete": 0,
                    "explicita": 0,
                    "corrige": 0,
                    "medeia": 0,
                    "cria_passo_novo": 0,
                    "sem_impacto_relevante": 0,
                    "manter": 0,
                    "densificar": 0,
                    "reformular": 0,
                    "dividir": 0,
                    "criar_intermedio": 0,
                    "deslocar": 0,
                    "sem_acao": 0,
                },
                "tipos_de_utilidade": {
                    "estrutural": 0,
                    "justificativa": 0,
                    "mediacional": 0,
                    "redacional": 0,
                    "tematica": 0,
                    "nenhuma": 0,
                },
            }

    for item in resultados:
        raiz = normalizar_dict(item.get("impacto_no_mapa_fragmento"))
        props = normalizar_lista(raiz.get("proposicoes_do_mapa_tocadas"))
        efeito = raiz.get("efeito_principal_no_mapa")
        utilidade = raiz.get("tipo_de_utilidade_principal")
        dec = normalizar_dict(raiz.get("decisao_final"))
        acao = dec.get("acao_recomendada_sobre_o_mapa")
        frag_id = item.get("fragment_id")

        for prop in props:
            if not isinstance(prop, dict):
                continue
            pid = prop.get("proposicao_id")
            if pid not in props_mapa:
                continue

            reg = props_mapa[pid]
            reg["contagens"]["total"] += 1
            if isinstance(efeito, str) and efeito in reg["contagens"]:
                reg["contagens"][efeito] += 1
            if isinstance(acao, str) and acao in reg["contagens"]:
                reg["contagens"][acao] += 1
            if isinstance(utilidade, str) and utilidade in reg["tipos_de_utilidade"]:
                reg["tipos_de_utilidade"][utilidade] += 1

            reg["fragmentos_relacionados"].append(
                {
                    "fragment_id": frag_id,
                    "grau_de_relevancia": prop.get("grau_de_relevancia"),
                    "tipo_de_relacao": prop.get("tipo_de_relacao"),
                    "efeito_principal_no_mapa": efeito,
                    "tipo_de_utilidade_principal": utilidade,
                    "acao_recomendada_sobre_o_mapa": acao,
                    "confianca_da_analise": dec.get("confianca_da_analise"),
                }
            )

    return {
        "timestamp": timestamp_utc(),
        "versao_extrator": VERSAO_EXTRATOR,
        "proposicoes": list(props_mapa.values()),
    }


# ============================================================
# RELATÓRIO FINAL
# ============================================================

def construir_relatorio_validacao(saida: List[Dict[str, Any]], estado: Dict[str, Any]) -> Dict[str, Any]:
    total = len(saida)
    por_efeito: Dict[str, int] = {}
    por_acao: Dict[str, int] = {}
    por_zona: Dict[str, int] = {}
    por_utilidade: Dict[str, int] = {}

    contagem_passos_tocados: Dict[str, int] = {}

    for item in saida:
        raiz = normalizar_dict(item.get("impacto_no_mapa_fragmento"))
        efeito = raiz.get("efeito_principal_no_mapa")
        zona = raiz.get("zona_filosofica_dominante")
        utilidade = raiz.get("tipo_de_utilidade_principal")
        dec = normalizar_dict(raiz.get("decisao_final"))
        acao = dec.get("acao_recomendada_sobre_o_mapa")

        if isinstance(efeito, str):
            por_efeito[efeito] = por_efeito.get(efeito, 0) + 1
        if isinstance(acao, str):
            por_acao[acao] = por_acao.get(acao, 0) + 1
        if isinstance(zona, str):
            por_zona[zona] = por_zona.get(zona, 0) + 1
        if isinstance(utilidade, str):
            por_utilidade[utilidade] = por_utilidade.get(utilidade, 0) + 1

        for prop in normalizar_lista(raiz.get("proposicoes_do_mapa_tocadas")):
            if not isinstance(prop, dict):
                continue
            pid = prop.get("proposicao_id")
            if isinstance(pid, str):
                contagem_passos_tocados[pid] = contagem_passos_tocados.get(pid, 0) + 1

    estado_fragmentos = normalizar_dict(estado.get("fragmentos"))
    falhados = [fid for fid, meta in estado_fragmentos.items() if normalizar_dict(meta).get("status") == "falhou"]

    passos_mais_tocados = sorted(contagem_passos_tocados.items(), key=lambda x: (-x[1], x[0]))[:15]

    return {
        "timestamp": timestamp_utc(),
        "versao_extrator": VERSAO_EXTRATOR,
        "modelo_principal": MODELO_PRINCIPAL,
        "modelo_arbitragem": MODELO_ARBITRAGEM,
        "total_resultados": total,
        "falhados": falhados,
        "distribuicao_efeito_principal_no_mapa": dict(sorted(por_efeito.items(), key=lambda x: (-x[1], x[0]))),
        "distribuicao_acao_recomendada": dict(sorted(por_acao.items(), key=lambda x: (-x[1], x[0]))),
        "distribuicao_zona_filosofica_dominante": dict(sorted(por_zona.items(), key=lambda x: (-x[1], x[0]))),
        "distribuicao_tipo_de_utilidade_principal": dict(sorted(por_utilidade.items(), key=lambda x: (-x[1], x[0]))),
        "passos_mais_tocados": [{"proposicao_id": pid, "n": n} for pid, n in passos_mais_tocados],
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    schema_obj = construir_schema_impacto_no_mapa()

    print("📂 A carregar dados...", flush=True)

    fragmentos = garantir_lista_fragmentos(carregar_json(FICHEIRO_FRAGMENTOS))
    cadencia_lista = garantir_lista_cadencia(carregar_json(FICHEIRO_CADENCIA))
    meta_percurso = carregar_json(FICHEIRO_META_PERCURSO)
    meta_indice = carregar_json(FICHEIRO_META_INDICE)
    indice_sequencial = carregar_json(FICHEIRO_INDICE_SEQUENCIAL)
    indice_argumentos = carregar_json(FICHEIRO_INDICE_ARGUMENTOS)
    argumentos_unificados = carregar_json(FICHEIRO_ARGUMENTOS_UNIFICADOS)
    conceitos = carregar_json(FICHEIRO_CONCEITOS)
    operacoes = carregar_json(FICHEIRO_OPERACOES)
    tratamento_filosofico = garantir_lista_tratamento(carregar_json(FICHEIRO_TRATAMENTO_FILOSOFICO))
    mapa_dedutivo = carregar_json(FICHEIRO_MAPA_DEDUTIVO)

    print(f"   ✔ fragmentos: {FICHEIRO_FRAGMENTOS}", flush=True)
    print(f"   ✔ cadencia: {FICHEIRO_CADENCIA}", flush=True)
    print(f"   ✔ meta_percurso: {FICHEIRO_META_PERCURSO}", flush=True)
    print(f"   ✔ meta_indice: {FICHEIRO_META_INDICE}", flush=True)
    print(f"   ✔ indice_sequencial: {FICHEIRO_INDICE_SEQUENCIAL}", flush=True)
    print(f"   ✔ indice_argumentos: {FICHEIRO_INDICE_ARGUMENTOS}", flush=True)
    print(f"   ✔ argumentos_unificados: {FICHEIRO_ARGUMENTOS_UNIFICADOS}", flush=True)
    print(f"   ✔ conceitos: {FICHEIRO_CONCEITOS}", flush=True)
    print(f"   ✔ operacoes: {FICHEIRO_OPERACOES}", flush=True)
    print(f"   ✔ tratamento_filosofico: {FICHEIRO_TRATAMENTO_FILOSOFICO}", flush=True)
    print(f"   ✔ mapa_dedutivo: {FICHEIRO_MAPA_DEDUTIVO}", flush=True)

    cadencia_idx = indexar_por_fragment_id(cadencia_lista)
    tratamento_idx = indexar_por_fragment_id(tratamento_filosofico)

    contexto_macro_minimo = construir_contexto_macro_minimo(
        meta_percurso=meta_percurso,
        meta_indice=meta_indice,
        indice_sequencial=indice_sequencial,
        indice_argumentos=indice_argumentos,
        argumentos_unificados=argumentos_unificados,
        conceitos=conceitos,
        operacoes=operacoes,
        mapa_dedutivo=mapa_dedutivo,
    )

    estado = carregar_json_opcional(FICHEIRO_ESTADO, {"fragmentos": {}})
    if not isinstance(estado, dict):
        estado = {"fragmentos": {}}
    if "fragmentos" not in estado or not isinstance(estado["fragmentos"], dict):
        estado["fragmentos"] = {}

    saida_existente = carregar_json_opcional(FICHEIRO_SAIDA, [])
    if not isinstance(saida_existente, list):
        saida_existente = []

    saida_idx = indexar_por_fragment_id(saida_existente)
    resultados = list(saida_existente)

    processados = 0
    ignorados = 0
    falhados = 0

    fragmentos_iter = fragmentos[:LIMITE_FRAGMENTOS_TESTE] if LIMITE_FRAGMENTOS_TESTE else fragmentos

    for ordem_loop, fragmento in enumerate(fragmentos_iter, start=1):
        fragment_id = (
            fragmento.get("fragment_id")
            or fragmento.get("fragmento_id")
            or fragmento.get("id_fragmento")
            or fragmento.get("id")
        )

        if not isinstance(fragment_id, str):
            falhados += 1
            registar_falha("SEM_ID", "pre_validacao", "fragmento_sem_id")
            continue

        estado_ant = normalizar_dict(estado["fragmentos"].get(fragment_id, {}))
        ja_ok = estado_ant.get("status") == "ok"
        foi_falha = estado_ant.get("status") == "falhou"

        if not FORCAR_REPROCESSAMENTO and ja_ok:
            ignorados += 1
            continue

        if foi_falha and not REPROCESSAR_FALHAS and not FORCAR_REPROCESSAMENTO:
            ignorados += 1
            continue

        print(f"\n🔹 [{ordem_loop}/{len(fragmentos_iter)}] {fragment_id}", flush=True)

        cadencia_item = cadencia_idx.get(fragment_id)
        tratamento_item = tratamento_idx.get(fragment_id)

        fragmento_payload = preparar_payload_fragmento(
            fragmento=fragmento,
            cadencia_item=cadencia_item,
            tratamento_item=tratamento_item,
            ordem_loop=ordem_loop,
        )

        try:
            resposta, logs = extrair_impacto_fragmento_no_mapa(
                fragmento_payload=fragmento_payload,
                schema_obj=schema_obj,
                contexto_macro_minimo=contexto_macro_minimo,
            )
        except Exception as e:
            falhados += 1
            detalhe = f"excecao_na_extracao:{e}"
            registar_falha(fragment_id, "extracao", detalhe)
            estado["fragmentos"][fragment_id] = {
                "status": "falhou",
                "timestamp": timestamp_utc(),
                "erro": detalhe,
            }
            gravar_json(FICHEIRO_ESTADO, estado)
            anexar_log_execucao(
                {
                    "timestamp": timestamp_utc(),
                    "fragment_id": fragment_id,
                    "status": "falhou",
                    "erro": detalhe,
                }
            )
            print(f"   ❌ {detalhe}", flush=True)
            print_parcial(processados, ignorados, falhados)
            continue

        if resposta is None:
            falhados += 1
            registar_falha(fragment_id, "extracao", "resposta_none")
            estado["fragmentos"][fragment_id] = {
                "status": "falhou",
                "timestamp": timestamp_utc(),
                "erro": "resposta_none",
            }
            gravar_json(FICHEIRO_ESTADO, estado)
            anexar_log_execucao(
                {
                    "timestamp": timestamp_utc(),
                    "fragment_id": fragment_id,
                    "status": "falhou",
                    "logs_pipeline": logs,
                }
            )
            print("   ❌ resposta_none", flush=True)
            print_parcial(processados, ignorados, falhados)
            continue

        resposta = normalizar_resultado_impacto(resposta)
        valid_schema = validar_resultado_schema(resposta, schema_obj)
        valid_coerencia = validar_coerencia_impacto_no_mapa(resposta)

        if not valid_schema.ok:
            falhados += 1
            registar_falha(fragment_id, "validacao_final_schema", valid_schema.erros)
            estado["fragmentos"][fragment_id] = {
                "status": "falhou",
                "timestamp": timestamp_utc(),
                "erro": valid_schema.erros,
            }
            gravar_json(FICHEIRO_ESTADO, estado)
            anexar_log_execucao(
                {
                    "timestamp": timestamp_utc(),
                    "fragment_id": fragment_id,
                    "status": "falhou",
                    "erro": valid_schema.erros,
                    "logs_pipeline": logs,
                }
            )
            print(f"   ❌ schema_final: {valid_schema.erros}", flush=True)
            print_parcial(processados, ignorados, falhados)
            continue

        if fragment_id in saida_idx:
            resultados = [r for r in resultados if r.get("fragment_id") != fragment_id]

        resultados.append(resposta)
        gravar_json(FICHEIRO_SAIDA, resultados)

        estado["fragmentos"][fragment_id] = {
            "status": "ok",
            "timestamp": timestamp_utc(),
            "score_fragilidade_final": valid_coerencia.score_fragilidade,
            "avisos_finais": valid_coerencia.avisos,
        }
        gravar_json(FICHEIRO_ESTADO, estado)

        anexar_log_execucao(
            {
                "timestamp": timestamp_utc(),
                "fragment_id": fragment_id,
                "status": "ok",
                "score_fragilidade_final": valid_coerencia.score_fragilidade,
                "avisos_finais": valid_coerencia.avisos,
                "logs_pipeline": logs,
            }
        )

        processados += 1
        print("   ✅ ok", flush=True)
        print_parcial(processados, ignorados, falhados)

    relatorio = construir_relatorio_validacao(resultados, estado)
    gravar_json(FICHEIRO_RELATORIO, relatorio)

    agregado = construir_agregado_por_proposicao(resultados, mapa_dedutivo)
    gravar_json(FICHEIRO_AGREGADO, agregado)

    print("\n========================================", flush=True)
    print("EXTRAÇÃO DE IMPACTO DOS FRAGMENTOS NO MAPA CONCLUÍDA", flush=True)
    print("========================================", flush=True)
    print(f"Resultados: {FICHEIRO_SAIDA}", flush=True)
    print(f"Estado:     {FICHEIRO_ESTADO}", flush=True)
    print(f"Falhas:     {FICHEIRO_FALHAS}", flush=True)
    print(f"Logs:       {FICHEIRO_LOGS}", flush=True)
    print(f"Relatório:  {FICHEIRO_RELATORIO}", flush=True)
    print(f"Agregado:   {FICHEIRO_AGREGADO}", flush=True)
    print("========================================", flush=True)


if __name__ == "__main__":
    main()