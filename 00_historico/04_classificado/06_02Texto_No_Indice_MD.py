import json
from collections import defaultdict

def gerar_manuscrito_final_md(caminho_dados, caminho_saida):
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            proposicoes = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar ficheiro: {e}")
        return

    # --- ESTRUTURA NARRATIVA ---
    estrutura = [
        {"bloco": "BLOCO I — ONTOLOGIA FUNDAMENTAL", "subsecoes": [
            {"titulo": "1.1 Os Axiomas do Campo", "termos": ["Axioma", "Ser", "Campo", "Espaço", "Não-ser", "Factualidade"]},
            {"titulo": "1.2 A Dinâmica da Existência", "termos": ["Atualização", "Potencialidade", "Poder-ser", "Movimento", "Tempo"]},
            {"titulo": "1.3 A Coesão do Real", "termos": ["Continuidade", "Relação", "Contínuo", "Gravidade", "Estabilidade"]},
            {"titulo": "1.4 Ordem e Escala", "termos": ["Escala ontológica", "Regularidade", "Padrão", "Limites ontológicos", "Admissibilidade"]}
        ]},
        {"bloco": "BLOCO II — MEDIAÇÃO", "subsecoes": [
            {"titulo": "2.1 A Ancoragem do Ente", "termos": ["Ser humano", "Corpo e biologia", "Ancoragem corporal", "Emoção", "Memória"]},
            {"titulo": "2.2 A Apreensão", "termos": ["Apreensão", "Consciência reflexiva", "Continuidade da consciência", "Ponto de vista", "Perspectiva"]},
            {"titulo": "2.3 Tradução e Cultura", "termos": ["Linguagem", "Representação", "Símbolo", "Significação", "Cultura", "Comunicação"]}
        ]},
        {"bloco": "BLOCO III — PATOLOGIA", "subsecoes": [
            {"titulo": "3.1 A Anatomia do Erro", "termos": ["Erro ontológico", "Erro categorial", "Erro de escala", "Mal", "Degeneração"]},
            {"titulo": "3.2 O Fechamento", "termos": ["Autorreferencialidade", "Eu-eu", "Círculos ontológicos", "Coerência", "Validade"]},
            {"titulo": "3.3 O Processo", "termos": ["Sistema", "Processo", "Norma", "Normatividade"]}
        ]},
        {"bloco": "BLOCO IV — REINTEGRAÇÃO", "subsecoes": [
            {"titulo": "4.1 A Adequação", "termos": ["Adequação", "Bem", "Responsabilidade ontológica", "Sabedoria"]},
            {"titulo": "4.2 O Dever-Ser", "termos": ["Dever-ser", "Valor", "Direção ontológica", "Direcionalidade"]},
            {"titulo": "4.3 O Direito", "termos": ["Direito como descrição", "Justiça", "Caso concreto", "Dignidade", "Liberdade situada"]}
        ]}
    ]

    ids_usados = set()
    total_processadas = len(proposicoes)

    def obter_nivel(p):
        grau = p.get('grau_de_integracao_ontologica', {})
        return grau.get('nivel', 0)

    # Garantir que a extensão seja .md
    if not caminho_saida.endswith('.md'):
        caminho_saida = caminho_saida.rsplit('.', 1)[0] + '.md'

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        # Cabeçalho Principal em Markdown
        f.write("# MANUSCRITO TAXONÓMICO FINAL\n")
        f.write("> **Ordenação:** Por Nível de Integração Ontológica\n\n")
        f.write("---\n\n")

        for b in estrutura:
            f.write(f"## {b['bloco']}\n\n")
            
            for sub in b['subsecoes']:
                f.write(f"### {sub['titulo']}\n\n")
                
                for termo in sub['termos']:
                    procs = [p for p in proposicoes if termo in p.get('classificacao', {}).get('camada_2_campos_ontologicos', [])]
                    
                    if procs:
                        procs.sort(key=obter_nivel)
                        f.write(f"#### 🏷️ Campo: {termo} ({len(procs)})\n\n")
                        
                        for p in procs:
                            c = p.get('classificacao', {})
                            nivel = obter_nivel(p)
                            exp = p.get('extracao_ontologica', {}).get('explicitação_minima', '---')
                            
                            # Uso de negrito e blocos de citação para destacar o conteúdo
                            f.write(f"- **[{nivel if nivel != 0 else 'N/A'}] ID: {p['id_proposicao']}** | {p['texto_literal']}\n")
                            f.write(f"  - **EXP:** {exp}\n")
                            f.write(f"  - `TAX` C0: {c.get('camada_0_tema_de_incidencia', [])} | C2: {c.get('camada_2_campos_ontologicos', [])}\n\n")
                            
                            ids_usados.add(p['id_proposicao'])
                f.write("---\n\n") # Separador de subseção

        # --- SEÇÃO DE SOBRAS (RESÍDUOS) ---
        sobras = [p for p in proposicoes if p['id_proposicao'] not in ids_usados]
        if sobras:
            f.write(f"# 🛠️ RESÍDUOS NÃO MAPEADOS (AUDITORIA)\n\n")
            sobras.sort(key=obter_nivel)
            for p in sobras:
                c = p.get('classificacao', {})
                nivel = obter_nivel(p)
                exp = p.get('extracao_ontologica', {}).get('explicitação_minima', '---')
                
                f.write(f"- **[{nivel if nivel != 0 else 'N/A'}] ID: {p['id_proposicao']}** | {p['texto_literal']}\n")
                f.write(f"  - **EXP:** {exp}\n")
                f.write(f"  - `TAX` C0: {c.get('camada_0_tema_de_incidencia', [])} | C2: {c.get('camada_2_campos_ontologicos', [])}\n\n")

    # --- PRINT FINAL DE CONTABILIDADE ---
    incorporadas = len(ids_usados)
    fora = len(sobras)
    
    print("\n" + "="*40)
    print(f"RELATÓRIO DE CONSOLIDAÇÃO (MARKDOWN):")
    print(f"Proposições Incorporadas: {incorporadas}")
    print(f"Proposições Fora (Resíduos): {fora}")
    print(f"TOTAL GERAL: {total_processadas}")
    print("="*40)
    print(f"Ficheiro guardado em: {caminho_saida}")

if __name__ == "__main__":
    # Nome do ficheiro alterado para .md
    gerar_manuscrito_final_md('Classificados_Final.json', 'MANUSCRITO_REVISADO_V4.md')