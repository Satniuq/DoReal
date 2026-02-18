import re

ficheiro_entrada = "../data/06_01Texto_No_Indice_TXT.txt"
ficheiro_saida = "../data/proposicoes_unicas_canonicas.txt"

padrao_proposicao = re.compile(
    r"""
    \[\d+\]\s+ID:\s*(P\d+)\s*\|.*?   # linha da proposição com contador e ID
    \n\s*EXP:.*?                    # linha EXP
    \n\s*TAX:.*?                    # linha TAX
    \n\s*-{5,}                      # linha de fecho
    """,
    re.DOTALL | re.VERBOSE
)

with open(ficheiro_entrada, "r", encoding="utf-8") as f:
    conteudo = f.read()

proposicoes = {}

for match in padrao_proposicao.finditer(conteudo):
    id_ = match.group(1)
    bloco = match.group(0).strip()

    # manter apenas a primeira ocorrência (forma canónica)
    if id_ not in proposicoes:
        proposicoes[id_] = bloco

# ordenar por número do ID
proposicoes_ordenadas = dict(
    sorted(proposicoes.items(), key=lambda x: int(x[0][1:]))
)

with open(ficheiro_saida, "w", encoding="utf-8") as f:
    for bloco in proposicoes_ordenadas.values():
        f.write(bloco + "\n\n")

print(
    f"Ficheiro criado com {len(proposicoes_ordenadas)} proposições únicas "
    f"na forma canónica: {ficheiro_saida}"
)
