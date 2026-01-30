import json
import pyperclip
import os
import winsound
import ctypes


STATE_FILE = "estado.txt"
DATA_FILE = "fragmentos_extraidos.json"

# carregar estado
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        index = int(f.read().strip())
else:
    index = 0

# carregar dados
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# recolher fragmentos que tenham "texto"
fragmentos_validos = []

for fid, conteudo in data.items():
    if isinstance(conteudo, dict) and "text" in conteudo:
        fragmentos_validos.append((fid, conteudo["text"]))

if index >= len(fragmentos_validos):
    print("⚠️ Não há mais fragmentos com 'text'.")
    exit()

fid, text = fragmentos_validos[index]

# copiar para clipboard
pyperclip.copy(text)

# guardar novo estado
with open(STATE_FILE, "w", encoding="utf-8") as f:
    f.write(str(index + 1))

winsound.MessageBeep()
ctypes.windll.user32.MessageBoxW(
    0,
    f"Copiado {fid}",
    "Fragmento copiado",
    0
)
