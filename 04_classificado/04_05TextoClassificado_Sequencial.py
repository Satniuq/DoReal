import json

def gerar_manuscrito_encadeado_detalhado(caminho_dados, caminho_saida):
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            proposicoes = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Ficheiro {caminho_dados} não encontrado.")
        return

    # 1. MAPEAMENTO ESTRUTURAL (4 Blocos / 16 Partes)
    mapeamento_blocos = {
        "I": ["Ontologia fundamental", "Ciência"],
        "II": ["Antropologia", "Consciência", "Linguagem"],
        "IV": ["Ética", "Direito", "Política", "Cultura"]
    }

    partes_definidas = {
        "I": [
            {"titulo": "PARTE 1: O Axioma do Ser", "termos": ["Ser", "Axioma", "Estabilidade", "Atualização", "Potencialidade"]},
            {"titulo": "PARTE 2: Coesão e Ordem", "termos": ["Continuidade", "Relação", "Campo", "Escala ontológica", "Gravidade"]},
            {"titulo": "PARTE 3: Possibilidade", "termos": ["Limites ontológicos", "Impossibilidade ontológica", "Admissibilidade", "Autorreferencialidade"]},
            {"titulo": "PARTE 4: Direção do Real", "termos": ["Bem", "Dever-ser", "Mal"]},
            {"titulo": "PARTE 5: Inteligibilidade", "termos": ["Adequação", "Conhecimento", "Apreensão", "Consciência reflexiva", "Relação eu–real"]}
        ],
        "II": [
            {"titulo": "PARTE 6: Ancoragem Bio-Ontológica", "termos": ["Ser humano", "Corpo e biologia", "Ancoragem corporal", "Emoção", "Memória"]},
            {"titulo": "PARTE 7: Consciência Reflexiva", "termos": ["Consciência reflexiva", "Continuidade da consciência", "Relação eu–real", "Ponto de vista", "Imaginação"]},
            {"titulo": "PARTE 8: Fenómeno da Apreensão", "termos": ["Apreensão", "Mediação", "Descrição", "Continuidade", "Atualização", "Padrão", "Modo de ser"]},
            {"titulo": "PARTE 9: Conhecimento e Cultura", "termos": ["Conhecimento", "Critério", "Avaliação", "Comunicação", "Cultura", "Representação"]}
        ],
        "III": [
            {"titulo": "PARTE 10: Curto-Circuito da Percepção", "termos": ["Apreensão", "Descrição", "Adequação", "Relação eu–real"]},
            {"titulo": "PARTE 11: Anatomia do Engano", "termos": ["Erro ontológico", "Erro categorial", "Escala ontológica", "Erro de escala"]},
            {"titulo": "PARTE 12: Consciência Alienada", "termos": ["Consciência reflexiva", "Círculos ontológicos", "Conhecimento", "Critério"]},
            {"titulo": "PARTE 13: Erosão Sistémica", "termos": ["Atualização", "Degeneração", "Modo de ser", "Dever-ser", "Mal"]}
        ],
        "IV": [
            {"titulo": "PARTE 14: Purgação da Patologia", "termos": ["Erro ontológico", "Erro categorial", "Degeneração", "Limites ontológicos"]},
            {"titulo": "PARTE 15: Método de Re-Ancoragem", "termos": ["Adequação", "Descrição", "Critério", "Apreensão", "Escala ontológica"]},
            {"titulo": "PARTE 16: Vontade Ética e Ordem", "termos": ["Bem", "Dever-ser", "Poder-ser", "Responsabilidade ontológica", "Justiça", "Direito como descrição"]}
        ]
    }

    # 2. SEPARAÇÃO INICIAL
    ids_processados = set()
    organizacao_por_bloco = { "I": [], "II": [], "III": [], "IV": [] }

    for p in proposicoes:
        c = p.get('classificacao', {})
        ops = str(c.get('camada_1_operacao_ontologica', [])).lower()
        temas = c.get('camada_0_tema_de_incidencia', [])
        
        bl_alvo = "IV"
        if any(kw in ops for kw in ["erro", "crítica", "patologia"]):
            bl_alvo = "III"
        else:
            for b_key, b_temas in mapeamento_blocos.items():
                if any(t in temas for t in b_temas):
                    bl_alvo = b_key
                    break
        organizacao_por_bloco[bl_alvo].append(p)

    # 3. ESCRITA FINAL DETALHADA
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("===============================================================================\n")
        f.write("        MANUSCRITO MESTRE: ORDENAÇÃO POR NÍVEL E CLASSIFICAÇÃO TOTAL          \n")
        f.write("===============================================================================\n\n")

        for b_id in ["I", "II", "III", "IV"]:
            f.write(f"\n{'='*80}\n BLOCO {b_id}\n{'='*80}\n")
            
            for parte in partes_definidas[b_id]:
                f.write(f"\n\n# {parte['titulo']}\n")
                f.write(f"{'#' * (len(parte['titulo']) + 2)}\n")

                for termo in parte['termos']:
                    # Filtrar e Ordenar por Nível
                    itens_filtrados = [p for p in organizacao_por_bloco[b_id] if termo in p.get('classificacao', {}).get('camada_2_campos_ontologicos', []) and p['id_proposicao'] not in ids_processados]
                    itens_ordenados = sorted(itens_filtrados, key=lambda x: x.get('grau_de_integracao_ontologica', {}).get('nivel', 0))

                    if itens_ordenados:
                        f.write(f"\n[EIXO: {termo.upper()}]\n")
                        f.write("-" * 40 + "\n")
                        for p in itens_ordenados:
                            classif = p.get('classificacao', {})
                            nivel = p.get('grau_de_integracao_ontologica', {}).get('nivel', 0)
                            
                            f.write(f"ID: {p['id_proposicao']} (NÍVEL {nivel})\n")
                            f.write(f"TEXTO: {p['texto_literal']}\n")
                            f.write(f"SÍNTESE: {p.get('extracao_ontologica', {}).get('explicitação_minima', '---')}\n")
                            f.write(f"CAMADAS: [C0: {', '.join(classif.get('camada_0_tema_de_incidencia', []))}] | ")
                            f.write(f"[C1: {', '.join(classif.get('camada_1_operacao_ontologica', []))}] | ")
                            f.write(f"[C2: {', '.join(classif.get('camada_2_campos_ontologicos', []))}]\n")
                            l3 = classif.get('camada_3_termos_filosoficos_de_contacto', [])
                            if l3: f.write(f"C3 (LÉXICO): {', '.join(l3)}\n")
                            f.write("." * 20 + "\n")
                            ids_processados.add(p['id_proposicao'])

            # EXAUSTIVIDADE
            restante = [p for p in organizacao_por_bloco[b_id] if p['id_proposicao'] not in ids_processados]
            if restante:
                f.write(f"\n# APÊNDICE DE CONSOLIDAÇÃO DO BLOCO {b_id}\n")
                for p in sorted(restante, key=lambda x: x.get('grau_de_integracao_ontologica', {}).get('nivel', 0)):
                    f.write(f"ID: {p['id_proposicao']} (NÍVEL {p.get('grau_de_integracao_ontologica', {}).get('nivel', 0)})\n")
                    f.write(f"TEXTO: {p['texto_literal']}\n---\n")
                    ids_processados.add(p['id_proposicao'])

    print(f"Manuscrito gerado com 1501 proposições detalhadas e ordenadas.")

# Execução
gerar_manuscrito_encadeado_detalhado('Classificados_Final.json', 'MANUSCRITO_REVISAO_NIVEL_FINAL.txt')