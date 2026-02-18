import re

ficheiro_entrada = "../data/06_01Texto_No_Indice_TXT.txt"
ficheiro_saida = "../data/ids_ordenados.txt"

padrao_id = re.compile(r"\bID:\s*(P\d+)\b")

with open(ficheiro_entrada, "r", encoding="utf-8") as f:
    conteudo = f.read()

ids = padrao_id.findall(conteudo)

ids_ordenados = sorted(
    set(ids),
    key=lambda x: int(x[1:])
)

with open(ficheiro_saida, "w", encoding="utf-8") as f:
    f.write(f"Número total de IDs encontrados: {len(ids_ordenados)}\n\n")
    for id_ in ids_ordenados:
        f.write(f"{id_}\n")

print(f"Ficheiro criado com sucesso: {ficheiro_saida}")
