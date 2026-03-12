from __future__ import annotations

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

FICHEIRO_FRAGMENTOS = CADENCIA_DIR / "01_segmentar_fragmentos" / "fragmentos_resegmentados.json"
FICHEIRO_SCHEMA = SCRIPT_DIR / "cadencia_schema.json"
FICHEIRO_META_PERCURSO = META_INDICE_DIR / "meta" / "meta_referencia_do_percurso.json"
FICHEIRO_META_INDICE = META_INDICE_DIR / "meta" / "meta_indice.json"
FICHEIRO_INDICE_SEQUENCIAL = META_INDICE_DIR / "indice" / "indice_sequencial.json"
FICHEIRO_INDICE_ARGUMENTOS = META_INDICE_DIR / "indice" / "indice_argumentos.json"
FICHEIRO_ARGUMENTOS_UNIFICADOS = META_INDICE_DIR / "indice" / "argumentos" / "argumentos_unificados.json"
FICHEIRO_LABELS_TIPOS = CADENCIA_DIR / "extrator" / "labels_tipos_fragmento.json"
FICHEIRO_LABELS_ERROS = CADENCIA_DIR / "extrator" / "labels_erros.json"

FICHEIRO_SAIDA = SCRIPT_DIR / "cadencia_extraida.json"
FICHEIRO_RELATORIO = SCRIPT_DIR / "cadencia_relatorio_validacao.json"
FICHEIRO_FRAGEIS = SCRIPT_DIR / "cadencia_casos_fragilizados.json"
FICHEIRO_ESTADO = SCRIPT_DIR / "estado_extrator_cadencia.json"
FICHEIRO_LOGS = SCRIPT_DIR / "cadencia_logs_execucao.json"

VERSAO_EXTRATOR = "extrator_cadencia_v1_gpt54"
MODELO_PRINCIPAL = "gpt-5.4"
MODELO_ARBITRAGEM = "gpt-5.4"

FORCAR_REPROCESSAMENTO = False
REPROCESSAR_FALHAS = True
GUARDAR_PROMPTS = False

MAX_RETRIES_SCHEMA = 2
MAX_RETRIES_INTERPRETACAO = 1

# Para smoke tests rápidos, por exemplo 3 ou 5.
# Em produção, deixar None.
LIMITE_FRAGMENTOS_TESTE = None

load_dotenv(ROOT_DIR / ".env")
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
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def carregar_json_opcional(caminho: Path, default: Any) -> Any:
    if not caminho.exists():
        return default
    return carregar_json(caminho)


def gravar_json(caminho: Path, dados: Any) -> None:
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
# NORMALIZAÇÃO / RESUMOS
# ============================================================


def garantir_lista_fragmentos(dados: Any) -> List[Dict[str, Any]]:
    if isinstance(dados, list):
        return dados
    if isinstance(dados, dict):
        if "fragmentos" in dados and isinstance(dados["fragmentos"], list):
            return dados["fragmentos"]
    raise ValueError("fragmentos_resegmentados.json não tem formato esperado")


def normalizar_relacoes_locais(valor: Any) -> Dict[str, Any]:
    return valor if isinstance(valor, dict) else {}


def normalizar_lista(valor: Any) -> List[Any]:
    if valor is None:
        return []
    if isinstance(valor, list):
        return valor
    return [valor]


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
    return fallback


def bucket_comprimento(n_chars: int) -> str:
    if n_chars < 220:
        return "curto"
    if n_chars < 700:
        return "medio"
    return "longo"


def resumir_labels_tipos(labels_tipos: Dict[str, Any]) -> Dict[str, Any]:
    tipos = []
    for item in labels_tipos.get("tipos_fragmento", []) or []:
        if not isinstance(item, dict):
            continue
        tipos.append(
            {
                "id": item.get("id"),
                "familia": item.get("familia"),
                "descricao": item.get("descricao"),
            }
        )
    return {
        "schema_version": labels_tipos.get("schema_version"),
        "criterio_ultimo": labels_tipos.get("criterio_ultimo"),
        "tipos_fragmento": tipos,
    }


