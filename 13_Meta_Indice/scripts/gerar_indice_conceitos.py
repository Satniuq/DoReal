# gerar_indice_conceitos.py
# Compilador determinístico do indice_conceitos.json
# MODELO FECHADO: só usa campos EXISTENTES nos conceitos

import json
import os
from typing import Dict, Any, List, Tuple

# ==========================================
# CONFIGURAÇÃO
# ==========================================

BASE_DIR = r"C:\Users\vanes\DoReal_Casa_Local\DoReal\13_Meta_Indice"

PATH_CONCEITOS = os.path.join(BASE_DIR, "dados_base", "todos_os_conceitos.json")
PATH_META_INDICE = os.path.join(BASE_DIR, "meta", "meta_indice.json")
PATH_OPERACOES = os.path.join(BASE_DIR, "dados_base", "operacoes.json")

OUT_INDICE = os.path.join(BASE_DIR, "dados_base", "indice_conceitos.json")

STRICT = True  # falha se encontrar operação inválida

# ==========================================
# UTILIDADES
# ==========================================

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==========================================
# META-ÍNDICE
# ==========================================

def extrair_regimes(meta: Dict[str, Any]) -> Dict[str, Any]:
    return meta["meta_indice"]["regimes"]

def mapa_operacao_para_regime(regimes: Dict[str, Any]) -> Dict[str, str]:
    m = {}
    for rid, r in regimes.items():
        for op in r.get("operacoes", []):
            m[op] = rid
    return m

def erros_por_regime_meta(regimes: Dict[str, Any]) -> Dict[str, List[str]]:
    out = {}
    for rid, r in regimes.items():
        erros = []
        for bloco in r.get("erros", {}).values():
            if isinstance(bloco, list):
                erros.extend(bloco)
        out[rid] = sorted(set(erros))
    return out

# ==========================================
# OPERAÇÕES (VALIDAÇÃO)
# ==========================================

def carregar_operacoes_validas(operacoes_json: Dict[str, Any]) -> set:
    return set(operacoes_json.keys())

# ==========================================
# EXTRAÇÃO DO CONCEITO
# ==========================================

def listar_operacoes(conceito: Dict[str, Any], operacoes_validas: set, erros: List[str]) -> List[str]:
    ops = []
    bloco = conceito.get("operacoes_ontologicas", {})
    if not isinstance(bloco, dict):
        return []

    for categoria, lista in bloco.items():
        if not isinstance(lista, list):
            continue
        for op in lista:
            if not isinstance(op, str):
                continue
            if op not in operacoes_validas:
                erros.append(f"{conceito.get('id')} -> operação inválida: {op}")
                if STRICT:
                    continue
                else:
                    continue
            ops.append(op)

    return sorted(set(ops))

def derivar_dependencias(conceito: Dict[str, Any]) -> Dict[str, List[str]]:
    dep = conceito.get("dependencias", {})
    return {
        "depende_de": sorted(dep.get("depende_de", [])),
        "pressupoe": sorted(dep.get("pressupoe", []))
    }

def derivar_relacoes(conceito: Dict[str, Any]) -> Dict[str, List[str]]:
    dep = conceito.get("dependencias", {})
    din = conceito.get("dinamica", {})
    return {
        "implica": sorted(dep.get("implica", [])),
        "gera": sorted(din.get("gera", [])),
        "exclui": []  # confirmado: não existe nos conceitos
    }

# ==========================================
# DERIVAÇÕES NORMATIVAS
# ==========================================

def derivar_regimes(ops: List[str], op_regime: Dict[str, str]) -> List[str]:
    return sorted({op_regime[o] for o in ops if o in op_regime})

def estatuto_meta(regimes: List[str], regimes_meta: Dict[str, Any]) -> str:
    prioridade = ["fundacional", "ontologico", "critico", "derivado", "corretivo"]
    encontrados = [regimes_meta[r]["estatuto"] for r in regimes if "estatuto" in regimes_meta[r]]
    for p in prioridade:
        if p in encontrados:
            return p
    return "ontologico"

def camada(nivel, dominio, estatuto):
    try:
        n = float(nivel)
    except Exception:
        n = None

    if n is not None and n <= 1:
        return "fundacional"
    if dominio == "epistemologico":
        return "epistemologica"
    if "etico" in str(dominio):
        return "etica"
    if estatuto == "processo_real":
        return "dinamica"
    return "estrutural"

def perfil(camada_val, dominio, estatuto):
    return {
        "fundacional": camada_val == "fundacional",
        "mediador": dominio == "epistemologico",
        "dinamico": estatuto == "processo_real",
        "normativo": estatuto == "derivacao_normativa",
        "sistemico": dominio == "sistemico"
    }

def observacoes(regimes):
    return {
        "transversal": len(regimes) > 2,
        "sensivel_a_escala": "REGIME_DIFERENCIACAO_ONTOLOGICA" in regimes,
        "requer_higiene_critica": any(r.startswith("REGIME_CRITICA") for r in regimes)
    }

# ==========================================
# COMPILAÇÃO FINAL
# ==========================================

def compilar_conceito(conceito, regimes_meta, op_regime, erros_meta, operacoes_validas, erros_ops):
    ops = listar_operacoes(conceito, operacoes_validas, erros_ops)
    regimes = derivar_regimes(ops, op_regime)

    est = conceito.get("estatuto_ontologico", {})
    estatuto = est.get("tipo", "")
    afirm = est.get("afirmacao_ontologica", False)

    cam = camada(conceito.get("nivel"), conceito.get("dominio"), estatuto)
    perf = perfil(cam, conceito.get("dominio"), estatuto)

    return {
        "id": conceito["id"],
        "nivel": conceito.get("nivel"),
        "camada": cam,
        "dominio": conceito.get("dominio"),
        "estatuto": estatuto,
        "afirmacao_ontologica": afirm,

        "perfil": perf,

        "dependencias": derivar_dependencias(conceito),
        "relacoes": derivar_relacoes(conceito),

        "regimes_ativaveis": regimes,
        "estatuto_meta": estatuto_meta(regimes, regimes_meta),

        "percursos": {
            "inicia": perf["fundacional"] and conceito.get("nivel") == 0,
            "termina": False
        },

        "erros_por_regime": {
            r: erros_meta[r]
            for r in regimes
            if erros_meta.get(r)
        },

        "riscos_estruturais": sorted(
            conceito.get("notas_de_protecao", {}).get("riscos_de_desvio", [])
        ),

        "observacoes_meta": observacoes(regimes)
    }

# ==========================================
# MAIN
# ==========================================

def main():
    conceitos = load_json(PATH_CONCEITOS)
    meta = load_json(PATH_META_INDICE)
    operacoes_json = load_json(PATH_OPERACOES)

    regimes = extrair_regimes(meta)
    op_regime = mapa_operacao_para_regime(regimes)
    erros_meta = erros_por_regime_meta(regimes)

    operacoes_validas = carregar_operacoes_validas(operacoes_json)

    indice = {}
    erros_ops = []

    for cid, conceito in conceitos.items():
        indice[cid] = compilar_conceito(
            conceito,
            regimes,
            op_regime,
            erros_meta,
            operacoes_validas,
            erros_ops
        )

    if STRICT and erros_ops:
        print("❌ Erro: operações inválidas encontradas.")
        for e in erros_ops:
            print(" -", e)
        raise SystemExit(1)

    save_json(OUT_INDICE, indice)
    print("✅ indice_conceitos.json gerado com sucesso.")

if __name__ == "__main__":
    main()