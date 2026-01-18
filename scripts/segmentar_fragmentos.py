import json
import re
from pathlib import Path

# ---------- parâmetros conservadores ----------
MIN_CHARS = 60      # abaixo disto, junta ao anterior
MAX_CHARS = 800     # acima disto, força divisão suave

SPLIT_REGEX = re.compile(
    r"(?<=[\.\?\!])\s+|\n{2,}"
)

def segmentar_texto(texto):
    partes = SPLIT_REGEX.split(texto)
    segmentos = []

    buffer = ""

    for parte in partes:
        parte = parte.strip()
        if not parte:
            continue

        if not buffer:
            buffer = parte
            continue

        if len(buffer) < MIN_CHARS:
            buffer += " " + parte
        else:
            segmentos.append(buffer.strip())
            buffer = parte

        if len(buffer) > MAX_CHARS:
            segmentos.append(buffer.strip())
            buffer = ""

    if buffer:
        segmentos.append(buffer.strip())

    return segmentos


if __name__ == "__main__":
    input_path = r"..\01_extraido\fragmentos_extraidos.json"
    output_path = r"..\02_segmentado\fragmentos_segmentados.json"

    data = json.loads(Path(input_path).read_text(encoding="utf-8"))

    output = {}

    for fid, frag in data.items():
        texto = frag["text"]
        segmentos = segmentar_texto(texto)

        for i, seg in enumerate(segmentos, start=1):
            sid = f"{fid}.{i}"
            output[sid] = {
                "origem": fid,
                "texto": seg
            }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✔ Segmentação concluída")
    print(f"✔ Fragmentos originais : {len(data)}")
    print(f"✔ Mini-fragmentos gerados : {len(output)}")
    print(f"✔ Ficheiro gerado em: {output_path}")
