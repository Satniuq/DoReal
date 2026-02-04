import json

def gerar_manuscrito_bloco4_narrativo(caminho_dados, caminho_saida):
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            proposicoes = json.load(f)
    except FileNotFoundError: return

    estrutura_narrativa = [
        {
            "titulo": "PARTE 1: O Enfrentamento do Escombro (A Purgação da Patologia)",
            "termos": ["Erro ontológico", "Erro categorial", "Erro de escala", "Mal", "Degeneração", "Impossibilidade ontológica", "Limites ontológicos"]
        },
        {
            "titulo": "PARTE 2: O Método de Re-Ancoragem (A Nova Apreensão)",
            "termos": ["Adequação", "Descrição", "Critério", "Regularidade", "Apreensão", "Escala ontológica", "Relação eu–real", "Consciência reflexiva"]
        },
        {
            "titulo": "PARTE 3: A Vontade e o Dever (O Motor da Mudança)",
            "termos": ["Bem", "Dever-ser", "Poder-ser", "Liberdade situada", "Responsabilidade ontológica", "Dignidade"]
        },
        {
            "titulo": "PARTE 4: A Estabilização do Sistema (A Ordem Social)",
            "termos": ["Continuidade", "Atualização", "Modo de ser", "Estabilidade", "Comunicação", "Mediação", "Relação", "Coordenação", "Estabilização sistémica"]
        },
        {
            "titulo": "PARTE 5: A Institucionalização do Real (Direito e Futuro)",
            "termos": ["Direito como descrição", "Justiça", "Caso concreto", "Dominância", "Aprendizagem", "Education ontológica", "Cultura", "Abertura do real"]
        }
    ]

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("============================================================\n")
        f.write("        BLOCO IV - A REINTEGRAÇÃO (ORGANIZAÇÃO NARRATIVA)   \n")
        f.write("============================================================\n")

        for parte in estrutura_narrativa:
            f.write(f"\n\n{'#'*65}\n")
            f.write(f" {parte['titulo']}\n")
            f.write(f"{'#'*65}\n")

            for termo in parte['termos']:
                # Filtro para Bloco IV: Temas como Ética, Direito, Política, Cultura
                itens_termo = [p for p in proposicoes if termo in p.get('classificacao', {}).get('camada_2_campos_ontologicos', []) 
                              and any(t in str(p.get('classificacao', {}).get('camada_0_tema_de_incidencia', [])) 
                              for t in ["Ética", "Direito", "Política", "Cultura"])]
                
                if itens_termo:
                    f.write(f"\n--- SEÇÃO: {termo.upper()} ({len(itens_termo)} itens) ---\n")
                    for p in itens_termo:
                        f.write(f"[{p['id_proposicao']}] {p['texto_literal']}\n\n")

    print(f"Manuscrito do Bloco IV gerado em: {caminho_saida}")

gerar_manuscrito_bloco4_narrativo('Classificados_Final.json', 'MANUSCRITO_BLOCO_IV_NARRATIVO.txt')