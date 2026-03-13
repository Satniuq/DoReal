import json
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# PATHS
# ============================================================

PASTA_SCRIPT = Path(__file__).resolve().parent
PASTA_INDICE = PASTA_SCRIPT.parent                  # .../13_Meta_Indice/indice
PASTA_META_INDICE = PASTA_INDICE.parent            # .../13_Meta_Indice
PASTA_META = PASTA_META_INDICE / "meta"
PASTA_ARGUMENTOS = PASTA_INDICE / "argumentos"
PASTA_CADENCIA = PASTA_META_INDICE / "cadência" / "04_extrator_q_faz_no_sistema"

CAMINHO_INDICE = PASTA_INDICE / "indice_sequencial.json"
CAMINHO_ARGUMENTOS = PASTA_ARGUMENTOS / "argumentos_unificados.json"
CAMINHO_META_PERCURSOS = PASTA_META / "meta_referencia_do_percurso.json"
CAMINHO_META_INDICE = PASTA_META / "meta_indice.json"
CAMINHO_TRATAMENTO_FRAGMENTOS = PASTA_CADENCIA / "tratamento_filosofico_fragmentos.json"
CAMINHO_INDICE_POR_PERCURSO = PASTA_INDICE / "indice_por_percurso.json"   # opcional

CAMINHO_SAIDA = PASTA_SCRIPT / "mapa_integral_do_indice.json"


# ============================================================
# UTILITÁRIOS BASE
# ============================================================

def carregar_json(caminho: Path) -> Any:
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def guardar_json(caminho: Path, dados: Any) -> None:
    with caminho.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def normalizar_texto(valor: Any, default: Optional[str] = None) -> Optional[str]:
    if valor is None:
        return default
    if isinstance(valor, str):
        valor = valor.strip()
        return valor if valor else default
    return valor


def normalizar_lista(valor: Any) -> List[Any]:
    if valor is None:
        return []
    if isinstance(valor, list):
        return valor
    return [valor]


def normalizar_dict(valor: Any) -> Dict[str, Any]:
    if isinstance(valor, dict):
        return valor
    return {}


def normalizar_int(valor: Any, default: int = 9999) -> int:
    try:
        return int(valor)
    except Exception:
        return default


def unique_preserve(seq: List[Any]) -> List[Any]:
    vistos = set()
    saida = []

    for x in seq:
        if isinstance(x, (dict, list)):
            chave = json.dumps(x, ensure_ascii=False, sort_keys=True)
        else:
            chave = str(x)

        if chave not in vistos:
            vistos.add(chave)
            saida.append(x)

    return saida


def exigir_ficheiros(*caminhos: Path) -> None:
    em_falta = [str(c) for c in caminhos if not c.exists()]
    if em_falta:
        raise FileNotFoundError(
            "Faltam ficheiros necessários:\n- " + "\n- ".join(em_falta)
        )


# ============================================================
# SCORE DE FRAGMENTOS
# ============================================================

def score_fragmento_para_exemplo(frag: Dict[str, Any]) -> int:
    score = 0

    grau = normalizar_texto(frag.get("grau_de_pertenca_ao_indice"))
    estado = normalizar_texto(frag.get("estado_argumentativo"))
    prioridade = normalizar_texto(frag.get("prioridade_de_aproveitamento"))
    reconstruivel = bool(frag.get("argumento_reconstruivel"))

    if grau == "forte":
        score += 5
    elif grau == "provavel":
        score += 3
    elif grau == "fraca":
        score += 1
    elif grau == "indefinida":
        score += 0

    if reconstruivel:
        score += 2

    if estado == "argumento_em_esboco":
        score += 2
    elif estado == "formulacao_pre_argumentativa":
        score += 1

    if prioridade == "alta":
        score += 2
    elif prioridade == "media":
        score += 1

    return score


# ============================================================
# ÍNDICE
# ============================================================

def extrair_lista_capitulos(indice: Any) -> List[Dict[str, Any]]:
    if isinstance(indice, list):
        return indice

    if isinstance(indice, dict):
        for chave in ("capitulos", "indice", "items", "entradas"):
            valor = indice.get(chave)
            if isinstance(valor, list):
                return valor

    raise ValueError("Não consegui encontrar a lista de capítulos em indice_sequencial.json.")


