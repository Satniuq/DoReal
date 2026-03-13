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
CADENCIA_DIR = SCRIPT_DIR.parent
META_INDICE_DIR = CADENCIA_DIR.parent
ROOT_DIR = META_INDICE_DIR.parent

# ----------------------------------------------------------------
# Resolução de ficheiros:
# 1) tenta a estrutura real do teu projeto (como no extrator_cadencia.py)
# 2) se não existir, cai para ficheiros no mesmo diretório do script
# ----------------------------------------------------------------

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

FICHEIRO_SAIDA = SCRIPT_DIR / "tratamento_filosofico_fragmentos.json"
FICHEIRO_ESTADO = SCRIPT_DIR / "estado_tratamento_filosofico.json"
FICHEIRO_FALHAS = SCRIPT_DIR / "falhas_tratamento_filosofico.json"
FICHEIRO_LOGS = SCRIPT_DIR / "tratamento_filosofico_logs_execucao.json"
FICHEIRO_RELATORIO = SCRIPT_DIR / "tratamento_filosofico_relatorio_validacao.json"

VERSAO_EXTRATOR = "extrator_tratamento_filosofico_v1_gpt54"
MODELO_PRINCIPAL = "gpt-5.4"
MODELO_ARBITRAGEM = "gpt-5.4"

FORCAR_REPROCESSAMENTO = False
REPROCESSAR_FALHAS = True
GUARDAR_PROMPTS = False

MAX_RETRIES_SCHEMA = 2
MAX_RETRIES_INTERPRETACAO = 1
MAX_RETRIES_FALLBACK = 1

LIMITE_FRAGMENTOS_TESTE = None

# Limites de contexto
MAX_ITEMS_ZONAS = 20
MAX_ITEMS_ARGUMENTOS = 25
MAX_ITEMS_INDICE = 20
MAX_ITEMS_CONCEITOS = 40
MAX_ITEMS_OPERACOES = 40
MAX_CHARS_FRAGMENTO = 4500
MAX_PROBLEMAS_ASSOCIADOS = 4

# Carrega .env tal como no extrator_cadencia.py
load_dotenv(ROOT_DIR / ".env")
load_dotenv(SCRIPT_DIR / ".env")
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

