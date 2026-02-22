from carregar_conceitos import carregar_conceitos
from collections import defaultdict

# =====================================================
# DETETOR v5 — DEPENDÊNCIAS IMPLÍCITAS (ALINHADO COM O TEU SCHEMA)
# =====================================================
#
# Semântica assumida (de acordo com o teu JSON):
#   - dependencias.depende_de  : condições constitutivas/estruturais
#   - dependencias.pressupoe   : pressuposições (não constitutivas, mas necessárias ao uso)
#   - dependencias.implica     : consequências / derivados
#   - dinamica.gera            : geração/produção (normalmente coincide com "implica")
#
# Logo:
#   - NÃO tratamos "dinamica.gera" como dependência.
#   - NÃO aplicamos "gera invertida" (gerador -> gerado) como dependência.
#   - Usamos "gera" para verificar coerência com "implica".
#
# Resultado:
#   - erros/avisos de dependência implícita passam a ser MUITO mais limpos.
#   - "gera" deixa de criar 50 falsos positivos.
# =====================================================


# =====================================================
# CONFIGURAÇÕES
# =====================================================

# Conceitos que nunca entram como dependência implícita (por desenho do sistema)
IGNORAR_DEPENDENCIAS_IMPLICITAS = {
    "D_REAL",  # critério último / campo ontológico: não é dependência local
}

# Em estatuto_ontologico, campos que NÃO contam como dependência
# (o teu "criterio_ultimo" é subordinação ao real, não fundação local)
CAMPOS_ESTATUTO_IGNORADOS = {"criterio_ultimo"}

# Origens que contam como "dependência" (isto deve aparecer em depende_de)
ORIGENS_DEPENDENCIA = {
    # Ex.: exterioridade_excluida pode não ser D_*, mas se houver referência D_* aqui conta
    # Em geral, qualquer referência D_* em estatuto_ontologico (exceto criterio_ultimo) é estrutural.
    "estatuto_ontologico",

    # Regras explícitas do schema
    "dependencias.depende_de",
}

# Origens que contam como "pressuposição" (isto pode estar em pressupoe)
ORIGENS_PRESSUPOSTAS = {
    "dependencias.pressupoe",
}

# Origens ignoradas para dependências implícitas (não fundam)
# Nota: aqui incluímos explicitamente "implica" e "dinamica" porque são consequências,
# não condições.
ORIGENS_IGNORADAS = {
    "dependencias.implica",
    "dinamica.gera",
    "dinamica.pode_gerar_erro",
    "dinamica.pode_ser_afetado_por",

    # operações são OP_*, e mesmo que apareça D_* aí, normalmente é referência metodológica
    # (mantém-se fora do detetor de dependências, para evitar ruído)
    "operacoes_ontologicas.fundacao",
    "operacoes_ontologicas.descricao",
    "operacoes_ontologicas.diferenciacao",
    "operacoes_ontologicas.critica",
    "operacoes_ontologicas.corretiva",
}


# =====================================================
# UTILIDADES
# =====================================================

def e_ontologico_real(c):
    return c.get("estatuto_ontologico", {}).get("afirmacao_ontologica") is True


def _is_ref(v):
    return isinstance(v, str) and v.startswith("D_")


def extrair_referencias_com_origem(c):
    """
    Extrai referências D_* com indicação da origem.

    Retorna:
        dict[ref -> set(origens)]
    """
    refs = defaultdict(set)

    # ---------- estatuto_ontologico ----------
    est = c.get("estatuto_ontologico", {})
    for k, v in est.items():
        if k in CAMPOS_ESTATUTO_IGNORADOS:
            continue
        if _is_ref(v):
            refs[v].add("estatuto_ontologico")

    # ---------- dependencias ----------
    deps = c.get("dependencias", {})
    for k, lista in deps.items():
        if not isinstance(lista, list):
            continue
        origem = f"dependencias.{k}"
        for v in lista:
            if _is_ref(v):
                refs[v].add(origem)

    # ---------- dinamica ----------
    dinamica = c.get("dinamica", {})
    for k, lista in dinamica.items():
        if not isinstance(lista, list):
            continue
        origem = f"dinamica.{k}"
        for v in lista:
            if _is_ref(v):
                refs[v].add(origem)

    # ---------- operacoes_ontologicas ----------
    # (normalmente não há D_* aqui, mas se houver não queremos ruído sem controlo)
    ops = c.get("operacoes_ontologicas", {})
    for k, lista in ops.items():
        if not isinstance(lista, list):
            continue
        origem = f"operacoes_ontologicas.{k}"
        for v in lista:
            if _is_ref(v):
                refs[v].add(origem)

    return refs


