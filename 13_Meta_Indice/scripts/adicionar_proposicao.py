import json
import os

BASE_DIR = r"C:\Users\vanes\DoReal_Casa_Local\DoReal\13_Meta_Indice"

PATH_PROPOSICOES = os.path.join(BASE_DIR, "dados_base", "proposicoes.json")
PATH_INDICE = os.path.join(BASE_DIR, "dados_base", "indice_conceitos.json")
PATH_OPERACOES = os.path.join(BASE_DIR, "dados_base", "operacoes.json")

def load(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    proposicoes = load(PATH_PROPOSICOES, [])
    indice = load(PATH_INDICE, {})
    operacoes = load(PATH_OPERACOES, {})

    print("Nova proposição\n")

    pid = f"P_{len(proposicoes)+1:04d}"
    texto = input("Texto da proposição: ").strip()

    conceitos = input("Conceitos (IDs separados por vírgula): ").split(",")
    conceitos = [c.strip() for c in conceitos if c.strip()]
    for c in conceitos:
        if c not in indice:
            raise ValueError(f"Conceito inválido: {c}")

    ops = input("Operações (IDs separados por vírgula): ").split(",")
    ops = [o.strip() for o in ops if o.strip()]
    for o in ops:
        if o not in operacoes:
            raise ValueError(f"Operação inválida: {o}")

    regime = input("Regime dominante: ").strip()
    tipo = input("Tipo (ontologica / epistemologica / etico_ontologica / critica): ").strip()

    prop = {
        "id": pid,
        "texto": texto,
        "conceitos_mobilizados": conceitos,
        "operacoes": ops,
        "regime": regime,
        "tipo": tipo,
        "estatuto_epistemico": "adequada",
        "criterio_de_validacao": "",
        "dependencias_explicitas": [],
        "gera": [],
        "possiveis_erros": [],
        "observacoes": []
    }

    proposicoes.append(prop)
    save(PATH_PROPOSICOES, proposicoes)

    print(f"\n✅ Proposição {pid} adicionada.")

if __name__ == "__main__":
    main()