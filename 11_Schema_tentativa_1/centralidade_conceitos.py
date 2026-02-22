from collections import defaultdict
from carregar_conceitos import carregar_conceitos
from extrair_dependencias import extrair_dependencias


def analisar_centralidade(conceitos, arestas):
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)

    for origem, destino, tipo in arestas:
        if tipo == "depende_de":
            # A depende de B → B é fundacional para A
            in_degree[origem] += 1
            out_degree[destino] += 1
        else:
            # implica / gera
            out_degree[origem] += 1
            in_degree[destino] += 1

    resultados = []

    for cid, c in conceitos.items():
        nivel = c["nivel"]
        total = in_degree[cid] + out_degree[cid]

        # peso simples: níveis mais baixos contam mais
        peso_nivel = 1 / (1 + float(nivel))
        centralidade_ponderada = total * peso_nivel

        resultados.append({
            "id": cid,
            "nivel": nivel,
            "in": in_degree[cid],
            "out": out_degree[cid],
            "total": total,
            "ponderada": round(centralidade_ponderada, 3)
        })

    return resultados


def imprimir_top(resultados, chave, titulo, n=15):
    print(f"\n=== {titulo} ===")
    for r in sorted(resultados, key=lambda x: x[chave], reverse=True)[:n]:
        print(
            f"{r['id']:30} "
            f"nível {r['nivel']:<3} | "
            f"in={r['in']:3} "
            f"out={r['out']:3} "
            f"total={r['total']:3} "
            f"pond={r['ponderada']:5}"
        )


if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")
    arestas = extrair_dependencias(conceitos)

    resultados = analisar_centralidade(conceitos, arestas)

    imprimir_top(resultados, "in", "MAIS FUNDACIONAIS (in-degree)")
    imprimir_top(resultados, "out", "MAIS PRODUTIVOS (out-degree)")
    imprimir_top(resultados, "total", "MAIS CENTRAIS (grau total)")
    imprimir_top(resultados, "ponderada", "CENTRALIDADE PONDERADA POR NÍVEL")