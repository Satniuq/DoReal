import json
import shutil
from pathlib import Path

FICHEIRO = Path("fragmentos_resegmentados.json")
BACKUP = Path("fragmentos_resegmentados.backup_antes_normalizacao.json")

TIPOS_UNIDADE_VALIDOS = {
    "bloco_unico",
    "afirmacao_curta",
    "distincao_conceptual",
    "desenvolvimento_curto",
    "desenvolvimento_medio",
    "sequencia_argumentativa",
    "objecao_local",
    "resposta_local",
    "transicao_reflexiva",
    "fragmento_intuitivo",
}

TIPO_SUBSTITUICAO = "desenvolvimento_curto"


def main():
    if not FICHEIRO.exists():
        print(f"Ficheiro não encontrado: {FICHEIRO}")
        return

    if not BACKUP.exists():
        shutil.copy2(FICHEIRO, BACKUP)

    with FICHEIRO.open("r", encoding="utf-8") as f:
        dados = json.load(f)

    alterados = []

    for frag in dados:
        frag_id = frag.get("fragmento_id", "<sem_id>")
        segmentacao = frag.get("segmentacao") or {}

        tipo = segmentacao.get("tipo_unidade")

        if tipo not in TIPOS_UNIDADE_VALIDOS:
            alterados.append((frag_id, tipo, TIPO_SUBSTITUICAO))
            segmentacao["tipo_unidade"] = TIPO_SUBSTITUICAO
            frag["segmentacao"] = segmentacao

    with FICHEIRO.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print("=" * 90)
    print("NORMALIZAÇÃO DE tipo_unidade")
    print("=" * 90)
    print(f"Ficheiro:   {FICHEIRO}")
    print(f"Backup:     {BACKUP}")
    print(f"Alterados:  {len(alterados)}")

    if alterados:
        print("\nFragmentos alterados:")
        for frag_id, antigo, novo in alterados:
            print(f"- [{frag_id}] {antigo} -> {novo}")

    print("=" * 90)


if __name__ == "__main__":
    main()