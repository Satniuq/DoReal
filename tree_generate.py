from pathlib import Path

# Pasta raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent

# Ficheiro de saída
OUTPUT_FILE = ROOT_DIR / "tree_output.txt"

# Pastas que normalmente convém ignorar
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".idea",
    ".vscode",
    "dist",
    "build",
}

# Ficheiros que normalmente convém ignorar
IGNORE_FILES = {
    ".DS_Store",
}

def should_ignore(path: Path) -> bool:
    return path.name in IGNORE_DIRS or path.name in IGNORE_FILES

def build_tree(path: Path, prefix: str = "") -> list[str]:
    lines = []

    try:
        entries = sorted(
            [p for p in path.iterdir() if not should_ignore(p)],
            key=lambda p: (p.is_file(), p.name.lower())
        )
    except PermissionError:
        lines.append(prefix + "[Acesso negado]")
        return lines

    for index, entry in enumerate(entries):
        is_last = index == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + entry.name)

        if entry.is_dir():
            extension = "    " if is_last else "│   "
            lines.extend(build_tree(entry, prefix + extension))

    return lines

def main():
    lines = [ROOT_DIR.name]
    lines.extend(build_tree(ROOT_DIR))

    content = "\n".join(lines)
    OUTPUT_FILE.write_text(content, encoding="utf-8")

    print(f"Tree gravada em: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()