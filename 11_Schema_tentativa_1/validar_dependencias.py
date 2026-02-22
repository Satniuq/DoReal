from collections import defaultdict
from carregar_conceitos import carregar_conceitos
from extrair_dependencias import extrair_dependencias


def validar_dependencias(conceitos, arestas):
    erros = []
    avisos = []

    # mapa id -> nível
    nivel = {cid: c["nivel"] for cid, c in conceitos.items()}

    for origem, destino, tipo in arestas:
        if origem not in nivel or destino not in nivel:
            avisos.append(f"Referência desconhecida: {origem} -> {destino}")
            continue

        n_origem = nivel[origem]
        n_destino = nivel[destino]

        # Regra 1: depende_de não pode subir de nível
        if tipo == "depende_de" and n_origem > n_destino:
            erros.append(
                f"{destino} (nível {n_destino}) depende de {origem} (nível {n_origem})"
            )

        # Regra 2: gera não deve violar escala (alerta, não erro)
        if tipo == "gera" and abs(n_origem - n_destino) > 1:
            avisos.append(
                f"{origem} gera {destino} com salto de escala ({n_origem} -> {n_destino})"
            )

    return erros, avisos


if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")
    arestas = extrair_dependencias(conceitos)

    erros, avisos = validar_dependencias(conceitos, arestas)

    print(f"Erros ontológicos: {len(erros)}")
    for e in erros:
        print("ERRO:", e)

    print(f"\nAvisos ontológicos: {len(avisos)}")
    for a in avisos[:10]:
        print("AVISO:", a)