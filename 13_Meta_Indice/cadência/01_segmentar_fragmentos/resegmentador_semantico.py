from __future__ import annotations

import os
import re
import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from google import genai

# =========================================================
# 0) CONFIGURAÇÃO
# =========================================================

VERSAO_SEGMENTADOR = "resegmentador_semantico_v4_1_duas_fases"
MODELO_IA = "models/gemini-2.5-flash"

FICHEIRO_ENTRADA = "containers_segmentacao.json"
FICHEIRO_SAIDA = "fragmentos_resegmentados.json"
FICHEIRO_ESTADO = "estado_resegmentador.json"
FICHEIRO_FALHAS = "falhas_resegmentador.json"

TENTATIVAS_POR_CONTAINER = 3
PAUSA_ENTRE_CHAMADAS = 1.2

FORCAR_REPROCESSAMENTO = False
REPROCESSAR_FALHAS = True

MAX_PARAGRAFOS_POR_CONTAINER = 10
MAX_CHARS_POR_CONTAINER = 4500
MAX_CONCEITOS = 5

# =========================================================
# 1) UTILITÁRIOS
# =========================================================

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")

def normalizar_espacos(texto: str) -> str:
    texto = (texto or "").replace("\u00A0", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()

def sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()

def limpar_json_envelope(texto: str) -> str:
    texto = re.sub(r"```(?:json)?\s*|\s*```", "", (texto or "")).strip()
    m = re.search(r"(\[.*\]|\{.*\})", texto, re.DOTALL)
    return m.group(1).strip() if m else texto.strip()

def safe_excerpt(s: str, n: int = 1500) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + " …(truncado)…"

def contar_frases_aprox(texto: str) -> int:
    texto = normalizar_espacos(texto)
    if not texto:
        return 0
    partes = re.split(r"[.!?]+(?:\s+|$)", texto)
    partes = [p.strip() for p in partes if p.strip()]
    return max(1, len(partes))

def tipo_material_default(container: Dict[str, Any]) -> str:
    t = container.get("tipo_material_fonte")
    return t if isinstance(t, str) and t.strip() else "misto"

def total_chars_container(paragrafos: List[Dict[str, Any]]) -> int:
    return sum(len(normalizar_espacos(p.get("texto", ""))) for p in paragrafos)

def densidade_aprox(texto: str) -> str:
    n = len(normalizar_espacos(texto))
    if n < 180:
        return "baixa"
    if n < 500:
        return "media"
    return "alta"

def confianca_nivel(v: Any) -> str:
    try:
        x = float(v)
    except Exception:
        if isinstance(v, str) and v in {"baixa", "media", "alta"}:
            return v
        return "media"
    if x < 0.45:
        return "baixa"
    if x < 0.75:
        return "media"
    return "alta"

def limpar_tema_curto(s: Any, max_palavras: int = 5) -> str:
    s = str(s or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" ,;:.–—-")
    palavras = s.split()
    if len(palavras) > max_palavras:
        palavras = palavras[:max_palavras]
    return " ".join(palavras)

def conceito_eh_aceitavel(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    if "(" in s or ")" in s:
        return False
    if len(s.split()) > 4:
        return False
    if re.search(r"\b(é|são|ser|estar|tem|têm|vai|vão|deve|devem|pode|podem)\b", s, re.IGNORECASE):
        return False
    return True

def limpar_conceitos(cur: Any, max_conceitos: int = 5) -> List[str]:
    if not isinstance(cur, list):
        return []
    out: List[str] = []
    vistos = set()

    for x in cur:
        s = str(x).strip()
        s = re.sub(r"\s+", " ", s)
        s = s.strip(" ,;:.–—-")
        if not conceito_eh_aceitavel(s):
            continue
        key = s.lower()
        if key in vistos:
            continue
        vistos.add(key)
        out.append(s)
        if len(out) >= max_conceitos:
            break

    return out

# =========================================================
# 2) ESTADO
# =========================================================

def carregar_estado(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {
            "versao_segmentador": VERSAO_SEGMENTADOR,
            "containers": {},
            "ultima_execucao": None
        }
    data = load_json(path)
    if not isinstance(data, dict):
        return {
            "versao_segmentador": VERSAO_SEGMENTADOR,
            "containers": {},
            "ultima_execucao": None
        }
    if not isinstance(data.get("containers"), dict):
        data["containers"] = {}
    data.setdefault("versao_segmentador", VERSAO_SEGMENTADOR)
    return data

def guardar_estado(path: str, estado: Dict[str, Any]) -> None:
    estado["versao_segmentador"] = VERSAO_SEGMENTADOR
    estado["ultima_execucao"] = now_ts()
    save_json(path, estado)

def carregar_fragmentos_existentes(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    data = load_json(path)
    return data if isinstance(data, list) else []

# =========================================================
# 3) FALHAS
# =========================================================

def registar_falha(
    container: Dict[str, Any],
    fase: str,
    erro: str,
    tentativa: int,
    prompt: str,
    resposta: str
) -> None:
    dados: List[Dict[str, Any]] = []
    if os.path.exists(FICHEIRO_FALHAS):
        try:
            x = load_json(FICHEIRO_FALHAS)
            if isinstance(x, list):
                dados = x
        except Exception:
            dados = []

    dados.append({
        "container_id": container.get("container_id"),
        "ordem_no_ficheiro": container.get("ordem_no_ficheiro"),
        "fase": fase,
        "erro": str(erro),
        "tentativa": tentativa,
        "timestamp": now_ts(),
        "prompt_excerto": safe_excerpt(prompt, 2200),
        "resposta_excerto": safe_excerpt(resposta, 2200)
    })
    save_json(FICHEIRO_FALHAS, dados)

# =========================================================
# 4) PROMPTS
# =========================================================

def construir_prompt_fase1_segmentacao(container: Dict[str, Any]) -> str:
    paragrafos = container.get("paragrafos", [])
    linhas = []
    for p in paragrafos:
        pid = p.get("paragrafo_id")
        txt = p.get("texto")
        linhas.append(f"[{pid}] {txt}")

    bloco_paragrafos = "\n\n".join(linhas)

    meta = {
        "container_id": container.get("container_id"),
        "titulo_container": container.get("titulo_container"),
        "data": container.get("data"),
        "tipo_material_fonte": tipo_material_default(container),
        "n_paragrafos": len(paragrafos),
        "n_chars_total": total_chars_container(paragrafos)
    }

    return f"""
És um segmentador semântico rigoroso e conservador.

TAREFA:
Agrupa os parágrafos consecutivos deste container em fragmentos semanticamente íntegros.

REGRAS:
1. Não reescrevas o texto.
2. Não expliques a decisão.
3. Não comentes o conteúdo.
4. Não escolhas D_*, CAP_* ou OP_*.
5. Não mudes a ordem.
6. Não repitas parágrafos.
7. Não deixes parágrafos por usar.
8. Cada parágrafo tem de aparecer exatamente uma vez.
9. Cada grupo tem de conter apenas IDs consecutivos e na ordem original.
10. Responde APENAS JSON válido.

METADADOS:
{json.dumps(meta, ensure_ascii=False, indent=2)}

PARÁGRAFOS:
{bloco_paragrafos}

DEVOLVE APENAS:
[
  {{
    "paragrafos_origem": ["ID1", "ID2"]
  }},
  {{
    "paragrafos_origem": ["ID3"]
  }}
]
""".strip()

def construir_prompt_fase2_enriquecimento(fragmento_base: Dict[str, Any]) -> str:
    meta = {
        "fragment_id": fragmento_base.get("fragment_id"),
        "paragrafos_agregados": fragmento_base.get("paragrafos_agregados"),
        "frases_aproximadas": fragmento_base.get("frases_aproximadas"),
        "n_chars_fragmento": fragmento_base.get("n_chars_fragmento"),
        "tipo_material_fonte": fragmento_base.get("tipo_material_fonte")
    }

    texto = fragmento_base.get("texto_fragmento", "")

    return f"""
És um anotador leve de fragmentos.

TAREFA:
Enriquecer este fragmento com metadados mínimos para análise de cadência.

REGRAS:
1. Não alteres o texto.
2. Não expliques longamente.
3. Não faças crítica filosófica.
4. Não escolhas D_*, CAP_* ou OP_*.
5. O tema dominante deve ser curto, seco e estrutural.
6. Evita títulos editoriais, expressivos ou demasiado bonitos.
7. Dá no máximo {MAX_CONCEITOS} conceitos.
8. Os conceitos devem ser nucleares e curtos.
9. Evita frases, juízos, citações e formulações interpretativas.
10. Responde APENAS JSON válido.

METADADOS:
{json.dumps(meta, ensure_ascii=False, indent=2)}

TEXTO:
{texto}

DEVOLVE APENAS:
{{
  "tipo_unidade": "bloco_unico | afirmacao_curta | distincao_conceptual | desenvolvimento_curto | desenvolvimento_medio | sequencia_argumentativa | objecao_local | resposta_local | transicao_reflexiva | fragmento_intuitivo",
  "criterio_de_unidade": "container_atomico | continuidade_tematica | continuidade_argumentativa | continuidade_definicional | continuidade_reflexiva | fecho_suficiente | mudanca_de_tema | mudanca_de_funcao | quebra_de_escala | quebra_de_objeto",
  "funcao_textual_dominante": "afirmacao | definicao | desenvolvimento | distincao | objecao | resposta | transicao | exploracao | pergunta_reflexiva | critica | sintese_provisoria",
  "tema_dominante_provisorio": "máx 5 palavras, expressão seca e estrutural",
  "conceitos_relevantes_provisorios": ["máx 5 conceitos curtos, nucleares e não frásicos"],
  "integridade_semantica": {{
    "grau": "baixo | medio | alto"
  }},
  "confianca_segmentacao": "baixa | media | alta"
}}
""".strip()

# =========================================================
# 5) VALIDAÇÃO FASE 1
# =========================================================

def validar_fase1_segmentacao(
    container: Dict[str, Any],
    resposta: Any
) -> Tuple[List[str], Optional[List[List[str]]]]:
    erros: List[str] = []

    if not isinstance(resposta, list):
        return ["A resposta da fase 1 não é uma lista JSON."], None

    ids_esperados = [
        p["paragrafo_id"]
        for p in container.get("paragrafos", [])
        if isinstance(p, dict) and isinstance(p.get("paragrafo_id"), str)
    ]
    set_esperados = set(ids_esperados)

    grupos: List[List[str]] = []
    ids_vistos: List[str] = []

    for i, item in enumerate(resposta, start=1):
        if not isinstance(item, dict):
            erros.append(f"Grupo {i} não é objeto.")
            continue

        pars = item.get("paragrafos_origem")
        if not isinstance(pars, list) or not pars or not all(isinstance(x, str) for x in pars):
            erros.append(f"Grupo {i} sem paragrafos_origem válidos.")
            continue

        if len(set(pars)) != len(pars):
            erros.append(f"Grupo {i} repete IDs internamente.")
            continue

        grupos.append(pars)
        ids_vistos.extend(pars)

    if erros:
        return erros, None

    set_vistos = set(ids_vistos)
    if set_vistos != set_esperados:
        faltam = sorted(list(set_esperados - set_vistos))
        sobram = sorted(list(set_vistos - set_esperados))
        if faltam:
            erros.append(f"Faltam parágrafos na fase 1: {faltam}")
        if sobram:
            erros.append(f"Há parágrafos inesperados na fase 1: {sobram}")

    repetidos = sorted({x for x in ids_vistos if ids_vistos.count(x) > 1})
    if repetidos:
        erros.append(f"Parágrafos repetidos na fase 1: {repetidos}")

    if ids_vistos != ids_esperados:
        erros.append("A ordem dos parágrafos não foi preservada na fase 1.")

    pos = {pid: i for i, pid in enumerate(ids_esperados)}
    for idx, grupo in enumerate(grupos, start=1):
        indices = [pos[g] for g in grupo]
        esperado = list(range(min(indices), max(indices) + 1))
        if indices != esperado:
            erros.append(f"Grupo {idx} não contém IDs consecutivos.")

    return erros, grupos if not erros else None

# =========================================================
# 6) CONSTRUÇÃO FRAGMENTOS BASE
# =========================================================

def construir_fragmentos_base(
    container: Dict[str, Any],
    grupos_segmentacao: List[List[str]]
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    map_pars = {
        p["paragrafo_id"]: p
        for p in container.get("paragrafos", [])
        if isinstance(p, dict) and isinstance(p.get("paragrafo_id"), str)
    }

    container_id = container.get("container_id")
    origem_ficheiro = container.get("origem_ficheiro")
    data = container.get("data")
    tipo_material_fonte = tipo_material_default(container)
    ordem_no_ficheiro = container.get("ordem_no_ficheiro")
    titulo_container = container.get("titulo_container")
    tem_header_formal = container.get("tem_header_formal")
    header_original = container.get("header_original")

    for i, grupo in enumerate(grupos_segmentacao, start=1):
        textos_originais = [map_pars[pid]["texto"] for pid in grupo if pid in map_pars]
        texto_fragmento = "\n\n".join(textos_originais).strip()
        texto_normalizado = normalizar_espacos(texto_fragmento)

        out.append({
            "fragment_id": f"{container_id}_SEG_{i:03d}",
            "origem": {
                "ficheiro": origem_ficheiro,
                "origem_id": container_id,
                "data": data,
                "titulo_container": titulo_container,
                "tem_header_formal": tem_header_formal,
                "header_original": header_original,
                "ordem_no_ficheiro": ordem_no_ficheiro,
                "blocos_fonte": [
                    {
                        "bloco_id": container_id,
                        "paragrafos_origem": grupo
                    }
                ]
            },
            "tipo_material_fonte": tipo_material_fonte,
            "texto_fragmento": texto_fragmento,
            "texto_normalizado": texto_normalizado,
            "texto_fonte_reconstituido": texto_fragmento,
            "paragrafos_agregados": len(grupo),
            "frases_aproximadas": contar_frases_aprox(texto_fragmento),
            "n_chars_fragmento": len(texto_normalizado),
            "densidade_aprox": densidade_aprox(texto_fragmento)
        })

    return out

# =========================================================
# 7) VALIDAÇÃO FASE 2
# =========================================================

def validar_fase2_enriquecimento(resposta: Any) -> Dict[str, Any]:
    if not isinstance(resposta, dict):
        return {
            "tipo_unidade": "desenvolvimento_curto",
            "criterio_de_unidade": "continuidade_argumentativa",
            "funcao_textual_dominante": "desenvolvimento",
            "tema_dominante_provisorio": "",
            "conceitos_relevantes_provisorios": [],
            "integridade_semantica": {"grau": "medio"},
            "confianca_segmentacao": "media"
        }

    integridade = resposta.get("integridade_semantica")
    if not isinstance(integridade, dict):
        integridade = {"grau": "medio"}

    grau = integridade.get("grau", "medio")
    if grau not in {"baixo", "medio", "alto"}:
        grau = "medio"

    conf = resposta.get("confianca_segmentacao", "media")
    conf = confianca_nivel(conf)

    tema = limpar_tema_curto(resposta.get("tema_dominante_provisorio"), max_palavras=5)
    conceitos = limpar_conceitos(resposta.get("conceitos_relevantes_provisorios"), max_conceitos=MAX_CONCEITOS)

    if grau in {"baixo", "medio"} and conf == "alta":
        conf = "media"

    return {
        "tipo_unidade": resposta.get("tipo_unidade") or "desenvolvimento_curto",
        "criterio_de_unidade": resposta.get("criterio_de_unidade") or "continuidade_argumentativa",
        "funcao_textual_dominante": resposta.get("funcao_textual_dominante") or "desenvolvimento",
        "tema_dominante_provisorio": tema,
        "conceitos_relevantes_provisorios": conceitos,
        "integridade_semantica": {"grau": grau},
        "confianca_segmentacao": conf
    }

# =========================================================
# 8) ENRIQUECIMENTO FINAL
# =========================================================

def aplicar_enriquecimento_fragmento(
    fragmento_base: Dict[str, Any],
    enriquecimento: Dict[str, Any],
    n_total_fragmentos_no_container: int,
    idx_fragmento: int
) -> Dict[str, Any]:
    fragmento = dict(fragmento_base)

    fragmento["segmentacao"] = {
        "tipo_unidade": enriquecimento["tipo_unidade"],
        "criterio_de_unidade": enriquecimento["criterio_de_unidade"],
        "houve_fusao_de_paragrafos": fragmento_base["paragrafos_agregados"] > 1,
        "houve_corte_interno": n_total_fragmentos_no_container > 1,
        "container_tipo_segmentacao": "segmentacao_semantica_duas_fases"
    }

    fragmento["funcao_textual_dominante"] = enriquecimento["funcao_textual_dominante"]
    fragmento["tema_dominante_provisorio"] = enriquecimento["tema_dominante_provisorio"].lower()
    fragmento["conceitos_relevantes_provisorios"] = [
        c.lower() for c in enriquecimento["conceitos_relevantes_provisorios"]
    ]
    fragmento["integridade_semantica"] = enriquecimento["integridade_semantica"]
    fragmento["confianca_segmentacao"] = enriquecimento["confianca_segmentacao"]

    cid = fragmento["origem"]["origem_id"]

    fragmento["relacoes_locais"] = {
        "fragmento_anterior": f"{cid}_SEG_{idx_fragmento-1:03d}" if idx_fragmento > 1 else None,
        "fragmento_seguinte": f"{cid}_SEG_{idx_fragmento+1:03d}" if idx_fragmento < n_total_fragmentos_no_container else None,
        "continua_anterior": idx_fragmento > 1,
        "prepara_seguinte": idx_fragmento < n_total_fragmentos_no_container
    }

    fragmento["estado_revisao"] = "segmentado_auto"
    fragmento["sinalizador_para_cadencia"] = {
        "pronto_para_extrator_cadencia": True,
        "requer_revisao_manual_prioritaria": enriquecimento["confianca_segmentacao"] == "baixa"
    }

    fragmento["_metadados_segmentador"] = {
        "modelo": MODELO_IA,
        "versao_segmentador": VERSAO_SEGMENTADOR,
        "timestamp": now_ts(),
        "hash_texto_normalizado": sha256(fragmento["texto_normalizado"])
    }

    return fragmento

# =========================================================
# 9) CONTROLO DE PROCESSAMENTO
# =========================================================

def deve_processar_container(
    container: Dict[str, Any],
    estado_containers: Dict[str, Any]
) -> bool:
    cid = container.get("container_id")
    reg = estado_containers.get(cid, {})

    status = reg.get("status")
    versao = reg.get("versao_segmentador")

    if FORCAR_REPROCESSAMENTO:
        return True

    if status == "ok" and versao == VERSAO_SEGMENTADOR:
        return False

    if status == "falha" and not REPROCESSAR_FALHAS:
        return False

    return True

def remover_fragmentos_de_container(
    fragmentos: List[Dict[str, Any]],
    container_id: str
) -> List[Dict[str, Any]]:
    out = []
    for f in fragmentos:
        origem = f.get("origem", {})
        if origem.get("origem_id") != container_id:
            out.append(f)
    return out

# =========================================================
# 10) MAIN
# =========================================================

def main() -> None:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY não encontrado no .env")

    if not os.path.exists(FICHEIRO_ENTRADA):
        raise FileNotFoundError(f"Ficheiro de entrada não encontrado: {FICHEIRO_ENTRADA}")

    client = genai.Client(api_key=api_key)

    containers = load_json(FICHEIRO_ENTRADA)
    if not isinstance(containers, list):
        raise RuntimeError("containers_segmentacao.json tem de ter raiz em lista.")

    estado = carregar_estado(FICHEIRO_ESTADO)
    estado_containers = estado.get("containers", {})
    if not isinstance(estado_containers, dict):
        estado_containers = {}
        estado["containers"] = estado_containers

    fragmentos_existentes = carregar_fragmentos_existentes(FICHEIRO_SAIDA)

    print("=" * 90)
    print(f"RESEGMENTADOR DUAS FASES | modelo={MODELO_IA} | versão={VERSAO_SEGMENTADOR}")
    print(f"Containers: {len(containers)} | saída atual: {len(fragmentos_existentes)} fragmentos")
    print("=" * 90)

    processados = 0
    ignorados = 0
    falhados = 0
    fragmentos_processados = 0

    for idx, container in enumerate(containers, start=1):
        cid = container.get("container_id")
        paragrafos = container.get("paragrafos", [])

        if not isinstance(paragrafos, list) or not paragrafos:
            print(f"\n▶ [{idx}/{len(containers)}] {cid} | vazio → ignorado")
            ignorados += 1
            continue

        total_chars = total_chars_container(paragrafos)

        if len(paragrafos) > MAX_PARAGRAFOS_POR_CONTAINER or total_chars > MAX_CHARS_POR_CONTAINER:
            print(
                f"\n▶ [{idx}/{len(containers)}] {cid} | demasiado grande "
                f"(parágrafos={len(paragrafos)}, chars={total_chars}) → falha preventiva"
            )
            estado_containers[cid] = {
                "status": "falha",
                "versao_segmentador": VERSAO_SEGMENTADOR,
                "ts": now_ts(),
                "tentativas": 0,
                "last_error": (
                    f"Container com {len(paragrafos)} parágrafos e {total_chars} chars "
                    f"ultrapassa limites ({MAX_PARAGRAFOS_POR_CONTAINER} / {MAX_CHARS_POR_CONTAINER})"
                )
            }
            guardar_estado(FICHEIRO_ESTADO, estado)
            falhados += 1
            continue

        if not deve_processar_container(container, estado_containers):
            ignorados += 1
            continue

        processados += 1
        print(f"\n▶ [{idx}/{len(containers)}] {cid} | parágrafos={len(paragrafos)} | chars={total_chars}")

        # =========================
        # FASE 1 — SEGMENTAÇÃO PURA
        # =========================
        prompt_f1 = construir_prompt_fase1_segmentacao(container)
        last_resp_f1 = ""
        grupos_segmentacao = None
        last_err = None

        for tentativa in range(1, TENTATIVAS_POR_CONTAINER + 1):
            try:
                resp = client.models.generate_content(
                    model=MODELO_IA,
                    contents=prompt_f1
                )
                last_resp_f1 = getattr(resp, "text", "") or ""
                raw = limpar_json_envelope(last_resp_f1)
                items = json.loads(raw)

                erros_f1, grupos_segmentacao = validar_fase1_segmentacao(container, items)
                if erros_f1:
                    raise ValueError(" | ".join(erros_f1))
                break

            except Exception as e:
                last_err = str(e)
                print(f"   ⚠️ Fase 1 tentativa {tentativa}/{TENTATIVAS_POR_CONTAINER} falhou: {e}")
                registar_falha(container, "fase_1_segmentacao", last_err, tentativa, prompt_f1, last_resp_f1)
                time.sleep(PAUSA_ENTRE_CHAMADAS)

        if grupos_segmentacao is None:
            falhados += 1
            estado_containers[cid] = {
                "status": "falha",
                "versao_segmentador": VERSAO_SEGMENTADOR,
                "ts": now_ts(),
                "tentativas": TENTATIVAS_POR_CONTAINER,
                "last_error": last_err
            }
            guardar_estado(FICHEIRO_ESTADO, estado)
            print("   ❌ Falhou definitivamente na fase 1.")
            continue

        fragmentos_base = construir_fragmentos_base(container, grupos_segmentacao)

        # =========================
        # FASE 2 — ENRIQUECIMENTO
        # =========================
        fragmentos_finais: List[Dict[str, Any]] = []

        for i_frag, frag_base in enumerate(fragmentos_base, start=1):
            prompt_f2 = construir_prompt_fase2_enriquecimento(frag_base)
            last_resp_f2 = ""
            enriquecimento_validado = None

            for tentativa in range(1, TENTATIVAS_POR_CONTAINER + 1):
                try:
                    resp = client.models.generate_content(
                        model=MODELO_IA,
                        contents=prompt_f2
                    )
                    last_resp_f2 = getattr(resp, "text", "") or ""
                    raw = limpar_json_envelope(last_resp_f2)
                    item = json.loads(raw)
                    enriquecimento_validado = validar_fase2_enriquecimento(item)
                    break

                except Exception as e:
                    last_err = str(e)
                    print(f"   ⚠️ Fase 2 frag {i_frag} tentativa {tentativa}/{TENTATIVAS_POR_CONTAINER} falhou: {e}")
                    registar_falha(container, f"fase_2_enriquecimento_frag_{i_frag}", last_err, tentativa, prompt_f2, last_resp_f2)
                    time.sleep(PAUSA_ENTRE_CHAMADAS)

            if enriquecimento_validado is None:
                enriquecimento_validado = {
                    "tipo_unidade": "desenvolvimento_curto",
                    "criterio_de_unidade": "continuidade_argumentativa",
                    "funcao_textual_dominante": "desenvolvimento",
                    "tema_dominante_provisorio": "",
                    "conceitos_relevantes_provisorios": [],
                    "integridade_semantica": {"grau": "medio"},
                    "confianca_segmentacao": "media"
                }

            frag_final = aplicar_enriquecimento_fragmento(
                frag_base,
                enriquecimento_validado,
                len(fragmentos_base),
                i_frag
            )
            fragmentos_finais.append(frag_final)

        fragmentos_existentes = remover_fragmentos_de_container(fragmentos_existentes, cid)
        fragmentos_existentes.extend(fragmentos_finais)
        save_json(FICHEIRO_SAIDA, fragmentos_existentes)

        estado_containers[cid] = {
            "status": "ok",
            "versao_segmentador": VERSAO_SEGMENTADOR,
            "ts": now_ts(),
            "tentativas": TENTATIVAS_POR_CONTAINER,
            "last_error": None,
            "n_fragmentos_gerados": len(fragmentos_finais),
            "modo": "duas_fases"
        }
        guardar_estado(FICHEIRO_ESTADO, estado)

        fragmentos_processados += len(fragmentos_finais)
        print(f"   ✅ OK | fragmentos gerados: {len(fragmentos_finais)}")

        time.sleep(PAUSA_ENTRE_CHAMADAS)

    print("\n" + "=" * 90)
    print("RESUMO")
    print(f"Processados:            {processados}")
    print(f"Ignorados:              {ignorados}")
    print(f"Falhados:               {falhados}")
    print(f"Fragmentos processados: {fragmentos_processados}")
    print(f"Saída:                  {FICHEIRO_SAIDA}")
    print(f"Estado:                 {FICHEIRO_ESTADO}")
    if os.path.exists(FICHEIRO_FALHAS):
        print(f"Falhas:                 {FICHEIRO_FALHAS}")
    print("=" * 90)

if __name__ == "__main__":
    main()