import json
from collections import defaultdict, Counter

def extrair_subblocos_principais(caminho_dados, caminho_saida):
    with open(caminho_dados, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # Mapeamento Base para Blocos (C0)
    mapeamento_blocos = {
        "Ontologia fundamental": "BLOCO I - A FUNDAÇÃO", "Ciência": "BLOCO I - A FUNDAÇÃO", "Técnica": "BLOCO I - A FUNDAÇÃO",
        "Antropologia": "BLOCO II - A MEDIAÇÃO", "Consciência": "BLOCO II - A MEDIAÇÃO", "Linguagem": "BLOCO II - A MEDIAÇÃO",
        "Filosofia": "BLOCO III - A PATOLOGIA", "Epistemologia": "BLOCO III - A PATOLOGIA",
        "Ética": "BLOCO IV - A REINTEGRAÇÃO", "Cultura": "BLOCO IV - A REINTEGRAÇÃO", "Política": "BLOCO IV - A REINTEGRAÇÃO"
    }

    # Estrutura: [Bloco][Subbloco] = [IDs]
    hierarquia = defaultdict(lambda: defaultdict(list))

    for prop in dados:
        pid = prop["id_proposicao"]
        temas = prop["classificacao"]["camada_0_tema_de_incidencia"]
        campos = prop["classificacao"].get("camada_2_campos_ontologicos", ["Sem Campo"])
        ops = prop["classificacao"]["camada_1_operacao_ontologica"]

        # Determinar Bloco (Prioridade III para críticas/erros)
        bloco_nome = "BLOCO IV - A REINTEGRAÇÃO"
        if any("erro" in op.lower() or "crítica" in op.lower() for op in ops):
            bloco_nome = "BLOCO III - A PATOLOGIA"
        else:
            for t in temas:
                if t in mapeamento_blocos:
                    bloco_nome = mapeamento_blocos[t]
                    break

        for campo in campos:
            hierarquia[bloco_nome][campo].append(pid)

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("=== GUIA SINTÉTICO DE ESTRUTURA (TOP 5 SUBBLOCOS POR CATEGORIA) ===\n")
        f.write(f"Total de proposições: {len(dados)}\n")
        
        # Ordenação fixa dos Blocos
        ordem_blocos = [
            "BLOCO I - A FUNDAÇÃO", 
            "BLOCO II - A MEDIAÇÃO", 
            "BLOCO III - A PATOLOGIA", 
            "BLOCO IV - A REINTEGRAÇÃO"
        ]

        for bloco in ordem_blocos:
            if bloco not in hierarquia: continue
            
            f.write(f"\n\n{bloco}\n")
            f.write("=" * len(bloco) + "\n")
            
            # Selecionar apenas os 5 subblocos mais vultuosos
            top_subblocos = sorted(hierarquia[bloco].items(), key=lambda x: len(x[1]), reverse=True)[:5]
            
            for subbloco, ids in top_subblocos:
                f.write(f"\n  > SUBBLOCO: {subbloco} ({len(ids)} itens)\n")
                # Escrever IDs em blocos de 12 para scannability
                for i in range(0, len(ids), 12):
                    f.write("    " + ", ".join(ids[i:i+12]) + "\n")
            
            f.write("\n" + "-"*60)

    print(f"Guia sintético gerado: {caminho_saida}")

extrair_subblocos_principais('Classificados_Final.json', 'ESTRUTURA_SINTETICA_SUBBLOCOS.txt')