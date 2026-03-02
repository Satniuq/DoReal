import os
import json
import re

# Pasta onde estão os ficheiros
PASTA_ARGUMENTOS = r"C:\Users\vanes\DoReal_Casa_Local\DoReal\13_Meta_Indice\indice\argumentos"

# Ficheiro de saída
FICHEIRO_SAIDA = os.path.join(PASTA_ARGUMENTOS, "argumentos_unificados.json")


def extrair_numero_inicial(nome_ficheiro):
    """
    Extrai o número inicial do nome do ficheiro.
    Ex.: '10_ARG_....json' -> 10
    """
    m = re.match(r"^(\d+)_", nome_ficheiro)
    if m:
        return int(m.group(1))
    return float("inf")


def unir_argumentos():
    ficheiros = [
        f for f in os.listdir(PASTA_ARGUMENTOS)
        if f.lower().endswith(".json") and f != os.path.basename(FICHEIRO_SAIDA)
    ]

    ficheiros.sort(key=extrair_numero_inicial)

    argumentos = []

    for nome in ficheiros:
        caminho = os.path.join(PASTA_ARGUMENTOS, nome)

        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = json.load(f)

        # opcional: guardar o nome do ficheiro de origem dentro de cada objeto
        conteudo["_ficheiro_origem"] = nome

        argumentos.append(conteudo)

    with open(FICHEIRO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(argumentos, f, ensure_ascii=False, indent=2)

    print(f"Unidos {len(argumentos)} ficheiros em:")
    print(FICHEIRO_SAIDA)


if __name__ == "__main__":
    unir_argumentos()