import json
from pathlib import Path
from math import ceil

INPUT = Path("instancia_total_real_meta_schema_mestre_v0_2.json")
OUTPUT_DIR = Path("instancia_total_dividida")

# Ajusta se ainda ficar demasiado grande.
# 500 = ficheiros mais pequenos; 1000/2000 = ficheiros maiores.
BATCH_SIZE = 500

OUTPUT_DIR.mkdir(exist_ok=True)

def write_json(filename, data):
    path = OUTPUT_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {
        "ficheiro": filename,
        "bytes": path.stat().st_size
    }

def split_list(prefix, items, wrapper_key):
    written = []
    total = len(items)
    if total == 0:
        written.append(write_json(f"{prefix}__vazio.json", {wrapper_key: []}))
        return written

    parts = ceil(total / BATCH_SIZE)
    for i in range(parts):
        start = i * BATCH_SIZE
        end = start + BATCH_SIZE
        chunk = items[start:end]
        filename = f"{prefix}__parte_{i+1:03d}.json"
        written.append(write_json(filename, {
            "parte": i + 1,
            "total_partes": parts,
            "offset_inicio": start,
            "offset_fim_exclusivo": min(end, total),
            wrapper_key: chunk
        }))
    return written

def main():
    with INPUT.open("r", encoding="utf-8") as f:
        data = json.load(f)

    index = {
        "origem": str(INPUT),
        "batch_size": BATCH_SIZE,
        "ficheiros": []
    }

    # 1. Bloco governativo pequeno
    bloco_governo = {
        "meta_schema": data.get("meta_schema"),
        "governanca": data.get("governanca"),
        "manifesto_de_cobertura": data.get("manifesto_de_cobertura")
    }
    index["ficheiros"].append(write_json("00_manifesto_governanca.json", bloco_governo))

    # 2. Fontes e peças governativas
    if "registro_de_fontes" in data:
        index["ficheiros"].append(
            write_json("01_registro_de_fontes.json", {
                "registro_de_fontes": data["registro_de_fontes"]
            })
        )

    if "pecas_governativas" in data:
        index["ficheiros"].append(
            write_json("02_pecas_governativas.json", {
                "pecas_governativas": data["pecas_governativas"]
            })
        )

    # 3. Entidades canónicas
    entidades = data.get("entidades_canonicas", {})

    for key, prefix in [
        ("fragmentos", "03_entidades_fragmentos"),
        ("containers", "04_entidades_containers"),
        ("conceitos", "05_entidades_conceitos"),
        ("operacoes", "06_entidades_operacoes"),
        ("proposicoes", "07_entidades_proposicoes"),
        ("argumentos", "08_entidades_argumentos"),
    ]:
        value = entidades.get(key)
        if isinstance(value, list):
            index["ficheiros"].extend(split_list(prefix, value, key))
        elif value is not None:
            index["ficheiros"].append(write_json(f"{prefix}.json", {key: value}))

    # 4. Entidades estruturais pequenas agrupadas
    estruturais = {}
    for key in ["percursos", "ramos", "cfs", "capitulos", "faixas_expositivas"]:
        if key in entidades:
            estruturais[key] = entidades[key]

    if estruturais:
        index["ficheiros"].append(
            write_json("09_entidades_percursos_ramos_capitulos.json", estruturais)
        )

    # 5. Arestas, arbitragem e projeções
    if "arestas_tipadas" in data:
        index["ficheiros"].extend(
            split_list("10_arestas_tipadas", data["arestas_tipadas"], "arestas_tipadas")
        )

    if "arbitragem_transversal" in data:
        index["ficheiros"].append(
            write_json("11_arbitragem_transversal.json", {
                "arbitragem_transversal": data["arbitragem_transversal"]
            })
        )

    if "projecoes_regeneraveis" in data:
        index["ficheiros"].append(
            write_json("12_projecoes_regeneraveis.json", {
                "projecoes_regeneraveis": data["projecoes_regeneraveis"]
            })
        )

    # 6. Índice final
    write_json("INDEX_INSTANCIA_TOTAL_DIVIDIDA.json", index)

    print("Divisão concluída.")
    print(f"Ficheiros criados em: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    main()