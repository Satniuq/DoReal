import json
import os
from collections import defaultdict, Counter

# ===== Caminhos relativos =====
PATH_DEFINICOES = r"../09_Prompt/config/definicoes.json"
PATH_PROPOSICOES = r"../09_Prompt/data/extracao_ontologica_final.json"

OUT_DIR = "data/auditoria_definicoes"

# ===== Util =====
def ler_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def limpar_nome(nome):
    return nome.replace("/", "_").replace(" ", "_")

# ===== Auditoria =====
def auditar():
    os.makedirs(OUT_DIR, exist_ok=True)

    defs = ler_json(PATH_DEFINICOES)
    props = ler_json(PATH_PROPOSICOES)

    # indexar proposições por campo principal
    props_por_def = defaultdict(list)

    for p in props:
        lv = p.get("localizacao_vertical", {}) or {}
        cp = lv.get("campo_principal")
        if cp:
            props_por_def[cp].append(p)

    for d in defs:
        did = d["id"]
        campo = d.get("campo", "")
        nivel = d.get("nivel", "")
        definicao = d.get("definicao", "")

        lista = props_por_def.get(did, [])

        operacoes = Counter()
        dependencias = Counter()

        for p in lista:
            for op in (p.get("operacao_ontologica") or []):
                operacoes[op] += 1
            for dep in (p.get("dependencias") or []):
                dependencias[dep] += 1

        # ordenar métricas
        ops_ordenadas = operacoes.most_common()
        deps_ordenadas = dependencias.most_common()

        # escrever ficheiro
        nome_ficheiro = limpar_nome(did) + ".txt"
        path_out = os.path.join(OUT_DIR, nome_ficheiro)

        with open(path_out, "w", encoding="utf-8") as f:
            f.write(f"DEFINIÇÃO: {did}\n")
            f.write(f"Campo: {campo}\n")
            f.write(f"Nível ontológico: {nivel}\n")
            f.write(f"Texto definição:\n{definicao}\n\n")

            f.write("=" * 60 + "\n")
            f.write(f"Total de proposições associadas: {len(lista)}\n\n")

            f.write("Operações ontológicas mais usadas:\n")
            for op, c in ops_ordenadas:
                f.write(f"  {op} → {c}\n")
            f.write("\n")

            f.write("Dependências mais frequentes:\n")
            for dep, c in deps_ordenadas:
                f.write(f"  {dep} → {c}\n")
            f.write("\n")

            f.write("=" * 60 + "\n")
            f.write("LISTA DE PROPOSIÇÕES:\n\n")

            for p in lista:
                f.write(f"{p.get('id_proposicao')}:\n")
                f.write(p.get("texto_literal", "") + "\n")
                f.write("-" * 40 + "\n")

    print("AUDITORIA CONCLUÍDA")
    print(f"Ficheiros gerados em: {OUT_DIR}")

if __name__ == "__main__":
    auditar()