def resumir_labels_erros(labels_erros: Dict[str, Any]) -> Dict[str, Any]:
    familias = []
    for item in labels_erros.get("familias", []) or []:
        if not isinstance(item, dict):
            continue
        familias.append(
            {
                "id": item.get("id"),
                "descricao": item.get("descricao"),
            }
        )

    erros = []
    for item in labels_erros.get("erros", []) or []:
        if not isinstance(item, dict):
            continue
        erros.append(
            {
                "id": item.get("id"),
                "tipo": item.get("tipo"),
                "descricao": item.get("descricao"),
            }
        )

    return {
        "schema_version": labels_erros.get("schema_version"),
        "criterio_ultimo": labels_erros.get("criterio_ultimo"),
        "familias": familias,
        "erros": erros,
    }


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
        "regimes": regimes_resumo
    }


def resumir_indice_argumentos(indice_argumentos: Any) -> Any:
    if isinstance(indice_argumentos, list):
        return indice_argumentos[:20]
    if isinstance(indice_argumentos, dict):
        resumo = {}
        for k, v in list(indice_argumentos.items())[:20]:
            resumo[k] = v
        return resumo
    return {}


def resumir_indice_sequencial(indice_sequencial: Any) -> Any:
    if isinstance(indice_sequencial, list):
        return indice_sequencial[:20]
    if isinstance(indice_sequencial, dict):
        resumo = {}
        for k, v in list(indice_sequencial.items())[:20]:
            resumo[k] = v
        return resumo
    return {}


def resumir_argumentos_unificados(argumentos_unificados: Any) -> List[Dict[str, Any]]:
    resumo = []
    if isinstance(argumentos_unificados, list):
        for item in argumentos_unificados[:25]:
            if not isinstance(item, dict):
                continue
            resumo.append(
                {
                    "id": item.get("id") or item.get("argumento_id"),
                    "titulo": item.get("titulo") or item.get("nome"),
                    "descricao": item.get("descricao") or item.get("resumo"),
                }
            )
    return resumo


# ============================================================
# CONTEXTO MACRO REDUZIDO
# ============================================================


def construir_contexto_macro_minimo(
    meta_percurso: Dict[str, Any],
    meta_indice: Any,
    indice_sequencial: Any,
    indice_argumentos: Any,
    argumentos_unificados: Any,
) -> Dict[str, Any]:
    zonas = []
    if isinstance(meta_percurso, dict):
        for zona_id, dados in meta_percurso.items():
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

    return {
        "regras_gerais": [
            "texto_fragmento manda sobre os campos auxiliares",
            "nao forcar encaixe definitivo no indice",
            "cadencia identifica funcao e lugar, nao ontologia final",
            "pontes entre zonas so quando sustentadas pelo texto",
            "tipo_fragmento_provavel e uma orientacao leve",
        ],
        "zonas_do_percurso": zonas,
        "meta_indice_resumo": resumir_meta_indice(meta_indice),
        "indice_sequencial_resumo": resumir_indice_sequencial(indice_sequencial),
        "indice_argumentos_resumo": resumir_indice_argumentos(indice_argumentos),
        "argumentos_unificados_resumo": resumir_argumentos_unificados(argumentos_unificados),
    }


# ============================================================
# PREPARAÇÃO DO PAYLOAD
# ============================================================


