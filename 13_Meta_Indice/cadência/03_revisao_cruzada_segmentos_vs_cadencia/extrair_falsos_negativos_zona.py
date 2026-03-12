import csv
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

FICHEIRO_ENTRADA = BASE_DIR / "zona_indefinida_prioritarias.csv"
FICHEIRO_SAIDA = BASE_DIR / "falsos_negativos_zona.csv"


# ============================================================
# UTILITÁRIOS
# ============================================================

def ler_csv(caminho: Path):
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def escrever_csv(caminho: Path, linhas, colunas):
    with caminho.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=colunas, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(linhas)


def norm(valor):
    if valor is None:
        return ""
    return str(valor).strip().lower()


def prioridade_funcao(valor):
    """
    Ordem:
    1. formulacao_inicial
    2. desenvolvimento
    3. critica_de_erro
    """
    v = norm(valor)
    mapa = {
        "formulacao_inicial": 0,
        "desenvolvimento": 1,
        "critica_de_erro": 2,
    }
    return mapa.get(v, 9)


def prioridade_aproveitamento(valor):
    """
    Primeiro apoio_argumentativo, depois material_a_retrabalhar.
    """
    v = norm(valor)
    mapa = {
        "apoio_argumentativo": 0,
        "material_a_retrabalhar": 1,
    }
    return mapa.get(v, 9)


def prioridade_confianca_cadencia(valor):
    """
    Primeiro baixa, depois media, depois alta.
    """
    v = norm(valor)
    mapa = {
        "baixa": 0,
        "media": 1,
        "alta": 2,
    }
    return mapa.get(v, 9)


def prioridade_revisao_humana(valor):
    return 0 if norm(valor) == "true" else 1


def chave_ordenacao(linha):
    ordem = linha.get("ordem_no_ficheiro", "")
    try:
        ordem_num = int(ordem)
    except Exception:
        ordem_num = 999999

    return (
        prioridade_revisao_humana(linha.get("necessita_revisao_humana")),
        prioridade_confianca_cadencia(linha.get("confianca_cadencia")),
        prioridade_funcao(linha.get("funcao_cadencia_principal")),
        prioridade_aproveitamento(linha.get("aproveitamento_editorial")),
        ordem_num,
        linha.get("fragment_id", ""),
    )


# ============================================================
# EXECUÇÃO
# ============================================================

linhas = ler_csv(FICHEIRO_ENTRADA)

funcoes_alvo = {
    "formulacao_inicial",
    "desenvolvimento",
    "critica_de_erro",
}

aproveitamentos_alvo = {
    "apoio_argumentativo",
    "material_a_retrabalhar",
}

filtradas = [
    l for l in linhas
    if norm(l.get("zona_provavel_percurso")) == "indefinida"
    and norm(l.get("integridade_semantica_grau")) == "alto"
    and norm(l.get("confianca_segmentacao")) == "alta"
    and norm(l.get("funcao_cadencia_principal")) in funcoes_alvo
    and norm(l.get("aproveitamento_editorial")) in aproveitamentos_alvo
]

filtradas.sort(key=chave_ordenacao)

for idx, linha in enumerate(filtradas, start=1):
    linha["prioridade_falso_negativo"] = idx
    linha["zona_sugerida_manual"] = ""
    linha["grau_de_conviccao_manual"] = ""
    linha["motivo_da_reclassificacao"] = ""
    linha["decisao_editorial_manual"] = ""
    linha["notas_revisor"] = ""

colunas_base = list(filtradas[0].keys()) if filtradas else []

extras = [
    "prioridade_falso_negativo",
    "zona_sugerida_manual",
    "grau_de_conviccao_manual",
    "motivo_da_reclassificacao",
    "decisao_editorial_manual",
    "notas_revisor",
]

colunas = [c for c in colunas_base if c not in extras] + extras

escrever_csv(FICHEIRO_SAIDA, filtradas, colunas)

print(f"Ficheiro criado: {FICHEIRO_SAIDA}")
print(f"Total de falsos negativos prováveis de zona: {len(filtradas)}")
print("Concluído.")