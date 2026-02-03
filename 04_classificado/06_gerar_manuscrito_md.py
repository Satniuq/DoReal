import json

def gerar_manuscrito_markdown(caminho_json, caminho_md):
    with open(caminho_json, 'r', encoding='utf-8') as f:
        dados_lista = json.load(f)
        # Criar dicionário para acesso rápido por ID
        dados = {p["id_proposicao"]: p for p in dados_lista}

    blocos = [
        ("BLOCO I - A FUNDAÇÃO (O REAL EM SI)", ["Ontologia fundamental", "Ciência", "Técnica"]),
        ("BLOCO II - A MEDIAÇÃO (O ANIMAL HUMANO)", ["Antropologia", "Consciência", "Linguagem"]),
        ("BLOCO III - A PATOLOGIA (O DESVIO E A CRÍTICA)", ["Filosofia", "Epistemologia"]),
        ("BLOCO IV - A REINTEGRAÇÃO (A VIDA E A CIDADE)", ["Ética", "Política", "Direito", "Economia", "Cultura"])
    ]

    ids_processados = set()

    with open(caminho_md, 'w', encoding='utf-8') as f:
        f.write("# O SER NO REAL: TRATADO DE ONTOLOGIA APLICADA\n")
        f.write(f"**Total de Proposições:** {len(dados)}\n\n---\n\n")

        for titulo, temas in blocos:
            f.write(f"## {titulo}\n\n")
            
            # Ordenar IDs para garantir a sequência P0001, P0002...
            for id_p in sorted(dados.keys()):
                if id_p in ids_processados: continue
                
                prop = dados[id_p]
                classif = prop.get("classificacao", {})
                c0 = classif.get("camada_0_tema_de_incidencia", [])
                c1 = classif.get("camada_1_operacao_ontologica", [])
                
                # Lógica de atribuição ao bloco
                atribuir = False
                if titulo == "BLOCO III - A PATOLOGIA (O DESVIO E A CRÍTICA)":
                    if any(t in temas for t in c0) or any("Erro" in op or "Crítica" in op for op in c1):
                        atribuir = True
                elif any(t in temas for t in c0):
                    atribuir = True
                elif titulo == "BLOCO IV - A REINTEGRAÇÃO (A VIDA E A CIDADE)":
                    atribuir = True

                if atribuir:
                    f.write(f"### {id_p}\n")
                    
                    # Chave correta: texto_literal
                    texto = prop.get('texto_literal', "Texto não encontrado")
                    f.write(f"> **{texto}**\n\n")
                    
                    # Adicionar a explicitação para ajudar no sentido da leitura
                    extracao = prop.get("extracao_ontologica", {})
                    expl_min = extracao.get("explicitação_minima", "")
                    if expl_min:
                        f.write(f"**Essência:** {expl_min}\n\n")
                    
                    f.write(f"* **Domínios:** {', '.join(c0)}\n")
                    f.write(f"* **Operação:** {', '.join(c1)}\n")
                    f.write(f"* **Campos:** {', '.join(classif.get('camada_2_campos_ontologicos', []))}\n")
                    
                    f.write("\n---\n\n")
                    ids_processados.add(id_p)

    print(f"Manuscrito gerado com sucesso: {caminho_md}")

# Execução
gerar_manuscrito_markdown('classificados3_ONTOLOGIA_TOTAL.json', 'MANUSCRITO_DO_REAL.md')