from pathlib import Path

# Pasta atual
pasta = Path.cwd()

# Ficheiro de saída
ficheiro_saida = pasta / "D_TODOS_UNIFICADOS.txt"

# Lista dos ficheiros D_*.txt, excluindo o próprio ficheiro de saída caso já exista
ficheiros = sorted(
    f for f in pasta.glob("D_*.txt")
    if f.name != ficheiro_saida.name
)

with ficheiro_saida.open("w", encoding="utf-8") as destino:
    for i, ficheiro in enumerate(ficheiros, start=1):
        conteudo = ficheiro.read_text(encoding="utf-8").strip()

        destino.write("=" * 80 + "\n")
        destino.write(f"{ficheiro.name}\n")
        destino.write("=" * 80 + "\n\n")
        destino.write(conteudo)
        destino.write("\n\n")

print(f"Unificação concluída. Ficheiro criado: {ficheiro_saida}")
print(f"Total de ficheiros unidos: {len(ficheiros)}")