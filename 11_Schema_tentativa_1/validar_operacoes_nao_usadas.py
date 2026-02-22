import json
import os

from carregar_conceitos import carregar_conceitos


CAMINHO_OPERACOES = os.path.join("operacoes", "operacoes.json")


def carregar_operacoes_declaradas():
    with open(CAMINHO_OPERACOES, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.keys())


def extrair_operacoes_conceito(c):
    usadas = set()

    # --- operações ontológicas ---
    ops = c.get("operacoes_ontologicas", {})
    for lista in ops.values():
        if isinstance(lista, list):
            usadas.update(lista)

    # --- notas de protecção ---
    notas = c.get("notas_de_protecao", {})
    usadas.update(notas.get("operacoes_de_reintegracao", []))

    return usadas


if __name__ == "__main__":
    operacoes_declaradas = carregar_operacoes_declaradas()
    conceitos = carregar_conceitos("conceitos")

    operacoes_usadas = set()

    for c in conceitos.values():
        operacoes_usadas.update(extrair_operacoes_conceito(c))

    nao_usadas = sorted(op for op in operacoes_declaradas if op not in operacoes_usadas)

    print(f"Operações declaradas: {len(operacoes_declaradas)}")
    print(f"Operações usadas em conceitos: {len(operacoes_usadas)}")
    print(f"Operações NÃO usadas: {len(nao_usadas)}")

    for op in nao_usadas:
        print("NAO USADA:", op)