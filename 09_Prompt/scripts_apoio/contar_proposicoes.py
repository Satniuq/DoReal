import re

ficheiro = "../data/06_01Texto_No_Indice_TXT.txt"

padrao_id = re.compile(r"\bID:\s*P\d+\b")

with open(ficheiro, "r", encoding="utf-8") as f:
    conteudo = f.read()

ids = padrao_id.findall(conteudo)

print(f"Número total de IDs encontrados: {len(ids)}")
