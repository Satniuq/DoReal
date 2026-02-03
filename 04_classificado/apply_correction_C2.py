import json

def limpar_sistema_integral(caminho_entrada, caminho_saida):
    with open(caminho_entrada, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # --- DICIONÁRIOS DE MAPEAMENTO (A "GRAVIDADE") ---

    mapa_c0 = {
        "Verdade": "Epistemologia",
        "Sistemas": "Cultura",
        "Conhecimento": "Epistemologia",
        "Comunicação": "Linguagem",
        "Sociologia": "Cultura",
        "Escala": "Ontologia fundamental"
    }

    mapa_c1 = {
        "Exclusão de exterioridade ontológica": "Rejeição de exterioridade ontológica",
        "Descrição de pressuposto implícito": "Pressuposto ontológico implícito",
        "Descrição funcional": "Continuidade funcional",
        "Identificação de regularidade": "Descrição de regularidade",
        "Identificação de erro como falha de descrição": "Identificação do erro como falha de descrição",
        "Identificação de relação estrutural": "Relação estrutural",
        "Identificação de limite ontológico": "Fixação de limite ontológico",
        "Dissolução de confusão conceptual": "Desambiguação conceptual",
        "Dissolução de falso problema": "Correção de falso problema",
        "Recondução do direito à descrição": "Recondução da filosofia à ontologia aplicada",
        "Subordinação da ação a critério ontológico": "Subordinação do dever-ser ao poder-ser"
    }

    mapa_c2 = {
        # Poder-ser
        "Ação": "Poder-ser", "Campo de ação": "Poder-ser", "Campo de possibilidades": "Poder-ser", 
        "Possibilidade": "Poder-ser", "Atividade mental": "Consciência reflexiva",
        # Limites e Estrutura
        "Causa": "Limites ontológicos", "Causalidade": "Limites ontológicos", 
        "Condição": "Limites ontológicos", "Condições ontológicas": "Limites ontológicos",
        "Necessidade ontológica": "Limites ontológicos", "Estratificação do real": "Escala ontológica",
        "Exterioridade ontológica": "Escala ontológica", "Estrutura do real": "Ser",
        # Ser e Manifestação
        "Descrição do real": "Ser", "Manifestação": "Ser", "Real": "Ser", "Totalidade": "Ser",
        # Sujeito
        "Consciência": "Consciência reflexiva", "Ser consciente reflexivo": "Consciência reflexiva",
        # Erro
        "Erro de critério": "Erro categorial", "Relativismo": "Erro categorial", 
        "Fundamentação ilegítima": "Erro categorial", "Mal (como desadequação)": "Mal",
        # Biologia (Nível 2)
        "Energia": "Corpo e biologia", "Energia adaptativa": "Corpo e biologia", 
        "Auto-preservação": "Corpo e biologia", "Adaptação": "Corpo e biologia"
    }

    # Termos da C2 que decidimos oficializar (não são alterados se já existirem)
    c2_novos_oficiais = ["Tempo", "Processo", "Instituições", "Linguagem"]

    for prop in dados:
        classif = prop.get("classificacao", {})
        
        # --- Limpeza Camada 0 ---
        c0_original = classif.get("camada_0_tema_de_incidencia", [])
        classif["camada_0_tema_de_incidencia"] = list(set([mapa_c0.get(t, t) for t in c0_original]))

        # --- Limpeza Camada 1 ---
        c1_original = classif.get("camada_1_operacao_ontologica", [])
        classif["camada_1_operacao_ontologica"] = list(set([mapa_c1.get(t, t) for t in c1_original]))

        # --- Limpeza Camada 2 ---
        c2_original = classif.get("camada_2_campos_ontologicos", [])
        nova_c2 = []
        for t in c2_original:
            termo_limpo = mapa_c2.get(t, t)
            if termo_limpo not in nova_c2:
                nova_c2.append(termo_limpo)
        classif["camada_2_campos_ontologicos"] = nova_c2

    # Guardar Resultado
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"Limpeza Integral Concluída. Ficheiro gerado: {caminho_saida}")

# Executar
limpar_sistema_integral('classificados3_limpo_C1.json', 'classificados3_FINAL_ESTRUTURADO.json')