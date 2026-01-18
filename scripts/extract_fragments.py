import re
import json
from pathlib import Path

def extract_fragments(md_path):
    text = Path(md_path).read_text(encoding="utf-8")

    pattern = re.compile(
        r"(##\s+F\d{4}[^\n]*)\n+(.*?)(?=\n+##\s+F\d{4}|\Z)",
        re.DOTALL
    )

    fragments = {}

    for match in pattern.finditer(text):
        header = match.group(1).strip()
        body = match.group(2).strip()

        id_match = re.search(r"F\d{4}", header)
        fragment_id = id_match.group() if id_match else None

        fragments[fragment_id] = {
            "header": header,
            "text": body
        }

    return fragments


if __name__ == "__main__":
    input_path = r"..\00_bruto\fragmentos.md"
    output_path = r"..\01_extraido\fragmentos_extraidos.json"

    fragments = extract_fragments(input_path)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fragments, f, ensure_ascii=False, indent=2)

    print(f"✔ {len(fragments)} fragmentos extraídos")
    print(f"✔ Ficheiro gerado em: {output_path}")
