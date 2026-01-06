import csv
from statistics import mean

with open("../output/dataset.csv", encoding="utf-8") as f:
    data = list(csv.DictReader(f))

print("Fragmentos:", len(data))
print("Média palavras:", mean(int(f["palavras"]) for f in data))
print("Fragmentos densos:", sum(1 for f in data if int(f["n_eixos"]) >= 2))
