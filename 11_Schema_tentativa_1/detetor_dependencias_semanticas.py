from carregar_conceitos import carregar_conceitos
from collections import defaultdict
import re

# =====================================================
# DETETOR v7 — DEPENDÊNCIAS SEMÂNTICAS (TEXTUAIS)
# =====================================================
#
# Este detetor:
#   - analisa texto das definições (definicao.texto)
#   - procura padrões linguísticos explícitos (regex)
#   - sugere dependências ontológicas POSSÍVEIS
#
# Este detetor NÃO:
#   - cria dependências automaticamente
#   - gera erros
#   - interfere com dependências estruturais
#
# Estado v7:
#   ✔ semanticamente estabilizado
#   ✔ silencia ontologia de fundo transversal
# =====================================================


# -----------------------------------------------------
# CONFIGURAÇÃO SEMÂNTICA GLOBAL
# -----------------------------------------------------

# Conceitos que NUNCA devem ser sugeridos semanticamente
# enquanto dependências, por funcionarem como
# ontologia de fundo transversal ao sistema
IGNORAR_SEMANTICO_GLOBAL = {
    "D_REAL",         # critério último, sempre presente
    "D_CAMPO",        # campo do real ≠ conceito técnico
    "D_RELACAO",      # relacionalidade difusa ≠ relação estrutural
    "D_LOCALIDADE",   # condição situada já garantida estruturalmente
}

# -----------------------------------------------------
# GATILHOS SEMÂNTICOS EXPLÍCITOS
# -----------------------------------------------------
#
# Cada entrada:
#   chave   -> conceito sugerido
#   valor   -> lista de (regex, peso)
#
# NOTA:
#   Estes gatilhos são deliberadamente conservadores.
#   O score mínimo filtra coincidência linguística fraca.
#

GATILHOS_SEMANTICOS = {
    "D_LIMITE": [
        (r"\blimite(s)?\b", 2),
        (r"\bdelimita(c|ç)(a|ã)o\b", 2),
        (r"\bexclu[ií]d[oa]\b", 3),
    ],
    "D_CONTINUIDADE": [
        (r"\bcontinu[ií]dade\b", 3),
        (r"\bsem ruptura\b", 2),
        (r"\bfluxo\b", 1),
    ],

    # Mantidos por completude,
    # mas neutralizados via IGNORAR_SEMANTICO_GLOBAL
    "D_CAMPO": [
        (r"\bcampo\b", 2),
        (r"\bconfigura[cç][aã]o relacional\b", 3),
    ],
    "D_LOCALIDADE": [
        (r"\blocalizad[oa]\b", 2),
        (r"\bsituad[oa]\b", 2),
    ],
    "D_RELACAO": [
        (r"\brela[cç][aã]o\b", 1),
        (r"\brelacional\b", 2),
    ],
}


# -----------------------------------------------------
# UTILIDADES
# -----------------------------------------------------

def extrair_texto_definicao(c):
    """
    Extrai o texto relevante para análise semântica.

    Neste sistema:
      - apenas definicao.texto é analisado
      - tudo convertido para lowercase
    """
    definicao = c.get("definicao", {})
    texto = definicao.get("texto")
    if isinstance(texto, str):
        return texto.lower()
    return ""


# -----------------------------------------------------
# DETEÇÃO SEMÂNTICA
# -----------------------------------------------------

def detetar_dependencias_semanticas(conceitos, score_minimo=2):
    """
    Deteta possíveis dependências semânticas
    a partir do texto das definições.

    score_minimo:
      1 -> permissivo (exploração)
      2 -> equilibrado (RECOMENDADO)
      3 -> apenas dependências muito fortes
    """
    sugestoes = defaultdict(list)

    for cid, c in conceitos.items():
        texto = extrair_texto_definicao(c)
        if not texto:
            continue

        # Dependências já assumidas
        declaradas = set(c.get("dependencias", {}).get("depende_de", []))
        declaradas |= set(c.get("dependencias", {}).get("pressupoe", []))

        for ref, padroes in GATILHOS_SEMANTICOS.items():

            # -------------------------------------------------
            # FILTROS DUROS (antes de qualquer regex)
            # -------------------------------------------------

            if ref == cid:
                continue

            if ref in IGNORAR_SEMANTICO_GLOBAL:
                continue

            if ref not in conceitos:
                continue

            if ref in declaradas:
                continue

            # -------------------------------------------------
            # MATCHING SEMÂNTICO
            # -------------------------------------------------

            score_total = 0
            matches = []

            for padrao, peso in padroes:
                if re.search(padrao, texto):
                    score_total += peso
                    matches.append(padrao)

            if score_total >= score_minimo:
                sugestoes[cid].append({
                    "sugere": ref,
                    "score": score_total,
                    "matches": matches,
                    "excerto": texto[:200] + ("..." if len(texto) > 200 else "")
                })

    return sugestoes


# -----------------------------------------------------
# EXECUÇÃO
# -----------------------------------------------------

if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")

    sugestoes = detetar_dependencias_semanticas(
        conceitos,
        score_minimo=2
    )

    print("\n=== DETETOR DE DEPENDÊNCIAS SEMÂNTICAS (v7) ===\n")

    total = 0
    for cid, itens in sorted(sugestoes.items()):
        print(f"💡 {cid}")
        for s in itens:
            print(
                f"   - sugere {s['sugere']} "
                f"(score={s['score']}, padrões={s['matches']})"
            )
            total += 1
        print()

    if total == 0:
        print("✅ Nenhuma dependência semântica relevante detetada.")
    else:
        print(f"Resumo: {total} sugestão(ões) semântica(s).")