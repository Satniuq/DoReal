import json
import os

from carregar_conceitos import carregar_conceitos


CAMINHO_OPERACOES = os.path.join("operacoes", "operacoes.json")


def carregar_operacoes_declaradas():
    with open(CAMINHO_OPERACOES, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.keys())


def extrair_operacoes_conceito(cid, c):
    usadas = set()

    # --- operações ontológicas ---
    ops = c.get("operacoes_ontologicas", {})
    for bloco, lista in ops.items():
        if isinstance(lista, list):
            for op in lista:
                usadas.add(op)

    # --- notas de proteção (reintegração) ---
    notas = c.get("notas_de_protecao", {})
    for op in notas.get("operacoes_de_reintegracao", []):
        usadas.add(op)

    return usadas


if __name__ == "__main__":
    operacoes_declaradas = carregar_operacoes_declaradas()
    conceitos = carregar_conceitos("conceitos")

    avisos = []

    for cid, c in conceitos.items():
        usadas = extrair_operacoes_conceito(cid, c)

        for op in sorted(usadas):
            if op not in operacoes_declaradas:
                avisos.append(
                    f"{cid}: usa operação não declarada '{op}'"
                )

    print(f"Operações não declaradas em conceitos: {len(avisos)}")
    for a in avisos:
        print("AVISO:", a)