def construir_schema_tratamento_filosofico() -> Dict[str, Any]:
    trabalhos = [
        "abre_problema_ontologico",
        "fixa_condicao_ontologica",
        "fixa_limite_ontologico",
        "exclui_impossibilidade_ontologica",
        "inscreve_elemento_no_real",
        "descreve_estrutura_do_real",
        "descreve_dinamica_ontologica",
        "identifica_dependencia_estrutural",
        "reconduz_relacionalmente",
        "estabiliza_definicao_estrutural",
        "distingue_niveis_ontologicos",
        "distingue_escala_de_analise",
        "identifica_campo_de_validade",
        "clarifica_mediacao",
        "desfaz_confusao_categorial",
        "reinscreve_consciencia_no_real",
        "limita_ponto_de_vista",
        "distingue_apreensao_de_representacao",
        "dessubstancializa_o_eu",
        "identifica_projecao_reflexiva",
        "fixa_criterio_de_verdade",
        "mostra_condicao_da_verdade",
        "identifica_erro_descritivo",
        "corrige_erro_epistemologico",
        "submete_representacao_ao_real",
        "identifica_cristalizacao_sistemica",
        "diagnostica_fechamento_simbolico",
        "identifica_substituicao_do_real",
        "diagnostica_degeneracao_autorreferencial",
        "prepara_reintegracao_ontologica",
        "deriva_dever_ser_do_ser",
        "subordina_normatividade_ao_real",
        "identifica_responsabilidade_ontologica",
        "identifica_dano_real",
        "deriva_criterio_do_bem",
        "faz_transicao_de_percurso",
        "prepara_argumento_seguinte",
        "fecha_bloco_anterior",
        "rearticula_material_disperso",
        "abre_aplicacao_setorial",
    ]

    problemas = [
        "estatuto_do_real",
        "condicoes_de_possibilidade_do_ser",
        "continuidade_do_real",
        "potencialidade_e_atualizacao",
        "limite_ontologico",
        "relacao_e_dependencia",
        "estrutura_do_movimento",
        "regularidade_e_estabilidade",
        "origem_da_consciencia",
        "consciencia_como_processo_no_real",
        "estatuto_do_eu",
        "localidade_do_ponto_de_vista",
        "apreensao_vs_representacao",
        "autorreferencialidade",
        "projecao_do_eu_no_real",
        "possibilidade_da_verdade",
        "criterio_de_verdade",
        "adequacao_entre_representacao_e_real",
        "origem_do_erro",
        "erro_descritivo",
        "erro_categorial",
        "erro_de_escala",
        "condicoes_da_correcao",
        "mediacao_simbolica",
        "cristalizacao_sistemica",
        "fechamento_simbolico",
        "substituicao_do_real_pelo_sistema",
        "validade_interna_vs_adequacao",
        "instituicao_de_criterios",
        "degradacao_autorreferencial_dos_sistemas",
        "tecnologia_como_mediacao_de_segunda_ordem",
        "fundamento_do_dever_ser",
        "subordinacao_da_normatividade_ao_real",
        "origem_do_bem",
        "responsabilidade_ontologica",
        "dano_real_e_reducao_de_potencialidades",
        "verdade_e_valor",
        "criterio_para_viver_bem",
        "ser_humano_como_ente_reflexivo",
        "cultura_como_estabilizacao_simbolica",
        "lei_e_fundamento_ontologico",
        "sociedade_e_erro_estabilizado",
        "escala_das_respostas_coletivas",
        "instituicoes_como_mediacoes_do_real",
        "ordem_do_percurso_filosofico",
        "condicoes_de_inteligibilidade_do_sistema",
        "relacao_entre_partes_do_sistema",
        "passagem_da_ontologia_para_a_epistemologia",
        "passagem_da_ontologia_para_a_etica",
        "passagem_da_descricao_para_a_correcao",
    ]

    papeis_editoriais = [
        "nucleo_de_capitulo",
        "apoio_argumentativo",
        "ponte_de_transicao",
        "nota_lateral_aproveitavel",
        "aplicacao_setorial",
        "material_a_retrabalhar",
        "arquivo_de_intuicoes",
    ]

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "tratamento_filosofico_fragmento.schema.json",
        "title": "Tratamento Filosófico do Fragmento",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "fragment_id",
            "origem_id",
            "ordem_no_ficheiro",
            "tratamento_filosofico_fragmento",
        ],
        "properties": {
            "fragment_id": {"type": "string"},
            "origem_id": {"type": ["string", "null"]},
            "ordem_no_ficheiro": {"type": "integer"},
            "tratamento_filosofico_fragmento": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "explicacao_textual_do_que_o_fragmento_tenta_fazer",
                    "trabalho_no_sistema",
                    "trabalho_no_sistema_secundario",
                    "descricao_funcional_curta",
                    "problema_filosofico_central",
                    "problemas_filosoficos_associados",
                    "tipo_de_problema",
                    "posicao_no_indice",
                    "estrutura_analitica",
                    "potencial_argumentativo",
                    "relacoes_no_sistema",
                    "destino_editorial",
                    "avaliacao_global",
                ],
                "properties": {
                    "explicacao_textual_do_que_o_fragmento_tenta_fazer": {
                        "type": "string"
                    },
                    "trabalho_no_sistema": {
                        "type": "string",
                        "enum": trabalhos,
                    },
                    "trabalho_no_sistema_secundario": {
                        "type": ["string", "null"],
                        "enum": trabalhos + [None],
                    },
                    "descricao_funcional_curta": {"type": "string"},
                    "problema_filosofico_central": {
                        "type": "string",
                        "enum": problemas,
                    },
                    "problemas_filosoficos_associados": {
                        "type": "array",
                        "items": {"type": "string", "enum": problemas},
                        "uniqueItems": True,
                    },
                    "tipo_de_problema": {
                        "type": "string",
                        "enum": [
                            "ontologico",
                            "epistemologico",
                            "etico",
                            "antropologico",
                            "mediacional",
                            "metaestrutural",
                            "misto",
                        ],
                    },
                    "posicao_no_indice": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "parte_id",
                            "capitulo_id",
                            "capitulo_titulo",
                            "subcapitulo_ou_zona_interna",
                            "argumento_canonico_relacionado",
                            "argumentos_canonicos_associados",
                            "grau_de_pertenca_ao_indice",
                            "modo_de_pertenca",
                            "justificacao_de_posicao_no_indice",
                        ],
                        "properties": {
                            "parte_id": {"type": ["string", "null"]},
                            "capitulo_id": {"type": ["string", "null"]},
                            "capitulo_titulo": {"type": ["string", "null"]},
                            "subcapitulo_ou_zona_interna": {"type": ["string", "null"]},
                            "argumento_canonico_relacionado": {"type": ["string", "null"]},
                            "argumentos_canonicos_associados": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "grau_de_pertenca_ao_indice": {
                                "type": "string",
                                "enum": ["nuclear", "forte", "provavel", "fraca", "indefinida"],
                            },
                            "modo_de_pertenca": {
                                "type": "string",
                                "enum": [
                                    "nucleo_de_capitulo",
                                    "apoio_argumentativo",
                                    "ponte_de_transicao",
                                    "preparacao_de_argumento",
                                    "aplicacao_local",
                                    "nota_lateral",
                                    "material_a_retrabalhar",
                                    "arquivo_sem_encaixe",
                                ],
                            },
                            "justificacao_de_posicao_no_indice": {"type": "string"},
                        },
                    },
                    "estrutura_analitica": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "objeto_em_analise",
                            "plano_ontologico",
                            "plano_epistemologico",
                            "plano_etico",
                            "plano_antropologico",
                            "plano_mediacional",
                            "distincao_central",
                            "dependencia_principal",
                            "criterio_implicado",
                            "erro_visado",
                            "consequencia_principal",
                            "pressuposto_ontologico_principal",
                            "pressupostos_secundarios",
                        ],
                        "properties": {
                            "objeto_em_analise": {"type": "string"},
                            "plano_ontologico": {"type": "string"},
                            "plano_epistemologico": {"type": "string"},
                            "plano_etico": {"type": "string"},
                            "plano_antropologico": {"type": "string"},
                            "plano_mediacional": {"type": "string"},
                            "distincao_central": {"type": "string"},
                            "dependencia_principal": {"type": "string"},
                            "criterio_implicado": {"type": "string"},
                            "erro_visado": {"type": "string"},
                            "consequencia_principal": {"type": "string"},
                            "pressuposto_ontologico_principal": {"type": "string"},
                            "pressupostos_secundarios": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                        },
                    },
                    "potencial_argumentativo": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "estado_argumentativo",
                            "premissas_implicitas",
                            "premissa_central_reconstruida",
                            "conclusao_visada",
                            "forma_de_inferencia",
                            "forca_logica_estimada",
                            "argumento_reconstruivel",
                            "necessita_reconstrucao_forte",
                            "observacoes_argumentativas",
                        ],
                        "properties": {
                            "estado_argumentativo": {
                                "type": "string",
                                "enum": [
                                    "intuicao_bruta",
                                    "exploracao_pre_conceptual",
                                    "formulacao_pre_argumentativa",
                                    "distincao_util_sem_argumento",
                                    "argumento_em_esboco",
                                    "argumento_quase_formalizavel",
                                    "argumento_formalizavel",
                                    "aplicacao_de_argumento",
                                    "sintese_pos_argumentativa",
                                ],
                            },
                            "premissas_implicitas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "premissa_central_reconstruida": {"type": "string"},
                            "conclusao_visada": {"type": "string"},
                            "forma_de_inferencia": {
                                "type": "string",
                                "enum": [
                                    "dedutiva",
                                    "abductiva",
                                    "reconducao_estrutural",
                                    "exclusao_por_impossibilidade",
                                    "critica_por_contradicao",
                                    "derivacao_normativa",
                                    "distincao_analitica",
                                    "descricao_estrutural",
                                    "mista",
                                    "nao_determinada",
                                ],
                            },
                            "forca_logica_estimada": {
                                "type": "string",
                                "enum": ["alta", "media", "baixa", "muito_baixa"],
                            },
                            "argumento_reconstruivel": {"type": "boolean"},
                            "necessita_reconstrucao_forte": {"type": "boolean"},
                            "observacoes_argumentativas": {"type": "string"},
                        },
                    },
                    "relacoes_no_sistema": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "depende_de_conceitos",
                            "mobiliza_operacoes",
                            "regimes_envolvidos",
                            "percursos_envolvidos",
                            "abre_para",
                            "corrige",
                            "prepara",
                            "pressupoe",
                            "entra_em_tensao_com",
                        ],
                        "properties": {
                            "depende_de_conceitos": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "mobiliza_operacoes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "regimes_envolvidos": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "percursos_envolvidos": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "abre_para": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "corrige": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "prepara": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "pressupoe": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "entra_em_tensao_com": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                        },
                    },
                    "destino_editorial": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "destino_editorial_fino",
                            "papel_editorial_primario",
                            "papel_editorial_secundario",
                            "prioridade_de_revisao",
                            "prioridade_de_aproveitamento",
                            "requer_reescrita",
                            "requer_densificacao",
                            "requer_formalizacao_logica",
                            "observacoes_editoriais",
                        ],
                        "properties": {
                            "destino_editorial_fino": {
                                "type": "string",
                                "enum": papeis_editoriais,
                            },
                            "papel_editorial_primario": {
                                "type": "string",
                                "enum": papeis_editoriais,
                            },
                            "papel_editorial_secundario": {
                                "type": ["string", "null"],
                                "enum": papeis_editoriais + [None],
                            },
                            "prioridade_de_revisao": {
                                "type": "string",
                                "enum": ["imediata", "alta", "media", "baixa"],
                            },
                            "prioridade_de_aproveitamento": {
                                "type": "string",
                                "enum": ["alta", "media", "baixa"],
                            },
                            "requer_reescrita": {"type": "boolean"},
                            "requer_densificacao": {"type": "boolean"},
                            "requer_formalizacao_logica": {"type": "boolean"},
                            "observacoes_editoriais": {"type": "string"},
                        },
                    },
                    "avaliacao_global": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "densidade_filosofica",
                            "clareza_atual",
                            "grau_de_estabilizacao",
                            "risco_de_ma_interpretacao",
                            "confianca_tratamento_filosofico",
                            "necessita_revisao_humana_filosofica",
                        ],
                        "properties": {
                            "densidade_filosofica": {
                                "type": "string",
                                "enum": ["alta", "media", "baixa"],
                            },
                            "clareza_atual": {
                                "type": "string",
                                "enum": ["claro", "razoavelmente_claro", "instavel", "muito_instavel"],
                            },
                            "grau_de_estabilizacao": {
                                "type": "string",
                                "enum": ["estavel", "semi_estavel", "provisorio", "muito_provisorio"],
                            },
                            "risco_de_ma_interpretacao": {
                                "type": "string",
                                "enum": ["alto", "medio", "baixo"],
                            },
                            "confianca_tratamento_filosofico": {
                                "type": "string",
                                "enum": ["alta", "media", "baixa"],
                            },
                            "necessita_revisao_humana_filosofica": {"type": "boolean"},
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
) -> Dict[str, Any]:
    return {
        "regras_gerais": [
            "texto_fragmento manda sobre os campos auxiliares",
            "nao confundir afinidade tematica com pertença estrutural",
            "nao forcar encaixe definitivo no indice",
            "nao tratar intuicao vaga como argumento forte",
            "quando houver duvida, usar valores fracos, null, listas vazias ou indefinida",
        ],
        "zonas_do_percurso": resumir_meta_percurso(meta_percurso),
        "meta_indice_resumo": resumir_meta_indice(meta_indice),
        "indice_sequencial_resumo": resumir_indice_sequencial(indice_sequencial),
        "indice_argumentos_resumo": resumir_indice_argumentos(indice_argumentos),
        "argumentos_unificados_resumo": resumir_argumentos_unificados(argumentos_unificados),
        "conceitos_resumo": resumir_conceitos(conceitos),
        "operacoes_resumo": resumir_operacoes(operacoes),
    }


