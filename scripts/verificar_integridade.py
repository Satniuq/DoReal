from collections import Counter

def contar_chars(path):
    with open(path, "r", encoding="utf-8") as f:
        return Counter(f.read())

a = contar_chars("fragmentos_ordenados_por_indice.md")
b = contar_chars("fragmentos_ordenados.md")

diff1 = a - b
diff2 = b - a

if not diff1 and not diff2:
    print("OK — nenhum carácter perdido ou criado.")
else:
    print("ERRO — diferenças encontradas.")
    print("Removidos:", diff1)
    print("Adicionados:", diff2)