def classificar_ausencia(cid, c, ref, origens, declaradas_depende_de, declaradas_pressupoe):
    """
    Decide se um ref usado deve existir em:
      - depende_de (dependência estrutural)
      - pressupoe (pressuposição)
      - ou é ignorável

    Retorna:
      ("erro"|"aviso"|None, msg)
    """

    # remover origens ignoradas
    origens_relevantes = {o for o in origens if o not in ORIGENS_IGNORADAS}
    if not origens_relevantes:
        return None, None

    # se já está declarada em algum sítio, não há ausência
    if ref in declaradas_depende_de or ref in declaradas_pressupoe:
        return None, None

    # Se aparece em origens de dependência, deveria estar em depende_de
    if any(o in ORIGENS_DEPENDENCIA for o in origens_relevantes):
        if e_ontologico_real(c):
            return "erro", f"dependência estrutural não declarada: {ref} (origens: {', '.join(sorted(origens_relevantes))})"
        return "aviso", f"pressuposição conceptual (conceito não-ontológico) não declarada: {ref} (origens: {', '.join(sorted(origens_relevantes))})"

    # Se aparece em pressupoe (ou equivalente), deveria estar em pressupoe
    if any(o in ORIGENS_PRESSUPOSTAS for o in origens_relevantes):
        # Pressuposição não é erro ontológico por defeito; é aviso útil.
        return "aviso", f"pressuposição não declarada: {ref} (origens: {', '.join(sorted(origens_relevantes))})"

    # Caso residual: aparece numa origem “relevante” mas não categorizada
    # (mantém-se aviso para não perder sinal, mas sem impor depende_de)
    return "aviso", f"referência potencialmente relevante não declarada: {ref} (origens: {', '.join(sorted(origens_relevantes))})"


# =====================================================
# DETEÇÃO DE DEPENDÊNCIAS IMPLÍCITAS
# =====================================================

def detetar_dependencias_implicitas_v5(conceitos):
    erros = defaultdict(list)
    avisos = defaultdict(list)

    for cid, c in conceitos.items():
        declaradas_depende_de = set(c.get("dependencias", {}).get("depende_de", []))
        declaradas_pressupoe = set(c.get("dependencias", {}).get("pressupoe", []))

        refs_por_origem = extrair_referencias_com_origem(c)

        for ref, origens in refs_por_origem.items():
            if ref == cid:
                continue
            if ref in IGNORAR_DEPENDENCIAS_IMPLICITAS:
                continue
            if ref not in conceitos:
                continue

            tipo, msg = classificar_ausencia(
                cid, c, ref, origens,
                declaradas_depende_de,
                declaradas_pressupoe
            )
            if not tipo:
                continue

            if tipo == "erro":
                erros[cid].append(msg)
            else:
                avisos[cid].append(msg)

    return erros, avisos


# =====================================================
# CHECKS DE COERÊNCIA "gera" VS "implica"
# =====================================================

def verificar_coerencia_gera_implica(conceitos):
    """
    No teu schema, "dinamica.gera" e "dependencias.implica" parecem redundantes.
    Este check ajuda-te a manter consistência:

      - Tudo o que está em dinamica.gera devia estar também em dependencias.implica
        (ou então decide-se que um deles deixa de existir).
      - E opcionalmente o inverso (implica deveria estar em gera) — deixo como aviso.

    Retorna:
      incoerencias: {cid: [msgs]}
    """
    incoerencias = defaultdict(list)

    for cid, c in conceitos.items():
        gera = set(c.get("dinamica", {}).get("gera", []) or [])
        implica = set(c.get("dependencias", {}).get("implica", []) or [])

        gera = {x for x in gera if _is_ref(x)}
        implica = {x for x in implica if _is_ref(x)}

        # gera que não está em implica
        falta_em_implica = sorted(gera - implica)
        if falta_em_implica:
            incoerencias[cid].append(
                f"'dinamica.gera' contém refs não listadas em 'dependencias.implica': {', '.join(falta_em_implica)}"
            )

        # implica que não está em gera (opcional; pode ser normal)
        falta_em_gera = sorted(implica - gera)
        if falta_em_gera:
            incoerencias[cid].append(
                f"'dependencias.implica' contém refs não listadas em 'dinamica.gera' (talvez ok): {', '.join(falta_em_gera)}"
            )

    return incoerencias


# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")

    erros, avisos = detetar_dependencias_implicitas_v5(conceitos)
    incoerencias = verificar_coerencia_gera_implica(conceitos)

    print("\n=== DETETOR DE DEPENDÊNCIAS IMPLÍCITAS (v5) ===\n")

    total_erros = 0
    for cid, msgs in sorted(erros.items()):
        print(f"❗ {cid}")
        for m in msgs:
            print(f"   - {m}")
            total_erros += 1
        print()

    total_avisos = 0
    for cid, msgs in sorted(avisos.items()):
        print(f"⚠️ {cid}")
        for m in msgs:
            print(f"   - {m}")
            total_avisos += 1
        print()

    print("\n=== CHECK DE COERÊNCIA: 'gera' vs 'implica' ===\n")
    total_inco = 0
    for cid, msgs in sorted(incoerencias.items()):
        print(f"🔎 {cid}")
        for m in msgs:
            print(f"   - {m}")
            total_inco += 1
        print()

    if total_erros == 0 and total_avisos == 0:
        print("✅ Nenhuma dependência implícita problemática detetada.")
    else:
        print(f"Resumo: {total_erros} erro(s), {total_avisos} aviso(s).")

    if total_inco == 0:
        print("✅ 'gera' e 'implica' estão coerentes (segundo as regras definidas).")
    else:
        print(f"Resumo coerência: {total_inco} conceito(s) com possíveis incoerências.")