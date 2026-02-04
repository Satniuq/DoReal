import json

def gerar_manuscrito_bloco1_narrativo(caminho_dados, caminho_saida):
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            proposicoes = json.load(f)
    except FileNotFoundError: return

    # Definimos a estrutura narrativa baseada no que acordámos
    estrutura_narrativa = [
        {
            "titulo": "PARTE 1: O Axioma do Ser e a Dinâmica Primordial",
            "termos": ["Ser", "Axioma", "Estabilidade", "Atualização", "Potencialidade"]
        },
        {
            "titulo": "PARTE 2: As Leis da Coesão e da Ordem Estrutural",
            "termos": ["Continuidade", "Relação", "Campo", "Escala ontológica", "Gravidade"]
        },
        {
            "titulo": "PARTE 3: O Perímetro da Possibilidade",
            "termos": ["Limites ontológicos", "Impossibilidade ontológica", "Admissibilidade", "Autorreferencialidade"]
        },
        {
            "titulo": "PARTE 4: A Tensão Ética e a Direção do Real",
            "termos": ["Bem", "Dever-ser", "Mal"]
        },
        {
            "titulo": "PARTE 5: A Fronteira da Inteligibilidade e o Prenúncio da Consciência",
            "termos": ["Adequação", "Conhecimento", "Erro ontológico", "Erro categorial", "Apreensão", "Consciência reflexiva", "Relação eu–real", "Continuidade da consciência", "Representação", "Critério"]
        }
    ]

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("============================================================\n")
        f.write("        BLOCO I - A FUNDAÇÃO (ORGANIZAÇÃO NARRATIVA)        \n")
        f.write("============================================================\n")

        for parte in estrutura_narrativa:
            f.write(f"\n\n{'#'*60}\n")
            f.write(f" {parte['titulo']}\n")
            f.write(f"{'#'*60}\n")

            for termo in parte['termos']:
                # Filtramos as proposições que pertencem a este termo dentro do Bloco I
                # (Assumindo a lógica de classificação anterior)
                itens_termo = [p for p in proposicoes if termo in p.get('classificacao', {}).get('camada_2_campos_ontologicos', [])]
                
                # Nota: Aqui podes adicionar um filtro extra para garantir que só entram as do Bloco I
                # Mas como os termos já são específicos da nossa lista do Bloco I, ele vai bater certo.

                if itens_termo:
                    f.write(f"\n--- SEÇÃO: {termo.upper()} ({len(itens_termo)} itens) ---\n")
                    for p in itens_termo:
                        f.write(f"[{p['id_proposicao']}] {p['texto_literal']}\n")

    print(f"Manuscrito do Bloco I gerado com sucesso em: {caminho_saida}")

# Execução
gerar_manuscrito_bloco1_narrativo('Classificados_Final.json', 'MANUSCRITO_BLOCO_I_NARRATIVO.txt')