def preparar_payload_fragmento(fragmento: Dict[str, Any], ordem_loop: int) -> Dict[str, Any]:
    relacoes = normalizar_relacoes_locais(fragmento.get("relacoes_locais"))
    texto = (fragmento.get("texto_fragmento") or "").strip()
    n_chars = int(fragmento.get("n_chars_fragmento") or len(texto))
    segmentacao = fragmento.get("segmentacao") if isinstance(fragmento.get("segmentacao"), dict) else {}
    origem = fragmento.get("origem") if isinstance(fragmento.get("origem"), dict) else {}

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
        "texto_fragmento": texto,
        "texto_normalizado": fragmento.get("texto_normalizado"),
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
    labels_tipos_resumo: Dict[str, Any],
    labels_erros_resumo: Dict[str, Any],
    fragmento_payload: Dict[str, Any],
) -> str:
    return f"""
És um extrator de cadência filosófica.

Objetivo:
identificar a função estrutural do fragmento no movimento do texto e no percurso do livro.

Regra central:
o texto_fragmento manda.
Os campos auxiliares ajudam, mas não substituem a leitura do texto.

Não deves:
- classificar ontologicamente de forma final;
- escolher o capítulo definitivo;
- forçar encaixes artificiais;
- usar o contexto macro como verdade superior contra o texto.

Usa por esta ordem:
1. texto_fragmento
2. estrutura local e relacoes_locais
3. anotação leve já existente
4. contexto macro reduzido

Regras adicionais:
- usa os nomes e enums do schema exatamente como estão;
- se houver dúvida real, reduz a confiança;
- usa null ou "indefinida" quando apropriado;
- marca necessita_revisao_humana=true quando necessário;
- tipo_fragmento_provavel é apenas orientação leve;
- só preenchas tipo_fragmento_provavel quando houver suporte textual suficiente;
- se incide_sobre_erro=false, tende a usar familia_erro_provavel="nao_aplicavel" e erro_dominante_provavel=null;
- não copies mecanicamente funcao_textual_dominante para funcao_cadencia_principal;
- lê o texto e decide pelo papel estrutural efetivo do fragmento.

funcao_cadencia_secundaria:
usa null por defeito.
Só a preenchas quando houver um segundo papel estrutural claramente autónomo e textual.
Não a uses apenas para nuance, hesitação classificatória, redundância com a função principal, ou simples sobreposição vaga.

centralidade:
não uses "exploratorio" como categoria-padrão para qualquer texto incompleto, oral ou provisório.
Distingue assim:
- nuclear: peça estrutural forte;
- auxiliar: apoio ou desenvolvimento sem ser centro;
- transitorio: passagem, ligação ou mudança de foco;
- exploratorio: ensaio, tateio ou hipótese ainda não estabilizada;
- estabilizador: consolida ou clarifica algo já em curso;
- dispersivo_aproveitavel: material útil mas pouco concentrado;
- nota_de_apoio: apoio lateral.
Na dúvida entre "auxiliar" e "exploratorio", não uses "exploratorio" automaticamente.

tipo_fragmento_provavel:
usa null por defeito.
Só o preenchas quando o texto sustentar claramente esse tipo de fragmento.
Não o infiras apenas por proximidade temática, palavras soltas ou semelhança vaga com categorias do sistema.
Se a formulação for oral, instável, incompleta, ensaística ou apenas insinuada, prefere null.

zona_provavel_percurso:
não escolhas uma zona apenas porque o fragmento toca num tema associado a essa zona.
Escolhe uma zona apenas quando o papel estrutural do fragmento no percurso a sustentar minimamente.
Se houver apenas afinidade temática vaga, usa "indefinida".

aproveitamento_editorial:
não escolhas "nucleo_de_capitulo" sem sinais textuais fortes.
Usa "material_a_retrabalhar" quando a ideia é útil mas a formulação ainda exige reelaboração significativa.

estatuto_no_percurso:
não uses "pertence_a_zona" apenas porque o fragmento tem afinidade temática com uma zona.
Usa "pertence_a_zona" apenas quando o papel estrutural do fragmento no percurso sustentar essa pertença com alguma clareza.
Se houver apenas afinidade temática, exploração inicial ou ligação ainda pouco estabilizada, prefere "solto_ainda_sem_encaixe".

familia_erro_provavel e erro_dominante_provavel:
usa estes campos com forte prudência.
Não escolhas uma família de erro forte ou um erro dominante específico apenas porque o fragmento critica, corrige ou problematiza algo.
Só atribuas familia_erro_provavel quando houver sinais textuais suficientemente claros de que o fragmento incide realmente sobre esse tipo de erro.
Só atribuas erro_dominante_provavel quando o texto sustentar de modo minimamente explícito esse erro específico.
Se houver apenas crítica vaga, diagnóstico incompleto, formulação oral, ou simples sugestão de desajuste, prefere:
- incide_sobre_erro = true, se isso fizer sentido;
- familia_erro_provavel = null ou a família mais prudente;
- erro_dominante_provavel = null.
Prefere subdeterminar o erro a especificá-lo cedo demais.
Não confundas crítica prática local, má formulação, ou instabilidade oral com crítica sistémica forte.

critica_sistemica, substituicao_do_real_por_sistema e tipos análogos:
não uses estas categorias apenas porque o fragmento critica leis, sistemas, discursos, instituições, mercado, tributação, crenças coletivas ou respostas sociais.
Só as uses quando o texto sustentar realmente que há substituição do problema real por uma coerência sistémica autónoma, ou que o sistema passa a comandar a resposta contra a realidade descrita.
Se houver apenas crítica prática, crítica institucional, crítica moral, ou crítica vaga a uma resposta errada, não subas automaticamente para crítica sistémica forte.
Na dúvida, mantém:
- zona_provavel_percurso = "indefinida" ou outra zona mais prudente;
- familia_erro_provavel = null ou a família menos forte;
- erro_dominante_provavel = null;
- tipo_fragmento_provavel = null.

SCHEMA:
{json.dumps(schema_json, ensure_ascii=False)}

CONTEXTO_MACRO_MINIMO:
{json.dumps(contexto_macro_minimo, ensure_ascii=False)}

LABELS_TIPOS_FRAGMENTO_RESUMO:
{json.dumps(labels_tipos_resumo, ensure_ascii=False)}

LABELS_ERROS_RESUMO:
{json.dumps(labels_erros_resumo, ensure_ascii=False)}

FRAGMENTO:
{json.dumps(fragmento_payload, ensure_ascii=False)}

DEVOLVE APENAS UM OBJETO JSON VÁLIDO COMPATÍVEL COM O SCHEMA.
""".strip()


