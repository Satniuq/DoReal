import json
from pathlib import Path
import re

def contar_palavras(texto):
    return len(re.findall(r"\b\w+\b", texto))

# caminhos
original_path = r"..\00_bruto\fragmentos.md"
extraido_path = r"..\01_extraido\fragmentos_extraidos.json"

# ler ficheiro original
texto_original = Path(original_path).read_text(encoding="utf-8")
palavras_original = contar_palavras(texto_original)

# ler ficheiro extraído
with open(extraido_path, "r", encoding="utf-8") as f:
    fragmentos = json.load(f)

texto_reconstruido = ""
for frag in fragmentos.values():
    texto_reconstruido += frag["header"] + "\n\n" + frag["text"] + "\n\n"

palavras_extraido = contar_palavras(texto_reconstruido)

print("Palavras no original :", palavras_original)
print("Palavras no extraído :", palavras_extraido)

if palavras_original == palavras_extraido:
    print("✔ VERIFICAÇÃO OK — nenhuma palavra perdida")
else:
    print("✘ ATENÇÃO — diferença detectada")
    print("Diferença:", palavras_original - palavras_extraido)
