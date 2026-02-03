import json

# 1. DEFINIÇÃO DAS REGRAS (LISTA OFICIAL)
REGRAS = {
    "camada_0": [
        "Ontologia fundamental", "Epistemologia", "Consciência", "Antropologia", 
        "Ética", "Política", "Direito", "Cultura", "Religião", "Educação", 
        "Linguagem", "Ciência", "Técnica", "Economia", "História", "Filosofia"
    ],
    "camada_1": [
        "Núcleo ontológico", "Afirmação ontológica primária", "Proposição ontológica básica",
        "Pressuposto ontológico implícito", "Identificação de condição ontológica",
        "Fixação de limite ontológico", "Exclusão ontológica", "Rejeição de exterioridade ontológica",
        "Clarificação", "Limpeza conceptual", "Desambiguação conceptual", "Distinção ontológica",
        "Dissolução de dicotomia falsa", "Correção de falso problema", "Redução de entidade ilegítima",
        "Redução de mistificação", "Dessubstancialização", "Descrição", "Descrição do real",
        "Descrição de mecanismo real", "Descrição de continuidade / atualização",
        "Descrição de regularidade", "Continuidade funcional", "Naturalização ontológica",
        "Ancoragem corporal", "Relação", "Relação estrutural", "Recondução relacional",
        "Integração local", "Ramificação ontológica", "Reinscrição estrutural",
        "Reinscrição do eu no real", "Reinscrição da consciência na relação",
        "Deslocamento de escala ontológica", "Diferenciação entre níveis de operação",
        "Deslocamento do ponto de vista", "Ampliação reflexiva do campo ontológico",
        "Identificação de mediação necessária", "Distinção apreensão / pensamento",
        "Limitação da reflexividade", "Crítica", "Crítica a discurso existente",
        "Identificação de erro categorial", "Identificação do erro como falha de descrição",
        "Fixação do erro como erro categorial", "Dissolução da coerência interna como critério",
        "Exclusão de critérios não-reais", "Identificação da verdade como critério ontológico",
        "Recondução da verdade à descrição", "Fixação do critério exterior ao eu",
        "Diferenciação entre verdade local e verdade do real", "Limitação estrutural do conhecimento",
        "Validação ontológica da ciência", "Derivação do valor a partir do ser",
        "Recondução da ética à ontologia", "Identificação do bem como adequação ao real",
        "Recondução do mal à inadequação", "Subordinação do dever-ser ao poder-ser",
        "Recondução da ação ética à relação", "Identificação do humano como animal real",
        "Recondução da consciência ao corpo", "Inscrição biológica dos modos de ser",
        "Identificação da emoção como primazia adaptativa", "Recondução da liberdade ao campo de possibilidades reais",
        "Identificação de dois modos fundamentais de ser", "Identificação da substituição do real por sistemas",
        "Identificação da transmissibilidade como condition ontológica", "Recondução da cultura à continuidade simbólica",
        "Identificação da crítica como apreensão relacional", "Recondução da filosofia à ontologia aplicada"
    ],
    "camada_2": [
        "Ser", "Não-ser", "Continuidade", "Potencialidade", "Atualização", "Impossibilidade ontológica",
        "Limites ontológicos", "Consciência reflexiva", "Apreensão", "Representação", "Mediação",
        "Ponto de vista", "Relação eu–real", "Continuidade da consciência", "Verdade como descrição",
        "Adequação", "Critério", "Validade", "Conhecimento", "Limites do conhecimento",
        "Erro ontológico", "Erro categorial", "Ética derivada do ser", "Bem", "Mal", "Dever-ser",
        "Poder-ser", "Liberdade situada", "Responsabilidade ontológica", "Ser humano", "Corpo e biologia",
        "Emoção", "Imaginação", "Memória", "Modo de ser", "Padrão", "Escala ontológica",
        "Círculos ontológicos", "Sistema", "Sistema simbólico", "Comunicação", "Estabilização sistémica",
        "Degeneração", "Cultura", "Transmissão do real", "Educação ontológica", "Política",
        "Direito como descrição", "Justiça", "Erro de escala"
    ]
}

def analisar_json(caminho_ficheiro):
    with open(caminho_ficheiro, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    encontrados = {
        "camada_0_tema_de_incidencia": set(),
        "camada_1_operacao_ontologica": set(),
        "camada_2_campos_ontologicos": set()
    }

    # Percorrer todas as proposições
    for prop in dados:
        classif = prop.get("classificacao", {})
        for camada in encontrados.keys():
            termos = classif.get(camada, [])
            for t in termos:
                encontrados[camada].add(t)

    # Comparação
    print("=== RELATÓRIO DE CONSISTÊNCIA ONTOLÓGICA ===\n")
    
    mapeamento = {
        "camada_0_tema_de_incidencia": ("camada_0", "CAMADA 0 (TEMAS)"),
        "camada_1_operacao_ontologica": ("camada_1", "CAMADA 1 (OPERAÇÕES)"),
        "camada_2_campos_ontologicos": ("camada_2", "CAMADA 2 (CAMPOS)")
    }

    for chave_json, (chave_regra, nome_exibicao) in mapeamento.items():
        fora_da_regra = encontrados[chave_json] - set(REGRAS[chave_regra])
        
        print(f"--- {nome_exibicao} ---")
        print(f"Total de termos únicos no ficheiro: {len(encontrados[chave_json])}")
        
        if fora_da_regra:
            print(f"AVISO: Foram encontrados {len(fora_da_regra)} termos fora das regras:")
            for termo in sorted(fora_da_regra):
                print(f"  [!] '{termo}'")
        else:
            print("✓ Todos os termos estão em conformidade.")
        print("\n")

# Execução (ajusta o nome do ficheiro se necessário)
analisar_json('classificados3.json')