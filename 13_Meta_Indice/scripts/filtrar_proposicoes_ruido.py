import os
import json
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PROPOSICOES_FILE = os.path.join(
    BASE_DIR, "dados_base", "proposicoes", "proposicoes_normalizadas.json"
)

OUTPUT_VALIDAS = os.path.join(
    BASE_DIR, "dados_base", "proposicoes", "proposicoes_filtradas.json"
)

OUTPUT_RUIDO = os.path.join(
    BASE_DIR, "dados_base", "proposicoes", "proposicoes_ruido.json"
)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def eh_ruido(texto: str) -> bool:

    texto_lower = texto.lower().strip()

    # 1. Perguntas
    if texto.strip().endswith("?"):
        return True

    # 2. Muito curto
    if len(texto.split()) < 4:
        return True

    # 3. Interjeições típicas
    if any(x in texto_lower for x in [
        "pá",
        "olha",
        "está bem",
        "pois",
        "risos",
        "boa pergunta",
        "não sei",
        "whatever"
    ]):
        return True

    # 4. Fragmentos iniciados por conjunção
    if re.match(r"^(mas|e|porque|então)\b", texto_lower):
        return True

    return False


if __name__ == "__main__":

    proposicoes = load_json(PROPOSICOES_FILE)

    validas = []
    ruido = []

    for p in proposicoes:

        texto = p.get("texto_literal", "")

        if eh_ruido(texto):
            ruido.append(p)
        else:
            validas.append(p)

    save_json(OUTPUT_VALIDAS, validas)
    save_json(OUTPUT_RUIDO, ruido)

    print("Total:", len(proposicoes))
    print("Válidas:", len(validas))
    print("Ruído:", len(ruido))