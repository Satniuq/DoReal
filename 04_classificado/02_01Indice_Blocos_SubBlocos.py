import json
from collections import defaultdict

def gerar_indice_estrutural(caminho_dados, caminho_saida):
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            lista_proposicoes = json.load(f)
    except FileNotFoundError:
        print(f"Erro: O ficheiro {caminho_dados} não foi encontrado.")
        return

    mapeamento_blocos = {
        "Ontologia fundamental": "BLOCO I - A FUNDAÇÃO", "Ciência": "BLOCO I - A FUNDAÇÃO", 
        "Antropologia": "BLOCO II - A MEDIAÇÃO", "Consciência": "BLOCO II - A MEDIAÇÃO", "Linguagem": "BLOCO II - A MEDIAÇÃO",
        "Filosofia": "BLOCO III - A PATOLOGIA", "Epistemologia": "BLOCO III - A PATOLOGIA",
        "Ética": "BLOCO IV - A REINTEGRAÇÃO", "Cultura": "BLOCO IV - A REINTEGRAÇÃO", 
        "Direito": "BLOCO IV - A REINTEGRAÇÃO", "Política": "BLOCO IV - A REINTEGRAÇÃO"
    }

    # Estrutura: indice[bloco][subbloco] = contador
    indice = defaultdict(lambda: defaultdict(int))
    total_geral = 0

    for prop in lista_proposicoes:
        total_geral += 1
        classif = prop.get("classificacao", {})
        temas = classif.get("camada_0_tema_de_incidencia", [])
        ops = classif.get("camada_1_operacao_ontologica", [])
        campos = classif.get("camada_2_campos_ontologicos", ["Geral"])

        # Lógica de Bloco
        bloco_nome = "BLOCO IV - A REINTEGRAÇÃO"
        if any("erro" in op.lower() or "crítica" in op.lower() for op in ops):
            bloco_nome = "BLOCO III - A PATOLOGIA"
        else:
            for t in temas:
                if t in mapeamento_blocos:
                    bloco_nome = mapeamento_blocos[t]
                    break

        # Contabilizar no subbloco (usa o primeiro campo da lista)
        subbloco = campos[0] if campos else "Geral"
        indice[bloco_nome][subbloco] += 1

    # Escrita do Índice
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("============================================================\n")
        f.write("           ÍNDICE ESTRUTURAL DA OBRA (SUMÁRIO)              \n")
        f.write(f"           TOTAL DE PROPOSIÇÕES MAPEADAS: {total_geral}      \n")
        f.write("============================================================\n")

        ordem_blocos = ["BLOCO I - A FUNDAÇÃO", "BLOCO II - A MEDIAÇÃO", "BLOCO III - A PATOLOGIA", "BLOCO IV - A REINTEGRAÇÃO"]
        
        for bloco in ordem_blocos:
            if bloco not in indice: continue
            
            f.write(f"\n{bloco}\n")
            f.write("=" * len(bloco) + "\n")
            
            # Ordenar subblocos por ordem alfabética ou por volume (escolhi volume aqui)
            subs_ordenados = sorted(indice[bloco].items(), key=lambda x: x[1], reverse=True)
            
            for subbloco, qtd in subs_ordenados:
                pontos = "." * (40 - len(subbloco))
                f.write(f"  > {subbloco} {pontos} {qtd} proposições\n")
            
            total_bloco = sum(indice[bloco].values())
            f.write(f"  TOTAL DO BLOCO: {total_bloco}\n")

    print(f"Índice gerado com sucesso em: {caminho_saida}")

# Execução
gerar_indice_estrutural('Classificados_Final.json', 'INDICE_DA_OBRA.txt')