def construir_mapa_partes(capitulos: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    partes: Dict[str, Any] = {}
    ordem_partes: List[str] = []

    capitulos_ordenados = sorted(capitulos, key=lambda x: (x.get("ordem", 9999), x.get("id") or ""))

    for cap in capitulos_ordenados:
        parte_id = normalizar_texto(cap.get("parte"), "SEM_PARTE")

        if parte_id not in partes:
            partes[parte_id] = {
                "parte_id": parte_id,
                "ordem": None,
                "capitulos_ids": [],
            }
            ordem_partes.append(parte_id)

        partes[parte_id]["capitulos_ids"].append(cap.get("id"))

    for i, parte_id in enumerate(ordem_partes, start=1):
        partes[parte_id]["ordem"] = i

    return partes, ordem_partes


def construir_capitulos_por_id(capitulos: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {
        cap.get("id"): cap
        for cap in capitulos
        if cap.get("id")
    }


def construir_capitulos_por_percurso(capitulos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    por_percurso: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for cap in capitulos:
        percurso = normalizar_texto(cap.get("percurso_axial"))
        if percurso:
            por_percurso[percurso].append(cap)

    for percurso in por_percurso:
        por_percurso[percurso].sort(key=lambda x: (x.get("ordem", 9999), x.get("id") or ""))

    return por_percurso


# ============================================================
# ARGUMENTOS
# ============================================================

def agrupar_argumentos_por_capitulo(argumentos: List[Dict[str, Any]]) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Dict[str, Any]]]:
    por_capitulo: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    por_id: Dict[str, Dict[str, Any]] = {}

    for arg in argumentos:
        arg_id = normalizar_texto(arg.get("id"))
        capitulo = normalizar_texto(arg.get("capitulo"))

        if arg_id:
            por_id[arg_id] = arg

        if capitulo:
            por_capitulo[capitulo].append(arg)

    return por_capitulo, por_id


def construir_argumentos_do_capitulo(argumentos_capitulo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    saida = []

    for arg in argumentos_capitulo:
        estrutura = normalizar_dict(arg.get("estrutura_logica"))
        ligacoes = normalizar_dict(arg.get("ligacoes_narrativas"))

        saida.append(
            {
                "argumento_id": arg.get("id"),
                "conceito_alvo": arg.get("conceito_alvo"),
                "natureza": arg.get("natureza"),
                "tipo_de_necessidade": arg.get("tipo_de_necessidade"),
                "nivel_de_operacao": arg.get("nivel_de_operacao"),
                "fundamenta": normalizar_lista(arg.get("fundamenta")),
                "pressupostos_ontologicos": normalizar_lista(arg.get("pressupostos_ontologicos")),
                "outputs_instalados": normalizar_lista(arg.get("outputs_instalados")),
                "operacoes_chave": normalizar_lista(arg.get("operacoes_chave")),
                "premissas": normalizar_lista(estrutura.get("premissas")),
                "deducoes_necessarias": normalizar_lista(estrutura.get("deducoes_necessarias")),
                "conclusao": estrutura.get("conclusao"),
                "depende_de_argumentos": normalizar_lista(ligacoes.get("depende_de_argumentos")),
                "prepara_argumentos": normalizar_lista(ligacoes.get("prepara_argumentos")),
                "back_links": normalizar_lista(ligacoes.get("back_links")),
                "forward_links": normalizar_lista(ligacoes.get("forward_links")),
            }
        )

    return saida


def construir_transicoes_narrativas(
    argumentos_capitulo: List[Dict[str, Any]],
    argumentos_por_id: Dict[str, Dict[str, Any]],
    capitulo_por_id: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    depende_de = []
    prepara = []
    capitulos_anteriores = []
    capitulos_seguintes = []

    for arg in argumentos_capitulo:
        ligacoes = normalizar_dict(arg.get("ligacoes_narrativas"))

        for arg_id in normalizar_lista(ligacoes.get("depende_de_argumentos")):
            alvo = argumentos_por_id.get(arg_id)
            depende_de.append(
                {
                    "argumento_id": arg_id,
                    "capitulo_id": alvo.get("capitulo") if alvo else None,
                    "conceito_alvo": alvo.get("conceito_alvo") if alvo else None,
                }
            )

        for arg_id in normalizar_lista(ligacoes.get("prepara_argumentos")):
            alvo = argumentos_por_id.get(arg_id)
            prepara.append(
                {
                    "argumento_id": arg_id,
                    "capitulo_id": alvo.get("capitulo") if alvo else None,
                    "conceito_alvo": alvo.get("conceito_alvo") if alvo else None,
                }
            )

        for cap_id in normalizar_lista(ligacoes.get("back_links")):
            cap = capitulo_por_id.get(cap_id)
            capitulos_anteriores.append(
                {
                    "capitulo_id": cap_id,
                    "titulo": cap.get("titulo") if cap else None,
                    "parte_id": cap.get("parte") if cap else None,
                    "via_argumento": arg.get("id"),
                }
            )

        for cap_id in normalizar_lista(ligacoes.get("forward_links")):
            cap = capitulo_por_id.get(cap_id)
            capitulos_seguintes.append(
                {
                    "capitulo_id": cap_id,
                    "titulo": cap.get("titulo") if cap else None,
                    "parte_id": cap.get("parte") if cap else None,
                    "via_argumento": arg.get("id"),
                }
            )

    return {
        "depende_de_argumentos": unique_preserve(depende_de),
        "prepara_argumentos": unique_preserve(prepara),
        "capitulos_anteriores_referidos": unique_preserve(capitulos_anteriores),
        "capitulos_seguintes_referidos": unique_preserve(capitulos_seguintes),
    }


# ============================================================
# FRAGMENTOS TRATADOS
# ============================================================

def achatar_fragmento_tratado(item: Dict[str, Any]) -> Dict[str, Any]:
    raiz = normalizar_dict(item.get("tratamento_filosofico_fragmento"))
    pos = normalizar_dict(raiz.get("posicao_no_indice"))
    pot = normalizar_dict(raiz.get("potencial_argumentativo"))
    dest = normalizar_dict(raiz.get("destino_editorial"))
    rel = normalizar_dict(raiz.get("relacoes_no_sistema"))
    aval = normalizar_dict(raiz.get("avaliacao_global"))

    return {
        "fragment_id": item.get("fragment_id"),
        "origem_id": item.get("origem_id"),
        "ordem_no_ficheiro": item.get("ordem_no_ficheiro"),

        "explicacao_textual_do_que_o_fragmento_tenta_fazer": raiz.get("explicacao_textual_do_que_o_fragmento_tenta_fazer"),
        "trabalho_no_sistema": raiz.get("trabalho_no_sistema"),
        "trabalho_no_sistema_secundario": raiz.get("trabalho_no_sistema_secundario"),
        "descricao_funcional_curta": raiz.get("descricao_funcional_curta"),
        "problema_filosofico_central": raiz.get("problema_filosofico_central"),
        "problemas_filosoficos_associados": normalizar_lista(raiz.get("problemas_filosoficos_associados")),
        "tipo_de_problema": raiz.get("tipo_de_problema"),

        "parte_id": pos.get("parte_id"),
        "capitulo_id": pos.get("capitulo_id"),
        "capitulo_titulo": pos.get("capitulo_titulo"),
        "subcapitulo_ou_zona_interna": pos.get("subcapitulo_ou_zona_interna"),
        "argumento_canonico_relacionado": pos.get("argumento_canonico_relacionado"),
        "argumentos_canonicos_associados": normalizar_lista(pos.get("argumentos_canonicos_associados")),
        "grau_de_pertenca_ao_indice": pos.get("grau_de_pertenca_ao_indice"),
        "modo_de_pertenca": pos.get("modo_de_pertenca"),
        "justificacao_de_posicao_no_indice": pos.get("justificacao_de_posicao_no_indice"),

        "estado_argumentativo": pot.get("estado_argumentativo"),
        "premissas_implicitas": normalizar_lista(pot.get("premissas_implicitas")),
        "premissa_central_reconstruida": pot.get("premissa_central_reconstruida"),
        "conclusao_visada": pot.get("conclusao_visada"),
        "forma_de_inferencia": pot.get("forma_de_inferencia"),
        "forca_logica_estimada": pot.get("forca_logica_estimada"),
        "argumento_reconstruivel": pot.get("argumento_reconstruivel"),
        "necessita_reconstrucao_forte": pot.get("necessita_reconstrucao_forte"),
        "observacoes_argumentativas": pot.get("observacoes_argumentativas"),

        "depende_de_conceitos": normalizar_lista(rel.get("depende_de_conceitos")),
        "mobiliza_operacoes": normalizar_lista(rel.get("mobiliza_operacoes")),
        "regimes_envolvidos": normalizar_lista(rel.get("regimes_envolvidos")),
        "percursos_envolvidos": normalizar_lista(rel.get("percursos_envolvidos")),
        "abre_para": normalizar_lista(rel.get("abre_para")),
        "corrige": normalizar_lista(rel.get("corrige")),
        "prepara": normalizar_lista(rel.get("prepara")),
        "pressupoe": normalizar_lista(rel.get("pressupoe")),
        "entra_em_tensao_com": normalizar_lista(rel.get("entra_em_tensao_com")),

        "destino_editorial_fino": dest.get("destino_editorial_fino"),
        "papel_editorial_primario": dest.get("papel_editorial_primario"),
        "papel_editorial_secundario": dest.get("papel_editorial_secundario"),
        "prioridade_de_revisao": dest.get("prioridade_de_revisao"),
        "prioridade_de_aproveitamento": dest.get("prioridade_de_aproveitamento"),
        "requer_reescrita": dest.get("requer_reescrita"),
        "requer_densificacao": dest.get("requer_densificacao"),
        "requer_formalizacao_logica": dest.get("requer_formalizacao_logica"),
        "observacoes_editoriais": dest.get("observacoes_editoriais"),

        "densidade_filosofica": aval.get("densidade_filosofica"),
        "clareza_atual": aval.get("clareza_atual"),
        "grau_de_estabilizacao": aval.get("grau_de_estabilizacao"),
        "risco_de_ma_interpretacao": aval.get("risco_de_ma_interpretacao"),
        "confianca_tratamento_filosofico": aval.get("confianca_tratamento_filosofico"),
        "necessita_revisao_humana_filosofica": aval.get("necessita_revisao_humana_filosofica"),

        "tratamento_filosofico_fragmento_raw": raiz,
    }


def agrupar_fragmentos_por_capitulo(fragmentos_tratados: List[Dict[str, Any]]) -> Tuple[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]]:
    por_capitulo: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    achatados: List[Dict[str, Any]] = []

    for item in fragmentos_tratados:
        frag = achatar_fragmento_tratado(item)
        achatados.append(frag)

        capitulo = normalizar_texto(frag.get("capitulo_id"))
        if capitulo:
            por_capitulo[capitulo].append(frag)

    return por_capitulo, achatados


# ============================================================
# APOIO POR PERCURSO (OPCIONAL)
# ============================================================

def _parece_id_capitulo(valor: Any) -> bool:
    return isinstance(valor, str) and valor.startswith("CAP_")


def _extrair_id_capitulo_de_item(item: Any) -> Optional[str]:
    if _parece_id_capitulo(item):
        return item

    if isinstance(item, dict):
        for chave in ("id", "capitulo_id"):
            valor = item.get(chave)
            if _parece_id_capitulo(valor):
                return valor

    return None


def _recolher_caps_ids_recursivo(valor: Any) -> List[str]:
    encontrados: List[str] = []

    if isinstance(valor, list):
        for item in valor:
            cap_id = _extrair_id_capitulo_de_item(item)
            if cap_id:
                encontrados.append(cap_id)

            if isinstance(item, (dict, list)):
                encontrados.extend(_recolher_caps_ids_recursivo(item))

    elif isinstance(valor, dict):
        for chave, subvalor in valor.items():
            if chave in (
                "caps_ids",
                "capitulos_ids",
                "capítulos_ids",
                "capitulos",
                "capítulos",
                "caps",
                "axial",
                "participante",
                "directo",
                "direto",
                "com_pressupostos",
            ):
                encontrados.extend(_recolher_caps_ids_recursivo(subvalor))
            else:
                cap_id = _extrair_id_capitulo_de_item(subvalor)
                if cap_id:
                    encontrados.append(cap_id)
                elif isinstance(subvalor, (dict, list)):
                    encontrados.extend(_recolher_caps_ids_recursivo(subvalor))

    return unique_preserve([x for x in encontrados if _parece_id_capitulo(x)])


def _procurar_bloco_percursos(indice_por_percurso: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(indice_por_percurso, dict):
        return {}

    percursos = indice_por_percurso.get("percursos")
    if isinstance(percursos, dict):
        return percursos

    candidatos = {}
    for chave, valor in indice_por_percurso.items():
        if not isinstance(valor, dict):
            continue

        if chave.startswith("P_"):
            candidatos[chave] = valor
            continue

        meta = valor.get("meta")
        directo = valor.get("directo")
        com_pressupostos = valor.get("com_pressupostos")

        if isinstance(meta, dict) or isinstance(directo, dict) or isinstance(com_pressupostos, dict):
            candidatos[chave] = valor

    return candidatos


def construir_apoio_por_percurso(indice_por_percurso: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not isinstance(indice_por_percurso, dict):
        return {}

    percursos = _procurar_bloco_percursos(indice_por_percurso)
    if not isinstance(percursos, dict):
        return {}

    saida: Dict[str, Dict[str, Any]] = {}

    for percurso_id, bloco in percursos.items():
        if not isinstance(bloco, dict):
            continue

        resumo = normalizar_dict(bloco.get("resumo"))

        meta = normalizar_dict(bloco.get("meta"))
        directo = normalizar_dict(bloco.get("directo"))
        com_pressupostos = normalizar_dict(bloco.get("com_pressupostos"))

        caps_ids = []
        caps_ids.extend(_recolher_caps_ids_recursivo(directo.get("caps_ids")))
        caps_ids.extend(_recolher_caps_ids_recursivo(directo.get("caps")))
        caps_ids.extend(_recolher_caps_ids_recursivo(directo.get("axial")))
        caps_ids.extend(_recolher_caps_ids_recursivo(directo.get("participante")))
        caps_ids.extend(_recolher_caps_ids_recursivo(com_pressupostos.get("caps")))
        caps_ids.extend(_recolher_caps_ids_recursivo(bloco))
        caps_ids = unique_preserve(caps_ids)

        percursos_base = normalizar_lista(com_pressupostos.get("percursos_base"))
        if not percursos_base:
            percursos_base = normalizar_lista(bloco.get("pressupostos_fecho"))
        if not percursos_base:
            percursos_base = normalizar_lista(meta.get("pressupoe_percursos"))

        # remover o próprio percurso e filtrar apenas ids válidos de percurso
        percursos_base = unique_preserve([
            p for p in percursos_base
            if isinstance(p, str) and p.startswith("P_") and p != percurso_id
        ])

        if not resumo:
            resumo = {
                "tipo_instancia": meta.get("tipo_instancia"),
                "n_caps_diretos": len(unique_preserve(_recolher_caps_ids_recursivo(directo))),
                "n_caps_com_pressupostos": len(unique_preserve(_recolher_caps_ids_recursivo(com_pressupostos))),
            }

        saida[percurso_id] = {
            "caps_ids": caps_ids,
            "resumo": resumo,
            "percursos_base": percursos_base,
        }

    return saida


# ============================================================
# INFERÊNCIAS
# ============================================================

def inferir_capitulos_pressupostos(
    capitulo_atual: Dict[str, Any],
    meta_percursos: Dict[str, Any],
    capitulos_por_percurso: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    percurso = normalizar_texto(capitulo_atual.get("percurso_axial"))
    ordem_atual = capitulo_atual.get("ordem", 9999)

    if not percurso:
        return []

    meta = meta_percursos.get(percurso)
    if not isinstance(meta, dict):
        return []

    percursos_pressupostos = normalizar_lista(meta.get("pressupoe_percursos"))
    candidatos = []

    for percurso_pressuposto in percursos_pressupostos:
        for cap in capitulos_por_percurso.get(percurso_pressuposto, []):
            if cap.get("ordem", 9999) < ordem_atual:
                candidatos.append(
                    {
                        "capitulo_id": cap.get("id"),
                        "titulo": cap.get("titulo"),
                        "parte_id": cap.get("parte"),
                        "ordem": cap.get("ordem"),
                        "via_percurso": percurso_pressuposto,
                    }
                )

    candidatos.sort(key=lambda x: (x.get("ordem", 9999), x.get("capitulo_id") or ""))
    return unique_preserve(candidatos)


def inferir_capitulos_seguintes_preparados(
    capitulo_atual: Dict[str, Any],
    argumentos_capitulo: List[Dict[str, Any]],
    capitulo_por_id: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    candidatos = []

    capitulo_atual_id = normalizar_texto(capitulo_atual.get("id"))
    ordem_atual = normalizar_int(capitulo_atual.get("ordem"))

    for arg in argumentos_capitulo:
        ligacoes = normalizar_dict(arg.get("ligacoes_narrativas"))

        for cap_id in normalizar_lista(ligacoes.get("forward_links")):
            if not isinstance(cap_id, str):
                continue

            # filtro 1: excluir auto-ligação
            if cap_id == capitulo_atual_id:
                continue

            cap = capitulo_por_id.get(cap_id)
            if not cap:
                continue

            ordem_destino = normalizar_int(cap.get("ordem"))

            # filtro 2: só aceitar capítulos posteriores
            if ordem_destino <= ordem_atual:
                continue

            candidatos.append(
                {
                    "capitulo_id": cap_id,
                    "titulo": cap.get("titulo"),
                    "parte_id": cap.get("parte"),
                    "ordem": cap.get("ordem"),
                    "via_argumento": arg.get("id"),
                }
            )

    candidatos.sort(key=lambda x: (x.get("ordem", 9999), x.get("capitulo_id") or ""))
    return unique_preserve(candidatos)


# ============================================================
# RESUMOS DE FRAGMENTOS
# ============================================================

def construir_subzonas_provisorias(fragmentos_capitulo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grupos = defaultdict(
        lambda: {
            "subzona": None,
            "total_fragmentos": 0,
            "fortes": 0,
            "provaveis": 0,
            "fracos": 0,
            "indefinidos": 0,
            "argumentos_canonicos": set(),
            "trabalhos_no_sistema": set(),
            "destinos_editoriais_finos": set(),
            "fragmentos_exemplo": [],
        }
    )

    for frag in fragmentos_capitulo:
        subzona = normalizar_texto(frag.get("subcapitulo_ou_zona_interna"), "SEM_SUBZONA")
        grau = normalizar_texto(frag.get("grau_de_pertenca_ao_indice"))
        argumento = normalizar_texto(frag.get("argumento_canonico_relacionado"))
        trabalho = normalizar_texto(frag.get("trabalho_no_sistema"))
        destino_fino = normalizar_texto(frag.get("destino_editorial_fino"))

        grupo = grupos[subzona]
        grupo["subzona"] = subzona
        grupo["total_fragmentos"] += 1

        if grau == "forte":
            grupo["fortes"] += 1
        elif grau == "provavel":
            grupo["provaveis"] += 1
        elif grau == "fraca":
            grupo["fracos"] += 1
        else:
            grupo["indefinidos"] += 1

        if argumento:
            grupo["argumentos_canonicos"].add(argumento)

        if trabalho:
            grupo["trabalhos_no_sistema"].add(trabalho)

        if destino_fino:
            grupo["destinos_editoriais_finos"].add(destino_fino)

        grupo["fragmentos_exemplo"].append(
            {
                "fragment_id": frag.get("fragment_id"),
                "grau_de_pertenca_ao_indice": frag.get("grau_de_pertenca_ao_indice"),
                "argumento_canonico_relacionado": frag.get("argumento_canonico_relacionado"),
                "descricao_funcional_curta": frag.get("descricao_funcional_curta"),
                "trabalho_no_sistema": frag.get("trabalho_no_sistema"),
                "score": score_fragmento_para_exemplo(frag),
            }
        )

    resultado = []

    for grupo in grupos.values():
        grupo["argumentos_canonicos"] = sorted(grupo["argumentos_canonicos"])
        grupo["trabalhos_no_sistema"] = sorted(grupo["trabalhos_no_sistema"])
        grupo["destinos_editoriais_finos"] = sorted(grupo["destinos_editoriais_finos"])

        grupo["fragmentos_exemplo"].sort(
            key=lambda x: (
                -x["score"],
                0 if x["grau_de_pertenca_ao_indice"] == "forte" else 1,
                x["fragment_id"] or "",
            )
        )
        grupo["fragmentos_exemplo"] = grupo["fragmentos_exemplo"][:8]
        resultado.append(grupo)

    resultado.sort(
        key=lambda x: (
            -x["fortes"],
            -x["provaveis"],
            -x["fracos"],
            -x["total_fragmentos"],
            x["subzona"],
        )
    )

    return resultado


def construir_fragmentos_prioritarios_resumidos(fragmentos_capitulo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    lista = []

    for frag in fragmentos_capitulo:
        lista.append(
            {
                "fragment_id": frag.get("fragment_id"),
                "origem_id": frag.get("origem_id"),
                "ordem_no_ficheiro": frag.get("ordem_no_ficheiro"),
                "grau_de_pertenca_ao_indice": frag.get("grau_de_pertenca_ao_indice"),
                "modo_de_pertenca": frag.get("modo_de_pertenca"),
                "argumento_canonico_relacionado": frag.get("argumento_canonico_relacionado"),
                "estado_argumentativo": frag.get("estado_argumentativo"),
                "argumento_reconstruivel": frag.get("argumento_reconstruivel"),
                "trabalho_no_sistema": frag.get("trabalho_no_sistema"),
                "descricao_funcional_curta": frag.get("descricao_funcional_curta"),
                "subcapitulo_ou_zona_interna": frag.get("subcapitulo_ou_zona_interna"),
                "destino_editorial_fino": frag.get("destino_editorial_fino"),
                "prioridade_de_aproveitamento": frag.get("prioridade_de_aproveitamento"),
                "score": score_fragmento_para_exemplo(frag),
            }
        )

    lista.sort(
        key=lambda x: (
            -x["score"],
            0 if x["grau_de_pertenca_ao_indice"] == "forte" else 1,
            x["ordem_no_ficheiro"] if x["ordem_no_ficheiro"] is not None else 999999,
            x["fragment_id"] or "",
        )
    )

    return lista[:20]


def construir_resumo_fragmentos(fragmentos_capitulo: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "total_fragmentos_prioritarios": len(fragmentos_capitulo),
        "fortes": sum(1 for f in fragmentos_capitulo if f.get("grau_de_pertenca_ao_indice") == "forte"),
        "provaveis": sum(1 for f in fragmentos_capitulo if f.get("grau_de_pertenca_ao_indice") == "provavel"),
        "fracos": sum(1 for f in fragmentos_capitulo if f.get("grau_de_pertenca_ao_indice") == "fraca"),
        "indefinidos": sum(1 for f in fragmentos_capitulo if f.get("grau_de_pertenca_ao_indice") == "indefinida"),
        "reconstruiveis": sum(1 for f in fragmentos_capitulo if f.get("argumento_reconstruivel")),
        "argumentos_em_esboco": sum(1 for f in fragmentos_capitulo if f.get("estado_argumentativo") == "argumento_em_esboco"),
        "formulacoes_pre_argumentativas": sum(1 for f in fragmentos_capitulo if f.get("estado_argumentativo") == "formulacao_pre_argumentativa"),
        "prioridade_alta": sum(1 for f in fragmentos_capitulo if f.get("prioridade_de_aproveitamento") == "alta"),
        "prioridade_media": sum(1 for f in fragmentos_capitulo if f.get("prioridade_de_aproveitamento") == "media"),
    }


def construir_resumo_cobertura(
    capitulos: List[Dict[str, Any]],
    argumentos_por_capitulo: Dict[str, List[Dict[str, Any]]],
    fragmentos_por_capitulo: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    capitulos_sem_argumentos = []
    capitulos_sem_fragmentos = []
    capitulos_com_cobertura_forte = []
    capitulos_com_cobertura_apenas_provavel = []

    for cap in capitulos:
        cap_id = cap.get("id")
        args = argumentos_por_capitulo.get(cap_id, [])
        frags = fragmentos_por_capitulo.get(cap_id, [])

        fortes = sum(1 for f in frags if f.get("grau_de_pertenca_ao_indice") == "forte")
        provaveis = sum(1 for f in frags if f.get("grau_de_pertenca_ao_indice") == "provavel")

        if not args:
            capitulos_sem_argumentos.append(cap_id)

        if not frags:
            capitulos_sem_fragmentos.append(cap_id)

        if fortes > 0:
            capitulos_com_cobertura_forte.append(cap_id)
        elif provaveis > 0:
            capitulos_com_cobertura_apenas_provavel.append(cap_id)

    return {
        "capitulos_sem_argumentos": capitulos_sem_argumentos,
        "capitulos_sem_fragmentos": capitulos_sem_fragmentos,
        "capitulos_com_cobertura_forte": capitulos_com_cobertura_forte,
        "capitulos_com_cobertura_apenas_provavel": capitulos_com_cobertura_apenas_provavel,
        "total_capitulos_sem_argumentos": len(capitulos_sem_argumentos),
        "total_capitulos_sem_fragmentos": len(capitulos_sem_fragmentos),
        "total_capitulos_com_cobertura_forte": len(capitulos_com_cobertura_forte),
        "total_capitulos_com_cobertura_apenas_provavel": len(capitulos_com_cobertura_apenas_provavel),
    }


# ============================================================
# MAPA DE CAPÍTULO E MAPA GLOBAL
# ============================================================

def construir_mapa_de_capitulo(
    capitulo: Dict[str, Any],
    argumentos_capitulo: List[Dict[str, Any]],
    fragmentos_capitulo: List[Dict[str, Any]],
    meta_percursos: Dict[str, Any],
    capitulos_por_percurso: Dict[str, List[Dict[str, Any]]],
    argumentos_por_id: Dict[str, Dict[str, Any]],
    capitulo_por_id: Dict[str, Dict[str, Any]],
    apoio_por_percurso: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    percurso_id = capitulo.get("percurso_axial")
    transicoes = construir_transicoes_narrativas(argumentos_capitulo, argumentos_por_id, capitulo_por_id)
    apoio_percurso = (apoio_por_percurso or {}).get(percurso_id, {})

    return {
        "capitulo_id": capitulo.get("id"),
        "titulo": capitulo.get("titulo"),
        "parte_id": capitulo.get("parte"),
        "ordem": capitulo.get("ordem"),
        "nivel": capitulo.get("nivel"),
        "campos": normalizar_lista(capitulo.get("campos")),
        "regime_principal": capitulo.get("regime_principal"),
        "regimes_secundarios": normalizar_lista(capitulo.get("regimes_secundarios")),
        "percurso_axial": percurso_id,
        "percursos_participantes": normalizar_lista(capitulo.get("percursos_participantes")),
        "estado_instalacao": capitulo.get("estado_instalacao"),
        "observacoes": normalizar_lista(capitulo.get("observacoes")),

        "apoio_percurso": {
            "caps_ids_no_percurso": apoio_percurso.get("caps_ids", []),
            "percursos_base": apoio_percurso.get("percursos_base", []),
            "resumo": apoio_percurso.get("resumo", {}),
        },

        "argumentos_canonicos": construir_argumentos_do_capitulo(argumentos_capitulo),
        "transicoes_narrativas": transicoes,

        "capitulos_anteriores_pressupostos": inferir_capitulos_pressupostos(
            capitulo_atual=capitulo,
            meta_percursos=meta_percursos,
            capitulos_por_percurso=capitulos_por_percurso,
        ),

        "capitulos_seguintes_preparados": inferir_capitulos_seguintes_preparados(
            capitulo_atual=capitulo,
            argumentos_capitulo=argumentos_capitulo,
            capitulo_por_id=capitulo_por_id,
        ),

        "subzonas_provisorias": construir_subzonas_provisorias(fragmentos_capitulo),
        "resumo_fragmentos_prioritarios": construir_resumo_fragmentos(fragmentos_capitulo),
        "fragmentos_prioritarios_exemplo": construir_fragmentos_prioritarios_resumidos(fragmentos_capitulo),
    }


def construir_mapa_global(
    meta_indice: Dict[str, Any],
    meta_percursos: Dict[str, Any],
    partes: Dict[str, Any],
    ordem_partes: List[str],
    capitulos: List[Dict[str, Any]],
    argumentos: List[Dict[str, Any]],
    fragmentos_achatados: List[Dict[str, Any]],
) -> Dict[str, Any]:
    meta_indice_real = meta_indice.get("meta_indice") if isinstance(meta_indice, dict) else meta_indice

    return {
        "meta_indice": meta_indice_real,
        "percursos_disponiveis": meta_percursos,
        "partes": [
            {
                "parte_id": parte_id,
                "ordem": partes[parte_id]["ordem"],
                "capitulos_ids": partes[parte_id]["capitulos_ids"],
            }
            for parte_id in ordem_partes
        ],
        "total_capitulos": len(capitulos),
        "total_argumentos": len(argumentos),
        "total_fragmentos_tratados": len(fragmentos_achatados),
        "total_fragmentos_fortes": sum(1 for f in fragmentos_achatados if f.get("grau_de_pertenca_ao_indice") == "forte"),
        "total_fragmentos_provaveis": sum(1 for f in fragmentos_achatados if f.get("grau_de_pertenca_ao_indice") == "provavel"),
        "total_fragmentos_fracos": sum(1 for f in fragmentos_achatados if f.get("grau_de_pertenca_ao_indice") == "fraca"),
        "total_fragmentos_indefinidos": sum(1 for f in fragmentos_achatados if f.get("grau_de_pertenca_ao_indice") == "indefinida"),
        "total_fragmentos_reconstruiveis": sum(1 for f in fragmentos_achatados if f.get("argumento_reconstruivel")),
    }


# ============================================================
# OUTPUT
# ============================================================

def imprimir_resumo(mapa: Dict[str, Any]) -> None:
    print("=" * 100)
    print("MAPA INTEGRAL DO ÍNDICE")
    print("=" * 100)
    print(f"Total de partes: {len(mapa['estrutura_global']['partes'])}")
    print(f"Total de capítulos: {len(mapa['capitulos'])}")
    print(f"Total de argumentos: {mapa['estrutura_global']['total_argumentos']}")
    print(f"Total de fragmentos tratados: {mapa['estrutura_global']['total_fragmentos_tratados']}")
    print("-" * 100)
    print("Primeiros 10 capítulos:")

    for cap in mapa["capitulos"][:10]:
        print(
            f"{cap['ordem']:02d}. {cap['capitulo_id']} | "
            f"{cap['titulo']} | "
            f"{cap['parte_id']} | "
            f"args={len(cap['argumentos_canonicos'])} | "
            f"subzonas={len(cap['subzonas_provisorias'])} | "
            f"frags={cap['resumo_fragmentos_prioritarios']['total_fragmentos_prioritarios']}"
        )

    print("-" * 100)
    print("Cobertura:")
    print(f"- capítulos sem argumentos: {mapa['resumo_cobertura']['total_capitulos_sem_argumentos']}")
    print(f"- capítulos sem fragmentos: {mapa['resumo_cobertura']['total_capitulos_sem_fragmentos']}")
    print(f"- capítulos com cobertura forte: {mapa['resumo_cobertura']['total_capitulos_com_cobertura_forte']}")
    print(f"- capítulos com cobertura apenas provável: {mapa['resumo_cobertura']['total_capitulos_com_cobertura_apenas_provavel']}")
    print("-" * 100)
    print(f"Ficheiro gerado: {CAMINHO_SAIDA}")
    print("=" * 100)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    exigir_ficheiros(
        CAMINHO_INDICE,
        CAMINHO_ARGUMENTOS,
        CAMINHO_META_PERCURSOS,
        CAMINHO_META_INDICE,
        CAMINHO_TRATAMENTO_FRAGMENTOS,
    )

    indice = carregar_json(CAMINHO_INDICE)
    argumentos = carregar_json(CAMINHO_ARGUMENTOS)
    meta_percursos = carregar_json(CAMINHO_META_PERCURSOS)
    meta_indice = carregar_json(CAMINHO_META_INDICE)
    fragmentos_tratados = carregar_json(CAMINHO_TRATAMENTO_FRAGMENTOS)

    indice_por_percurso = (
        carregar_json(CAMINHO_INDICE_POR_PERCURSO)
        if CAMINHO_INDICE_POR_PERCURSO.exists()
        else None
    )

    capitulos = extrair_lista_capitulos(indice)
    capitulos = sorted(capitulos, key=lambda x: (x.get("ordem", 9999), x.get("id") or ""))

    partes, ordem_partes = construir_mapa_partes(capitulos)
    capitulo_por_id = construir_capitulos_por_id(capitulos)
    capitulos_por_percurso = construir_capitulos_por_percurso(capitulos)
    argumentos_por_capitulo, argumentos_por_id = agrupar_argumentos_por_capitulo(argumentos)
    fragmentos_por_capitulo, fragmentos_achatados = agrupar_fragmentos_por_capitulo(fragmentos_tratados)
    apoio_por_percurso = construir_apoio_por_percurso(indice_por_percurso)

    mapa = {
        "fontes": {
            "indice_sequencial": str(CAMINHO_INDICE),
            "argumentos_unificados": str(CAMINHO_ARGUMENTOS),
            "meta_referencia_do_percurso": str(CAMINHO_META_PERCURSOS),
            "meta_indice": str(CAMINHO_META_INDICE),
            "tratamento_filosofico_fragmentos": str(CAMINHO_TRATAMENTO_FRAGMENTOS),
            "indice_por_percurso": str(CAMINHO_INDICE_POR_PERCURSO) if indice_por_percurso is not None else None,
        },
        "estrutura_global": construir_mapa_global(
            meta_indice=meta_indice,
            meta_percursos=meta_percursos,
            partes=partes,
            ordem_partes=ordem_partes,
            capitulos=capitulos,
            argumentos=argumentos,
            fragmentos_achatados=fragmentos_achatados,
        ),
        "resumo_cobertura": construir_resumo_cobertura(
            capitulos=capitulos,
            argumentos_por_capitulo=argumentos_por_capitulo,
            fragmentos_por_capitulo=fragmentos_por_capitulo,
        ),
        "capitulos": [],
    }

    for capitulo in capitulos:
        cap_id = capitulo.get("id")
        argumentos_capitulo = argumentos_por_capitulo.get(cap_id, [])
        fragmentos_capitulo = fragmentos_por_capitulo.get(cap_id, [])

        mapa["capitulos"].append(
            construir_mapa_de_capitulo(
                capitulo=capitulo,
                argumentos_capitulo=argumentos_capitulo,
                fragmentos_capitulo=fragmentos_capitulo,
                meta_percursos=meta_percursos,
                capitulos_por_percurso=capitulos_por_percurso,
                argumentos_por_id=argumentos_por_id,
                capitulo_por_id=capitulo_por_id,
                apoio_por_percurso=apoio_por_percurso,
            )
        )

    guardar_json(CAMINHO_SAIDA, mapa)
    imprimir_resumo(mapa)


if __name__ == "__main__":
    main()