def construir_prompt_correcao_schema(
    schema_json: Dict[str, Any],
    fragmento_payload: Dict[str, Any],
    resposta_anterior: Any,
    erros_validacao: List[str],
) -> str:
    return f"""
Corrige a resposta anterior apenas para a tornar compatível com o schema.
Não reinterpretes desnecessariamente o fragmento.

Regras:
- mantém a leitura anterior sempre que possível;
- corrige apenas o necessário para aderir ao schema e aos enums;
- devolve apenas um objeto JSON válido.

SCHEMA:
{json.dumps(schema_json, ensure_ascii=False)}

FRAGMENTO:
{json.dumps(fragmento_payload, ensure_ascii=False)}

RESPOSTA_ANTERIOR:
{json.dumps(resposta_anterior, ensure_ascii=False)}

ERROS_DE_VALIDACAO:
{json.dumps(erros_validacao, ensure_ascii=False)}
""".strip()


def construir_prompt_arbitragem(
    schema_json: Dict[str, Any],
    fragmento_payload: Dict[str, Any],
    resposta_anterior: Any,
    motivos_reprompt: List[str],
) -> str:
    return f"""
Reavalia a classificação de cadência deste fragmento.

Objetivo:
resolver ambiguidade real, escolhendo a interpretação mais defensável e prudente.

Regras:
- o texto manda;
- prefere prudência a excesso interpretativo;
- se a zona ou o tipo não forem suficientemente sustentados, usa null ou "indefinida";
- se a confiança for baixa, assinala revisão humana;
- mantém compatibilidade exata com o schema.

Critérios de prudência adicionais:

funcao_cadencia_secundaria:
mantém null salvo quando o segundo papel estrutural for realmente claro e não apenas um aspeto lateral do principal.
Se a crítica de erro surgir apenas como dimensão lateral de uma formulação inicial, não a uses como função secundária.

centralidade:
não uses "exploratorio" só porque o texto é imperfeito ou oral.

tipo_fragmento_provavel:
usa null por defeito.
Só o preenchas quando o texto sustentar claramente esse tipo com formulação minimamente estável.
Se o fragmento for oral, hesitante, incompleto, ensaístico ou apenas aproximativo, usa null mesmo que exista semelhança parcial com um tipo conhecido.
Prefere perder tipificação a tipificar cedo demais.

zona_provavel_percurso:
não confundas afinidade temática vaga com pertença estrutural a uma zona.
Na dúvida, usa "indefinida".

estatuto_no_percurso:
não confundas afinidade temática com pertença estrutural ao percurso.
Na dúvida, prefere "solto_ainda_sem_encaixe".

familia_erro_provavel e erro_dominante_provavel:
não especifiques erro forte sem apoio textual claro.
Na dúvida, mantém erro_dominante_provavel = null e evita subir cedo para crítica sistémica ou categorias duras.

critica_sistemica e erro estrutural forte:
não subas para essas categorias sem apoio textual claro.
Crítica a sistema, lei, discurso ou instituição não basta por si só.
Na dúvida, prefere leitura mais fraca e deixa erro_dominante_provavel = null.

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


# ============================================================
# CHAMADA AO MODELO
# ============================================================


def _normalizar_schema_para_strict(schema: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(schema, dict):
        schema = dict(schema)

        if schema.get("type") == "object":
            schema.setdefault("additionalProperties", False)
            props = schema.get("properties") or {}
            schema["properties"] = {
                k: _normalizar_schema_para_strict(v) if isinstance(v, dict) else v
                for k, v in props.items()
            }

        elif schema.get("type") == "array" and isinstance(schema.get("items"), dict):
            schema["items"] = _normalizar_schema_para_strict(schema["items"])

        elif "anyOf" in schema and isinstance(schema["anyOf"], list):
            schema["anyOf"] = [
                _normalizar_schema_para_strict(x) if isinstance(x, dict) else x
                for x in schema["anyOf"]
            ]

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
    schema_strict = _normalizar_schema_para_strict(schema_obj)

    response = CLIENT.responses.create(
        model=model,
        input=prompt,
        store=False,
        text={
            "format": {
                "type": "json_schema",
                "name": "cadencia_fragmento",
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


def validar_resultado_schema(resultado: Dict[str, Any], schema_cadencia: Dict[str, Any]) -> ResultadoValidacao:
    erros: List[str] = []
    avisos: List[str] = []

    if not isinstance(resultado, dict):
        erros.append("resultado_nao_e_objeto")
        return ResultadoValidacao(False, erros, avisos)

    try:
        jsonschema.validate(instance=resultado, schema=schema_cadencia)
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
    cad = resultado.get("cadencia") or {}
    avisos: List[str] = []
    motivos: List[str] = []
    score = 0

    if cad.get("incide_sobre_erro") is False and cad.get("familia_erro_provavel") not in (None, "nao_aplicavel"):
        motivos.append("familia_erro_preenchida_sem_incidencia")
        score += 2

    if cad.get("estatuto_no_percurso") == "ponte_entre_zonas" and cad.get("ponte_entre_zonas") is False:
        motivos.append("estatuto_ponte_sem_flag_ponte")
        score += 2

    if cad.get("confianca_cadencia") == "baixa":
        score += 1
        if cad.get("necessita_revisao_humana") is False:
            avisos.append("confianca_baixa_sem_revisao_humana")

    if cad.get("zona_provavel_percurso") == "indefinida":
        score += 1
        motivos.append("zona_indefinida")

    if cad.get("incide_sobre_erro") is True and cad.get("erro_dominante_provavel") is None:
        score += 1
        avisos.append("erro_sem_dominante")

    if cad.get("funcao_cadencia_secundaria") is not None:
        score += 1
        avisos.append("dupla_funcao")

    if cad.get("tipo_fragmento_provavel") is not None and cad.get("confianca_cadencia") == "baixa":
        score += 1
        avisos.append("tipo_fragmento_fraco")

    return ResultadoCoerencia(
        ok=(score < 2),
        score_fragilidade=score,
        motivos_reprompt=motivos,
        avisos=avisos,
    )


# ============================================================
# DECISÃO DE REPROMPT
# ============================================================


def precisa_reprompt(valid_schema: ResultadoValidacao, valid_coerencia: ResultadoCoerencia) -> Tuple[bool, str]:
    if not valid_schema.ok:
        return True, "schema"
    if valid_coerencia.score_fragilidade >= 2:
        return True, "interpretacao"
    return False, ""


# ============================================================
# PIPELINE POR FRAGMENTO
# ============================================================


def extrair_cadencia_fragmento(
    fragmento_payload: Dict[str, Any],
    schema_cadencia: Dict[str, Any],
    contexto_macro_minimo: Dict[str, Any],
    labels_tipos_resumo: Dict[str, Any],
    labels_erros_resumo: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    logs: Dict[str, Any] = {
        "fragment_id": fragmento_payload.get("fragment_id"),
        "etapas": [],
    }

    print("   🤖 Extração principal...", flush=True)

    prompt = construir_prompt_extracao(
        schema_json=schema_cadencia,
        contexto_macro_minimo=contexto_macro_minimo,
        labels_tipos_resumo=labels_tipos_resumo,
        labels_erros_resumo=labels_erros_resumo,
        fragmento_payload=fragmento_payload,
    )
    logs["etapas"].append({"tipo": "extracao_principal"})
    if GUARDAR_PROMPTS:
        logs["prompt_extracao"] = prompt

    resposta = chamar_modelo_json_schema(prompt, schema_cadencia, MODELO_PRINCIPAL)
    valid_schema = validar_resultado_schema(resposta, schema_cadencia)

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
                schema_json=schema_cadencia,
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

            resposta2 = chamar_modelo_json_schema(prompt2, schema_cadencia, MODELO_PRINCIPAL)
            valid_schema2 = validar_resultado_schema(resposta2, schema_cadencia)

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
                schema_json=schema_cadencia,
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

            resposta3 = chamar_modelo_json_schema(prompt3, schema_cadencia, MODELO_ARBITRAGEM)
            valid_schema3 = validar_resultado_schema(resposta3, schema_cadencia)

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
                resposta_final = resposta3
                resposta_corrente = resposta3
                valid_coerencia = valid_coerencia3
                if valid_coerencia3.score_fragilidade < 2:
                    return resposta3, logs
            else:
                logs["etapas"].append(
                    {
                        "tipo": "falha_schema_pos_arbitragem",
                        "tentativa": tentativa,
                        "erros": valid_schema3.erros,
                    }
                )

        if resposta_final is not None:
            return resposta_final, logs

    return resposta if valid_schema.ok else None, logs


# ============================================================
# ESTADO INCREMENTAL
# ============================================================


def carregar_estado() -> Dict[str, Any]:
    if not FICHEIRO_ESTADO.exists():
        return {"versao_extrator": VERSAO_EXTRATOR, "fragmentos": {}}
    return carregar_json(FICHEIRO_ESTADO)


def deve_processar_fragmento(fragment_id: str, estado: Dict[str, Any]) -> bool:
    if FORCAR_REPROCESSAMENTO:
        return True

    info = (estado.get("fragmentos") or {}).get(fragment_id)
    if not info:
        return True

    if info.get("status") == "ok" and info.get("versao_extrator") == VERSAO_EXTRATOR:
        return False

    if info.get("status") == "falha" and not REPROCESSAR_FALHAS:
        return False

    return True


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================


def main() -> None:
    fragmentos_raw = carregar_json(FICHEIRO_FRAGMENTOS)
    fragmentos = garantir_lista_fragmentos(fragmentos_raw)

    schema_cadencia_root = carregar_json(FICHEIRO_SCHEMA)
    schema_cadencia = schema_cadencia_root.get("items", schema_cadencia_root)

    meta_percurso = carregar_json(FICHEIRO_META_PERCURSO)
    meta_indice = carregar_json_opcional(FICHEIRO_META_INDICE, {})
    indice_sequencial = carregar_json_opcional(FICHEIRO_INDICE_SEQUENCIAL, {})
    indice_argumentos = carregar_json_opcional(FICHEIRO_INDICE_ARGUMENTOS, {})
    argumentos_unificados = carregar_json_opcional(FICHEIRO_ARGUMENTOS_UNIFICADOS, [])
    labels_tipos = carregar_json(FICHEIRO_LABELS_TIPOS)
    labels_erros = carregar_json(FICHEIRO_LABELS_ERROS)

    contexto_macro_minimo = construir_contexto_macro_minimo(
        meta_percurso=meta_percurso,
        meta_indice=meta_indice,
        indice_sequencial=indice_sequencial,
        indice_argumentos=indice_argumentos,
        argumentos_unificados=argumentos_unificados,
    )
    labels_tipos_resumo = resumir_labels_tipos(labels_tipos)
    labels_erros_resumo = resumir_labels_erros(labels_erros)

    estado = carregar_estado()

    saida_existente: List[Dict[str, Any]] = (
        carregar_json(FICHEIRO_SAIDA) if FICHEIRO_SAIDA.exists() else []
    )
    saida_por_id = {
        x["fragment_id"]: x
        for x in saida_existente
        if isinstance(x, dict) and x.get("fragment_id")
    }

    logs_execucao: List[Dict[str, Any]] = []

    processados = 0
    ignorados = 0
    falhados = 0

    total_fragmentos = len(fragmentos)

    for idx, frag in enumerate(fragmentos, start=1):
        if LIMITE_FRAGMENTOS_TESTE is not None and idx > LIMITE_FRAGMENTOS_TESTE:
            break

        if not isinstance(frag, dict):
            falhados += 1
            print(f"   ❌ [{idx}/{total_fragmentos}] Fragmento inválido: não é objeto", flush=True)
            logs_execucao.append(
                {
                    "ordem_no_ficheiro_loop": idx,
                    "erro": "fragmento_nao_e_objeto",
                    "tipo_recebido": type(frag).__name__,
                }
            )
            print_parcial(processados, ignorados, falhados)
            continue

        fragment_id = (
            frag.get("fragment_id")
            or frag.get("fragmento_id")
            or frag.get("id_fragmento")
            or frag.get("id")
        )

        if not fragment_id:
            falhados += 1
            print(f"   ❌ [{idx}/{total_fragmentos}] Fragmento sem id", flush=True)
            logs_execucao.append(
                {
                    "ordem_no_ficheiro_loop": idx,
                    "erro": "fragmento_sem_id",
                    "chaves_disponiveis": list(frag.keys()),
                }
            )
            print_parcial(processados, ignorados, falhados)
            continue

        print(f"\n▶ [{idx}/{total_fragmentos}] {fragment_id}", flush=True)

        if not deve_processar_fragmento(fragment_id, estado):
            ignorados += 1
            print("   ⏭️ Ignorado (já processado)", flush=True)
            print_parcial(processados, ignorados, falhados)
            continue

        info_anterior = (estado.get("fragmentos") or {}).get(fragment_id, {})
        tentativas = int(info_anterior.get("tentativas", 0)) + 1

        payload = preparar_payload_fragmento(frag, idx)

        try:
            resultado, logs = extrair_cadencia_fragmento(
                fragmento_payload=payload,
                schema_cadencia=schema_cadencia,
                contexto_macro_minimo=contexto_macro_minimo,
                labels_tipos_resumo=labels_tipos_resumo,
                labels_erros_resumo=labels_erros_resumo,
            )
            logs_execucao.append(logs)

            if resultado is None:
                falhados += 1
                print("   ❌ Falhou: resultado_none", flush=True)
                estado.setdefault("fragmentos", {})[fragment_id] = {
                    "status": "falha",
                    "versao_extrator": VERSAO_EXTRATOR,
                    "tentativas": tentativas,
                    "ts": timestamp_utc(),
                    "last_error": "resultado_none",
                }
                print_parcial(processados, ignorados, falhados)
                continue

            cad = resultado.get("cadencia", {})
            print(
                f"   ✅ OK | função={cad.get('funcao_cadencia_principal')} | "
                f"zona={cad.get('zona_provavel_percurso')} | "
                f"confiança={cad.get('confianca_cadencia')}",
                flush=True,
            )

            saida_por_id[fragment_id] = resultado
            processados += 1
            estado.setdefault("fragmentos", {})[fragment_id] = {
                "status": "ok",
                "versao_extrator": VERSAO_EXTRATOR,
                "tentativas": tentativas,
                "ts": timestamp_utc(),
                "last_error": None,
            }
            print_parcial(processados, ignorados, falhados)

        except Exception as e:
            falhados += 1
            print(f"   ❌ Exceção: {e}", flush=True)
            logs_execucao.append(
                {
                    "fragment_id": fragment_id,
                    "erro": str(e),
                }
            )
            estado.setdefault("fragmentos", {})[fragment_id] = {
                "status": "falha",
                "versao_extrator": VERSAO_EXTRATOR,
                "tentativas": tentativas,
                "ts": timestamp_utc(),
                "last_error": str(e),
            }
            print_parcial(processados, ignorados, falhados)

    saida_final = [
        saida_por_id[k]
        for k in sorted(
            saida_por_id.keys(),
            key=lambda x: (
                saida_por_id[x].get("ordem_no_ficheiro", 10**9),
                x,
            ),
        )
    ]

    gravar_json(FICHEIRO_SAIDA, saida_final)
    gravar_json(FICHEIRO_ESTADO, estado)
    gravar_json(FICHEIRO_LOGS, logs_execucao)

    frageis = [
        x for x in saida_final
        if isinstance(x, dict)
        and isinstance(x.get("cadencia"), dict)
        and x["cadencia"].get("necessita_revisao_humana")
    ]
    gravar_json(FICHEIRO_FRAGEIS, frageis)

    relatorio = {
        "versao_extrator": VERSAO_EXTRATOR,
        "modelo_principal": MODELO_PRINCIPAL,
        "modelo_arbitragem": MODELO_ARBITRAGEM,
        "processados": processados,
        "ignorados": ignorados,
        "falhados": falhados,
        "total_fragmentos_input": len(fragmentos),
        "total_saida": len(saida_final),
        "total_frageis": len(frageis),
        "timestamp": timestamp_utc(),
    }
    gravar_json(FICHEIRO_RELATORIO, relatorio)

    print("=" * 90, flush=True)
    print(f"EXTRATOR DE CADÊNCIA | modelo={MODELO_PRINCIPAL} | versão={VERSAO_EXTRATOR}", flush=True)
    print(f"Fragmentos totais: {len(fragmentos)} | saída atual: {len(saida_final)}", flush=True)
    print("=" * 90, flush=True)
    print(f"Processados: {processados}", flush=True)
    print(f"Ignorados:  {ignorados}", flush=True)
    print(f"Falhados:   {falhados}", flush=True)
    print(f"Saída:      {FICHEIRO_SAIDA.name}", flush=True)
    print(f"Relatório:  {FICHEIRO_RELATORIO.name}", flush=True)
    print(f"Frágeis:    {FICHEIRO_FRAGEIS.name}", flush=True)
    print(f"Estado:     {FICHEIRO_ESTADO.name}", flush=True)
    print(f"Logs:       {FICHEIRO_LOGS.name}", flush=True)
    print("=" * 90, flush=True)


if __name__ == "__main__":
    main()