# validar_indice_conceitos.py
# Validador completo do indice_conceitos.json
# Com suporte a AXIOMAS ONTOLÓGICOS, MEDIACIONAIS e EPISTEMOLÓGICOS IMPLÍCITOS

import json
import os

BASE_DIR = r"C:\Users\JoseVitorinoQuintas\DoReal\13_Meta_Indice"

PATH_CONCEITOS = os.path.join(BASE_DIR, "dados_base", "todos_os_conceitos.json")
PATH_INDICE = os.path.join(BASE_DIR, "dados_base", "indice_conceitos.json")
PATH_OPERACOES = os.path.join(BASE_DIR, "dados_base", "operacoes.json")
PATH_META = os.path.join(BASE_DIR, "meta", "meta_indice.json")

OUT_ERROS = os.path.join(BASE_DIR, "dados_base", "validacao_erros.json")
OUT_WARNINGS = os.path.join(BASE_DIR, "dados_base", "validacao_warnings.json")

# ======================================================
# AXIOMAS IMPLÍCITOS
# ======================================================

AXIOMAS_ONTOLOGICOS = {
    "D_RELACAO",
    "D_POTENCIALIDADE",
    "D_PODER_SER",
    "D_DETERMINACAO",
    "D_SER",
    "D_REAL",
    "D_CONTINUIDADE",
    "D_TEMPO"
}

AXIOMAS_MEDIACIONAIS = {
    "D_SIMBOLO",
    "D_LINGUAGEM"
}

AXIOMAS_EPISTEMOLOGICOS = {
    "D_ADEQUACAO",
    "D_CRITERIO",
    "D_VERDADE",
    "D_VALIDADE"
}

AXIOMAS_TODOS = (
    AXIOMAS_ONTOLOGICOS
    | AXIOMAS_MEDIACIONAIS
    | AXIOMAS_EPISTEMOLOGICOS
)

# ======================================================

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def ok(msg): print(f"  ✔️ {msg}")
def warn(msg): print(f"  ⚠️ {msg}")
def err(msg): print(f"  ❌ {msg}")

# ======================================================

def validar():
    conceitos = load_json(PATH_CONCEITOS)
    indice = load_json(PATH_INDICE)
    operacoes = load_json(PATH_OPERACOES)
    meta = load_json(PATH_META)["meta_indice"]["regimes"]

    operacoes_validas = set(operacoes.keys())

    erros = []
    warnings = []

    print("\n================ VALIDACAO INDICE =================\n")

    for cid, idx in indice.items():
        print(f"▶ {cid}")
        c = conceitos.get(cid)

        if not c:
            err("conceito inexistente em todos_os_conceitos.json")
            erros.append((cid, "conceito inexistente"))
            print()
            continue

        is_axioma = cid in AXIOMAS_TODOS

        # ----------------- estrutura -----------------
        obrig = [
            "id","nivel","camada","dominio","estatuto","afirmacao_ontologica",
            "perfil","dependencias","relacoes","regimes_ativaveis",
            "estatuto_meta","percursos","erros_por_regime",
            "riscos_estruturais","observacoes_meta"
        ]

        for k in obrig:
            if k not in idx:
                err(f"campo obrigatório em falta: {k}")
                erros.append((cid, f"falta {k}"))

        # ----------------- igualdade direta -----------------
        for k in ["nivel","dominio"]:
            if idx[k] != c[k]:
                err(f"{k} divergente (indice={idx[k]} / conceito={c[k]})")
                erros.append((cid, f"{k} divergente"))

        est = c["estatuto_ontologico"]
        if idx["estatuto"] != est["tipo"]:
            err("estatuto ontologico divergente")
            erros.append((cid, "estatuto divergente"))

        if idx["afirmacao_ontologica"] != est["afirmacao_ontologica"]:
            err("afirmacao_ontologica divergente")
            erros.append((cid, "afirmacao divergente"))

        # ----------------- dependencias -----------------
        dep = c["dependencias"]

        if is_axioma:
            ok("axioma — dependências não exigidas")
        else:
            depende_de = sorted(dep.get("depende_de", []))
            pressupoe = sorted(dep.get("pressupoe", []))

            if idx["dependencias"]["depende_de"] != depende_de:
                err("depende_de divergente")
                erros.append((cid, "depende_de divergente"))

            if idx["dependencias"]["pressupoe"] != pressupoe:
                err("pressupoe divergente")
                erros.append((cid, "pressupoe divergente"))

        # ----------------- relacoes -----------------
        if idx["relacoes"]["implica"] != sorted(dep.get("implica", [])):
            err("implica divergente")
            erros.append((cid, "implica divergente"))

        if idx["relacoes"]["gera"] != sorted(c.get("dinamica", {}).get("gera", [])):
            err("gera divergente")
            erros.append((cid, "gera divergente"))

        # ----------------- operações → regimes -----------------
        ops = []
        for lst in c["operacoes_ontologicas"].values():
            ops += lst

        ops = set(ops)
        for o in ops:
            if o not in operacoes_validas:
                err(f"operacao invalida: {o}")
                erros.append((cid, f"operacao invalida {o}"))

        regimes_esperados = set()
        for r, bloco in meta.items():
            if ops & set(bloco.get("operacoes", [])):
                regimes_esperados.add(r)

        if set(idx["regimes_ativaveis"]) != regimes_esperados:
            err("regimes_ativaveis incorretos")
            warn(f"esperado: {sorted(regimes_esperados)}")
            warn(f"indice:   {idx['regimes_ativaveis']}")
            erros.append((cid, "regimes incorretos"))

        # ----------------- erros por regime -----------------
        for r, lst in idx["erros_por_regime"].items():
            if r not in regimes_esperados:
                err(f"erro_por_regime em regime nao ativo: {r}")
                erros.append((cid, f"erro em regime nao ativo {r}"))

            erros_validos = []
            for bloco in meta[r].get("erros", {}).values():
                erros_validos += bloco

            for e in lst:
                if e not in erros_validos:
                    err(f"erro invalido no regime {r}: {e}")
                    erros.append((cid, f"erro invalido {e}"))

        # ----------------- percursos -----------------
        if idx["percursos"].get("termina") is True:
            err("termina nao pode ser true")
            erros.append((cid, "termina true"))

        # ----------------- riscos -----------------
        riscos = c["notas_de_protecao"]["riscos_de_desvio"]
        if sorted(idx["riscos_estruturais"]) != sorted(riscos):
            err("riscos_estruturais divergentes")
            erros.append((cid, "riscos divergentes"))

        if cid not in [e[0] for e in erros]:
            ok("validação completa")

        print()

    with open(OUT_ERROS, "w", encoding="utf-8") as f:
        json.dump(erros, f, ensure_ascii=False, indent=2)

    with open(OUT_WARNINGS, "w", encoding="utf-8") as f:
        json.dump(warnings, f, ensure_ascii=False, indent=2)

    print("\n================ RESUMO =================")
    print(f"Erros: {len(erros)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Relatorio erros: {OUT_ERROS}")
    print("========================================\n")

# ======================================================

if __name__ == "__main__":
    validar()