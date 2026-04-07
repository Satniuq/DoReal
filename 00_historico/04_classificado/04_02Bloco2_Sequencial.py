import json

def gerar_manuscrito_bloco2_narrativo(caminho_dados, caminho_saida):
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            proposicoes = json.load(f)
    except FileNotFoundError:
        print(f"Erro: O ficheiro {caminho_dados} não foi encontrado.")
        return

    # Estrutura Narrativa definida para o Bloco II
    # O script filtrará proposições que contenham estes termos na camada_2
    estrutura_narrativa = [
        {
            "titulo": "PARTE 1: A Ancoragem Bio-Ontológica",
            "termos": ["Ser humano", "Corpo e biologia", "Ancoragem corporal", "Emoção", "Memória"]
        },
        {
            "titulo": "PARTE 2: O Despertar da Consciência",
            "termos": ["Consciência reflexiva", "Continuidade da consciência", "Relação eu–real", "Ponto de vista", "Imaginação"]
        },
        {
            "titulo": "PARTE 3: O Fenómeno da Apreensão (O Processador do Real)",
            "termos": ["Apreensão", "Mediação", "Descrição", "Continuidade", "Atualização", "Padrão", "Modo de ser", "Potencialidade", "Escala ontológica"]
        },
        {
            "titulo": "PARTE 4: A Construção do Conhecimento e da Cultura",
            "termos": ["Conhecimento", "Critério", "Avaliação", "Limites do conhecimento", "Comunicação", "Cultura", "Representação"]
        },
        {
            "titulo": "PARTE 5: A Tensão da Liberdade e o Risco do Desvio",
            "termos": ["Liberdade situada", "Poder-ser", "Dignidade", "Adequação", "Bem", "Dever-ser", "Erro ontológico", "Erro categorial", "Degeneração", "Círculos ontológicos"]
        }
    ]

    # Mapeamento para garantir que só pegamos proposições que o teu índice atribuiu ao Bloco II
    # (Baseado na lógica de temas de incidência e ausência de 'erro/crítica' nas operações para evitar o Bloco III)
    mapeamento_bloco2 = ["Antropologia", "Consciência", "Linguagem"]

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("============================================================\n")
        f.write("        BLOCO II - A MEDIAÇÃO (ORGANIZAÇÃO NARRATIVA)       \n")
        f.write("============================================================\n")

        total_bloco = 0

        for parte in estrutura_narrativa:
            f.write(f"\n\n{'#'*65}\n")
            f.write(f" {parte['titulo']}\n")
            f.write(f"{'#'*65}\n")

            for termo in parte['termos']:
                # Filtro: O termo deve estar na camada_2 E a proposição deve pertencer à lógica do Bloco II
                itens_termo = []
                for p in proposicoes:
                    classif = p.get('classificacao', {})
                    temas = classif.get('camada_0_tema_de_incidencia', [])
                    ops = classif.get('camada_1_operacao_ontologica', [])
                    campos = classif.get('camada_2_campos_ontologicos', [])

                    # Lógica de pertença ao Bloco II:
                    is_bloco2 = any(t in mapeamento_bloco2 for t in temas)
                    is_not_patologia = not any("erro" in op.lower() or "crítica" in op.lower() for op in ops)

                    if termo in campos and (is_bloco2 and is_not_patologia):
                        itens_termo.append(p)

                if itens_termo:
                    total_bloco += len(itens_termo)
                    f.write(f"\n--- SEÇÃO: {termo.upper()} ({len(itens_termo)} itens) ---\n")
                    f.write("-" * 40 + "\n")
                    for p in itens_termo:
                        f.write(f"[{p['id_proposicao']}] {p['texto_literal']}\n\n")

        f.write(f"\n\nFIM DO BLOCO II. Total de proposições organizadas: {total_bloco}\n")

    print(f"CONCLUÍDO! Manuscrito do Bloco II gerado em: {caminho_saida}")
    print(f"Total de proposições no ficheiro: {total_bloco}")

# Execução
gerar_manuscrito_bloco2_narrativo('Classificados_Final.json', 'MANUSCRITO_BLOCO_II_NARRATIVO.txt')