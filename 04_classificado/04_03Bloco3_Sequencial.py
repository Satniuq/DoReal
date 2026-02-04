import json

def gerar_manuscrito_bloco3_narrativo(caminho_dados, caminho_saida):
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            proposicoes = json.load(f)
    except FileNotFoundError: return

    estrutura_narrativa = [
        {
            "titulo": "PARTE 1: A Falha na Fonte (O Curto-Circuito da Percepção)",
            "termos": ["Apreensão", "Descrição", "Regularidade", "Campo", "Adequação", "Relação eu–real", "Proposição"]
        },
        {
            "titulo": "PARTE 2: A Anatomia do Engano (A Mecânica do Erro)",
            "termos": ["Erro ontológico", "Erro categorial", "Escala ontológica", "Erro de escala", "Limites ontológicos", "Impossibilidade ontológica"]
        },
        {
            "titulo": "PARTE 3: A Patologia da Consciência (O Sujeito Alienado)",
            "termos": ["Consciência reflexiva", "Continuidade da consciência", "Círculos ontológicos", "Círculo", "Conhecimento", "Limites do conhecimento", "Critério"]
        },
        {
            "titulo": "PARTE 4: A Erosão do Sistema (A Degeneração em Curso)",
            "termos": ["Atualização", "Continuidade", "Processo", "Contingência", "Degeneração", "Modo de ser", "Mediação", "Corpo e biologia"]
        },
        {
            "titulo": "PARTE 5: A Crise do Valor e o Grito pela Cura",
            "termos": ["Bem", "Dever-ser", "Poder-ser", "Mal", "Comunicação", "Relação", "Liberdade situada"]
        }
    ]

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("============================================================\n")
        f.write("        BLOCO III - A PATOLOGIA (ORGANIZAÇÃO NARRATIVA)     \n")
        f.write("============================================================\n")

        for parte in estrutura_narrativa:
            f.write(f"\n\n{'#'*65}\n")
            f.write(f" {parte['titulo']}\n")
            f.write(f"{'#'*65}\n")

            for termo in parte['termos']:
                # Filtro específico para o Bloco III (onde a operação é crítica/erro)
                itens_termo = [p for p in proposicoes if termo in p.get('classificacao', {}).get('camada_2_campos_ontologicos', []) 
                              and any(op in str(p.get('classificacao', {}).get('camada_1_operacao_ontologica', [])).lower() 
                              for op in ["erro", "crítica", "patologia"])]
                
                if itens_termo:
                    f.write(f"\n--- SEÇÃO: {termo.upper()} ({len(itens_termo)} itens) ---\n")
                    for p in itens_termo:
                        f.write(f"[{p['id_proposicao']}] {p['texto_literal']}\n\n")

    print(f"Manuscrito do Bloco III gerado em: {caminho_saida}")

gerar_manuscrito_bloco3_narrativo('Classificados_Final.json', 'MANUSCRITO_BLOCO_III_NARRATIVO.txt')