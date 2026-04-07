import json
from collections import defaultdict

def extrair_indice_taxonomico(caminho_dados, caminho_saida):
    try:
        # Correção do nome da variável no open
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            proposicoes = json.load(f)
    except FileNotFoundError:
        print(f"Erro: O ficheiro {caminho_dados} não foi encontrado.")
        return
    except Exception as e:
        print(f"Erro ao ler JSON: {e}")
        return

    # Estrutura: Bloco -> Termo C2 -> Lista de IDs
    indice = {
        "I": defaultdict(list),
        "II": defaultdict(list),
        "III": defaultdict(list),
        "IV": defaultdict(list)
    }

    nomes_blocos = {
        "I": "BLOCO I - ONTOLOGIA FUNDAMENTAL (FUNDAÇÃO)",
        "II": "BLOCO II - ANTROPOLOGIA E CONSCIÊNCIA (MEDIAÇÃO)",
        "III": "BLOCO III - PATOLOGIA E CRÍTICA (ERRO)",
        "IV": "BLOCO IV - ÉTICA E DIREITO (REINTEGRAÇÃO)"
    }

    for p in proposicoes:
        c = p.get('classificacao', {})
        ops = str(c.get('camada_1_operacao_ontologica', [])).lower()
        temas = c.get('camada_0_tema_de_incidencia', [])
        
        # Lógica de atribuição de Bloco baseada na tua taxonomia
        if any(kw in ops for kw in ["erro", "crítica", "patologia", "degeneração", "falso"]):
            bl_id = "III"
        elif any(t in temas for t in ["Ética", "Direito", "Política", "Justiça"]):
            bl_id = "IV"
        elif any(t in temas for t in ["Consciência", "Antropologia", "Linguagem", "Cultura"]):
            bl_id = "II"
        else:
            bl_id = "I"

        campos_c2 = c.get('camada_2_campos_ontologicos', [])
        if not campos_c2:
            campos_c2 = ["Sem Classificação C2"]

        for termo in campos_c2:
            indice[bl_id][termo].append(p['id_proposicao'])

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("============================================================\n")
        f.write("          ÍNDICE TAXONÓMICO INTEGRAL (ESTRUTURA C2)         \n")
        f.write(f"          TOTAL DE PROPOSIÇÕES PROCESSADAS: {len(proposicoes)}\n")
        f.write("============================================================\n\n")

        for bl_id in ["I", "II", "III", "IV"]:
            f.write(f"\n{'='*70}\n")
            f.write(f" {nomes_blocos[bl_id]}\n")
            f.write(f"{'='*70}\n")

            # Ordenar termos alfabeticamente para facilitar a localização
            termos_ordenados = sorted(indice[bl_id].keys())
            
            for termo in termos_ordenados:
                ids = indice[bl_id][termo]
                f.write(f"\n[{termo.upper()}] ({len(ids)} proposições)\n")
                
                # Agrupar IDs em linhas de 10 para não criar listas infinitas
                for i in range(0, len(ids), 10):
                    f.write(f"  > {', '.join(ids[i:i+10])}\n")

    print(f"Concluído! Índice gerado em: {caminho_saida}")

# Execução do script
if __name__ == "__main__":
    extrair_indice_taxonomico('Classificados_Final.json', 'INDICE_TAXONOMICO_FINAL.txt')