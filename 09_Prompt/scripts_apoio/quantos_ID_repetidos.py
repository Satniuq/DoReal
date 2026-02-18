from collections import Counter
import re

padrao_id = re.compile(r"\bID:\s*(P\d+)\b")

with open("../data/06_01Texto_No_Indice_TXT.txt", "r", encoding="utf-8") as f:
    ids = padrao_id.findall(f.read())

contagem = Counter(ids)

for id_, n in sorted(contagem.items(), key=lambda x: int(x[0][1:])):
    print(f"{id_}: {n}")
