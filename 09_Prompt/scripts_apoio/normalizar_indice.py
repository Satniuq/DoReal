from pathlib import Path
import hashlib

ficheiro = Path("data/06_01Texto_No_Indice_TXT.txt")
backup = Path("data/06_01Texto_No_Indice_TXT_BACKUP.txt")

# 1) ler texto original
texto_original = ficheiro.read_text(encoding="utf-8")

# 2) guardar backup integral
backup.write_text(texto_original, encoding="utf-8")

# 3) checksum antes
hash_antes = hashlib.sha256(texto_original.encode("utf-8")).hexdigest()

# 4) substituir APENAS o delimitador errado
texto_corrigido = texto_original.replace("!!!!!!!!!!", "----------")

# 5) checksum depois (do texto corrigido)
hash_depois = hashlib.sha256(texto_corrigido.encode("utf-8")).hexdigest()

# 6) escrever ficheiro corrigido
ficheiro.write_text(texto_corrigido, encoding="utf-8")

print("✔ Ficheiro corrigido")
print("✔ Backup criado:", backup.name)
print("SHA antes :", hash_antes)
print("SHA depois:", hash_depois)
