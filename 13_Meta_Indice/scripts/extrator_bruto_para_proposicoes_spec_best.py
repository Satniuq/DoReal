# extrator_bruto_para_proposicoes_spec_best_v3.py
# SPEC BEST v3:
# - Campo principal escolhido determinísticamente (não pela IA)
# - Anti-modalização conservadora (quando o parágrafo é interrogativo/hipotético)
# - OP_* validadas por meta_indice (se existir) e por conceito (se existir em todos_os_conceitos)
# - Paths portáteis por DOREAL_ROOT

from __future__ import annotations

import os
import re
import json
import time
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from dotenv import load_dotenv
from google import genai

# =====================================================
# 0) CONFIGURAÇÃO
# =====================================================

VERSAO_EXTRATOR = "spec_best_v3"
VERSAO_REGRAS = "v3"

FORCAR_REPROCESSAMENTO = False
REPROCESSAR_FALHAS = True
TENTATIVAS_POR_UNIDADE = 3
PAUSA_ENTRE_CHAMADAS = 1.1

MODELO_IA = "models/gemini-2.5-flash"
MAX_PROPOSICOES_POR_UNIDADE = 12

# Contenção determinística
MAX_SECUNDARIOS = 2
MAX_PERCURSO = 4

# Ancoragem lexical (0 permissivo; 2 mais exigente)
MIN_SCORE_SEC = 1
MIN_SCORE_PERC = 1
MIN_SCORE_CP = 1  # para aceitar troca de campo_principal

# Heurística parágrafos pequenos
DESCARTAR_MUITO_PEQUENO = True
MIN_CHARS_PARAGRAFO = 20
HEURISTICA_CONCEPTUAL_RE = re.compile(
    r"\b(define|defini|implica|logo|portanto|causa|razão|condição|necessário|suficiente|é|são)\b|[:;—-]|“|”|\"|’|'",
    re.IGNORECASE
)

# =====================================================
# 0.1) PATHS PORTÁTEIS
# =====================================================

def _guess_root(default_here: bool = True) -> str:
    load_dotenv()
    root = os.getenv("DOREAL_ROOT")
    if root and os.path.isdir(root):
        return root
    if default_here:
        here = os.path.abspath(os.path.dirname(__file__))
        cand = os.path.abspath(os.path.join(here, "..", ".."))
        if os.path.isdir(cand):
            return cand
    return os.getcwd()

DOREAL_ROOT = _guess_root()

BRUTO_MD = os.path.join(DOREAL_ROOT, "00_bruto", "fragmentos.md")
CONCEITOS_FILE = os.path.join(DOREAL_ROOT, "13_Meta_Indice", "dados_base", "todos_os_conceitos.json")
CAPITULOS_FILE = os.path.join(DOREAL_ROOT, "13_Meta_Indice", "meta", "mapa_capitulos.json")
META_INDICE_FILE = os.path.join(DOREAL_ROOT, "13_Meta_Indice", "meta", "meta_indice.json")  # opcional

PROPOSICOES_OUT = os.path.join(DOREAL_ROOT, "13_Meta_Indice", "data", "proposicoes_extraidas.json")
ESTADO_OUT      = os.path.join(DOREAL_ROOT, "13_Meta_Indice", "data", "estado_extrator.json")
FALHAS_OUT      = os.path.join(DOREAL_ROOT, "13_Meta_Indice", "data", "falhas_extrator.json")


# =====================================================
# 1) UTILITÁRIOS
# =====================================================

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def normalizar_espacos(s: str) -> str:
    s = (s or "").replace("\u00A0", " ")
    s = re.sub(r"[ \t]+", " ", s).strip()
    return s

def limpar_json_envelope(texto: str) -> str:
    texto = re.sub(r"```(?:json)?\s*|\s*```", "", (texto or "")).strip()
    m = re.search(r"(\[.*\]|\{.*\})", texto, re.DOTALL)
    return m.group(1).strip() if m else texto.strip()

def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")

def safe_excerpt(s: str, n: int = 1200) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + " …(truncado)…"

def yyyymmdd_from_date(date_str: Optional[str]) -> str:
    if not date_str:
        return "00000000"
    return date_str.replace("-", "")

