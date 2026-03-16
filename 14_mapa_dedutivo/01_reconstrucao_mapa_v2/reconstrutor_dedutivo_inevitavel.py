from __future__ import annotations

import ast
import json
import math
import re
from collections import Counter, defaultdict, deque
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


# ============================================================
# CONFIGURAÇÃO
# ============================================================

# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA_BASE = Path(__file__).resolve().parent
PASTA_MAPA = PASTA_BASE.parent
RAIZ_PROJETO = PASTA_MAPA.parent

PASTA_META_INDICE = RAIZ_PROJETO / "13_Meta_Indice"
PASTA_INDICE = PASTA_META_INDICE / "indice"
PASTA_ARGUMENTOS = PASTA_INDICE / "argumentos"
PASTA_DADOS_BASE = PASTA_META_INDICE / "dados_base"
PASTA_META = PASTA_META_INDICE / "meta"
PASTA_CADENCIA = PASTA_META_INDICE / "cadência" / "04_extrator_q_faz_no_sistema"

FICHEIROS = {
    "mapa": PASTA_MAPA / "02_mapa_dedutivo_arquitetura_fragmentos.json",
    "revisao": PASTA_MAPA / "revisao_estrutural_do_mapa.json",
    "indice_por_percurso": PASTA_INDICE / "indice_por_percurso.json",
    "argumentos": PASTA_ARGUMENTOS / "argumentos_unificados.json",
    "conceitos": PASTA_DADOS_BASE / "todos_os_conceitos.json",
    "operacoes": PASTA_DADOS_BASE / "operacoes.json",
    "meta_percurso": PASTA_META / "meta_referencia_do_percurso.json",
    "meta_indice": PASTA_META / "meta_indice.json",
    "tratamento_fragmentos": PASTA_CADENCIA / "tratamento_filosofico_fragmentos.json",
    "impacto_fragmentos": PASTA_MAPA / "impacto_fragmentos_no_mapa.json",
    "impacto_relatorio": PASTA_MAPA / "impacto_fragmentos_no_mapa_relatorio_validacao.json",
    "fecho_p25_p30": PASTA_BASE / "fecho_manual_corredor_P25_P30.json",
    "fecho_p33_p37": PASTA_BASE / "fecho_manual_corredor_P33_P37.json",
    "fecho_p42_p48": PASTA_BASE / "fecho_manual_corredor_P42_P48.json",
    "fecho_p50": PASTA_BASE / "fecho_manual_corredor_P50.json",
}

SAIDA_MAPA = PASTA_BASE / "mapa_dedutivo_reconstrucao_inevitavel_v3.json"
SAIDA_RELATORIO = PASTA_BASE / "relatorio_reconstrucao_inevitavel_v3.json"

STOPWORDS = {
    "a", "ao", "aos", "à", "às", "o", "os", "as", "um", "uma", "uns", "umas", "de", "da", "das", "do", "dos",
    "e", "ou", "que", "em", "no", "nos", "na", "nas", "por", "para", "com", "sem", "ser", "há", "é", "são",
    "como", "mais", "menos", "já", "não", "nao", "se", "só", "so", "isto", "isso", "aquele", "aquela", "aquilo",
    "todo", "toda", "todos", "todas", "mesmo", "mesma", "mesmos", "mesmas", "entre", "sobre", "contra", "desde",
    "pelo", "pela", "pelos", "pelas", "seu", "sua", "seus", "suas", "dele", "dela", "deles", "delas", "lhe", "lhes",
}

PALAVRAS_FRACAS = {
    "coisa", "coisas", "algo", "alguma", "algum", "alguns", "algumas", "material", "materiais", "passo", "passos",
    "sistema", "realidade", "real", "estrutura", "estrutural", "modo", "forma", "nível", "nivel", "zona", "plano",
    "proposição", "proposicao", "proposições", "proposicoes", "questão", "questao"
}

PESOS_RELEVANCIA = {"baixo": 0.35, "medio": 0.65, "alto": 1.0}
PESOS_PRIORIDADE = {"baixa": 0.25, "media": 0.6, "alta": 0.85, "muito_alta": 1.0}
PESOS_ESTABILIDADE = {
    "globalmente_estavel": 0.80,
    "estavel_mas_a_densificar": 0.72,
    "a_reformular": 0.45,
    "nao_testado_pelos_fragmentos": 0.55,
}

FONTES_PRIORITARIAS = {
    "fecho_manual": 5,
    "revisao_estrutural": 4,
    "mapa_base": 3,
    "argumentos_e_percursos": 2,
    "apoio_fragmentario": 1,
}

LIMIAR_SIMILARIDADE_FUSAO = 0.86
LIMIAR_SIMILARIDADE_APOIO = 0.92
LIMIAR_COMPATIBILIDADE_FORMULACAO = 0.36
LIMIAR_PROMOCAO_MEDIACAO = 2.20


# ============================================================
# UTILITÁRIOS BASE
# ============================================================


def carregar_json(caminho: Path) -> Any:
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)



def guardar_json(caminho: Path, dados: Any) -> None:
    with caminho.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)



def agora_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()



def texto_limpo(valor: Any) -> Optional[str]:
    if valor is None:
        return None
    if isinstance(valor, list):
        valor = " ".join(str(x) for x in valor if x is not None)
    if not isinstance(valor, str):
        valor = str(valor)
    valor = re.sub(r"\s+", " ", valor).strip()
    return valor or None



