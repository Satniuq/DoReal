#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tratar_fragmentos_resegmentados_api.py

Script incremental para tratar fragmentos novos já resegmentados.

Colocar em:
  00_Pipeline_fragmentos/01_scripts/tratar_fragmentos_resegmentados_api.py

Entrada padrão:
  00_Pipeline_fragmentos/04_outputs_prontos_para_integrar/fragmentos_resegmentados__*.json

Saída principal:
  00_Pipeline_fragmentos/05_tratamento/06_instancia_parcial_novas_runs/
    03_entidades_fragmentos__parte_003.json

Não altera as partes canónicas 001/002.
"""
from __future__ import annotations

import argparse, hashlib, json, os, re, time, unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

SCRIPT_VERSION = "tratamento_fragmentos_resegmentados_api_v1_3"
DEFAULT_MODEL = "gpt-5.4"

SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = PIPELINE_DIR.parent
BASE_REF_DIR = PIPELINE_DIR / "02_base_referencia"
INSTANCIA_DIR = BASE_REF_DIR / "instancia_total_dividida"
READY_DIR = PIPELINE_DIR / "04_outputs_prontos_para_integrar"
TRAT_DIR = PIPELINE_DIR / "05_tratamento"
CONTEXT_DIR = TRAT_DIR / "00_contexto_tratamento"
CACHE_DIR = TRAT_DIR / "01_cache_api"
OUT_FRAGMENT_DIR = TRAT_DIR / "02_outputs_por_fragmento"
REPORT_DIR = TRAT_DIR / "03_relatorios"
PARTIAL_DIR = TRAT_DIR / "06_instancia_parcial_novas_runs"
BASE_PARTS = [INSTANCIA_DIR / "03_entidades_fragmentos__parte_001.json", INSTANCIA_DIR / "03_entidades_fragmentos__parte_002.json"]

STOPWORDS = set("a à ao aos as às e é o os um uma uns umas de do da dos das em no na nos nas por para com sem que se não nao como mas ou porque quando isto isso aquilo este esta estes estas ele ela eles elas eu tu nós nos vos lhe lhes me te também tambem mais menos muito pouco ser estar ter há ha vai vou era foi são sao seja pronto sei lá la".split())

TEMPLATE_JSON = r'''
{
  "camada_textual_derivada": {
    "estado_limpeza": "limpeza_minima",
    "texto_limpo": "",
    "resumo_alteracoes": ["Limpeza textual gerada automaticamente."],
    "notas_cautela": ["Revisão humana recomendada antes de uso expositivo forte."],
    "modelo": "",
    "gerado_em_utc": "",
    "sinalizar_revisao_humana": true
  },
  "camada_analitica": {
    "cadencia": {
      "funcao_cadencia_principal": "formulacao_inicial",
      "funcao_cadencia_secundaria": null,
      "direcao_movimento": "introduz",
      "grau_de_abertura_argumentativa": "introducao",
      "centralidade": "exploratorio",
      "estatuto_no_percurso": "solto_ainda_sem_encaixe",
      "zona_provavel_percurso": "indefinida",
      "ponte_entre_zonas": false,
      "prepara_fragmento_seguinte": false,
      "fecha_algo_anterior": false,
      "incide_sobre_erro": false,
      "familia_erro_provavel": "nao_aplicavel",
      "erro_dominante_provavel": null,
      "dominio_contributivo_principal": "indefinido",
      "tipo_fragmento_provavel": "fragmento_intuitivo",
      "aproveitamento_editorial": "material_a_retrabalhar",
      "necessita_revisao_humana": true,
      "confianca_cadencia": "baixa",
      "justificacao_curta_cadencia": "Cadência gerada automaticamente; rever antes de uso estrutural forte."
    },
    "tratamento_filosofico": {
      "explicacao_textual_do_que_o_fragmento_tenta_fazer": "A rever.",
      "trabalho_no_sistema": "material_sem_encaixe",
      "trabalho_no_sistema_secundario": null,
      "descricao_funcional_curta": "Material a rever.",
      "problema_filosofico_central": "indefinido",
      "problemas_filosoficos_associados": [],
      "tipo_de_problema": "indefinido",
      "posicao_no_indice": {
        "parte_id": null,
        "capitulo_id": null,
        "capitulo_titulo": null,
        "subcapitulo_ou_zona_interna": null,
        "argumento_canonico_relacionado": null,
        "argumentos_canonicos_associados": [],
        "grau_de_pertenca_ao_indice": "indefinida",
        "modo_de_pertenca": "material_a_retrabalhar",
        "justificacao_de_posicao_no_indice": "Encaixe ainda não estabilizado."
      },
      "estrutura_analitica": {
        "objeto_em_analise": "A rever.",
        "plano_ontologico": "A rever.",
        "plano_epistemologico": "A rever.",
        "plano_etico": "A rever.",
        "plano_antropologico": "A rever.",
        "plano_mediacional": "A rever.",
        "distincao_central": "A rever.",
        "dependencia_principal": "A rever.",
        "criterio_implicado": "A rever.",
        "erro_visado": "A rever.",
        "consequencia_principal": "A rever.",
        "pressuposto_ontologico_principal": "Há real e o fragmento deve ser reconduzido ao real que tenta dizer.",
        "pressupostos_secundarios": []
      },
      "potencial_argumentativo": {
        "estado_argumentativo": "formulacao_pre_argumentativa",
        "premissas_implicitas": [],
        "premissa_central_reconstruida": "A rever.",
        "conclusao_visada": "A rever.",
        "forma_de_inferencia": "indefinida",
        "forca_logica_estimada": "baixa",
        "argumento_reconstruivel": false,
        "necessita_reconstrucao_forte": true,
        "observacoes_argumentativas": "A rever."
      },
      "relacoes_no_sistema": {
        "depende_de_conceitos": [],
        "mobiliza_operacoes": [],
        "regimes_envolvidos": [],
        "percursos_envolvidos": [],
        "abre_para": [],
        "corrige": [],
        "prepara": [],
        "pressupoe": [],
        "entra_em_tensao_com": []
      },
      "destino_editorial": {
        "destino_editorial_fino": "material_a_retrabalhar",
        "papel_editorial_primario": "material_a_retrabalhar",
        "papel_editorial_secundario": "apoio_argumentativo",
        "prioridade_de_revisao": "alta",
        "prioridade_de_aproveitamento": "media",
        "requer_reescrita": true,
        "requer_densificacao": true,
        "requer_formalizacao_logica": false,
        "observacoes_editoriais": "Rever antes de integração canónica."
      },
      "avaliacao_global": {
        "densidade_filosofica": "media",
        "clareza_atual": "instavel",
        "grau_de_estabilizacao": "muito_provisorio",
        "risco_de_ma_interpretacao": "alto",
        "confianca_tratamento_filosofico": "baixa",
        "necessita_revisao_humana_filosofica": true
      }
    },
    "impacto_no_mapa": {
      "resumo_do_fragmento_para_o_mapa": "A rever.",
      "tese_principal_relevante": "A rever.",
      "zona_filosofica_dominante": "indefinida",
      "tipo_de_utilidade_principal": "tematica",
      "proposicoes_do_mapa_tocadas": [],
      "efeito_principal_no_mapa": "sem_impacto_relevante",
      "efeitos_secundarios": [],
      "impacto_editorial_e_dedutivo": {
        "tipo_de_densificacao": "nao_se_aplica",
        "o_que_o_fragmento_acrescenta_ao_mapa": "A rever.",
        "justificacao_nova_que_fornece": "A rever.",
        "objecoes_que_ajuda_a_bloquear": [],
        "mediacao_que_fornece": "nao fornece mediacao estrutural",
        "conceitos_ou_distincoes_novas": [],
        "obriga_a_reescrever_o_passo": false,
        "obriga_a_dividir_o_passo": false,
        "obriga_a_criar_passo_intermedio": false,
        "proposta_de_nova_formulacao": null,
        "proposta_de_novo_passo": null,
        "entre_que_passos_deveria_entrar": []
      },
      "decisao_final": {
        "acao_recomendada_sobre_o_mapa": "sem_acao",
        "prioridade_editorial": "baixa",
        "confianca_da_analise": "baixa",
        "necessita_revisao_humana": true,
        "observacao_final": "A rever."
      }
    },
    "proposicoes_extraidas": []
  },
  "camada_estrutural": {
    "conceitos_acionados": [],
    "operacoes_acionadas": [],
    "proposicoes_relacionadas": [],
    "argumentos_relacionados": [],
    "percursos_relacionados": [],
    "ramos_relacionados": []
  },
  "camada_expositiva": {
    "cfs_envolvidos": [],
    "capitulos_envolvidos": [],
    "faixas_envolvidas": [],
    "papel_editorial": "api_ok",
    "travoes": ["não usar como prova estrutural fechada"],
    "fontes_locais_governativas": [
      {"tipo_entidade": "peca_governativa", "id": "PG_GRELHA_RECONHECIMENTO"},
      {"tipo_entidade": "peca_governativa", "id": "PG_PROLOGO_SOBERANO"},
      {"tipo_entidade": "peca_governativa", "id": "PG_README_CAPITULOS"},
      {"tipo_entidade": "peca_governativa", "id": "PG_README_FINAL_METODO"}
    ]
  },
  "estado_local": {
    "estado_validacao": "valido_com_cautela",
    "estado_excecao": "sem_excecao_mas_baixa_confianca",
    "excecao_ids": [],
    "necessita_revisao_humana": true,
    "confianca": "baixa"
  }
}
'''


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    for p in [READY_DIR, TRAT_DIR, CONTEXT_DIR, CACHE_DIR, OUT_FRAGMENT_DIR, REPORT_DIR, PARTIAL_DIR]:
        p.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_text(path: Path, max_chars: Optional[int] = None) -> str:
    if not path.exists():
        return ""
    txt = path.read_text(encoding="utf-8", errors="ignore")
    return txt[:max_chars] if max_chars and len(txt) > max_chars else txt


def norm_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00A0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def norm_match(text: str) -> str:
    text = norm_text(text).casefold()
    text = re.sub(r"[#*_`>\[\]{}()]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def toks(text: str) -> set[str]:
    return {t for t in re.findall(r"\w{4,}", norm_match(text)) if t not in STOPWORDS and not t.isdigit()}


def score(q: set[str], candidate: str) -> float:
    c = toks(candidate)
    if not q or not c:
        return 0.0
    return len(q & c) / max(1, len(q | c))


def sha(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def compact(text: Any, n: int = 600) -> str:
    s = norm_text(str(text or ""))
    return s if len(s) <= n else s[:n].rstrip() + " [...]"


def deep_update(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_update(base[k], v)
        else:
            base[k] = v
    return base


def list_str(value: Any, limit: int = 12) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    out = []
    for x in value[:limit]:
        s = str(x).strip()
        if s and s not in out:
            out.append(s)
    return out


def as_bool(v: Any, default: bool = False) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        if v.lower() in {"true", "sim", "yes", "1"}:
            return True
        if v.lower() in {"false", "não", "nao", "no", "0"}:
            return False
    return default


def infer_entity_type(rid: str) -> str:
    if rid.startswith("D_"):
        return "conceito"
    if rid.startswith("OP_"):
        return "operacao"
    if rid.startswith("ARG_"):
        return "argumento"
    if rid.startswith("CAP_") or rid.startswith("PROLOGO"):
        return "capitulo"
    if rid.startswith("CF"):
        return "cf"
    if rid.startswith("RA_"):
        return "ramo"
    if rid.startswith("P"):
        return "proposicao"
    return "entidade"


def entity_refs(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []
    out, seen = [], set()
    for r in value:
        if isinstance(r, str):
            rid = r.strip()
            tipo = infer_entity_type(rid)
        elif isinstance(r, dict):
            rid = str(r.get("id") or "").strip()
            tipo = str(r.get("tipo_entidade") or "").strip() or infer_entity_type(rid)
        else:
            continue
        if rid and (tipo, rid) not in seen:
            seen.add((tipo, rid))
            out.append({"tipo_entidade": tipo, "id": rid})
    return out


def simple_clean(text: str) -> str:
    text = norm_text(text)
    text = re.sub(r"\b(não é\?\s*){2,}", "não é? ", text, flags=re.I)
    text = re.sub(r"\b(sei lá,?\s*){2,}", "sei lá, ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def default_layers(fragment: Dict[str, Any], generated_by: str, model: str) -> Dict[str, Any]:
    data = json.loads(TEMPLATE_JSON)
    text = fragment.get("texto_fragmento") or fragment.get("texto_normalizado") or ""
    clean = simple_clean(text)
    tema = fragment.get("tema_dominante_provisorio") or "tema a rever"
    data["camada_textual_derivada"]["texto_limpo"] = clean
    data["camada_textual_derivada"]["modelo"] = model if generated_by == "api" else "heuristico_local"
    data["camada_textual_derivada"]["gerado_em_utc"] = utc_now()
    data["camada_analitica"]["cadencia"]["prepara_fragmento_seguinte"] = bool((fragment.get("relacoes_locais") or {}).get("prepara_seguinte"))
    data["camada_analitica"]["cadencia"]["incide_sobre_erro"] = "erro" in norm_match(text)
    data["camada_analitica"]["cadencia"]["tipo_fragmento_provavel"] = (fragment.get("segmentacao") or {}).get("tipo_unidade") or "fragmento_intuitivo"
    data["camada_analitica"]["tratamento_filosofico"]["explicacao_textual_do_que_o_fragmento_tenta_fazer"] = f"O fragmento parece explorar {tema}, mas requer revisão para estabilização."
    data["camada_analitica"]["tratamento_filosofico"]["descricao_funcional_curta"] = compact(tema, 180)
    data["camada_analitica"]["tratamento_filosofico"]["problemas_filosoficos_associados"] = list_str(fragment.get("conceitos_relevantes_provisorios"), 8)
    data["camada_analitica"]["tratamento_filosofico"]["estrutura_analitica"]["objeto_em_analise"] = compact(clean, 260)
    data["camada_analitica"]["impacto_no_mapa"]["resumo_do_fragmento_para_o_mapa"] = compact(clean, 350)
    if generated_by == "api":
        data["camada_analitica"]["cadencia"]["confianca_cadencia"] = "media"
        data["camada_analitica"]["tratamento_filosofico"]["avaliacao_global"]["grau_de_estabilizacao"] = "provisorio"
        data["camada_analitica"]["tratamento_filosofico"]["avaliacao_global"]["confianca_tratamento_filosofico"] = "media"
        data["camada_analitica"]["impacto_no_mapa"]["decisao_final"]["confianca_da_analise"] = "media"
        data["estado_local"]["estado_validacao"] = "valido_com_cautela"
        data["estado_local"]["confianca"] = "media"
    else:
        data["camada_expositiva"]["papel_editorial"] = "heuristico_a_rever"
        data["camada_expositiva"]["travoes"] = ["tratamento heurístico local", "não usar como prova estrutural fechada"]
        data["estado_local"]["estado_validacao"] = "a_rever"
        data["estado_local"]["confianca"] = "baixa"
    return data


def find_file(name: str, search_project: bool = False) -> Optional[Path]:
    for root in [CONTEXT_DIR, BASE_REF_DIR, INSTANCIA_DIR, PIPELINE_DIR]:
        p = root / name
        if p.exists():
            return p
    if search_project:
        ignored = {".git", "__pycache__", "node_modules", ".venv", "venv"}
        for p in PROJECT_ROOT.rglob(name):
            if p.is_file() and not any(part in ignored for part in p.parts):
                return p
    return None


def find_glob(pattern: str, search_project: bool = False) -> List[Path]:
    out: List[Path] = []
    for root in [CONTEXT_DIR, BASE_REF_DIR, INSTANCIA_DIR, PIPELINE_DIR]:
        for p in root.glob(pattern):
            if p.is_file() and p not in out:
                out.append(p)
    if search_project:
        ignored = {".git", "__pycache__", "node_modules", ".venv", "venv"}
        for p in PROJECT_ROOT.rglob(pattern):
            if p.is_file() and not any(part in ignored for part in p.parts) and p not in out:
                out.append(p)
    return sorted(out)


def load_base_fragments() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for p in BASE_PARTS:
        if p.exists():
            data = read_json(p)
            if isinstance(data, dict) and isinstance(data.get("fragmentos"), list):
                out.extend([x for x in data["fragmentos"] if isinstance(x, dict)])
    return out


def load_ready(input_paths: Optional[List[str]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    if input_paths:
        paths = []
        for raw in input_paths:
            p = Path(raw)
            if not p.is_absolute():
                for c in [Path.cwd() / p, SCRIPT_DIR / p, PIPELINE_DIR / p, READY_DIR / p]:
                    if c.exists():
                        p = c.resolve()
                        break
            if not p.exists():
                raise SystemExit(f"[erro] Input não encontrado: {raw}")
            paths.append(p)
    else:
        paths = sorted(READY_DIR.glob("fragmentos_resegmentados__*.json"))
    items: List[Dict[str, Any]] = []
    used: List[str] = []
    seen: set[str] = set()
    for p in paths:
        data = read_json(p)
        frags = data.get("fragmentos") if isinstance(data, dict) else data if isinstance(data, list) else None
        if not isinstance(frags, list):
            raise SystemExit(f"[erro] Formato não reconhecido: {p}")
        used.append(str(p))
        for f in frags:
            fid = f.get("fragment_id") if isinstance(f, dict) else None
            if fid and fid not in seen:
                seen.add(fid)
                items.append(f)
    return items, used


def load_proposicoes(search_project: bool) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for p in find_glob("07_entidades_proposicoes__parte_*.json", search_project):
        data = read_json(p)
        if not isinstance(data, dict):
            continue
        for x in data.get("proposicoes", []) or []:
            if not isinstance(x, dict):
                continue
            loc = x.get("localizacao_vertical") or {}
            out.append({
                "id": x.get("id"), "texto_literal": x.get("texto_literal"),
                "campo_principal": loc.get("campo_principal"),
                "campos_secundarios": loc.get("campos_secundarios", []),
                "operacao_ontologica": x.get("operacao_ontologica", []),
                "dependencias": x.get("dependencias", []), "gera": x.get("gera", [])
            })
    return [x for x in out if x.get("id")]


def load_argumentos(search_project: bool) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for p in find_glob("08_entidades_argumentos__parte_*.json", search_project):
        data = read_json(p)
        if not isinstance(data, dict):
            continue
        for x in data.get("argumentos", []) or []:
            if not isinstance(x, dict):
                continue
            est = x.get("estrutura_logica") or {}
            out.append({"id": x.get("id"), "capitulo": x.get("capitulo"), "conceito_alvo": x.get("conceito_alvo"), "conclusao": est.get("conclusao"), "premissas": (est.get("premissas") or [])[:3]})
    return [x for x in out if x.get("id")]


def load_percursos(search_project: bool) -> List[Dict[str, Any]]:
    p = find_file("09_entidades_percursos_ramos_capitulos.json", search_project)
    if not p:
        return []
    data = read_json(p)
    out: List[Dict[str, Any]] = []
    for x in data.get("percursos", []) if isinstance(data, dict) else []:
        desc = x.get("descricao") or {}
        out.append({"id": x.get("id"), "nome": x.get("nome"), "tipo": x.get("tipo"), "descricao": desc.get("texto") if isinstance(desc, dict) else desc})
    return [x for x in out if x.get("id")]


def load_chapters(search_project: bool) -> List[Dict[str, Any]]:
    p = find_file("MAPEAMENTO_FRAGMENTOS_POR_CAPITULO.md", search_project)
    if not p:
        return []
    text = read_text(p)
    matches = list(re.finditer(r"^##\s+(.+)$", text, re.M))
    out: List[Dict[str, Any]] = []
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        if not (title.startswith("PRÓLOGO") or title.startswith("Capítulo")):
            continue
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append({"titulo": title, "texto": compact(text[start:end], 2800)})
    return out


def load_notes(search_project: bool) -> Dict[str, str]:
    names = ["00_manifesto_governanca.json", "11_arbitragem_transversal.json", "NOTA_DE_DESTINACAO_DA_OBRA.md", "NOTA_DE_LEITURA_DOS_CAPITULOS__SER_DIZER_ERRO_REINSCRICAO.md", "Nota_voz_cadencia_expositiva.md", "MERGED__02_capitulos_provisorios.md"]
    out: Dict[str, str] = {}
    for name in names:
        p = find_file(name, search_project)
        if not p:
            continue
        if p.suffix.lower() == ".json":
            data = read_json(p)
            if name == "00_manifesto_governanca.json" and isinstance(data, dict):
                data = {"meta_schema": data.get("meta_schema", {}), "governanca": data.get("governanca", {})}
            elif name == "11_arbitragem_transversal.json" and isinstance(data, dict):
                data = {"arbitragem_transversal_excertos": (data.get("arbitragem_transversal") or [])[:20]}
            out[name] = compact(json.dumps(data, ensure_ascii=False), 5000)
        else:
            out[name] = compact(read_text(p), 5000)
    return out


def select(items: List[Dict[str, Any]], text: str, keys: List[str], limit: int) -> List[Dict[str, Any]]:
    q = toks(text)
    scored = []
    for item in items:
        cand = " ".join(json.dumps(item.get(k, ""), ensure_ascii=False) if isinstance(item.get(k), (dict, list)) else str(item.get(k, "")) for k in keys)
        s = score(q, cand)
        if s > 0:
            clipped = {k: compact(v, 500) if isinstance(v, str) else v[:8] if isinstance(v, list) else v for k, v in item.items()}
            clipped["_score_contextual"] = round(s, 4)
            scored.append((s, clipped))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored[:limit]]


def canonical_examples(base: List[Dict[str, Any]], text: str, limit: int = 3) -> List[Dict[str, Any]]:
    q = toks(text)
    scored = []
    for f in base:
        anal = f.get("camada_analitica") or {}
        if not anal.get("tratamento_filosofico"):
            continue
        emp = f.get("camada_empirica") or {}
        txt = f.get("camada_textual_derivada") or {}
        cand = " ".join([emp.get("texto_fragmento") or "", txt.get("texto_limpo") or "", json.dumps(anal.get("tratamento_filosofico"), ensure_ascii=False)[:2000]])
        scored.append((score(q, cand), f))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: List[Dict[str, Any]] = []
    for s, f in scored[:limit]:
        emp = f.get("camada_empirica") or {}
        txt = f.get("camada_textual_derivada") or {}
        anal = f.get("camada_analitica") or {}
        trat = anal.get("tratamento_filosofico") or {}
        imp = anal.get("impacto_no_mapa") or {}
        out.append({
            "fragment_id": f.get("fragment_id"),
            "score_contextual": round(s, 4),
            "texto_limpo": compact(txt.get("texto_limpo") or emp.get("texto_fragmento"), 700),
            "cadencia": anal.get("cadencia"),
            "tratamento_filosofico": {
                "explicacao": compact(trat.get("explicacao_textual_do_que_o_fragmento_tenta_fazer"), 600),
                "trabalho_no_sistema": trat.get("trabalho_no_sistema"),
                "descricao_funcional_curta": trat.get("descricao_funcional_curta"),
                "problema_filosofico_central": trat.get("problema_filosofico_central"),
                "tipo_de_problema": trat.get("tipo_de_problema"),
                "avaliacao_global": trat.get("avaliacao_global"),
            },
            "impacto_no_mapa": {
                "resumo": imp.get("resumo_do_fragmento_para_o_mapa"),
                "tese": imp.get("tese_principal_relevante"),
                "zona": imp.get("zona_filosofica_dominante"),
                "proposicoes": (imp.get("proposicoes_do_mapa_tocadas") or [])[:4],
                "decisao_final": imp.get("decisao_final"),
            },
            "camada_estrutural": f.get("camada_estrutural"),
            "camada_expositiva": f.get("camada_expositiva"),
        })
    return out


def build_context(fragment: Dict[str, Any], base: List[Dict[str, Any]], search_project: bool) -> Dict[str, Any]:
    text = fragment.get("texto_fragmento") or fragment.get("texto_normalizado") or ""
    return {
        "exemplos_canonicos": canonical_examples(base, text, 3),
        "proposicoes_candidatas": select(load_proposicoes(search_project), text, ["texto_literal", "campo_principal", "campos_secundarios", "operacao_ontologica", "dependencias", "gera"], 10),
        "argumentos_candidatos": select(load_argumentos(search_project), text, ["id", "capitulo", "conceito_alvo", "conclusao", "premissas"], 6),
        "percursos_candidatos": select(load_percursos(search_project), text, ["id", "nome", "tipo", "descricao"], 8),
        "capitulos_candidatos": select(load_chapters(search_project), text, ["titulo", "texto"], 6),
        "notas_governativas": load_notes(search_project),
    }


def prompt_for(fragment: Dict[str, Any], context: Dict[str, Any], model: str) -> str:
    frag = {k: fragment.get(k) for k in ["fragment_id", "tipo_material_fonte", "texto_fragmento", "texto_normalizado", "segmentacao", "funcao_textual_dominante", "tema_dominante_provisorio", "conceitos_relevantes_provisorios", "integridade_semantica", "confianca_segmentacao", "relacoes_locais"]}
    obj = {
        "tarefa": "Trata filosoficamente este fragmento resegmentado novo, produzindo camadas compatíveis com a instância canónica DoReal.",
        "idioma": "português de Portugal",
        "regras": [
            "A base empírica prevalece: não inventes conteúdo que não esteja no fragmento.",
            "A limpeza melhora legibilidade, mas não apaga ambiguidade relevante.",
            "Se o fragmento for fraco, visual, editorial, oral ou meta-livro, marca revisão humana e não forces impacto forte no mapa.",
            "A camada estrutural deve usar apenas ids realmente apoiados pelo texto ou deixar arrays vazios.",
            "A camada expositiva governa uso e travões; não forces capítulo.",
            "Cadência transversal: ser em causa → dizer/representar → erro/desvio → reinscrição no real.",
            "Responde apenas com JSON válido, sem markdown.",
        ],
        "fragmento": frag,
        "contexto_candidato": context,
        "template_de_saida": default_layers(fragment, "api", model),
    }
    return json.dumps(obj, ensure_ascii=False, indent=2)


def parse_json_obj(text: str) -> Dict[str, Any]:
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        obj = json.loads(text[start:end + 1])
        if isinstance(obj, dict):
            return obj
    raise ValueError("resposta sem objeto JSON válido")


def extract_response_text(resp: Any) -> str:
    if hasattr(resp, "output_text") and resp.output_text:
        return str(resp.output_text)
    parts = []
    for item in getattr(resp, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            if getattr(content, "text", None):
                parts.append(content.text)
    return "\n".join(parts).strip()


def call_api(client: Any, model: str, prompt: str, retries: int, sleep: float) -> Dict[str, Any]:
    last = None
    schema = {"type": "object", "additionalProperties": True, "required": ["camada_textual_derivada", "cadencia", "tratamento_filosofico", "impacto_no_mapa", "camada_estrutural", "camada_expositiva", "estado_local"], "properties": {}}
    for attempt in range(retries):
        try:
            try:
                resp = client.responses.create(model=model, input=prompt, store=False, text={"format": {"type": "json_schema", "name": "tratamento_fragmento", "schema": schema, "strict": False}})
                return parse_json_obj(extract_response_text(resp))
            except Exception:
                resp = client.chat.completions.create(model=model, messages=[{"role": "system", "content": "Responde apenas com JSON válido."}, {"role": "user", "content": prompt}], response_format={"type": "json_object"})
                return parse_json_obj(resp.choices[0].message.content or "")
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(sleep)
    raise RuntimeError(f"falha API: {last}")


def normalize_result(raw: Dict[str, Any], fragment: Dict[str, Any], generated_by: str, model: str) -> Dict[str, Any]:
    base = default_layers(fragment, generated_by, model)
    raw = raw if isinstance(raw, dict) else {}
    anal = raw.get("camada_analitica") if isinstance(raw.get("camada_analitica"), dict) else {}
    for key in ["cadencia", "tratamento_filosofico", "impacto_no_mapa", "proposicoes_extraidas"]:
        if key in raw and key not in anal:
            anal[key] = raw.get(key)
    raw["camada_analitica"] = anal
    deep_update(base, raw)

    text = fragment.get("texto_fragmento") or fragment.get("texto_normalizado") or ""
    txt = base["camada_textual_derivada"]
    txt["texto_limpo"] = norm_text(txt.get("texto_limpo") or simple_clean(text))
    txt["resumo_alteracoes"] = list_str(txt.get("resumo_alteracoes"), 8) or ["Limpeza textual gerada automaticamente."]
    txt["notas_cautela"] = list_str(txt.get("notas_cautela"), 8)
    txt["modelo"] = model if generated_by == "api" else "heuristico_local"
    txt["gerado_em_utc"] = utc_now()
    txt["sinalizar_revisao_humana"] = as_bool(txt.get("sinalizar_revisao_humana"), True)

    anal = base["camada_analitica"]
    anal["proposicoes_extraidas"] = anal.get("proposicoes_extraidas") if isinstance(anal.get("proposicoes_extraidas"), list) else []

    estrut = base["camada_estrutural"]
    for key in ["conceitos_acionados", "operacoes_acionadas", "proposicoes_relacionadas", "argumentos_relacionados", "percursos_relacionados", "ramos_relacionados"]:
        estrut[key] = entity_refs(estrut.get(key))

    expo = base["camada_expositiva"]
    for key in ["cfs_envolvidos", "capitulos_envolvidos", "faixas_envolvidas", "fontes_locais_governativas"]:
        expo[key] = entity_refs(expo.get(key))
    if not expo["fontes_locais_governativas"]:
        expo["fontes_locais_governativas"] = default_layers(fragment, "api", model)["camada_expositiva"]["fontes_locais_governativas"]
    expo["travoes"] = list_str(expo.get("travoes"), 10)

    estado = base["estado_local"]
    estado["necessita_revisao_humana"] = as_bool(estado.get("necessita_revisao_humana"), True)
    estado["excecao_ids"] = list_str(estado.get("excecao_ids"), 10)
    return base


def empirical_layer(f: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["origem", "tipo_material_fonte", "texto_fragmento", "texto_normalizado", "texto_fonte_reconstituido", "paragrafos_agregados", "frases_aproximadas", "n_chars_fragmento", "densidade_aprox", "segmentacao", "funcao_textual_dominante", "tema_dominante_provisorio", "conceitos_relevantes_provisorios", "integridade_semantica", "confianca_segmentacao", "relacoes_locais", "_metadados_segmentador"]
    return {k: f.get(k) for k in keys}


def canonical_fragment(src: Dict[str, Any], layers: Dict[str, Any], model: str, generated_by: str) -> Dict[str, Any]:
    return {
        "fragment_id": src.get("fragment_id"),
        "camada_empirica": empirical_layer(src),
        "camada_textual_derivada": layers["camada_textual_derivada"],
        "camada_analitica": layers["camada_analitica"],
        "camada_estrutural": layers["camada_estrutural"],
        "camada_expositiva": layers["camada_expositiva"],
        "estado_local": layers["estado_local"],
        "_metadados_tratamento_incremental": {
            "versao_script": SCRIPT_VERSION,
            "modelo": model if generated_by == "api" else "heuristico_local",
            "gerado_em_utc": utc_now(),
            "hash_texto_empirico": sha(src.get("texto_normalizado") or src.get("texto_fragmento") or ""),
            "gerado_por_api": generated_by == "api",
        },
    }


def cache_path(f: Dict[str, Any]) -> Path:
    return CACHE_DIR / f"{f.get('fragment_id')}.tratamento_api.json"


def load_cache(f: Dict[str, Any], force: bool) -> Optional[Dict[str, Any]]:
    p = cache_path(f)
    if force or not p.exists():
        return None
    data = read_json(p)
    h = sha(f.get("texto_normalizado") or f.get("texto_fragmento") or "")
    if data.get("hash_texto_empirico") == h and isinstance(data.get("result"), dict):
        return data["result"]
    return None


def save_cache(f: Dict[str, Any], result: Dict[str, Any], model: str, source: str) -> None:
    write_json(cache_path(f), {"fragment_id": f.get("fragment_id"), "hash_texto_empirico": sha(f.get("texto_normalizado") or f.get("texto_fragmento") or ""), "modelo": model, "source": source, "gerado_em_utc": utc_now(), "result": result})


def treat_fragment(f: Dict[str, Any], base: List[Dict[str, Any]], client: Optional[Any], args: argparse.Namespace, counters: Dict[str, int]) -> Dict[str, Any]:
    cached = load_cache(f, args.force)
    if cached is not None:
        counters["cache"] += 1
        layers = normalize_result(cached, f, "api", args.model)
        return canonical_fragment(f, layers, args.model, "api")
    context = build_context(f, base, args.search_project_context)
    if client is not None and not args.local_only:
        raw = call_api(client, args.model, prompt_for(f, context, args.model), args.retries, args.sleep)
        counters["api"] += 1
        save_cache(f, raw, args.model, "api")
        layers = normalize_result(raw, f, "api", args.model)
        return canonical_fragment(f, layers, args.model, "api")
    raw = default_layers(f, "heuristico", "heuristico_local")
    counters["local"] += 1
    save_cache(f, raw, "heuristico_local", "local")
    layers = normalize_result(raw, f, "heuristico", "heuristico_local")
    return canonical_fragment(f, layers, "heuristico_local", "heuristico")


def existing_base_ids() -> set[str]:
    return {str(f.get("fragment_id")) for f in load_base_fragments() if f.get("fragment_id")}


def existing_incremental() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for p in PARTIAL_DIR.glob("03_entidades_fragmentos__parte_*.json"):
        data = read_json(p)
        if isinstance(data, dict):
            for f in data.get("fragmentos", []) or []:
                if isinstance(f, dict) and f.get("fragment_id"):
                    out[str(f["fragment_id"])] = f
    return out


def sort_key(fid: str) -> Tuple[int, str]:
    m = re.search(r"F(\d+)", fid or "")
    return (int(m.group(1)) if m else 10**9, fid or "")


def count_base() -> int:
    total = 0
    for p in BASE_PARTS:
        if p.exists():
            data = read_json(p)
            if isinstance(data, dict) and isinstance(data.get("fragmentos"), list):
                total += len(data["fragmentos"])
    return total


def write_parts(new_items: List[Dict[str, Any]], args: argparse.Namespace) -> List[Path]:
    merged = existing_incremental()
    for f in new_items:
        merged[str(f["fragment_id"])] = f
    ordered = sorted(merged.values(), key=lambda f: sort_key(str(f.get("fragment_id"))))
    chunks = [ordered[i:i + args.max_part_size] for i in range(0, len(ordered), args.max_part_size)]
    written: List[Path] = []
    offset = count_base()
    total_parts = args.part_num + len(chunks) - 1 if chunks else args.part_num
    for idx, chunk in enumerate(chunks):
        num = args.part_num + idx
        p = PARTIAL_DIR / f"03_entidades_fragmentos__parte_{num:03d}.json"
        payload = {
            "parte": num,
            "total_partes": total_parts,
            "offset_inicio": offset,
            "offset_fim_exclusivo": offset + len(chunk),
            "fragmentos": chunk,
            "_metadados_incrementais": {
                "versao_script": SCRIPT_VERSION,
                "gerado_em_utc": utc_now(),
                "estado": "incremental_nao_integrado_na_base_canonica",
                "observacao": "Parte incremental tratada. Não altera as partes canónicas 001/002.",
            },
        }
        write_json(p, payload)
        written.append(p)
        offset += len(chunk)
    return written


def write_report(written: List[Path], treated: List[Dict[str, Any]], inputs: List[str], counters: Dict[str, int], errors: List[Dict[str, str]]) -> Tuple[Path, Path]:
    index_path = PARTIAL_DIR / "INDEX_NOVOS_FRAGMENTOS_TRATADOS.json"
    report_path = REPORT_DIR / f"relatorio_tratamento_novas_runs__{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    outs = []
    for p in written:
        data = read_json(p)
        outs.append({"ficheiro": str(p), "parte": data.get("parte"), "offset_inicio": data.get("offset_inicio"), "offset_fim_exclusivo": data.get("offset_fim_exclusivo"), "n_fragmentos": len(data.get("fragmentos", []))})
    write_json(index_path, {"gerado_em_utc": utc_now(), "versao_script": SCRIPT_VERSION, "estado": "incremental_tratado_nao_integrado_na_base_canonica", "input_files": inputs, "outputs": outs, "fragmentos_tratados_ou_atualizados": [f.get("fragment_id") for f in treated], "estatisticas": {**counters, "errors": len(errors), "error_items": errors}})
    lines = ["# Relatório — tratamento incremental de fragmentos resegmentados", "", "## Estado", "", "- Estado: `incremental_tratado_nao_integrado_na_base_canonica`", f"- Gerado em UTC: `{utc_now()}`", "", "## Inputs", ""]
    lines += [f"- `{x}`" for x in inputs]
    lines += ["", "## Estatísticas", "", f"- Processados/atualizados: {counters['processed']}", f"- Ignorados: {counters['skipped']}", f"- Cache: {counters['cache']}", f"- Chamadas API: {counters['api']}", f"- Fallback local: {counters['local']}", f"- Erros: {len(errors)}", "", "## Outputs", ""]
    for o in outs:
        lines.append(f"- `{Path(o['ficheiro']).name}` — fragmentos: {o['n_fragmentos']} — offsets: {o['offset_inicio']}–{o['offset_fim_exclusivo']}")
    lines += ["", "## Fragmentos tratados/atualizados", ""]
    for f in treated:
        st = f.get("estado_local", {})
        lines.append(f"- `{f.get('fragment_id')}` — validação: `{st.get('estado_validacao')}` — confiança: `{st.get('confianca')}`")
    if errors:
        lines += ["", "## Erros", ""]
        lines += [f"- `{e.get('fragment_id')}` — {e.get('erro')}" for e in errors]
    lines += ["", "## Nota", "", "Esta saída ainda não substitui a instância canónica. Serve como parte incremental tratada, a validar antes de integração definitiva."]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return index_path, report_path


def make_client(args: argparse.Namespace) -> Optional[Any]:
    if load_dotenv:
        for p in [SCRIPT_DIR / ".env", PIPELINE_DIR / ".env", PROJECT_ROOT / ".env"]:
            if p.exists():
                load_dotenv(p)
        load_dotenv()
    if args.local_only or OpenAI is None or not os.getenv("OPENAI_API_KEY"):
        return None
    return OpenAI()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Trata fragmentos resegmentados novos e gera parte incremental 003.")
    p.add_argument("--input", action="append", default=None, help="JSON de fragmentos resegmentados. Por defeito usa 04_outputs_prontos_para_integrar/*.json")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--local-only", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--update-existing", action="store_true")
    p.add_argument("--include-existing-base", action="store_true")
    p.add_argument("--part-num", type=int, default=3)
    p.add_argument("--max-part-size", type=int, default=500)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("--sleep", type=float, default=1.0)
    p.add_argument("--search-project-context", action="store_true")
    return p


def main() -> int:
    ensure_dirs()
    args = build_parser().parse_args()
    client = make_client(args)
    if client is None and not args.local_only:
        print("[aviso] OPENAI_API_KEY/biblioteca openai indisponível; a usar fallback local.")
        args.local_only = True
    frags, inputs = load_ready(args.input)
    if args.limit is not None:
        frags = frags[:max(0, args.limit)]
    base_ids = existing_base_ids()
    inc = existing_incremental()
    base = load_base_fragments()
    counters = {"processed": 0, "skipped": 0, "cache": 0, "api": 0, "local": 0}
    errors: List[Dict[str, str]] = []
    treated: List[Dict[str, Any]] = []
    print("=" * 78)
    print("TRATAMENTO INCREMENTAL DE FRAGMENTOS RESEGMENTADOS")
    print("=" * 78)
    print(f"Pipeline:      {PIPELINE_DIR}")
    print(f"Inputs:        {len(inputs)} ficheiro(s)")
    print(f"Fragmentos:    {len(frags)}")
    print(f"Modo:          {'heuristico_local' if args.local_only else 'api_openai'}")
    print(f"Modelo:        {args.model if not args.local_only else 'heuristico_local'}")
    print("-" * 78)
    for i, f in enumerate(frags, 1):
        fid = str(f.get("fragment_id") or "")
        if not fid:
            continue
        if not args.include_existing_base and fid in base_ids:
            counters["skipped"] += 1
            print(f"[{i}/{len(frags)}] {fid}: ignorado — já existe na base canónica")
            continue
        if fid in inc and not args.update_existing and not args.force:
            counters["skipped"] += 1
            print(f"[{i}/{len(frags)}] {fid}: ignorado — já existe na incremental")
            continue
        try:
            print(f"[{i}/{len(frags)}] {fid}: tratar")
            cf = treat_fragment(f, base, client, args, counters)
            treated.append(cf)
            counters["processed"] += 1
            write_json(OUT_FRAGMENT_DIR / f"{fid}.fragmento_tratado.json", cf)
        except Exception as exc:
            errors.append({"fragment_id": fid, "erro": str(exc)})
            print(f"[erro] {fid}: {exc}")
    written = write_parts(treated, args) if treated else []
    index_path, report_path = write_report(written, treated, inputs, counters, errors)
    print("-" * 78)
    print("CONCLUÍDO")
    print("-" * 78)
    print(f"Processados:   {counters['processed']}")
    print(f"Ignorados:     {counters['skipped']}")
    print(f"Cache:         {counters['cache']}")
    print(f"Chamadas API:  {counters['api']}")
    print(f"Fallback:      {counters['local']}")
    print(f"Erros:         {len(errors)}")
    for p in written:
        print(f"Parte escrita: {p}")
    print(f"Index:         {index_path}")
    print(f"Relatório:     {report_path}")
    print("=" * 78)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
