import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple

FICHEIRO_ENTRADA = "fragmentos.md"
FICHEIRO_SAIDA = "containers_segmentacao.json"

HEADER_RE = re.compile(
    r"^##\s+(F\d{4})(?:\s+—\s+(.*?))?\s*$",
    re.MULTILINE
)

DATA_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

# Limites de segurança
MAX_PARAGRAFOS_POR_CONTAINER = 8
MAX_CHARS_POR_CONTAINER = 4000


def normalizar_espacos(texto: str) -> str:
    texto = texto.replace("\u00A0", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def separar_paragrafos(texto: str) -> List[str]:
    texto = texto.replace("\r\n", "\n").replace("\r", "\n").strip()
    blocos = re.split(r"\n\s*\n+", texto)
    return [b.strip() for b in blocos if b.strip()]


def inferir_tipo_material(container_texto: str) -> str:
    t = container_texto.lower()

    if "[proposta gpt]" in t or "[resposta do autor]" in t or "chatgpt" in t:
        return "dialogo_com_ia"

    if "—" in container_texto and len(container_texto.split()) > 120:
        return "fragmento_reflexivo"

    if len(container_texto.split()) > 180:
        return "fragmento_editorial"

    return "misto"


def extrair_titulo_e_data(resto_header: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not resto_header:
        return None, None

    resto = resto_header.strip()
    data_match = DATA_RE.search(resto)
    data = data_match.group(1) if data_match else None

    titulo = resto
    if data:
        titulo = titulo.replace(data, "").strip(" —-–")

    titulo = titulo.strip()
    if not titulo:
        titulo = None

    return titulo, data


def construir_paragrafos(container_id: str, paragrafos_raw: List[str]) -> List[Dict[str, Any]]:
    paragrafos = []
    for i, p in enumerate(paragrafos_raw, start=1):
        texto_norm = normalizar_espacos(p)
        paragrafos.append({
            "paragrafo_id": f"{container_id}_P{i:02d}",
            "ordem_no_container": i,
            "texto": p.strip(),
            "texto_normalizado": texto_norm,
            "n_chars": len(texto_norm),
            "n_linhas_aprox": max(1, p.count("\n") + 1)
        })
    return paragrafos


def criar_container(
    container_id: str,
    header_original: Optional[str],
    titulo_container: Optional[str],
    data: Optional[str],
    paragrafos_raw: List[str],
    ordem_no_ficheiro: int,
    tem_header_formal: bool,
    origem_ficheiro: str,
    observacoes_extra: Optional[List[str]] = None,
) -> Dict[str, Any]:
    corpo = "\n\n".join(paragrafos_raw)
    tipo_material = inferir_tipo_material(corpo)

    paragrafos = construir_paragrafos(container_id, paragrafos_raw)

    observacoes = []
    if not tem_header_formal:
        observacoes.append("container sem header formal")
    if titulo_container:
        observacoes.append("título presente no cabeçalho")
    if tipo_material == "dialogo_com_ia":
        observacoes.append("contém marcas de diálogo com IA")
    if observacoes_extra:
        observacoes.extend(observacoes_extra)

    return {
        "container_id": container_id,
        "titulo_container": titulo_container,
        "data": data,
        "origem_ficheiro": origem_ficheiro,
        "tipo_material_fonte": tipo_material,
        "ordem_no_ficheiro": ordem_no_ficheiro,
        "tem_header_formal": tem_header_formal,
        "header_original": header_original,
        "paragrafos": paragrafos,
        "n_paragrafos": len(paragrafos),
        "observacoes_container": observacoes
    }


def dividir_em_subcontainers(
    base_container_id: str,
    header_original: Optional[str],
    titulo_container: Optional[str],
    data: Optional[str],
    paragrafos_raw: List[str],
    ordem_inicial: int,
    tem_header_formal: bool,
    origem_ficheiro: str,
) -> List[Dict[str, Any]]:
    """
    Divide um bloco grande em subcontainers automáticos:
    F0241_A01, F0241_A02, ...
    """
    containers = []
    chunk = []
    chunk_chars = 0
    ordem = ordem_inicial
    sub_idx = 1

    for p in paragrafos_raw:
        p_norm = normalizar_espacos(p)
        p_chars = len(p_norm)

        precisa_fechar = False

        if chunk:
            if len(chunk) >= MAX_PARAGRAFOS_POR_CONTAINER:
                precisa_fechar = True
            elif chunk_chars + p_chars > MAX_CHARS_POR_CONTAINER:
                precisa_fechar = True

        if precisa_fechar:
            sub_id = f"{base_container_id}_A{sub_idx:02d}"
            containers.append(
                criar_container(
                    container_id=sub_id,
                    header_original=header_original,
                    titulo_container=titulo_container,
                    data=data,
                    paragrafos_raw=chunk,
                    ordem_no_ficheiro=ordem,
                    tem_header_formal=tem_header_formal,
                    origem_ficheiro=origem_ficheiro,
                    observacoes_extra=[
                        f"subcontainer automático derivado de {base_container_id}",
                        f"chunk {sub_idx}"
                    ]
                )
            )
            ordem += 1
            sub_idx += 1
            chunk = []
            chunk_chars = 0

        chunk.append(p)
        chunk_chars += p_chars

    if chunk:
        sub_id = f"{base_container_id}_A{sub_idx:02d}"
        containers.append(
            criar_container(
                container_id=sub_id,
                header_original=header_original,
                titulo_container=titulo_container,
                data=data,
                paragrafos_raw=chunk,
                ordem_no_ficheiro=ordem,
                tem_header_formal=tem_header_formal,
                origem_ficheiro=origem_ficheiro,
                observacoes_extra=[
                    f"subcontainer automático derivado de {base_container_id}",
                    f"chunk {sub_idx}"
                ]
            )
        )

    return containers


def processar_bloco(
    container_id: str,
    header_original: Optional[str],
    titulo_container: Optional[str],
    data: Optional[str],
    corpo: str,
    ordem_no_ficheiro: int,
    tem_header_formal: bool,
    origem_ficheiro: str
) -> List[Dict[str, Any]]:
    paragrafos_raw = separar_paragrafos(corpo)

    total_chars = sum(len(normalizar_espacos(p)) for p in paragrafos_raw)

    if (
        len(paragrafos_raw) > MAX_PARAGRAFOS_POR_CONTAINER
        or total_chars > MAX_CHARS_POR_CONTAINER
    ):
        return dividir_em_subcontainers(
            base_container_id=container_id,
            header_original=header_original,
            titulo_container=titulo_container,
            data=data,
            paragrafos_raw=paragrafos_raw,
            ordem_inicial=ordem_no_ficheiro,
            tem_header_formal=tem_header_formal,
            origem_ficheiro=origem_ficheiro
        )

    return [
        criar_container(
            container_id=container_id,
            header_original=header_original,
            titulo_container=titulo_container,
            data=data,
            paragrafos_raw=paragrafos_raw,
            ordem_no_ficheiro=ordem_no_ficheiro,
            tem_header_formal=tem_header_formal,
            origem_ficheiro=origem_ficheiro
        )
    ]


def processar_ficheiro(caminho: str) -> List[Dict[str, Any]]:
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()

    conteudo = conteudo.replace("\r\n", "\n").replace("\r", "\n")

    matches = list(HEADER_RE.finditer(conteudo))
    containers = []
    ordem = 1
    auto_count = 1

    if not matches:
        container_id = f"AUTO_{auto_count:04d}"
        containers.extend(
            processar_bloco(
                container_id=container_id,
                header_original=None,
                titulo_container=None,
                data=None,
                corpo=conteudo,
                ordem_no_ficheiro=ordem,
                tem_header_formal=False,
                origem_ficheiro=os.path.basename(caminho)
            )
        )
        return containers

    # Texto antes do primeiro header
    inicio_primeiro = matches[0].start()
    prefixo = conteudo[:inicio_primeiro].strip()
    if prefixo:
        container_id = f"AUTO_{auto_count:04d}"
        novos = processar_bloco(
            container_id=container_id,
            header_original=None,
            titulo_container=None,
            data=None,
            corpo=prefixo,
            ordem_no_ficheiro=ordem,
            tem_header_formal=False,
            origem_ficheiro=os.path.basename(caminho)
        )
        containers.extend(novos)
        ordem += len(novos)
        auto_count += 1

    for idx, m in enumerate(matches):
        container_id = m.group(1).strip()
        resto_header = m.group(2).strip() if m.group(2) else None
        header_original = m.group(0).strip()

        titulo_container, data = extrair_titulo_e_data(resto_header)

        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(conteudo)
        corpo = conteudo[start:end].strip()

        novos = processar_bloco(
            container_id=container_id,
            header_original=header_original,
            titulo_container=titulo_container,
            data=data,
            corpo=corpo,
            ordem_no_ficheiro=ordem,
            tem_header_formal=True,
            origem_ficheiro=os.path.basename(caminho)
        )
        containers.extend(novos)
        ordem += len(novos)

    return containers


def guardar_json(caminho: str, dados: Any) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def main():
    containers = processar_ficheiro(FICHEIRO_ENTRADA)
    guardar_json(FICHEIRO_SAIDA, containers)

    print("=" * 60)
    print(f"Containers criados: {len(containers)}")
    print(f"Saída: {FICHEIRO_SAIDA}")
    print("=" * 60)


if __name__ == "__main__":
    main()