# ============================================================
# PREPARAÇÃO DO PAYLOAD
# ============================================================

def preparar_payload_fragmento(
    fragmento: Dict[str, Any],
    cadencia_item: Optional[Dict[str, Any]],
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
És um extrator de tratamento filosófico de fragmentos.

Objetivo:
preencher rigorosamente um objeto JSON conforme ao schema fornecido, identificando:
- o que o fragmento tenta fazer,
- o seu trabalho no sistema,
- o problema filosófico central,
- a sua posição provável no índice,
- a sua estrutura analítica,
- o seu potencial argumentativo,
- as suas relações no sistema,
- o seu destino editorial,
- e a sua avaliação global.

Regra central:
o texto_fragmento manda.
Os campos auxiliares ajudam, mas não substituem a leitura do texto.

Não deves:
- resumir apenas o tema;
- inventar encaixes fortes no índice;
- confundir afinidade temática com pertença estrutural;
- tratar uma intuição vaga como argumento formalizável;
- preencher campos por obrigação formal quando o texto não os sustenta minimamente.

Usa por esta ordem:
1. texto_fragmento
2. texto_normalizado e texto_fonte_reconstituido
3. relacoes_locais e sinais_automaticos
4. cadencia_preexistente
5. contexto macro reduzido

Regras adicionais:
- usa os nomes e enums do schema exatamente como estão;
- se houver dúvida real, reduz a força da classificação;
- usa null, listas vazias, "indefinida", "nao_determinada" ou "arquivo_sem_encaixe" quando apropriado;
- "explicacao_textual_do_que_o_fragmento_tenta_fazer" deve ter 1 a 3 frases;
- "descricao_funcional_curta" deve ser curta, direta e não literária;
- "problemas_filosoficos_associados" não deve ter mais de 4 itens;
- "trabalho_no_sistema_secundario" só quando houver um segundo gesto claramente autónomo;
- em "posicao_no_indice", distingue posição forte de mera afinidade;
- em "potencial_argumentativo", avalia a formulação atual do fragmento, não a sua melhor versão futura;
- em "relacoes_no_sistema", preencher apenas relações explicitamente sustentadas pelo texto do fragmento ou por metadados já existentes; não projetar o lugar futuro do fragmento no sistema;
- se houver apenas afinidade vaga com conceitos, operações, regimes ou percursos, preferir listas vazias;
- não usar códigos de conceitos, operações, regimes ou percursos apenas porque parecem compatíveis com o tema; só usar quando houver apoio textual ou estrutural suficientemente claro;
- se o fragmento estiver demasiado instável, podes deixar vários campos em forma fraca.

Critérios decisivos:
- "trabalho_no_sistema": que trabalho do sistema ficaria por fazer se este fragmento desaparecesse?
- "problema_filosofico_central": qual o problema dominante sem o qual o fragmento não faria sentido?
- "grau_de_pertenca_ao_indice": nuclear, forte, provavel, fraca ou indefinida com prudência.
- "estado_argumentativo": distinguir cuidadosamente entre intuição, exploração, formulação pré-argumentativa, esboço de argumento e argumento formalizável.
- "destino_editorial": avaliar utilidade real para o livro, não apenas interesse abstrato.

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
- se um campo não puder ser sustentado, enfraquece-o em vez de forçar precisão.

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
- não assumir posição forte no índice sem sinais textuais claros ou muito sólidos;
- não transformar afinidade temática em pertença estrutural;
- não reconstruir argumento forte quando apenas existe intuição vaga;
- se houver dúvida entre manter um valor forte e enfraquecê-lo, enfraquece-o;
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
1. explicar o que o fragmento tenta fazer;
2. identificar o trabalho principal no sistema;
3. identificar o problema filosófico central;
4. avaliar o estado argumentativo;
5. propor um destino editorial prudente.

Estratégia:
- não forçar posição no índice se não houver base;
- não forçar estrutura analítica completa se o fragmento não a suportar;
- usa null, listas vazias, "indefinida", "nao_determinada" e classificações fracas;
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
    """
    Produz uma versão do schema compatível com o response_format/json_schema da API.
    Mantém o schema rico para validação local, mas remove keywords que a API pode rejeitar.
    """
    if isinstance(schema, list):
        return [_normalizar_schema_para_strict(x) for x in schema]

    if not isinstance(schema, dict):
        return schema

    schema = copy.deepcopy(schema)

    # Keywords que não são necessárias para a geração e que podem rebentar na API
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
                "name": "tratamento_filosofico_fragmento",
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


def validar_coerencia_logica(resultado: Dict[str, Any]) -> ResultadoCoerencia:
    avisos: List[str] = []
    motivos: List[str] = []
    score = 0

    raiz = normalizar_dict(resultado.get("tratamento_filosofico_fragmento"))
    pos = normalizar_dict(raiz.get("posicao_no_indice"))
    pot = normalizar_dict(raiz.get("potencial_argumentativo"))
    dest = normalizar_dict(raiz.get("destino_editorial"))
    aval = normalizar_dict(raiz.get("avaliacao_global"))
    rel = normalizar_dict(raiz.get("relacoes_no_sistema"))

    if len(normalizar_lista(raiz.get("problemas_filosoficos_associados"))) > MAX_PROBLEMAS_ASSOCIADOS:
        motivos.append("demasiados_problemas_associados")
        score += 2

    grau = pos.get("grau_de_pertenca_ao_indice")
    capitulo_id = pos.get("capitulo_id")
    modo = pos.get("modo_de_pertenca")

    if grau in ("nuclear", "forte") and not capitulo_id:
        motivos.append("encaixe_forte_sem_capitulo")
        score += 2

    if grau == "nuclear" and modo not in ("nucleo_de_capitulo", "apoio_argumentativo"):
        motivos.append("nuclear_com_modo_fraco")
        score += 2

    estado_arg = pot.get("estado_argumentativo")
    reconstruivel = pot.get("argumento_reconstruivel")
    forma = pot.get("forma_de_inferencia")
    forca = pot.get("forca_logica_estimada")

    if estado_arg == "intuicao_bruta" and reconstruivel is True:
        motivos.append("intuicao_bruta_marcada_como_reconstruivel")
        score += 2

    if estado_arg in ("intuicao_bruta", "exploracao_pre_conceptual") and reconstruivel is True:
        motivos.append("estado_argumentativo_fraco_com_argumento_reconstruivel")
        score += 2

    if estado_arg in ("intuicao_bruta", "exploracao_pre_conceptual") and forma not in (
        "nao_determinada",
        "descricao_estrutural",
        "distincao_analitica",
    ):
        avisos.append("forma_de_inferencia_forte_demais_para_estado_fraco")
        score += 1

    if estado_arg == "argumento_formalizavel" and forca in ("muito_baixa", "baixa"):
        motivos.append("argumento_formalizavel_com_forca_baixa")
        score += 2

    if estado_arg in ("intuicao_bruta", "exploracao_pre_conceptual"):
        if len(normalizar_lista(rel.get("regimes_envolvidos"))) > 1:
            avisos.append("regimes_demasiado_determinados_para_fragmento_muito_instavel")
            score += 1

        n_rel = sum(len(normalizar_lista(rel.get(k))) for k in [
            "depende_de_conceitos",
            "mobiliza_operacoes",
            "regimes_envolvidos",
            "percursos_envolvidos",
            "abre_para",
            "corrige",
            "prepara",
            "pressupoe",
            "entra_em_tensao_com",
        ])
        if n_rel > 10:
            avisos.append("sobrepreenchimento_relacional_em_fragmento_instavel")
            score += 1

    if aval.get("confianca_tratamento_filosofico") == "baixa" and aval.get("necessita_revisao_humana_filosofica") is False:
        avisos.append("confianca_baixa_sem_revisao_humana")
        score += 1

    if dest.get("destino_editorial_fino") == "nucleo_de_capitulo":
        avisos.append("valor_invalido_em_destino_editorial_fino")
        score += 1

    papel_primario = dest.get("papel_editorial_primario")
    prioridade_aproveitamento = dest.get("prioridade_de_aproveitamento")
    if papel_primario == "arquivo_de_intuicoes" and prioridade_aproveitamento == "alta":
        avisos.append("arquivo_de_intuicoes_com_aproveitamento_alto")
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

def extrair_tratamento_fragmento(
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
    valid_schema = validar_resultado_schema(resposta, schema_obj)

    if valid_schema.ok:
        valid_coerencia = validar_coerencia_logica(resposta)
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
            valid_schema2 = validar_resultado_schema(resposta2, schema_obj)

            if valid_schema2.ok:
                valid_coerencia2 = validar_coerencia_logica(resposta2)
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
            valid_schema3 = validar_resultado_schema(resposta3, schema_obj)

            if valid_schema3.ok:
                valid_coerencia3 = validar_coerencia_logica(resposta3)
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
        except Exception as e:
            logs["etapas"].append({"tipo": "erro_fallback", "tentativa": tentativa, "erro": str(e)})
            continue

        valid_schema4 = validar_resultado_schema(resposta4, schema_obj)
        if valid_schema4.ok:
            valid_coerencia4 = validar_coerencia_logica(resposta4)
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
# RELATÓRIO FINAL
# ============================================================

def construir_relatorio_validacao(saida: List[Dict[str, Any]], estado: Dict[str, Any]) -> Dict[str, Any]:
    total = len(saida)
    por_trabalho: Dict[str, int] = {}
    por_problema: Dict[str, int] = {}
    por_estado_arg: Dict[str, int] = {}
    por_grau_encaixe: Dict[str, int] = {}

    for item in saida:
        raiz = normalizar_dict(item.get("tratamento_filosofico_fragmento"))
        pos = normalizar_dict(raiz.get("posicao_no_indice"))
        pot = normalizar_dict(raiz.get("potencial_argumentativo"))

        trab = raiz.get("trabalho_no_sistema")
        prob = raiz.get("problema_filosofico_central")
        est_arg = pot.get("estado_argumentativo")
        grau = pos.get("grau_de_pertenca_ao_indice")

        if isinstance(trab, str):
            por_trabalho[trab] = por_trabalho.get(trab, 0) + 1
        if isinstance(prob, str):
            por_problema[prob] = por_problema.get(prob, 0) + 1
        if isinstance(est_arg, str):
            por_estado_arg[est_arg] = por_estado_arg.get(est_arg, 0) + 1
        if isinstance(grau, str):
            por_grau_encaixe[grau] = por_grau_encaixe.get(grau, 0) + 1

    estado_fragmentos = normalizar_dict(estado.get("fragmentos"))
    falhados = [fid for fid, meta in estado_fragmentos.items() if normalizar_dict(meta).get("status") == "falhou"]

    return {
        "timestamp": timestamp_utc(),
        "versao_extrator": VERSAO_EXTRATOR,
        "modelo_principal": MODELO_PRINCIPAL,
        "modelo_arbitragem": MODELO_ARBITRAGEM,
        "total_resultados": total,
        "falhados": falhados,
        "distribuicao_trabalho_no_sistema": dict(sorted(por_trabalho.items(), key=lambda x: (-x[1], x[0]))),
        "distribuicao_problema_filosofico_central": dict(sorted(por_problema.items(), key=lambda x: (-x[1], x[0]))),
        "distribuicao_estado_argumentativo": dict(sorted(por_estado_arg.items(), key=lambda x: (-x[1], x[0]))),
        "distribuicao_grau_de_pertenca_ao_indice": dict(sorted(por_grau_encaixe.items(), key=lambda x: (-x[1], x[0]))),
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    schema_obj = construir_schema_tratamento_filosofico()

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

    print(f"   ✔ fragmentos: {FICHEIRO_FRAGMENTOS}", flush=True)
    print(f"   ✔ cadencia: {FICHEIRO_CADENCIA}", flush=True)
    print(f"   ✔ meta_percurso: {FICHEIRO_META_PERCURSO}", flush=True)
    print(f"   ✔ meta_indice: {FICHEIRO_META_INDICE}", flush=True)
    print(f"   ✔ indice_sequencial: {FICHEIRO_INDICE_SEQUENCIAL}", flush=True)
    print(f"   ✔ indice_argumentos: {FICHEIRO_INDICE_ARGUMENTOS}", flush=True)
    print(f"   ✔ argumentos_unificados: {FICHEIRO_ARGUMENTOS_UNIFICADOS}", flush=True)
    print(f"   ✔ conceitos: {FICHEIRO_CONCEITOS}", flush=True)
    print(f"   ✔ operacoes: {FICHEIRO_OPERACOES}", flush=True)

    cadencia_idx = indexar_por_fragment_id(cadencia_lista)

    contexto_macro_minimo = construir_contexto_macro_minimo(
        meta_percurso=meta_percurso,
        meta_indice=meta_indice,
        indice_sequencial=indice_sequencial,
        indice_argumentos=indice_argumentos,
        argumentos_unificados=argumentos_unificados,
        conceitos=conceitos,
        operacoes=operacoes,
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
        fragmento_payload = preparar_payload_fragmento(fragmento, cadencia_item, ordem_loop)

        try:
            resposta, logs = extrair_tratamento_fragmento(
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

        valid_schema = validar_resultado_schema(resposta, schema_obj)
        valid_coerencia = validar_coerencia_logica(resposta)

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

        # Remover versão anterior, se existir
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

    print("\n========================================", flush=True)
    print("EXTRAÇÃO DE TRATAMENTO FILOSÓFICO CONCLUÍDA", flush=True)
    print("========================================", flush=True)
    print(f"Resultados: {FICHEIRO_SAIDA}", flush=True)
    print(f"Estado:     {FICHEIRO_ESTADO}", flush=True)
    print(f"Falhas:     {FICHEIRO_FALHAS}", flush=True)
    print(f"Logs:       {FICHEIRO_LOGS}", flush=True)
    print(f"Relatório:  {FICHEIRO_RELATORIO}", flush=True)
    print("========================================", flush=True)


if __name__ == "__main__":
    main()