def lista_textos(valor: Any) -> List[str]:
    if not isinstance(valor, list):
        return []
    vistos: Set[str] = set()
    saida: List[str] = []
    for item in valor:
        t = texto_limpo(item)
        if t and t not in vistos:
            vistos.add(t)
            saida.append(t)
    return saida



def garantir_lista(valor: Any) -> List[Any]:
    return valor if isinstance(valor, list) else []



def garantir_dict(valor: Any) -> Dict[str, Any]:
    return valor if isinstance(valor, dict) else {}



def parse_estado_estrutural(valor: Any) -> Dict[str, Any]:
    if isinstance(valor, dict):
        return valor
    if isinstance(valor, str):
        try:
            obj = ast.literal_eval(valor)
            if isinstance(obj, dict):
                return obj
        except Exception:
            return {}
    return {}



def numero_prop(prop_id: str) -> int:
    m = re.search(r"(\d+)$", str(prop_id))
    return int(m.group(1)) if m else 999999



def ordenar_props(props: Iterable[str]) -> List[str]:
    return sorted({str(p) for p in props if p}, key=numero_prop)



def normalizar_token(token: str) -> str:
    token = token.lower()
    token = token.replace("ç", "c")
    token = token.replace("á", "a").replace("à", "a").replace("â", "a").replace("ã", "a")
    token = token.replace("é", "e").replace("ê", "e")
    token = token.replace("í", "i")
    token = token.replace("ó", "o").replace("ô", "o").replace("õ", "o")
    token = token.replace("ú", "u")
    return token



def tokenizar(texto: Optional[str]) -> List[str]:
    if not texto:
        return []
    bruto = re.findall(r"[\wÀ-ÿ-]+", texto.lower())
    toks: List[str] = []
    for t in bruto:
        tn = normalizar_token(t)
        if len(tn) <= 2:
            continue
        if tn in STOPWORDS or tn in PALAVRAS_FRACAS:
            continue
        toks.append(tn)
    return toks



def conjunto_tokens(*textos: Optional[str]) -> Set[str]:
    out: Set[str] = set()
    for t in textos:
        out.update(tokenizar(t))
    return out



def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)



def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))



def media(valores: Iterable[float]) -> float:
    vals = list(valores)
    return sum(vals) / len(vals) if vals else 0.0


# ============================================================
# EXTRAÇÃO E NORMALIZAÇÃO DAS FONTES
# ============================================================


