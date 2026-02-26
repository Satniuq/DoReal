import os

# Pasta atual (onde o script é executado)
PASTA = os.getcwd()

# Ficheiro de saída
FICHEIRO_SAIDA = os.path.join(PASTA, "conteudo_completo.txt")

# Extensões a extrair
EXTENSOES = (".json", ".py")

with open(FICHEIRO_SAIDA, "w", encoding="utf-8") as saida:
    for nome_ficheiro in sorted(os.listdir(PASTA)):
        if nome_ficheiro.endswith(EXTENSOES) and nome_ficheiro != os.path.basename(__file__):
            caminho = os.path.join(PASTA, nome_ficheiro)

            saida.write("=" * 80 + "\n")
            saida.write(f"FICHEIRO: {nome_ficheiro}\n")
            saida.write("=" * 80 + "\n\n")

            with open(caminho, "r", encoding="utf-8") as f:
                saida.write(f.read())

            saida.write("\n\n")

print(f"Extração concluída. Ficheiro criado em:\n{FICHEIRO_SAIDA}")