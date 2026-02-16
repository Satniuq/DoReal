from google import genai
import json
import time
import re

# ==========================================
# CONFIGURAÇÃO (Nomes corrigidos para 2026)
# ==========================================
API_KEY = "AIzaSyAmvLHhjYwbcAtGZshMEUaJsBAMgowQopM"
FICHEIRO_REGRAS = "02_01_prompt.txt"
FICHEIRO_MANUSCRITO = "06_01Texto_No_Indice_TXT.txt"
FICHEIRO_SAIDA = "teste_5_fragmentos.json"

# Usamos o 2.5 Flash que apareceu no teu diagnóstico
MODELO = "gemini-2.5-flash" 

client = genai.Client(api_key=API_KEY)

def limpar_json(texto):
    """Remove blocos de código markdown da resposta."""
    texto_limpo = re.sub(r'```json\s*|```', '', texto)
    return texto_limpo.strip()

def processar():
    print("--- A Iniciar Extração Ontológica (Modo Teste) ---")
    
    try:
        with open(FICHEIRO_REGRAS, "r", encoding="utf-8") as f:
            regras_mestre = f.read()
        with open(FICHEIRO_MANUSCRITO, "r", encoding="utf-8") as f:
            conteudo = f.read()
    except Exception as e:
        print(f"Erro ao ler ficheiros: {e}")
        return

    # Split e limpeza: remove fragmentos muito curtos ou vazios
    fragmentos = [f.strip() for f in conteudo.split('----------') if len(f.strip()) > 30]
    
    # Seleciona apenas os primeiros 5 para o teste
    fragmentos_para_teste = fragmentos[:5]
    print(f"Encontrados {len(fragmentos)} fragmentos. A processar os primeiros {len(fragmentos_para_teste)}.")

    resultados_finais = []

    for i, texto_frag in enumerate(fragmentos_para_teste):
        print(f"[{i+1}/5] A analisar fragmento...")

        # Montamos o prompt injetando as regras e o fragmento
        prompt_final = f"""
{regras_mestre}

---
CONTEXTO DE EXECUÇÃO:
Aplica o método acima ao fragmento abaixo. 
Responde APENAS com o objeto JSON.

FRAGMENTO:
{texto_frag}
"""

        try:
            # Chamada à API com o modelo 2.5
            response = client.models.generate_content(
                model=MODELO,
                contents=prompt_final
            )
            
            if response.text:
                json_puro = limpar_json(response.text)
                ficha = json.loads(json_puro)
                resultados_finais.append(ficha)
                
                # Grava a cada passo para segurança
                with open(FICHEIRO_SAIDA, "w", encoding="utf-8") as f_out:
                    json.dump(resultados_finais, f_out, ensure_ascii=False, indent=2)
            
            # Pausa de 1 segundo (o 2.5 Flash é muito rápido)
            time.sleep(1)

        except Exception as e:
            print(f"Erro no fragmento {i+1}: {e}")
            continue

    print(f"\nSucesso! O ficheiro '{FICHEIRO_SAIDA}' foi criado com as 5 extrações.")

if __name__ == "__main__":
    processar()