def extrair_proposicoes_do_mapa(mapa: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    props: Dict[str, Dict[str, Any]] = {}

    def walk(x: Any, bloco_id: Optional[str] = None, bloco_titulo: Optional[str] = None) -> None:
        if isinstance(x, dict):
            if isinstance(x.get("id"), str) and x["id"].startswith("P"):
                item = deepcopy(x)
                if bloco_id and "bloco_id" not in item:
                    item["bloco_id"] = bloco_id
                if bloco_titulo and "bloco_titulo" not in item:
                    item["bloco_titulo"] = bloco_titulo
                props[item["id"]] = item
                return
            bloco_id_local = bloco_id
            bloco_titulo_local = bloco_titulo
            if isinstance(x.get("id"), str) and x["id"].startswith("BLOCO"):
                bloco_id_local = x.get("id")
                bloco_titulo_local = x.get("titulo")
            for v in x.values():
                walk(v, bloco_id_local, bloco_titulo_local)
        elif isinstance(x, list):
            for v in x:
                walk(v, bloco_id, bloco_titulo)

    walk(mapa)
    return dict(sorted(props.items(), key=lambda kv: numero_prop(kv[0])))



def normalizar_revisao(revisao: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    itens = garantir_lista(revisao.get("revisao_por_proposicao"))
    return {str(item.get("proposicao_id")): item for item in itens if isinstance(item, dict) and item.get("proposicao_id")}



def normalizar_fechos() -> Dict[str, Dict[str, Any]]:
    saida: Dict[str, Dict[str, Any]] = {}
    for chave in ["fecho_p25_p30", "fecho_p33_p37", "fecho_p42_p48", "fecho_p50"]:
        data = carregar_json(FICHEIROS[chave])
        for ficha in garantir_lista(data.get("fichas")):
            if isinstance(ficha, dict) and ficha.get("proposicao_id"):
                ficha = deepcopy(ficha)
                ficha["__fonte_fecho__"] = chave
                saida[str(ficha["proposicao_id"])] = ficha
    return saida



def construir_indices_argumentos(argumentos: List[Dict[str, Any]]) -> Tuple[Dict[str, List[Dict[str, Any]]], Set[str], List[str]]:
    por_capitulo: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    ids: Set[str] = set()
    referencias_encontradas: Set[str] = set()

    for arg in argumentos:
        if not isinstance(arg, dict):
            continue
        aid = texto_limpo(arg.get("id"))
        if aid:
            ids.add(aid)
        cap = texto_limpo(arg.get("capitulo")) or "SEM_CAPITULO"
        por_capitulo[cap].append(arg)
        referencias_encontradas.update(re.findall(r"ARG_[A-Z0-9_]+", json.dumps(arg, ensure_ascii=False)))

    dependencias_ausentes = sorted(ref for ref in referencias_encontradas if ref not in ids)
    return dict(por_capitulo), ids, dependencias_ausentes



def construir_lookup_tratamento(tratamento: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for item in tratamento:
        if not isinstance(item, dict):
            continue
        fid = texto_limpo(item.get("fragment_id"))
        if fid:
            out[fid] = item
    return out



def construir_lookup_impacto(impacto: List[Dict[str, Any]]) -> Tuple[Dict[str, List[Dict[str, Any]]], Set[str]]:
    por_prop: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    all_fragment_ids: Set[str] = set()
    for item in impacto:
        if not isinstance(item, dict):
            continue
        fid = texto_limpo(item.get("fragment_id"))
        if fid:
            all_fragment_ids.add(fid)
        bloco = garantir_dict(item.get("impacto_no_mapa_fragmento"))
        for toque in garantir_lista(bloco.get("proposicoes_do_mapa_tocadas")):
            if not isinstance(toque, dict):
                continue
            pid = texto_limpo(toque.get("proposicao_id"))
            if pid:
                por_prop[pid].append(item)
    return dict(por_prop), all_fragment_ids



def extrair_capitulo_numero(capitulo_id: Optional[str]) -> Optional[int]:
    if not capitulo_id:
        return None
    m = re.search(r"CAP_(\d+)", capitulo_id)
    return int(m.group(1)) if m else None


# ============================================================
# HEURÍSTICAS DE CONTEÚDO
# ============================================================


def tokens_ancora_do_passo(mapa_item: Dict[str, Any], revisao_item: Dict[str, Any]) -> Set[str]:
    base = garantir_dict(revisao_item.get("base_dedutiva_existente"))
    return conjunto_tokens(
        texto_limpo(mapa_item.get("proposicao")),
        texto_limpo(mapa_item.get("descricao_curta")),
        texto_limpo(base.get("tese_minima")),
        texto_limpo(base.get("formulacao_filosofico_academica")),
    )



def score_compatibilidade_formulacao(candidata: Optional[str], mapa_item: Dict[str, Any], revisao_item: Dict[str, Any]) -> float:
    cand = conjunto_tokens(candidata)
    if not cand:
        return 0.0
    ancora = tokens_ancora_do_passo(mapa_item, revisao_item)
    if not ancora:
        return 0.0
    sobrepos = len(cand & ancora) / max(1, len(ancora))
    jac = jaccard(cand, ancora)

    bonus = 0.0
    prop = normalizar_token(texto_limpo(mapa_item.get("proposicao")) or "")
    if "dignidade" in prop and "dignidade" in cand:
        bonus += 0.12
    if "consciencia" in prop and "consciencia" in cand:
        bonus += 0.12
    if "verdade" in prop and "verdade" in cand:
        bonus += 0.08
    if "criterio" in prop and "criterio" in cand:
        bonus += 0.08
    if "bem" in prop and "bem" in cand:
        bonus += 0.08
    if "liberdade" in prop and "liberdade" in cand:
        bonus += 0.08

    penalidade = 0.0
    # penaliza formulações genéricas ou deslocadas do passo
    if len(cand & ancora) <= 1 and len(cand) >= 4:
        penalidade += 0.16
    if {"bem", "mal"} & cand and "apreensao" in ancora and "apreensao" not in cand:
        penalidade += 0.22
    if "dignidade" in cand and "dignidade" not in ancora:
        penalidade += 0.14

    return clamp(0.55 * jac + 0.45 * sobrepos + bonus - penalidade)



def escolher_formulacao_final(mapa_item: Dict[str, Any], revisao_item: Dict[str, Any], fecho_item: Optional[Dict[str, Any]]) -> Tuple[str, str, float, List[str]]:
    base = garantir_dict(revisao_item.get("base_dedutiva_existente"))
    candidatos: List[Tuple[str, str]] = []
    observacoes: List[str] = []

    # ordem: fecho manual -> revisão -> mapa
    if fecho_item:
        c1 = texto_limpo(fecho_item.get("formulacao_v2_provisoria"))
        if c1:
            candidatos.append(("fecho_manual", c1))
        c2 = texto_limpo(fecho_item.get("proposicao_atual"))
        if c2:
            candidatos.append(("fecho_manual_atual", c2))
    c3 = texto_limpo(revisao_item.get("proposta_de_reformulacao"))
    if c3:
        candidatos.append(("revisao_estrutural", c3))
    c4 = texto_limpo(base.get("formulacao_filosofico_academica"))
    if c4:
        candidatos.append(("base_academica", c4))
    c5 = texto_limpo(base.get("tese_minima"))
    if c5:
        candidatos.append(("base_tese", c5))
    c6 = texto_limpo(mapa_item.get("proposicao"))
    if c6:
        candidatos.append(("mapa_base", c6))

    melhor_texto = c6 or c5 or c4 or ""
    melhor_origem = "mapa_base"
    melhor_score = 0.0

    for origem, texto in candidatos:
        score = score_compatibilidade_formulacao(texto, mapa_item, revisao_item)
        if origem.startswith("fecho_manual") and score < LIMIAR_COMPATIBILIDADE_FORMULACAO:
            observacoes.append(f"Formulação manual rejeitada por baixa compatibilidade semântica ({score:.2f}).")
            continue
        if origem == "revisao_estrutural" and score < LIMIAR_COMPATIBILIDADE_FORMULACAO * 0.9:
            observacoes.append(f"Reformulação da revisão rejeitada por compatibilidade insuficiente ({score:.2f}).")
            continue
        prioridade = 0.03 if origem.startswith("fecho_manual") else 0.01 if origem == "revisao_estrutural" else 0.0
        score_total = score + prioridade
        if score_total > melhor_score:
            melhor_score = score_total
            melhor_texto = texto
            melhor_origem = origem

    if not melhor_texto:
        melhor_texto = texto_limpo(mapa_item.get("proposicao")) or ""
        melhor_origem = "mapa_base"
    return melhor_texto, melhor_origem, round(clamp(melhor_score), 3), observacoes



def recolher_objecoes(revisao_item: Dict[str, Any], fecho_item: Optional[Dict[str, Any]], impactos_prop: List[Dict[str, Any]]) -> List[str]:
    base = garantir_dict(revisao_item.get("base_dedutiva_existente"))
    out = lista_textos(base.get("objecoes_tipicas_a_bloquear"))
    if fecho_item:
        for obj in lista_textos(fecho_item.get("objecoes_a_bloquear")):
            if obj not in out:
                out.append(obj)
    freq: Counter[str] = Counter()
    for item in impactos_prop:
        bloco = garantir_dict(item.get("impacto_no_mapa_fragmento"))
        ded = garantir_dict(bloco.get("impacto_editorial_e_dedutivo"))
        for obj in lista_textos(ded.get("objecoes_que_ajuda_a_bloquear")):
            freq[obj] += 1
    for obj, _ in freq.most_common(12):
        if obj not in out:
            out.append(obj)
    return out[:12]



def recolher_fragmentos_apoio(impactos_prop: List[Dict[str, Any]], tratamento_lookup: Dict[str, Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    scores: List[Tuple[float, str]] = []
    sem_tratamento: Set[str] = set()
    for item in impactos_prop:
        fid = texto_limpo(item.get("fragment_id"))
        if not fid:
            continue
        bloco = garantir_dict(item.get("impacto_no_mapa_fragmento"))
        toques = garantir_lista(bloco.get("proposicoes_do_mapa_tocadas"))
        toque_local = next((t for t in toques if garantir_dict(t).get("proposicao_id")), {})
        relev = PESOS_RELEVANCIA.get(texto_limpo(garantir_dict(toque_local).get("grau_de_relevancia")) or "", 0.4)
        decisao = garantir_dict(bloco.get("decisao_final"))
        prior = PESOS_PRIORIDADE.get(texto_limpo(decisao.get("prioridade_editorial")) or "", 0.4)
        ded = garantir_dict(bloco.get("impacto_editorial_e_dedutivo"))
        bonus = 0.0
        if lista_textos(ded.get("objecoes_que_ajuda_a_bloquear")):
            bonus += 0.15
        mediacao = texto_limpo(ded.get("mediacao_que_fornece")) or ""
        if mediacao and "nao fornece" not in mediacao.lower():
            bonus += 0.10
        if fid in tratamento_lookup:
            tr = garantir_dict(tratamento_lookup[fid].get("tratamento_filosofico_fragmento"))
            trabalho = texto_limpo(tr.get("trabalho_no_sistema")) or ""
            if trabalho:
                bonus += 0.10
        else:
            sem_tratamento.add(fid)
        scores.append((relev + prior + bonus, fid))
    melhores = [fid for _, fid in sorted(scores, reverse=True)[:12]]
    return melhores, ordenar_props(sem_tratamento)



def construir_apoio_argumentativo(indice_por_percurso: Dict[str, Any], argumentos_por_capitulo: Dict[str, List[Dict[str, Any]]], numero: int) -> Dict[str, Any]:
    capitulo_id = f"CAP_{numero:02d}_"
    capitulo_match = None
    for cap in argumentos_por_capitulo.keys():
        if cap.startswith(capitulo_id):
            capitulo_match = cap
            break
    argumentos = argumentos_por_capitulo.get(capitulo_match or "", [])

    percursos_relacionados: Set[str] = set()
    for percurso_id, bloco in garantir_dict(indice_por_percurso.get("percursos")).items():
        caps_ids: List[str] = []
        for sec in ["directo", "com_pressupostos", "meta", "resumo"]:
            caps_ids.extend(re.findall(r"CAP_\d+_[A-Z_]+", json.dumps(garantir_dict(bloco.get(sec)), ensure_ascii=False)))
        if any(extrair_capitulo_numero(c) == numero for c in caps_ids):
            percursos_relacionados.add(percurso_id)

    return {
        "argumentos_ids": [texto_limpo(a.get("id")) for a in argumentos if texto_limpo(a.get("id"))][:8],
        "percursos_ids": sorted(percursos_relacionados),
        "n_argumentos": len(argumentos),
        "n_percursos": len(percursos_relacionados),
    }



def classificar_funcional(pid: str, revisao_item: Dict[str, Any], fecho_item: Optional[Dict[str, Any]], indeg: int, outdeg: int, promocao: bool) -> str:
    diagnostico = garantir_dict(revisao_item.get("diagnostico_estrutural"))
    estado = texto_limpo(revisao_item.get("estado_estrutural_estimado")) or texto_limpo(diagnostico.get("estabilidade")) or texto_limpo(garantir_dict(revisao_item.get("decisao_reconstrutiva")).get("estado_estrutural_estimado")) or ""
    acao = texto_limpo(diagnostico.get("acao_estrutural_recomendada")) or texto_limpo(garantir_dict(revisao_item.get("decisao_reconstrutiva")).get("acao_estrutural_recomendada")) or ""
    if promocao:
        return "mediacao_necessaria"
    if fecho_item:
        decisao = texto_limpo(fecho_item.get("decisao_editorial_v2")) or ""
        if "explicitar media" in decisao.lower() or "subdiv" in decisao.lower():
            return "mediacao_necessaria"
    if indeg + outdeg >= 4 and estado != "a_reformular":
        return "nucleo"
    if acao in {"explicitar_mediacoes", "reformular"}:
        return "mediacao_necessaria"
    if indeg <= 1 and outdeg <= 1 and estado == "globalmente_estavel":
        return "apoio_expositivo"
    return "nucleo" if (indeg + outdeg) >= 3 else "mediacao_necessaria"



def calcular_inevitabilidade(revisao_item: Dict[str, Any], apoio_argumentativo: Dict[str, Any], indeg: int, outdeg: int, fecho_item: Optional[Dict[str, Any]], n_fragmentos: int, n_objecoes: int) -> Tuple[str, float]:
    diagnostico = garantir_dict(revisao_item.get("diagnostico_estrutural"))
    estado = texto_limpo(revisao_item.get("estado_estrutural_estimado")) or texto_limpo(diagnostico.get("estabilidade")) or texto_limpo(garantir_dict(revisao_item.get("decisao_reconstrutiva")).get("estado_estrutural_estimado")) or "nao_testado_pelos_fragmentos"
    estabilidade = PESOS_ESTABILIDADE.get(estado, 0.55)
    centralidade = clamp((indeg + outdeg) / 6)
    ancoragem = clamp((apoio_argumentativo.get("n_argumentos", 0) / 3) * 0.65 + (apoio_argumentativo.get("n_percursos", 0) / 3) * 0.35)
    fragmentaria = clamp(math.log1p(n_fragmentos) / math.log(35), 0, 1)
    objecoes = clamp(n_objecoes / 8)
    prioridade_local = 1.0 if fecho_item else 0.0

    score = (
        0.28 * estabilidade +
        0.22 * centralidade +
        0.20 * ancoragem +
        0.15 * fragmentaria +
        0.08 * objecoes +
        0.07 * prioridade_local
    )
    score = clamp(score)
    if score >= 0.82:
        grau = "muito_alto"
    elif score >= 0.66:
        grau = "alto"
    elif score >= 0.48:
        grau = "medio"
    else:
        grau = "baixo"
    return grau, round(score, 3)



def identificar_promocao_mediacional(revisao_item: Dict[str, Any], impactos_prop: List[Dict[str, Any]], fecho_item: Optional[Dict[str, Any]]) -> Tuple[bool, float, List[str]]:
    justificacoes: List[str] = []
    score = 0.0
    base = garantir_dict(revisao_item.get("base_dedutiva_existente"))
    mediacoes_base = lista_textos(base.get("mediacoes_em_falta_no_mapa"))
    if mediacoes_base:
        score += 0.8
        justificacoes.append("Há mediações em falta explicitadas na base dedutiva.")

    if fecho_item:
        mediacoes_fecho = lista_textos(fecho_item.get("mediacoes_em_falta"))
        if mediacoes_fecho:
            score += min(1.0, 0.25 * len(mediacoes_fecho))
            justificacoes.append("O fecho manual mantém défice mediacional local.")
        decisao = texto_limpo(fecho_item.get("decisao_editorial_v2")) or ""
        if "explicitar" in decisao.lower() or "subdiv" in decisao.lower():
            score += 0.55
            justificacoes.append("O fecho manual aponta para explicitação ou subdivisão.")

    n_mediacionais = 0
    n_criar_passo = 0
    for item in impactos_prop:
        bloco = garantir_dict(item.get("impacto_no_mapa_fragmento"))
        tipo = texto_limpo(bloco.get("tipo_de_utilidade_principal")) or ""
        ded = garantir_dict(bloco.get("impacto_editorial_e_dedutivo"))
        decisao = garantir_dict(bloco.get("decisao_final"))
        prior = PESOS_PRIORIDADE.get(texto_limpo(decisao.get("prioridade_editorial")) or "", 0.4)
        if tipo == "mediacional":
            n_mediacionais += 1
            score += 0.18 * prior
        if ded.get("obriga_a_criar_passo_intermedio"):
            n_criar_passo += 1
            score += 0.35 * prior
        mediacao = texto_limpo(ded.get("mediacao_que_fornece")) or ""
        if mediacao and "nao fornece" not in mediacao.lower():
            score += 0.08

    if n_mediacionais:
        justificacoes.append(f"Há {n_mediacionais} fragmento(s) com utilidade mediacional dominante.")
    if n_criar_passo:
        justificacoes.append(f"Há {n_criar_passo} fragmento(s) que sugerem passo intermédio.")

    return score >= LIMIAR_PROMOCAO_MEDIACAO, round(score, 3), justificacoes[:5]


# ============================================================
# ORDENAÇÃO E REDUNDÂNCIA
# ============================================================


def ordem_topologica_conservadora(registos: Dict[str, Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
    ids = list(registos)
    indeg: Dict[str, int] = {pid: 0 for pid in ids}
    adjs: Dict[str, Set[str]] = {pid: set() for pid in ids}
    conflitos: List[Dict[str, Any]] = []

    for pid, r in registos.items():
        for dep in r.get("depende_de", []):
            if dep not in registos:
                conflitos.append({"tipo": "dependencia_externa_ignorada", "passo": pid, "depende_de": dep})
                continue
            if pid == dep:
                conflitos.append({"tipo": "auto_dependencia", "passo": pid})
                continue
            if pid not in adjs[dep]:
                adjs[dep].add(pid)
                indeg[pid] += 1

    fila = deque(sorted([pid for pid, grau in indeg.items() if grau == 0], key=numero_prop))
    ordem: List[str] = []
    while fila:
        atual = fila.popleft()
        ordem.append(atual)
        for nxt in sorted(adjs[atual], key=numero_prop):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                fila.append(nxt)

    if len(ordem) != len(ids):
        restantes = [pid for pid in ids if pid not in ordem]
        conflitos.append({"tipo": "ciclo_ou_bloqueio_parcial", "passos": ordenar_props(restantes)})
        ordem.extend(sorted(restantes, key=numero_prop))

    return ordem, conflitos



def identificar_relacoes_de_redundancia(registos: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    ids = sorted(registos, key=numero_prop)
    proximidades: List[Dict[str, Any]] = []
    fundiveis: List[Dict[str, Any]] = []
    rebaixaveis: List[Dict[str, Any]] = []

    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if abs(numero_prop(a) - numero_prop(b)) > 3:
                continue
            ra, rb = registos[a], registos[b]
            ta = conjunto_tokens(ra.get("proposicao_final"), ra.get("tese_minima"), ra.get("descricao_curta"))
            tb = conjunto_tokens(rb.get("proposicao_final"), rb.get("tese_minima"), rb.get("descricao_curta"))
            sim = jaccard(ta, tb)
            if sim < 0.70:
                continue
            item = {
                "a": a,
                "b": b,
                "similaridade": round(sim, 3),
                "a_classificacao": ra.get("classificacao_funcional"),
                "b_classificacao": rb.get("classificacao_funcional"),
            }
            proximidades.append(item)
            travoes = 0
            if ra.get("fonte_decisao_prioritaria") == "fecho_manual":
                travoes += 1
            if rb.get("fonte_decisao_prioritaria") == "fecho_manual":
                travoes += 1
            if ra.get("grau_de_inevitabilidade") in {"alto", "muito_alto"}:
                travoes += 1
            if rb.get("grau_de_inevitabilidade") in {"alto", "muito_alto"}:
                travoes += 1
            if sim >= LIMIAR_SIMILARIDADE_FUSAO and travoes <= 1:
                fundiveis.append(item)
            elif sim >= LIMIAR_SIMILARIDADE_APOIO and travoes >= 2:
                rebaixaveis.append(item)

    return {
        "proximidades": sorted(proximidades, key=lambda x: (-x["similaridade"], numero_prop(x["a"]))),
        "fundiveis": sorted(fundiveis, key=lambda x: (-x["similaridade"], numero_prop(x["a"]))),
        "rebaixaveis_para_apoio": sorted(rebaixaveis, key=lambda x: (-x["similaridade"], numero_prop(x["a"]))),
    }


# ============================================================
# RECONSTRUÇÃO PRINCIPAL
# ============================================================


def reconstruir() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    mapa = carregar_json(FICHEIROS["mapa"])
    revisao = carregar_json(FICHEIROS["revisao"])
    indice_por_percurso = carregar_json(FICHEIROS["indice_por_percurso"])
    argumentos = carregar_json(FICHEIROS["argumentos"])
    conceitos = carregar_json(FICHEIROS["conceitos"])
    operacoes = carregar_json(FICHEIROS["operacoes"])
    meta_percurso = carregar_json(FICHEIROS["meta_percurso"])
    meta_indice = carregar_json(FICHEIROS["meta_indice"])
    tratamento = carregar_json(FICHEIROS["tratamento_fragmentos"])
    impacto = carregar_json(FICHEIROS["impacto_fragmentos"])
    impacto_relatorio = carregar_json(FICHEIROS["impacto_relatorio"])

    props_mapa = extrair_proposicoes_do_mapa(mapa)
    revisao_por_id = normalizar_revisao(revisao)
    fechos_por_id = normalizar_fechos()
    argumentos_por_capitulo, argumentos_ids, argumentos_ausentes = construir_indices_argumentos(argumentos)
    tratamento_lookup = construir_lookup_tratamento(tratamento)
    impacto_por_prop, all_impact_fragment_ids = construir_lookup_impacto(impacto)

    registos: Dict[str, Dict[str, Any]] = {}
    conflitos: List[Dict[str, Any]] = []
    fragmentos_sem_tratamento_usados: Set[str] = set()
    promoviveis: List[Dict[str, Any]] = []

    # pré-cálculo indegree/outdegree a partir do mapa/revisão
    indeg: Dict[str, int] = defaultdict(int)
    outdeg: Dict[str, int] = defaultdict(int)
    for pid, item in props_mapa.items():
        deps = ordenar_props(item.get("depende_de") or revisao_por_id.get(pid, {}).get("depende_de") or [])
        preps = ordenar_props(item.get("prepara") or revisao_por_id.get(pid, {}).get("prepara") or [])
        indeg[pid] = len([d for d in deps if d in props_mapa])
        outdeg[pid] = len([p for p in preps if p in props_mapa])

    for pid, mapa_item in props_mapa.items():
        rev = revisao_por_id.get(pid, {})
        fecho = fechos_por_id.get(pid)
        impactos_prop = impacto_por_prop.get(pid, [])
        base = garantir_dict(rev.get("base_dedutiva_existente"))
        decisao_rec = garantir_dict(rev.get("decisao_reconstrutiva"))

        proposicao_final, origem_formulacao, score_formulacao, obs_formulacao = escolher_formulacao_final(mapa_item, rev, fecho)
        objecoes = recolher_objecoes(rev, fecho, impactos_prop)
        fragmentos_apoio, sem_tratamento = recolher_fragmentos_apoio(impactos_prop, tratamento_lookup)
        fragmentos_sem_tratamento_usados.update(sem_tratamento)
        apoio_argumentativo = construir_apoio_argumentativo(indice_por_percurso, argumentos_por_capitulo, numero_prop(pid))
        promover, score_promocao, just_promocao = identificar_promocao_mediacional(rev, impactos_prop, fecho)
        classificacao = classificar_funcional(pid, rev, fecho, indeg[pid], outdeg[pid], promover)
        grau, score_inevit = calcular_inevitabilidade(rev, apoio_argumentativo, indeg[pid], outdeg[pid], fecho, len(fragmentos_apoio), len(objecoes))

        if promover:
            promoviveis.append({
                "proposicao_id": pid,
                "score_promocao": score_promocao,
                "razoes": just_promocao,
            })

        diagnostico = garantir_dict(rev.get("diagnostico_estrutural"))
        estado = (
            texto_limpo(diagnostico.get("acao_estrutural_recomendada"))
            or texto_limpo(fecho.get("decisao_editorial_v2") if fecho else None)
            or texto_limpo(diagnostico.get("necessidade_principal"))
            or texto_limpo(diagnostico.get("estabilidade"))
            or texto_limpo(rev.get("estado_estrutural_estimado"))
            or "manter"
        )

        fonte_decisao = "fecho_manual" if fecho else "revisao_estrutural" if rev else "mapa_base"

        justificacao_min = (
            texto_limpo(fecho.get("justificacao_atual") if fecho else None)
            or texto_limpo(base.get("justificacao_interna_do_passo"))
            or texto_limpo(mapa_item.get("justificacao", {}).get("justificacao_interna_do_passo"))
            or texto_limpo(mapa_item.get("descricao_curta"))
            or proposicao_final
        )

        mediacoes = []
        for x in lista_textos(base.get("mediacoes_em_falta_no_mapa")) + lista_textos(fecho.get("mediacoes_em_falta") if fecho else []):
            if x not in mediacoes:
                mediacoes.append(x)

        observacoes_editoriais = []
        observacoes_editoriais.extend(obs_formulacao)
        if fecho:
            d = texto_limpo(fecho.get("defice_principal"))
            if d:
                observacoes_editoriais.append(f"Défice principal do fecho manual: {d}")
        diag = texto_limpo(decisao_rec.get("diagnostico_reconstrutivo"))
        if diag:
            observacoes_editoriais.append(diag)

        registos[pid] = {
            "id": pid,
            "numero_original": numero_prop(pid),
            "bloco_id": texto_limpo(rev.get("bloco_id")) or texto_limpo(mapa_item.get("bloco_id")),
            "bloco_titulo": texto_limpo(rev.get("bloco_titulo")) or texto_limpo(mapa_item.get("bloco_titulo")),
            "numero_final": None,
            "proposicao_final": proposicao_final,
            "proposicao_original": texto_limpo(mapa_item.get("proposicao")),
            "descricao_curta": texto_limpo(rev.get("descricao_curta")) or texto_limpo(mapa_item.get("descricao_curta")),
            "funcao_no_sistema": texto_limpo(fecho.get("funcao_no_percurso") if fecho else None) or texto_limpo(decisao_rec.get("funcao_no_sistema")) or texto_limpo(rev.get("descricao_curta")) or texto_limpo(mapa_item.get("descricao_curta")),
            "depende_de": ordenar_props(rev.get("depende_de") or mapa_item.get("depende_de")),
            "prepara": ordenar_props(rev.get("prepara") or mapa_item.get("prepara")),
            "tese_minima": texto_limpo(fecho.get("nucleo_que_se_mantem") if fecho else None) or texto_limpo(base.get("tese_minima")) or proposicao_final,
            "justificacao_minima_suficiente": justificacao_min,
            "objecoes_bloqueadas": objecoes,
            "fragmentos_de_apoio_final": fragmentos_apoio,
            "estatuto_no_mapa": estado,
            "classificacao_funcional": classificacao,
            "nucleo": texto_limpo(fecho.get("nucleo_que_se_mantem") if fecho else None) or texto_limpo(base.get("tese_minima")) or proposicao_final,
            "mediacao_necessaria": mediacoes,
            "apoio_expositivo": lista_textos(fecho.get("apoio_expositivo") if fecho else [])[:8],
            "grau_de_inevitabilidade": grau,
            "score_de_inevitabilidade": score_inevit,
            "fonte_decisao_prioritaria": fonte_decisao,
            "fonte_formulacao_escolhida": origem_formulacao,
            "score_compatibilidade_formulacao": score_formulacao,
            "apoio_argumentativo": apoio_argumentativo,
            "promovivel_a_mediacao_autonoma": promover,
            "score_promocao_mediacional": score_promocao,
            "observacoes_editoriais": observacoes_editoriais[:10],
        }

    ordem_final, conflitos_ordem = ordem_topologica_conservadora(registos)
    conflitos.extend(conflitos_ordem)
    for i, pid in enumerate(ordem_final, start=1):
        registos[pid]["numero_final"] = i

    redundancias = identificar_relacoes_de_redundancia(registos)
    mantidos = [pid for pid in ordem_final]
    reduzidos = [pid for pid, r in registos.items() if r["classificacao_funcional"] == "apoio_expositivo"]
    promovidos = [x["proposicao_id"] for x in promoviveis]
    reordenados = [pid for pid in ordem_final if registos[pid]["numero_original"] != registos[pid]["numero_final"]]

    mapa_saida = {
        "meta": {
            "gerado_em_utc": agora_utc(),
            "script": Path(__file__).name,
            "versao": "3.0.0",
            "objetivo": "Reconstrução dedutiva inevitável orientada para compressão estrutural conservadora e uso editorial canónico.",
        },
        "fontes": {k: v.name for k, v in FICHEIROS.items()},
        "hierarquia_de_decisao": [
            "fecho manual de corredor",
            "revisão estrutural por proposição",
            "mapa dedutivo base",
            "argumentos unificados e índice por percurso",
            "apoio fragmentário",
        ],
        "estatisticas_metaestruturais": {
            "n_conceitos": len(conceitos) if isinstance(conceitos, dict) else len(garantir_lista(conceitos)),
            "n_operacoes": len(operacoes) if isinstance(operacoes, dict) else len(garantir_lista(operacoes)),
            "n_percursos_meta": len(garantir_dict(meta_percurso.get("percursos")) or meta_percurso),
            "n_argumentos": len(argumentos),
            "n_fragmentos_impacto": len(all_impact_fragment_ids),
            "n_fragmentos_tratamento": len(tratamento_lookup),
            "n_capitulos_meta": len(garantir_lista(meta_indice.get("capitulos"))) if isinstance(meta_indice, dict) else 0,
        },
        "passos": [registos[pid] for pid in ordem_final],
    }

    dist_class = Counter(r["classificacao_funcional"] for r in registos.values())
    dist_est = Counter(r["estatuto_no_mapa"] for r in registos.values())
    dist_inev = Counter(r["grau_de_inevitabilidade"] for r in registos.values())

    relatorio = {
        "meta": {
            "gerado_em_utc": agora_utc(),
            "script": Path(__file__).name,
            "versao": "3.0.0",
            "objetivo": "Relatório auxiliar da reconstrução dedutiva inevitável, com redundâncias, promoções mediacionais e conflitos de decisão.",
        },
        "fontes": {k: v.name for k, v in FICHEIROS.items()},
        "resumo_global": {
            "total_passos": len(registos),
            "classificacao_funcional": dict(dist_class),
            "estatuto_no_mapa": dict(dist_est),
            "grau_de_inevitabilidade": dict(dist_inev),
            "fragmentos_sem_tratamento_filosofico_usados": ordenar_props(fragmentos_sem_tratamento_usados),
            "argumentos_referidos_mas_ausentes": argumentos_ausentes,
            "resumo_impacto_original": impacto_relatorio,
        },
        "passos_mantidos": mantidos,
        "passos_reduzidos_a_apoio_expositivo": ordenar_props(reduzidos),
        "passos_reordenados": ordenar_props(reordenados),
        "passos_fundiveis_sugeridos": redundancias["fundiveis"],
        "proximidades_nao_fundidas": redundancias["proximidades"][:25],
        "passos_rebaixaveis_para_apoio": redundancias["rebaixaveis_para_apoio"],
        "mediacoes_promoviveis_a_passo": sorted(promoviveis, key=lambda x: (-x["score_promocao"], numero_prop(x["proposicao_id"]))),
        "zonas_ainda_frageis": [
            {
                "proposicao_id": pid,
                "grau_de_inevitabilidade": r["grau_de_inevitabilidade"],
                "score_de_inevitabilidade": r["score_de_inevitabilidade"],
                "classificacao_funcional": r["classificacao_funcional"],
                "estatuto_no_mapa": r["estatuto_no_mapa"],
                "fonte_decisao_prioritaria": r["fonte_decisao_prioritaria"],
            }
            for pid, r in sorted(registos.items(), key=lambda kv: (kv[1]["score_de_inevitabilidade"], numero_prop(kv[0])))[:12]
        ],
        "conflitos_de_decisao_resolvidos": conflitos,
        "notas_metodologicas": [
            "As formulações provisórias dos fechos manuais só são adotadas quando passam um teste de compatibilidade semântica com o passo original.",
            "A ordem final é topológica e conservadora: respeita dependências, mas evita reordenações agressivas sem necessidade lógica forte.",
            "A identificação de fusões é apenas sugestiva; o script sinaliza proximidades e travões arquitetónicos antes de propor fusão.",
            "Os fragmentos comandam densificação, bloqueio de objeções e promoção mediacional, não a arquitetura principal.",
        ],
    }

    return mapa_saida, relatorio


# ============================================================
# EXECUÇÃO
# ============================================================


def main() -> None:
    mapa_saida, relatorio = reconstruir()
    guardar_json(SAIDA_MAPA, mapa_saida)
    guardar_json(SAIDA_RELATORIO, relatorio)
    print(f"Gerado: {SAIDA_MAPA.name}")
    print(f"Gerado: {SAIDA_RELATORIO.name}")


if __name__ == "__main__":
    main()
