import re
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT = BASE_DIR / "00_bruto" / "fragmentos.md"
OUTPUT = BASE_DIR / "output" / "fragmentos.csv"

# --- LER FRAGMENTOS ---
with open(INPUT, encoding="utf-8") as f:
    text = f.read()

# procura blocos do tipo:
# ## F0123
# texto...
pattern = re.compile(
    r"##\s*(?:Fragmento\s*)?(F\d{4}).*?\n(.*?)(?=\n##\s*(?:Fragmento\s*)?F\d{4}|\Z)",
    re.S
)


matches = pattern.findall(text)

rows = []
for fid, body in matches:
    body = body.strip()
    rows.append({
        "id": fid,
        "texto": body,
        "palavras": len(body.split())
    })

# --- ESCREVER CSV (CORRETO PARA TEXTO MULTILINHA) ---
with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["id", "texto", "palavras"],
        quoting=csv.QUOTE_ALL
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"{len(rows)} fragmentos processados.")
