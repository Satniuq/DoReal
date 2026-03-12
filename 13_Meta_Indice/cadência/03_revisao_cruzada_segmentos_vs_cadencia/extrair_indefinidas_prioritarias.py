import csv
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

FICHEIRO_ENTRADA = BASE_DIR / "tabela_revisao_cadencia.csv"
FICHEIRO_SAIDA = BASE_DIR / "zona_indefinida_prioritarias.csv"


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
    Ordem de revisão:
    1. formulacao_inicial
    2. desenvolvimento
    3. critica_de_erro
    4. resto
    """
    v = norm(valor)
    mapa = {
        "formulacao_inicial": 0,
        "desenvolvimento": 1,
        "critica_de_erro": 2,
    }
    return mapa.get(v, 9)


def prioridade_integridade(valor):
    """
    alto primeiro, depois medio, depois baixo
    """
    v = norm(valor)
    mapa = {
        "alto": 0,
        "media": 1,
        "medio": 1,
        "baixo": 2,
    }
    return mapa.get(v, 9)


def prioridade_confianca_segmentacao(valor):
    """
    alta primeiro, depois media, depois baixa
    """
    v = norm(valor)
    mapa = {
        "alta": 0,
        "media": 1,
        "baixa": 2,
    }
    return mapa.get(v, 9)


def prioridade_revisao_humana(valor):
    return 0 if norm(valor) == "true" else 1


def prioridade_confianca_cadencia(valor):
    """
    baixa primeiro, porque são os mais urgentes
    """
    v = norm(valor)
    mapa = {
        "baixa": 0,
        "media": 1,
        "alta": 2,
    }
    return mapa.get(v, 9)


def prioridade_aproveitamento(valor):
    """
    Primeiro os que parecem falsos negativos:
    - material_a_retrabalhar
    - nota_lateral_aproveitavel
    - apoio_argumentativo
    - nucleo_de_capitulo
    """
    v = norm(valor)
    mapa = {
        "material_a_retrabalhar": 0,
        "nota_lateral_aproveitavel": 1,
        "apoio_argumentativo": 2,
        "nucleo_de_capitulo": 3,
    }
    return mapa.get(v, 9)


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
        prioridade_integridade(linha.get("integridade_semantica_grau")),
        prioridade_confianca_segmentacao(linha.get("confianca_segmentacao")),
        prioridade_aproveitamento(linha.get("aproveitamento_editorial")),
        ordem_num,
        linha.get("fragment_id", ""),
    )


# ============================================================
# EXECUÇÃO
# ============================================================

linhas = ler_csv(FICHEIRO_ENTRADA)

indefinidas = [
    l for l in linhas
    if norm(l.get("zona_provavel_percurso")) == "indefinida"
]

indefinidas.sort(key=chave_ordenacao)

# acrescentar colunas auxiliares visíveis para revisão
for idx, linha in enumerate(indefinidas, start=1):
    linha["prioridade_revisao"] = idx
    linha["hipotese_de_trabalho"] = ""
    linha["zona_revista_manualmente"] = ""
    linha["funcao_revista_manualmente"] = ""
    linha["decisao_editorial_manual"] = ""
    linha["notas_revisor"] = ""

# escolher colunas principais já existentes + auxiliares
colunas_base = list(indefinidas[0].keys()) if indefinidas else []

# garantir que as colunas auxiliares ficam no fim
extras = [
    "prioridade_revisao",
    "hipotese_de_trabalho",
    "zona_revista_manualmente",
    "funcao_revista_manualmente",
    "decisao_editorial_manual",
    "notas_revisor",
]

colunas = [c for c in colunas_base if c not in extras] + extras

escrever_csv(FICHEIRO_SAIDA, indefinidas, colunas)

print(f"Ficheiro criado: {FICHEIRO_SAIDA}")
print(f"Total de casos com zona indefinida: {len(indefinidas)}")
print("Concluído.")