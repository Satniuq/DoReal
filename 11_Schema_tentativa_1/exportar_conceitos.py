import json
from carregar_conceitos import carregar_conceitos


def exportar_conceitos(
    pasta_conceitos="conceitos",
    ficheiro_saida="todos_os_conceitos.json"
):
    conceitos = carregar_conceitos(pasta_conceitos)

    with open(ficheiro_saida, "w", encoding="utf-8") as f:
        json.dump(
            conceitos,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"✔ {len(conceitos)} conceitos exportados para '{ficheiro_saida}'")


if __name__ == "__main__":
    exportar_conceitos()