import json
from collections import defaultdict

def gerar_manuscrito_final_v4(caminho_dados, caminho_saida):
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

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("============================================================\n")
        f.write("     MANUSCRITO TAXONÓMICO (APENAS ID E TEXTO LITERAL)      \n")
        f.write("============================================================\n\n")

        for b in estrutura:
            f.write(f"\n{'='*80}\n {b['bloco']}\n{'='*80}\n")
            for sub in b['subsecoes']:
                f.write(f"\n[SUBSEÇÃO: {sub['titulo'].upper()}]\n")
                
                for termo in sub['termos']:
                    procs = [p for p in proposicoes if termo in p.get('classificacao', {}).get('camada_2_campos_ontologicos', [])]
                    
                    if procs:
                        procs.sort(key=obter_nivel)
                        f.write(f"\n--- CAMPO: {termo} ({len(procs)}) ---\n")
                        for p in procs:
                            # Extração simplificada: apenas ID e Texto
                            f.write(f"ID: {p['id_proposicao']} | {p['texto_literal']}\n")
                            ids_usados.add(p['id_proposicao'])

        # --- SEÇÃO DE SOBRAS ---
        sobras = [p for p in proposicoes if p['id_proposicao'] not in ids_usados]
        if sobras:
            f.write(f"\n\n{'#'*80}\n RESÍDUOS NÃO MAPEADOS\n{'#'*80}\n")
            sobras.sort(key=obter_nivel)
            for p in sobras:
                f.write(f"ID: {p['id_proposicao']} | {p['texto_literal']}\n")

    incorporadas = len(ids_usados)
    fora = len(sobras)
    
    print("\n" + "="*40)
    print(f"RELATÓRIO DE CONSOLIDAÇÃO:")
    print(f"Proposições Incorporadas: {incorporadas}")
    print(f"Proposições Fora (Resíduos): {fora}")
    print(f"TOTAL GERAL: {total_processadas}")
    print("="*40)
    print(f"Ficheiro guardado em: {caminho_saida}")

if __name__ == "__main__":
    gerar_manuscrito_final_v4('Classificados_Final.json', 'MANUSCRITO_SIMPLIFICADO.txt')