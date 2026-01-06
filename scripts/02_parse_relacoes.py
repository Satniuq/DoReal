from pathlib import Path
from collections import defaultdict
import re

BASE_DIR = Path(__file__).resolve().parent.parent

FILES = {
    "conceitos": BASE_DIR / "01_indexacao" / "conceitos.md",
    "eixos": BASE_DIR / "01_indexacao" / "eixos.md",
    "teses": BASE_DIR / "01_indexacao" / "teses.md",
    "tensoes": BASE_DIR / "02_relacoes" / "tensoes.md",
}

def parse_relacoes(path):
    rel = defaultdict(set)
    with open(path, encoding="utf-8") as f:
        text = f.read()

    blocks = text.split("## ")
    for b in blocks:
        if not b.strip():
            continue

        # código do conceito/eixo/tese/tensão
        header = b.splitlines()[0]
        codigo = header.split("—")[0].strip()

        # TODOS os fragmentos referidos no bloco
        fids = set(re.findall(r"F\d{4}", b))
        for fid in fids:
            rel[fid].add(codigo)

    return rel

relations = {}
for name, path in FILES.items():
    relations[name] = parse_relacoes(path)
    print(f"{name}: {len(relations[name])} fragmentos com ligações")
