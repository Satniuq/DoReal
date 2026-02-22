from collections import defaultdict
from typing import List, Tuple
from carregar_conceitos import carregar_conceitos


Aresta = Tuple[str, str, str]  # (origem, destino, tipo)


def extrair_dependencias(conceitos) -> List[Aresta]:
    """
    Extrai relações ontológicas entre conceitos.

    Tipos:
        - depende_de   (A depende_de B)  => B -> A
        - implica      (A implica B)     => A -> B
        - gera         (A gera B)        => A -> B
    """
    arestas: List[Aresta] = []

    for cid, c in conceitos.items():
        deps = c.get("dependencias", {})

        for origem in deps.get("depende_de", []):
            arestas.append((origem, cid, "depende_de"))

        for destino in deps.get("implica", []):
            arestas.append((cid, destino, "implica"))

        for destino in c.get("dinamica", {}).get("gera", []):
            arestas.append((cid, destino, "gera"))

    return arestas


if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")
    arestas = extrair_dependencias(conceitos)

    print(f"Relações ontológicas encontradas: {len(arestas)}")
    for a in arestas[:10]:
        print(a)