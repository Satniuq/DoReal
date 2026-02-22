import json
from pathlib import Path
from typing import Dict, Any, Tuple, List


def carregar_conceitos(base_path: str = "conceitos") -> Dict[str, Any]:
    """
    Carrega todos os conceitos JSON sob base_path (ex.: conceitos/nivel_1/*.json ...).

    Retorna:
        dict: { "D_SER": {...}, ... }

    Lança:
        FileNotFoundError: se base_path não existir.
        NotADirectoryError: se base_path não for uma pasta.
        ValueError: se houver JSON inválido, falta de 'id', ou ids duplicados.
    """
    base = Path(base_path)

    if not base.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {base.resolve()}")
    if not base.is_dir():
        raise NotADirectoryError(f"Não é uma pasta: {base.resolve()}")

    conceitos: Dict[str, Any] = {}
    ids_origem: Dict[str, Path] = {}

    # Ordenar para resultados determinísticos
    for nivel_dir in sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name):
        for ficheiro in sorted(nivel_dir.glob("*.json"), key=lambda p: p.name):
            try:
                with open(ficheiro, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"JSON inválido em {ficheiro.resolve()} (linha {e.lineno}, coluna {e.colno}): {e.msg}"
                ) from e

            cid = data.get("id")
            if not cid or not isinstance(cid, str):
                raise ValueError(f"Falta 'id' (string) em: {ficheiro.resolve()}")

            if cid in conceitos:
                raise ValueError(
                    f"ID duplicado '{cid}':\n"
                    f"- {ids_origem[cid].resolve()}\n"
                    f"- {ficheiro.resolve()}"
                )

            conceitos[cid] = data
            ids_origem[cid] = ficheiro

    return conceitos


if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")
    print(f"Conceitos carregados: {len(conceitos)}")