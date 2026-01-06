from pathlib import Path
import csv
from collections import defaultdict
import re

print("=== BUILD DATASET DEBUG START ===")

# --- BASE DIR ---
BASE_DIR = Path(__file__).resolve().parent.parent
print("[DEBUG] BASE_DIR =", BASE_DIR)

# --- FRAGMENTOS CSV ---
FRAGMENTOS_CSV = BASE_DIR / "output" / "fragmentos.csv"
print("[DEBUG] FRAGMENTOS_CSV =", FRAGMENTOS_CSV)
print("[DEBUG] EXISTS FRAGMENTOS_CSV =", FRAGMENTOS_CSV.exists())

if not FRAGMENTOS_CSV.exists():
    raise FileNotFoundError(f"fragmentos.csv não encontrado em {FRAGMENTOS_CSV}")

# --- CONTAR LINHAS BRUTAS ---
with open(FRAGMENTOS_CSV, encoding="utf-8") as f:
    total_linhas = sum(1 for _ in f)

print("[DEBUG] TOTAL LINHAS NO CSV (inclui header) =", total_linhas)

# --- LER CSV ---
with open(FRAGMENTOS_CSV, encoding="utf-8") as f:
    fragmentos = list(csv.DictReader(f))

print("[DEBUG] FRAGMENTOS LIDOS (DictReader) =", len(fragmentos))

if fragmentos:
    print("[DEBUG] PRIMEIRO FRAGMENTO ID =", fragmentos[0].get("id"))
    print("[DEBUG] ÚLTIMO FRAGMENTO ID =", fragmentos[-1].get("id"))

# --- FICHEIROS DE RELAÇÕES ---
FILES = {
    "conceitos": BASE_DIR / "01_indexacao" / "conceitos.md",
    "eixos": BASE_DIR / "01_indexacao" / "eixos.md",
    "teses": BASE_DIR / "01_indexacao" / "teses.md",
    "tensoes": BASE_DIR / "02_relacoes" / "tensoes.md",
}

def parse_relacoes(path):
    rel = defaultdict(set)

    print(f"[DEBUG] A LER RELAÇÕES DE {path} (exists={path.exists()})")

    if not path.exists():
        return rel

    with open(path, encoding="utf-8") as f:
        text = f.read()

    blocks = text.split("## ")
    for b in blocks:
        if not b.strip():
            continue

        header = b.splitlines()[0]
        codigo = header.split("—")[0].strip()

        fids = set(re.findall(r"F\d{4}", b))
        for fid in fids:
            rel[fid].add(codigo)

    return rel

# --- CARREGAR RELAÇÕES ---
relations = {}
for name, path in FILES.items():
    relations[name] = parse_relacoes(path)
    print(f"[DEBUG] {name}: {len(relations[name])} fragmentos ligados")

# --- ENRIQUECER FRAGMENTOS (SEM FILTRAR) ---
for f in fragmentos:
    fid = f["id"]
    f["n_conceitos"] = len(relations["conceitos"].get(fid, []))
    f["n_eixos"] = len(relations["eixos"].get(fid, []))
    f["n_teses"] = len(relations["teses"].get(fid, []))
    f["n_tensoes"] = len(relations["tensoes"].get(fid, []))

# --- OUTPUT ---
OUTPUT = BASE_DIR / "output" / "dataset.csv"
print("[DEBUG] OUTPUT =", OUTPUT)

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fragmentos[0].keys())
    writer.writeheader()
    writer.writerows(fragmentos)

print("[DEBUG] DATASET ESCRITO COM", len(fragmentos), "FRAGMENTOS")
print("=== BUILD DATASET DEBUG END ===")
