import os
import sys
import json
from typing import Dict, List, Set, Tuple, Any

# ==========================================================
# CONTEXTO DO PROJECTO
# ==========================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

SCHEMA_DIR = os.path.join(PROJECT_ROOT, "11_Schema_tentativa_1")
ESTADOS_DIR = os.path.join(PROJECT_ROOT, "12_Estados_finais_de_mundo")

if SCHEMA_DIR not in sys.path:
    sys.path.insert(0, SCHEMA_DIR)

from carregar_conceitos import carregar_conceitos  # noqa


# ==========================================================
# CONFIG
# ==========================================================

PASTA_PERCURSOS = os.path.join(SCHEMA_DIR, "percursos")
PASTA_CONCEITOS = os.path.join(SCHEMA_DIR, "conceitos")
PASTA_ESTADOS = ESTADOS_DIR
FICHEIRO_CRITERIOS = os.path.join(PASTA_ESTADOS, "criterios_de_inferencia.json")


# ==========================================================
# UTILIDADES
# ==========================================================

def carregar_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def carregar_percurso(pid: str) -> dict:
    for f in os.listdir(PASTA_PERCURSOS):
        if f.endswith(".json"):
            p = carregar_json(os.path.join(PASTA_PERCURSOS, f))
            if p.get("id") == pid:
                return p
    raise ValueError(f"Percurso não encontrado: {pid}")


def carregar_criterios() -> dict:
    if not os.path.isfile(FICHEIRO_CRITERIOS):
        raise FileNotFoundError(
            f"Ficheiro de critérios não encontrado:\n{FICHEIRO_CRITERIOS}"
        )
    return carregar_json(FICHEIRO_CRITERIOS)


# ==========================================================
# MÉTRICAS BÁSICAS
# ==========================================================

def analisar_dependencias(conceito: dict, ativos: Set[str]) -> Tuple[Set[str], Set[str]]:
    deps = set(conceito.get("dependencias", {}).get("depende_de", []))
    faltam = deps - ativos
    return deps, faltam


def estado_ontologico(deps: Set[str], faltam: Set[str], ja_vivido: bool) -> str:
    if not deps:
        return "origem não fundacional"
    if not faltam:
        return "intensificação legítima"
    if ja_vivido:
        return "reinscrição com ausência assumida"
    return "emergência situada com ausência"


def is_fundacional(conceito: dict) -> bool:
    est = conceito.get("estatuto_ontologico", {})
    if est.get("afirmacao_ontologica") is not True:
        return False
    return conceito.get("nivel", 99) <= 2


# ==========================================================
# DETECTORES ESTRUTURAIS
# ==========================================================

def classificar_ausencias_fundacionais(
    ausencias: Set[str],
    conceitos: Dict[str, dict]
) -> Any:
    fundacionais = {
        cid for cid in ausencias
        if cid in conceitos and is_fundacional(conceitos[cid])
    }
    if not fundacionais:
        return False
    return True if len(fundacionais) >= 3 else "parciais"


def inferir_impossibilidade_ontologica(metricas: Dict[str, Any]) -> bool:
    return (
        metricas["ausencias_fundacionais_persistentes"] is True
        and metricas["intensificacoes_legitimas"] == 0
    )


def inferir_relacao_com_o_real(percurso: dict, metricas: Dict[str, Any]) -> str:
    if metricas.get("impossibilidade_ontologica") is True:
        return "invocada"

    seq = percurso.get("sequencia", [])
    if seq and seq[-1] == "D_REAL":
        return "efetiva"
    if "D_REAL" in seq:
        return "intermitente"
    return "substituida"


# ==========================================================
# MOTOR DE CRITÉRIOS
# ==========================================================

def parse_condicao(cond, valor) -> bool:
    if isinstance(cond, bool):
        return valor is cond
    if isinstance(cond, int):
        return valor == cond
    if isinstance(cond, str):
        cond = cond.strip()
        if cond.startswith(">="):
            return isinstance(valor, int) and valor >= int(cond[2:])
        if cond.startswith("=="):
            return isinstance(valor, int) and valor == int(cond[2:])
        return valor == cond
    return False


def avaliar_estado(cfg: dict, metricas: Dict[str, Any]) -> Tuple[bool, List[str]]:
    just = []

    for k, cond in cfg.get("padroes_necessarios", {}).items():
        val = metricas.get(k)
        ok = parse_condicao(cond, val)
        just.append(f"[NEC] {k}: {val} ⟶ {cond} => {'OK' if ok else 'NOK'}")
        if not ok:
            return False, just

    for k, cond in cfg.get("padroes_excludentes", {}).items():
        val = metricas.get(k)
        bate = parse_condicao(cond, val)
        just.append(f"[EXC] {k}: {val} ⟶ {cond} => {'BATE' if bate else 'NÃO BATE'}")
        if bate:
            return False, just

    return True, just


