import pyperclip
import os
import winsound
import ctypes
import re

# Configurações de ficheiros
STATE_FILE = "estado.txt"
# Usa o caminho que forneceste
DATA_FILE = r"C:\Users\vanes\DoReal_Casa_Local\DoReal\05_verdades\01_01_Extrai_verdades.txt"

# 1. Carregar ou inicializar o índice de progresso
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            index = int(f.read().strip())
        except ValueError:
            index = 0
else:
    index = 0

# 2. Carregar e processar o ficheiro de texto
fragmentos_validos = []

if not os.path.exists(DATA_FILE):
    print(f"⚠️ Erro: Ficheiro não encontrado em: {DATA_FILE}")
    exit()

with open(DATA_FILE, "r", encoding="utf-8") as f:
    for linha in f:
        # Procura o padrão "ID: P0000 | Texto..."
        match = re.search(r"ID:\s*(P\d+)\s*\|\s*(.*)", linha)
        if match:
            fid = match.group(1)
            text = match.group(2).strip()
            fragmentos_validos.append((fid, text))

# 3. Verificar se ainda há fragmentos para processar
if index >= len(fragmentos_validos):
    print("⚠️ Chegaste ao fim dos fragmentos disponíveis.")
    # Opcional: fazer reset ao índice se quiseres recomeçar
    # with open(STATE_FILE, "w") as f: f.write("0")
    exit()

fid, text = fragmentos_validos[index]

# 4. Copiar para o clipboard
# Formatei para incluir o ID na cópia, facilita a tua organização ao extrair a verdade
conteudo_para_copiar = f"Fragmento {fid}:\n{text}"
pyperclip.copy(conteudo_para_copiar)

# 5. Guardar o novo estado (próximo índice)
with open(STATE_FILE, "w", encoding="utf-8") as f:
    f.write(str(index + 1))

# 6. Notificações
winsound.MessageBeep()
ctypes.windll.user32.MessageBoxW(
    0, 
    f"Copiado ID: {fid}\n\nRestam: {len(fragmentos_validos) - (index + 1)}", 
    "Extrai Verdades", 
    0
)

print(f"✅ Sucesso: {fid} copiado para a área de transferência.")