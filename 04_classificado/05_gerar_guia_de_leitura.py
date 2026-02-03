import json

def criar_guia_txt(caminho_entrada, caminho_saida):
    with open(caminho_entrada, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    blocos = {
        "BLOCO I - A FUNDAÇÃO (O REAL EM SI)": [],
        "BLOCO II - A MEDIAÇÃO (O ANIMAL HUMANO)": [],
        "BLOCO III - A PATOLOGIA (O DESVIO E A CRÍTICA)": [],
        "BLOCO IV - A REINTEGRAÇÃO (A VIDA E A CIDADE)": []
    }

    for prop in dados:
        id_p = prop["id_proposicao"]
        c0 = prop["classificacao"]["camada_0_tema_de_incidencia"]
        c1 = prop["classificacao"]["camada_1_operacao_ontologica"]

        # BLOCO III (Patologia) - Prioritário para capturar a crítica
        if any(t in ["Filosofia", "Epistemologia"] for t in c0) or \
           any("Erro categorial" in op or "Crítica" in op for op in c1):
            blocos["BLOCO III - A PATOLOGIA (O DESVIO E A CRÍTICA)"].append(id_p)
        
        # BLOCO I (Fundação)
        elif any(t in ["Ontologia fundamental", "Ciência", "Técnica"] for t in c0):
            blocos["BLOCO I - A FUNDAÇÃO (O REAL EM SI)"].append(id_p)
            
        # BLOCO II (Mediação)
        elif any(t in ["Antropologia", "Consciência", "Linguagem"] for t in c0):
            blocos["BLOCO II - A MEDIAÇÃO (O ANIMAL HUMANO)"].append(id_p)
            
        # BLOCO IV (Reintegração)
        else:
            blocos["BLOCO IV - A REINTEGRAÇÃO (A VIDA E A CIDADE)"].append(id_p)

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        for titulo, ids in blocos.items():
            f.write(f"{titulo}\n")
            f.write("-" * len(titulo) + "\n")
            f.write(f"Total: {len(ids)} proposições\n")
            # Agrupa os IDs em linhas de 10 para facilitar a leitura
            for i in range(0, len(ids), 10):
                f.write(", ".join(ids[i:i+10]) + "\n")
            f.write("\n\n")

    print(f"Guia de leitura gerado: {caminho_saida}")

criar_guia_txt('classificados3_ONTOLOGIA_TOTAL.json', 'GUIA_DE_LEITURA_ONTOLOGICA.txt')