# ==========================================================
# EXECUÇÃO DO PERCURSO
# ==========================================================

def narrar_passo(cid: str, conceito: dict, ativos: Set[str], volta: int, historico: Set[str]) -> dict:
    deps, faltam = analisar_dependencias(conceito, ativos)
    ja_vivido = cid in historico
    estado = estado_ontologico(deps, faltam, ja_vivido)

    print(f"\n→ {cid}")
    print(f"  [volta {volta} — {estado}]")

    if faltam:
        print(f"  Ausências ontológicas assumidas: {', '.join(sorted(faltam))}")

    afirm = conceito.get("estatuto_ontologico", {}).get("afirmacao_ontologica")
    print(f"  Afirmação ontológica: {afirm}")

    if estado == "intensificação legítima":
        print("  O campo aprofunda-se sem rutura.")
    else:
        print("  Nada é imposto. O real permanece critério silencioso.")

    return {
        "cid": cid,
        "faltam": faltam,
        "estado": estado,
        "afirmacao": afirm
    }


def ver_percurso_espiral(pid: str, voltas: int = 2, mostrar_justificacao: bool = True) -> None:
    conceitos = carregar_conceitos(PASTA_CONCEITOS)
    percurso = carregar_percurso(pid)
    criterios = carregar_criterios()

    print("\n" + "=" * 70)
    print(f"PERCURSO EM ESPIRAL: {percurso.get('nome', pid)}")
    print("=" * 70)

    ativos: Set[str] = set()
    historico: Set[str] = set()
    ausencias_por_volta: List[Set[str]] = []
    intensificacoes_por_volta: List[int] = []

    for volta in range(1, voltas + 1):
        ausencias = set()
        intensificacoes = 0

        for cid in percurso["sequencia"]:
            conceito = conceitos[cid]
            info = narrar_passo(cid, conceito, ativos, volta, historico)

            if info["estado"] == "intensificação legítima":
                intensificacoes += 1

            ausencias |= info["faltam"]
            ativos.add(cid)
            historico.add(cid)

        ausencias_por_volta.append(ausencias)
        intensificacoes_por_volta.append(intensificacoes)

    # ======================================================
    # MÉTRICAS GLOBAIS
    # ======================================================

    ausencias_globais = set().union(*ausencias_por_volta)

    metricas: Dict[str, Any] = {
        "intensificacoes_legitimas": sum(intensificacoes_por_volta),
        "ausencias_fundacionais_persistentes": classificar_ausencias_fundacionais(
            ausencias_globais, conceitos
        )
    }

    metricas["impossibilidade_ontologica"] = inferir_impossibilidade_ontologica(metricas)
    metricas["relacao_com_o_real"] = inferir_relacao_com_o_real(percurso, metricas)

    # ======================================================
    # RELATÓRIO
    # ======================================================

    print("\n" + "-" * 70)
    print("RELATÓRIO FINAL — MÉTRICAS")
    print("-" * 70)
    for k, v in metricas.items():
        print(f"• {k}: {v}")
    if metricas.get("impossibilidade_ontologica") is True:
            print("• Diagnóstico ontológico: impossibilidade estrutural do poder-ser.")

    print("\n" + "-" * 70)
    print("INFERÊNCIA — ESTADO FINAL DE MUNDO")
    print("-" * 70)

    aplicaveis = []
    for cfg in criterios.get("criterios", []):
        ok, just = avaliar_estado(cfg, metricas)
        if ok:
            aplicaveis.append((cfg["estado_final"], just))

    if not aplicaveis:
        print("⚠️  Nenhum estado inferido.")
    else:
        estado, just = aplicaveis[0]
        print(f"✅ Estado inferido: {estado}")
        if mostrar_justificacao:
            print("\nJustificação:")
            for j in just:
                print(" ", j)

    print("\n" + "-" * 70)
    print("O percurso não fecha.")
    print("Cada retorno aumenta a responsabilidade ontológica.")
    print("O que permanece aberto é a prática situada.")
    print("-" * 70)


# ==========================================================
# EXECUÇÃO
# ==========================================================

if __name__ == "__main__":
    ver_percurso_espiral(
        pid="P_PERCURSO_ONTOLOGICAMENTE_ESTERIL_POR_INVERSAO_DIRECIONAL",
        voltas=2,
        mostrar_justificacao=True
    )