def ensure_list(x: Any) -> List[Any]:
    if x is None:
        return []
    return x if isinstance(x, list) else []

def ensure_str(x: Any) -> Optional[str]:
    return x if isinstance(x, str) else None

def ensure_float_01(x: Any) -> Optional[float]:
    try:
        v = float(x)
        if 0.0 <= v <= 1.0:
            return v
    except Exception:
        pass
    return None

def dedupe_preserve_order(xs: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for x in xs:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


# =====================================================
# 2) CONFIG: D_*, CAP_*, OP_*
# =====================================================

def carregar_conceitos(path: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Conceitos não encontrados: {path}")
    data = load_json(path)
    if not isinstance(data, dict):
        raise RuntimeError("todos_os_conceitos.json: raiz tem de ser dict.")
    conceitos = {k: v for k, v in data.items()
                 if isinstance(k, str) and k.startswith("D_") and isinstance(v, dict)}
    if not conceitos:
        raise RuntimeError("Não encontrei chaves D_* em todos_os_conceitos.json.")
    return conceitos

def nivel_conceito(conceitos: Dict[str, Dict[str, Any]], did: str) -> Optional[int]:
    info = conceitos.get(did, {})
    n = info.get("nivel", None)
    try:
        return int(n)
    except Exception:
        return None

def definicao_len(conceitos: Dict[str, Dict[str, Any]], did: str) -> int:
    info = conceitos.get(did, {})
    d = info.get("definicao")
    txt = ""
    if isinstance(d, dict):
        txt = d.get("texto", "") if isinstance(d.get("texto"), str) else ""
    elif isinstance(d, str):
        txt = d
    return len(normalizar_espacos(txt))

def carregar_capitulos(path: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Capítulos não encontrados: {path}")
    data = load_json(path)
    if not isinstance(data, dict):
        raise RuntimeError("capitulos.json: raiz tem de ser dict.")
    return data

def construir_campo_to_caps(capitulos: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    mapa: Dict[str, List[str]] = {}
    for cap, info in capitulos.items():
        if not (isinstance(cap, str) and cap.startswith("CAP_") and isinstance(info, dict)):
            continue
        campos = info.get("campos", [])
        if not isinstance(campos, list):
            continue
        for d in campos:
            if isinstance(d, str) and d.startswith("D_"):
                mapa.setdefault(d, []).append(cap)
    for d in list(mapa.keys()):
        mapa[d] = sorted(set(mapa[d]))
    return mapa

def extrair_ops_meta_indice(path: str) -> Set[str]:
    if not path or not os.path.exists(path):
        return set()
    try:
        meta = load_json(path)
    except Exception:
        return set()

    root = meta.get("meta_indice", meta) if isinstance(meta, dict) else {}
    regimes = root.get("regimes", {}) if isinstance(root, dict) else {}
    ops: Set[str] = set()
    if isinstance(regimes, dict):
        for _, rinfo in regimes.items():
            if isinstance(rinfo, dict):
                o = rinfo.get("operacoes", [])
                if isinstance(o, list):
                    for x in o:
                        if isinstance(x, str) and x.startswith("OP_"):
                            ops.add(x)
    return ops

def ops_por_conceito(conceitos: Dict[str, Dict[str, Any]]) -> Dict[str, Set[str]]:
    """
    Usa o formato que mostraste:
      "operacoes_ontologicas": { "fundacao":[...], "descricao":[...], ... }
    ou, se for lista, aceita também.
    """
    out: Dict[str, Set[str]] = {}
    for did, info in conceitos.items():
        s: Set[str] = set()
        oo = info.get("operacoes_ontologicas")
        if isinstance(oo, dict):
            for _, arr in oo.items():
                if isinstance(arr, list):
                    for x in arr:
                        if isinstance(x, str) and x.startswith("OP_"):
                            s.add(x)
        elif isinstance(oo, list):
            for x in oo:
                if isinstance(x, str) and x.startswith("OP_"):
                    s.add(x)
        out[did] = s
    return out


# =====================================================
# 3) SPLIT: container + parágrafos
# =====================================================

HEADER_RE = re.compile(r"^##\s+(F\d{4})\s+—\s+(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)

@dataclass
class UnidadeBruta:
    origem_id: str
    data: Optional[str]
    n_paragrafo: int
    texto: str
    hash_unidade: str

def ler_bruto(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Ficheiro bruto não encontrado: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def split_por_paragrafos(texto: str) -> List[str]:
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    blocos = re.split(r"\n\s*\n+", texto)
    return [b.strip() for b in blocos if b.strip()]

def deve_descartar_paragrafo(p: str) -> bool:
    if not DESCARTAR_MUITO_PEQUENO:
        return False
    p2 = p.strip()
    if len(p2) >= MIN_CHARS_PARAGRAFO:
        return False
    return HEURISTICA_CONCEPTUAL_RE.search(p2) is None

def extrair_unidades(md: str) -> List[UnidadeBruta]:
    md = md.replace("\r\n", "\n").replace("\r", "\n")
    matches = list(HEADER_RE.finditer(md))

    containers: List[Tuple[str, Optional[str], str]] = []

    if matches:
        for i, m in enumerate(matches):
            origem_id = m.group(1).strip()
            data = m.group(2).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
            corpo = md[start:end].strip()
            containers.append((origem_id, data, corpo))

        usados = [False] * len(md)
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
            for j in range(start, end):
                usados[j] = True
        resto = "".join(ch if not usados[i] else "\n" for i, ch in enumerate(md)).strip()
        if resto:
            containers.append(("BRUTO", None, resto))
    else:
        containers.append(("BRUTO", None, md.strip()))

    unidades: List[UnidadeBruta] = []
    for origem_id, data, corpo in containers:
        paras = split_por_paragrafos(corpo)
        n = 0
        for p in paras:
            if deve_descartar_paragrafo(p):
                continue
            n += 1
            texto_literal = p.strip()
            texto_norm = normalizar_espacos(texto_literal)
            h = sha256(texto_norm)
            unidades.append(UnidadeBruta(origem_id=origem_id, data=data, n_paragrafo=n,
                                         texto=texto_literal, hash_unidade=h))
    return unidades


# =====================================================
# 4) ESTADO + dedupe
# =====================================================

def carregar_estado(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {
            "versao_extrator": VERSAO_EXTRATOR,
            "versao_regras": VERSAO_REGRAS,
            "unidades": {},
            "ultima_execucao": None,
        }
    data = load_json(path)
    if not isinstance(data, dict):
        return {
            "versao_extrator": VERSAO_EXTRATOR,
            "versao_regras": VERSAO_REGRAS,
            "unidades": {},
            "ultima_execucao": None,
        }
    if not isinstance(data.get("unidades"), dict):
        data["unidades"] = {}
    data.setdefault("versao_extrator", VERSAO_EXTRATOR)
    data.setdefault("versao_regras", VERSAO_REGRAS)
    return data

def guardar_estado(path: str, estado: Dict[str, Any]) -> None:
    estado["versao_extrator"] = VERSAO_EXTRATOR
    estado["versao_regras"] = VERSAO_REGRAS
    estado["ultima_execucao"] = now_ts()
    save_json(path, estado)

def carregar_proposicoes(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    data = load_json(path)
    return data if isinstance(data, list) else []

def hashes_proposicoes_existentes(props: List[Dict[str, Any]]) -> Set[str]:
    return {p["hash_proposicao"] for p in props if isinstance(p, dict) and isinstance(p.get("hash_proposicao"), str)}


# =====================================================
# 5) CAP_* + tipo ponte
# =====================================================

def cap_principal(campo: str, campo_to_caps: Dict[str, List[str]]) -> Optional[str]:
    caps = campo_to_caps.get(campo, [])
    return caps[0] if caps else None

def caps_dos_campos(campos: List[str], campo_to_caps: Dict[str, List[str]]) -> Set[str]:
    out: Set[str] = set()
    for c in campos:
        for cap in campo_to_caps.get(c, []):
            out.add(cap)
    return out

def tipo_ponte_ou_normal(cap_princ: Optional[str], caps_rel: Set[str], niveis: Set[int], percurso_caps: Set[str]) -> str:
    caps_total = set(caps_rel) | set(percurso_caps)
    if cap_princ:
        caps_total.add(cap_princ)
    if len(caps_total) >= 2 or len(niveis) >= 2 or len(percurso_caps) >= 2:
        return "ponte"
    return "normal"


# =====================================================
# 6) ANCORAGEM + escolha determinística do campo_principal
# =====================================================

TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_]+", re.UNICODE)

def tokens(s: str) -> Set[str]:
    return set(TOKEN_RE.findall((s or "").lower()))

def conceito_texto_base(conceitos: Dict[str, Dict[str, Any]], did: str) -> str:
    info = conceitos.get(did, {})
    nome = info.get("nome", "") if isinstance(info.get("nome"), str) else ""
    defin = ""
    d = info.get("definicao")
    if isinstance(d, dict):
        defin = d.get("texto", "") if isinstance(d.get("texto"), str) else ""
    elif isinstance(d, str):
        defin = d
    return f"{nome} {normalizar_espacos(defin)[:240]}"

def score_ancoragem_conceito(conceitos: Dict[str, Dict[str, Any]], did: str, texto_prop: str, texto_paragrafo: str) -> int:
    t_conc = tokens(conceito_texto_base(conceitos, did))
    t_txt = tokens(texto_prop) | tokens(texto_paragrafo)
    return len(t_conc & t_txt)

def escolher_campo_principal_deterministico(
    conceitos: Dict[str, Dict[str, Any]],
    candidatos: List[str],
    texto_prop: str,
    texto_paragrafo: str
) -> Optional[str]:
    cand = [c for c in dedupe_preserve_order(candidatos) if isinstance(c, str) and c in conceitos]
    if not cand:
        return None

    # ranking: score ancoragem > nível > definição curta > id
    scored: List[Tuple[int, int, int, str]] = []
    for did in cand:
        sc = score_ancoragem_conceito(conceitos, did, texto_prop, texto_paragrafo)
        nv = nivel_conceito(conceitos, did)
        nv = nv if isinstance(nv, int) else -10_000
        dl = definicao_len(conceitos, did)
        scored.append((sc, nv, -dl, did))

    scored.sort(reverse=True)
    best_sc, _, _, best = scored[0]
    if best_sc < MIN_SCORE_CP:
        return None
    return best

def cortar_secundarios(conceitos: Dict[str, Dict[str, Any]], cp: str, cs: List[str]) -> List[str]:
    cs2 = [d for d in dedupe_preserve_order(cs) if d != cp and d in conceitos]

    def key(did: str) -> Tuple[int, int, str]:
        n = nivel_conceito(conceitos, did)
        n = n if isinstance(n, int) else -10_000
        return (-n, definicao_len(conceitos, did), did)

    cs2.sort(key=key)
    return cs2[:MAX_SECUNDARIOS]

def sanitizar_percurso(conceitos: Dict[str, Dict[str, Any]], percurso: List[str], cp: str) -> List[str]:
    p = [d for d in dedupe_preserve_order(percurso) if d in conceitos]
    if cp not in p:
        p.append(cp)
    p = [d for d in p if d != cp] + [cp]
    if len(p) > MAX_PERCURSO:
        p = p[-MAX_PERCURSO:]
    return p

def filtrar_por_ancoragem(conceitos: Dict[str, Dict[str, Any]], cp: str, cs: List[str], percurso: List[str],
                          texto_prop: str, texto_paragrafo: str) -> Tuple[List[str], List[str]]:
    cs2 = []
    for d in cs:
        if d == cp:
            continue
        if score_ancoragem_conceito(conceitos, d, texto_prop, texto_paragrafo) >= MIN_SCORE_SEC:
            cs2.append(d)

    p2 = []
    for d in percurso:
        if score_ancoragem_conceito(conceitos, d, texto_prop, texto_paragrafo) >= MIN_SCORE_PERC:
            p2.append(d)

    return dedupe_preserve_order(cs2), dedupe_preserve_order(p2)


# =====================================================
# 7) Anti-modalização conservadora
# =====================================================

RE_MODAL_START = re.compile(r"^(É necessário|É preciso|Deve haver|Tem de haver)\b", re.IGNORECASE)

def paragrafo_e_interrogativo_ou_hipotetico(par: str) -> bool:
    p = (par or "")
    # sinais: "?" OU padrões orais típicos ("o que é que", "não é?", "mas", "se calhar")
    if "?" in p:
        return True
    if re.search(r"\bo que é que\b|\bserá que\b|\bnão é\?\b|\bse calhar\b", p, re.IGNORECASE):
        return True
    # "tem de haver" numa pergunta oral sem ponto de interrogação
    if re.search(r"\b(o que é que )?tem de haver\b", p, re.IGNORECASE):
        return True
    return False

def desmodalizar_se_adequado(texto_prop: str, texto_paragrafo: str) -> Tuple[str, Optional[str]]:
    """
    Troca só o arranque modal por uma formulação neutra, quando o parágrafo é interrogativo/hipotético.
    Não mexe no resto.
    """
    t = texto_prop.strip()
    if not RE_MODAL_START.search(t):
        return t, None
    if not paragrafo_e_interrogativo_ou_hipotetico(texto_paragrafo):
        return t, None

    # substituições conservadoras
    t2 = re.sub(r"^(É necessário que exista|É necessário haver)\s+", "Coloca-se a questão de haver ", t, flags=re.IGNORECASE)
    t2 = re.sub(r"^(É necessário que exista)\s+", "Coloca-se a questão de existir ", t2, flags=re.IGNORECASE)
    t2 = re.sub(r"^(É necessário)\s+", "Coloca-se a questão de ", t2, flags=re.IGNORECASE)
    t2 = re.sub(r"^(Deve haver)\s+", "Coloca-se a hipótese de haver ", t2, flags=re.IGNORECASE)
    t2 = re.sub(r"^(Tem de haver)\s+", "Coloca-se a questão de haver ", t2, flags=re.IGNORECASE)

    if t2 != t:
        return t2, "desmodalizado_por_contexto"
    return t, None


# =====================================================
# 8) IA: contexto + prompt
# =====================================================

def construir_contexto_conceitos(conceitos: Dict[str, Dict[str, Any]], limite_chars: int = 22000) -> str:
    linhas: List[str] = []
    for did in sorted(conceitos.keys()):
        info = conceitos[did]
        nome = info.get("nome", "") if isinstance(info.get("nome"), str) else ""
        n = info.get("nivel", None)
        defin = ""
        d = info.get("definicao")
        if isinstance(d, dict):
            defin = d.get("texto", "") if isinstance(d.get("texto"), str) else ""
        elif isinstance(d, str):
            defin = d
        defin = normalizar_espacos(defin)[:240]
        linhas.append(f"- {did} (N{n}) {nome}: {defin}")

    txt = "\n".join(linhas)
    if len(txt) <= limite_chars:
        return txt

    out: List[str] = []
    total = 0
    for ln in linhas:
        if total + len(ln) + 1 > limite_chars:
            break
        out.append(ln)
        total += len(ln) + 1
    out.append("... (contexto truncado)")
    return "\n".join(out)

def construir_contexto_ops(ops_meta: Set[str]) -> str:
    if not ops_meta:
        return "NÃO DISPONÍVEL. Devolve operacoes: []."
    return ", ".join(sorted(ops_meta))

def construir_prompt(unidade: UnidadeBruta, contexto_conceitos: str, ops_meta: Set[str], max_props: int) -> str:
    ctx_ops = construir_contexto_ops(ops_meta)
    return f"""
AGE COMO COMPILADOR ONTOLÓGICO RÍGIDO.

OBJETIVO:
Segmenta o PARÁGRAFO em proposições atómicas.
Para cada proposição, fornece CANDIDATOS de classificação:
- campo_principal (D_*)
- campos_secundarios (D_*) (poucos)
- percurso (D_*) (curto)
- operacoes (OP_*) apenas se disponíveis

REGRAS:
1) Responde APENAS JSON (array).
2) Máximo de {max_props} proposições.
3) "texto": reescrita mínima/quase literal; NÃO acrescentar.
4) Evita modais fortes (necessário/deve) se o parágrafo for interrogativo.
5) D_* e OP_* têm de existir no contexto.

CONTEXTO DE CONCEITOS (D_*):
{contexto_conceitos}

CONTEXTO DE OPERAÇÕES (OP_*):
{ctx_ops}

PARÁGRAFO:
{unidade.texto}

ESQUEMA:
[
  {{
    "texto": "…",
    "campo_principal": "D_…",
    "campos_secundarios": ["D_…"],
    "percurso": ["D_…"],
    "operacoes": ["OP_…"],
    "confianca": 0.0,
    "nota_curta": "opcional"
  }}
]
""".strip()


# =====================================================
# 9) OUTPUT
# =====================================================

def id_estavel(data_frag: Optional[str], hash_prop: str) -> str:
    return f"P{yyyymmdd_from_date(data_frag)}_{hash_prop[:12]}"

def normalizar_texto_proposicao(s: str) -> str:
    return normalizar_espacos(s)


# =====================================================
# 10) FALHAS
# =====================================================

def registar_falha(unidade: UnidadeBruta, erro: str, tentativa: int, prompt: str, resposta: str) -> None:
    dados: List[Dict[str, Any]] = []
    if os.path.exists(FALHAS_OUT):
        try:
            x = load_json(FALHAS_OUT)
            if isinstance(x, list):
                dados = x
        except Exception:
            dados = []

    dados.append({
        "hash_unidade": unidade.hash_unidade,
        "origem_id": unidade.origem_id,
        "data": unidade.data,
        "n_paragrafo": unidade.n_paragrafo,
        "erro": str(erro),
        "tentativa": tentativa,
        "timestamp": now_ts(),
        "bloco": safe_excerpt(unidade.texto, 1400),
        "prompt_excerto": safe_excerpt(prompt, 1600),
        "resposta_excerto": safe_excerpt(resposta, 1600),
    })
    save_json(FALHAS_OUT, dados)


# =====================================================
# 11) MAIN
# =====================================================

def _must_exist(path: str, label: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{label} não encontrado: {path}")

def main() -> None:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY não encontrado no .env")

    client = genai.Client(api_key=api_key)

    _must_exist(BRUTO_MD, "BRUTO_MD")
    _must_exist(CONCEITOS_FILE, "CONCEITOS_FILE")
    _must_exist(CAPITULOS_FILE, "CAPITULOS_FILE")

    conceitos = carregar_conceitos(CONCEITOS_FILE)
    capitulos = carregar_capitulos(CAPITULOS_FILE)
    campo_to_caps = construir_campo_to_caps(capitulos)

    ops_meta = extrair_ops_meta_indice(META_INDICE_FILE)  # opcional
    ops_conc = ops_por_conceito(conceitos)

    contexto_conceitos = construir_contexto_conceitos(conceitos)

    md = ler_bruto(BRUTO_MD)
    unidades = extrair_unidades(md)

    props = carregar_proposicoes(PROPOSICOES_OUT)
    hashes_prop = hashes_proposicoes_existentes(props)

    estado = carregar_estado(ESTADO_OUT)
    unidades_estado: Dict[str, Any] = estado.get("unidades", {})
    if not isinstance(unidades_estado, dict):
        unidades_estado = {}
        estado["unidades"] = unidades_estado

    print("=" * 95)
    print(f"EXTRATOR (SPEC BEST v3) | root={DOREAL_ROOT}")
    print(f"Unidades: {len(unidades)} | D_*: {len(conceitos)} | CAP_*: {len([k for k in capitulos if isinstance(k,str) and k.startswith('CAP_')])} | OP_* meta: {len(ops_meta)}")
    print(f"Existentes: {len(props)} | VERSAO_REGRAS={VERSAO_REGRAS} | FORCAR={FORCAR_REPROCESSAMENTO} | REPROCESSAR_FALHAS={REPROCESSAR_FALHAS}")
    print(f"Limites: secundários={MAX_SECUNDARIOS} percurso={MAX_PERCURSO} | MIN_SCORE_CP={MIN_SCORE_CP} sec={MIN_SCORE_SEC} perc={MIN_SCORE_PERC}")
    print("=" * 95)

    processadas = ignoradas = falhadas = novas = 0

    for idx, u in enumerate(unidades, start=1):
        h = u.hash_unidade
        reg = unidades_estado.get(h, {})
        status = reg.get("status")
        vreg = reg.get("versao_regras")

        deve = True
        if not FORCAR_REPROCESSAMENTO:
            if status == "ok" and vreg == VERSAO_REGRAS:
                deve = False
            elif status == "falha" and not REPROCESSAR_FALHAS:
                deve = False
        if not deve:
            ignoradas += 1
            continue

        processadas += 1
        print(f"\n▶ [{idx}/{len(unidades)}] {u.origem_id} | data={u.data or 'null'} | n={u.n_paragrafo} | hash={h[:12]}…")

        prompt = construir_prompt(u, contexto_conceitos, ops_meta, MAX_PROPOSICOES_POR_UNIDADE)
        prompt_hash = sha256(prompt)
        last_resp = ""
        last_err = None

        for tentativa in range(1, TENTATIVAS_POR_UNIDADE + 1):
            try:
                resp = client.models.generate_content(model=MODELO_IA, contents=prompt)
                last_resp = getattr(resp, "text", "") or ""
                raw = limpar_json_envelope(last_resp)
                items = json.loads(raw)
                if not isinstance(items, list):
                    raise ValueError("IA não devolveu um array JSON.")

                props_novas: List[Dict[str, Any]] = []

                for it in items:
                    if not isinstance(it, dict):
                        continue

                    texto = normalizar_texto_proposicao(ensure_str(it.get("texto")) or "")
                    if not texto or len(texto) < 3:
                        continue

                    # anti-modalização determinística (quando o parágrafo é interrogativo/hipotético)
                    texto2, nota_desmod = desmodalizar_se_adequado(texto, u.texto)
                    texto = texto2

                    cp_ai = ensure_str(it.get("campo_principal"))
                    cs_ai = [x for x in ensure_list(it.get("campos_secundarios")) if isinstance(x, str)]
                    percurso_ai = [x for x in ensure_list(it.get("percurso")) if isinstance(x, str)]
                    ops_ai = [x for x in ensure_list(it.get("operacoes")) if isinstance(x, str)]
                    conf = ensure_float_01(it.get("confianca")) or 0.5
                    nota = ensure_str(it.get("nota_curta"))

                    # Validar candidatos D_*
                    candidatos = []
                    if cp_ai and cp_ai in conceitos:
                        candidatos.append(cp_ai)
                    candidatos += [d for d in cs_ai if d in conceitos]
                    candidatos += [d for d in percurso_ai if d in conceitos]
                    candidatos = dedupe_preserve_order(candidatos)

                    # Campo principal: escolha determinística (ponto crucial)
                    cp = escolher_campo_principal_deterministico(conceitos, candidatos, texto, u.texto)
                    if not cp:
                        # fallback clássico: nível mais alto / definição curta
                        cp = candidatos[0] if candidatos else None
                    if not cp or cp not in conceitos:
                        continue

                    # Secundários e percurso (limpeza + ancoragem)
                    cs = [d for d in cs_ai if d in conceitos and d != cp]
                    percurso = [d for d in percurso_ai if d in conceitos]

                    # se o cp da IA for diferente do cp escolhido, rebaixa para secundário (se for válido)
                    if cp_ai and cp_ai in conceitos and cp_ai != cp:
                        cs = [cp_ai] + cs

                    cs = cortar_secundarios(conceitos, cp, cs)
                    percurso = sanitizar_percurso(conceitos, percurso, cp)
                    cs, percurso = filtrar_por_ancoragem(conceitos, cp, cs, percurso, texto, u.texto)
                    cs = cortar_secundarios(conceitos, cp, cs)
                    percurso = sanitizar_percurso(conceitos, percurso, cp)

                    # OP_*: validação dupla (meta_indice + por conceito, se existir)
                    ops_clean: List[str] = []
                    if ops_ai:
                        cand_ops = [op for op in ops_ai if isinstance(op, str) and op.startswith("OP_")]
                        if ops_meta:
                            cand_ops = [op for op in cand_ops if op in ops_meta]
                        # se houver whitelist por conceito, aplica
                        whitelist = ops_conc.get(cp, set())
                        if whitelist:
                            cand_ops = [op for op in cand_ops if op in whitelist]
                        ops_clean = dedupe_preserve_order(cand_ops)

                    # dedupe global
                    hprop = sha256(texto)
                    if hprop in hashes_prop:
                        continue

                    # CAP_* (determinístico)
                    cap_p = cap_principal(cp, campo_to_caps)
                    caps_rel = caps_dos_campos(cs + percurso, campo_to_caps)
                    if cap_p:
                        caps_rel.discard(cap_p)

                    percurso_caps = caps_dos_campos(percurso, campo_to_caps)
                    niveis: Set[int] = set()
                    for d in [cp] + cs + percurso:
                        n = nivel_conceito(conceitos, d)
                        if isinstance(n, int):
                            niveis.add(n)

                    tipo = tipo_ponte_ou_normal(cap_p, caps_rel, niveis, percurso_caps)

                    # nota final
                    nota_final = nota
                    if nota_desmod:
                        nota_final = (nota_final + " | " if nota_final else "") + nota_desmod

                    props_novas.append({
                        "id": id_estavel(u.data, hprop),
                        "origem": {
                            "ficheiro": os.path.basename(BRUTO_MD),
                            "origem_id": u.origem_id,
                            "data": u.data,
                            "n_paragrafo": u.n_paragrafo,
                            "hash_unidade": u.hash_unidade,
                        },
                        "texto": texto,
                        "hash_proposicao": hprop,
                        "classificacao": {
                            "campo_principal": cp,
                            "campos_secundarios": cs,
                            "capitulo_principal": cap_p if cap_p else "CAP_NAO_MAPEADO",
                            "capitulos_relacionados": sorted(caps_rel),
                            "tipo": tipo,
                            "percurso": percurso,
                            "operacoes_ontologicas": ops_clean,
                            "confianca": conf,
                            "nota": nota_final,
                        },
                        "ia": {
                            "modelo": MODELO_IA,
                            "versao_regras": VERSAO_REGRAS,
                            "prompt_hash": prompt_hash,
                        },
                        "timestamp": now_ts(),
                    })

                if not props_novas:
                    raise ValueError("Nenhuma proposição nova/válida após validação/dedupe.")

                for p in props_novas:
                    props.append(p)
                    hashes_prop.add(p["hash_proposicao"])
                novas += len(props_novas)
                save_json(PROPOSICOES_OUT, props)

                unidades_estado[h] = {
                    "status": "ok",
                    "versao_regras": VERSAO_REGRAS,
                    "ts": now_ts(),
                    "tentativas": tentativa,
                    "last_error": None,
                    "origem_id": u.origem_id,
                    "data": u.data,
                    "n_paragrafo": u.n_paragrafo,
                }
                guardar_estado(ESTADO_OUT, estado)

                print(f"   ✅ Guardadas: {len(props_novas)} | total={len(props)}")
                break

            except Exception as e:
                last_err = str(e)
                print(f"   ⚠️ Tentativa {tentativa}/{TENTATIVAS_POR_UNIDADE} falhou: {e}")
                registar_falha(u, last_err, tentativa, prompt, last_resp)
                time.sleep(PAUSA_ENTRE_CHAMADAS)

        else:
            falhadas += 1
            unidades_estado[h] = {
                "status": "falha",
                "versao_regras": VERSAO_REGRAS,
                "ts": now_ts(),
                "tentativas": TENTATIVAS_POR_UNIDADE,
                "last_error": last_err,
                "origem_id": u.origem_id,
                "data": u.data,
                "n_paragrafo": u.n_paragrafo,
            }
            guardar_estado(ESTADO_OUT, estado)
            print("   ❌ Falhou definitivamente (registado em falhas).")

        time.sleep(PAUSA_ENTRE_CHAMADAS)

    print("\n" + "=" * 95)
    print("RESUMO")
    print(f"Processadas: {processadas} | Ignoradas: {ignoradas} | Falhadas: {falhadas} | Novas: {novas}")
    print(f"Saída:  {PROPOSICOES_OUT}")
    print(f"Estado: {ESTADO_OUT}")
    if os.path.exists(FALHAS_OUT):
        print(f"Falhas: {FALHAS_OUT}")
    print("=" * 95)


if __name__ == "__main__":
    main()