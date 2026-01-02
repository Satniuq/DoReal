from pathlib import Path

BASE = Path("DoReal")

structure = {
    "00_bruto": ["fragmentos.md"],
    "01_indexacao": ["conceitos.md", "teses.md", "eixos.md", "problemas.md"],
    "02_relacoes": ["ligacoes_provisorias.md", "tensoes.md"],
    "03_historico": ["decisoes.md"],
    "04_filософos": ["heidegger.md", "aristoteles.md", "kant.md"],
}

BASE.mkdir(exist_ok=True)

(Path(BASE / "README.md")).touch(exist_ok=True)

for folder, files in structure.items():
    folder_path = BASE / folder
    folder_path.mkdir(exist_ok=True)
    for file in files:
        (folder_path / file).touch(exist_ok=True)

print("Estrutura DoReal criada com sucesso.")
