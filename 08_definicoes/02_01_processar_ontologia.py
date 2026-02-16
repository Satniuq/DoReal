import google.generativeai as genai
import json
import time
import re

# ==========================================
# CONFIGURAÇÃO
# ==========================================
API_KEY = "AIzaSyAmvLHhjYwbcAtGZshMEUaJsBAMgowQopM"
FICHEIRO_REGRAS = "02_01_prompt.txt"
FICHEIRO_MANUSCRITO = "06_01Texto_No_Indice_TXT.txt"
FICHEIRO_SAIDA = "extrações_ontologicas_final.json"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

def limpar_json(texto):
    """Remove blocos de código markdown caso a IA os inclua."""
    texto_limpo = re.sub(r'```json\s*|```', '', texto)
    return texto_limpo.strip()

def processar():
    # 1. Ler as Regras Mestre (O teu Prompt)
    print("A ler regras e definições...")
    with open(FICHEIRO_REGRAS, "r", encoding="utf-8") as f:
        regras_mestre = f.read()

    # 2. Ler o Manuscrito
    print("A ler manuscrito...")
    with open(FICHEIRO_MANUSCRITO, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # 3. Dividir por fragmentos usando o teu delimitador '----------'
    fragmentos = conteudo.split('----------')
    print(f"Encontrados {len(fragmentos)} fragmentos para processar.")

    resultados_finais = []

    for i, frag in enumerate(fragmentos):
        texto_frag = frag.strip()
        if not texto_frag or len(texto_frag) < 20: # Ignora blocos vazios ou cabeçalhos
            continue

        print(f"[{i+1}/{len(fragmentos)}] A processar fragmento...")

        prompt_final = f"""
{regras_mestre}

---
CONTEXTO DE EXECUÇÃO:
Aplica o método acima estritamente ao fragmento abaixo.
Responde APENAS com o objeto JSON, sem texto adicional.

FRAGMENTO:
{texto_frag}
"""

        try:
            # Chamada à API
            response = model.generate_content(prompt_final)
            
            # Tratar a resposta
            json_puro = limpar_json(response.text)
            ficha_extração = json.loads(json_puro)
            
            resultados_finais.append(ficha_extração)
            
            # Guardar progresso imediato (backup)
            with open(FICHEIRO_SAIDA, "w", encoding="utf-8") as f_out:
                json.dump(resultados_finais, f_out, ensure_ascii=False, indent=2)

            # Pausa curta para evitar limites da API gratuita
            time.sleep(2)

        except Exception as e:
            print(f"Erro no fragmento {i+1}: {e}")
            continue

    print(f"\nConcluído! O ficheiro '{FICHEIRO_SAIDA}' foi populado com sucesso.")

if __name__ == "__main__":
    processar()