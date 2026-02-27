import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PROPOSICOES_FILE = os.path.join(
    BASE_DIR, "dados_base", "proposicoes", "proposicoes_filtradas.json"
)

MAPA_CAPITULOS_FILE = os.path.join(BASE_DIR, "meta", "mapa_capitulos.json")

INDICE_CAPITULO_FILE = os.path.join(
    BASE_DIR, "indices_derivados", "indice_proposicoes_por_capitulo.json"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR, "indices_derivados", "manuscrito_estrutural.txt"
)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":

    proposicoes = load_json(PROPOSICOES_FILE)
    mapa_capitulos = load_json(MAPA_CAPITULOS_FILE)
    indice_capitulos = load_json(INDICE_CAPITULO_FILE)

    # mapa id -> texto
    texto_por_id = {
        p["id_proposicao"]: p["texto_literal"]
        for p in proposicoes
    }

    # organizar capítulos por parte e ordem numérica
    capitulos_ordenados = sorted(
        mapa_capitulos.items(),
        key=lambda x: (
            x[1]["parte"],
            int(x[0].split("_")[1])
        )
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

        parte_atual = None

        for cap_id, info in capitulos_ordenados:

            parte = info["parte"]

            if parte != parte_atual:
                f.write("\n" + "=" * 80 + "\n")
                f.write(parte + "\n")
                f.write("=" * 80 + "\n\n")
                parte_atual = parte

            f.write("\n" + "-" * 60 + "\n")
            f.write(cap_id + "\n")
            f.write("-" * 60 + "\n\n")

            propos_ids = indice_capitulos.get(cap_id, [])

            for pid in sorted(propos_ids):
                texto = texto_por_id.get(pid, "[TEXTO NÃO ENCONTRADO]")
                f.write(f"{pid} — {texto}\n")

    print("✔ manuscrito_estrutural.txt gerado com sucesso.")