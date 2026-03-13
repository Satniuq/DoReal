import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# PATHS
# ============================================================

PASTA_SCRIPT = Path(__file__).resolve().parent
CAMINHO_MAPA = PASTA_SCRIPT / "mapa_integral_do_indice.json"
CAMINHO_SAIDA = PASTA_SCRIPT / "mapa_integral_do_indice_legivel.md"


# ============================================================
# UTILITÁRIOS
# ============================================================

def carregar_json(caminho: Path) -> Any:
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def guardar_texto(caminho: Path, texto: str) -> None:
    with caminho.open("w", encoding="utf-8") as f:
        f.write(texto)


def normalizar_lista(valor: Any) -> List[Any]:
    if valor is None:
        return []
    if isinstance(valor, list):
        return valor
    return [valor]


def texto(valor: Any, default: str = "—") -> str:
    if valor is None:
        return default
    if isinstance(valor, str):
        v = valor.strip()
        return v if v else default
    return str(valor)


def juntar_lista_simples(valores: Any, default: str = "—") -> str:
    lista = [str(v) for v in normalizar_lista(valores) if v not in (None, "", [])]
    return ", ".join(lista) if lista else default


def indent(texto_base: str, n: int = 2) -> str:
    prefixo = " " * n
    return "\n".join(prefixo + linha if linha else "" for linha in texto_base.splitlines())


def linha_titulo_md(nivel: int, titulo: str) -> str:
    return f"{'#' * nivel} {titulo}\n"


# ============================================================
# FORMATADORES
# ============================================================

def formatar_lista_bullets(itens: List[str], vazio: str = "- —") -> str:
    if not itens:
        return vazio
    return "\n".join(f"- {item}" for item in itens)


def formatar_argumentos(argumentos: List[Dict[str, Any]]) -> str:
    if not argumentos:
        return "- —"

    blocos = []
    for arg in argumentos:
        linhas = [
            f"**{texto(arg.get('argumento_id'))}** — {texto(arg.get('conceito_alvo'))}",
            f"  - natureza: {texto(arg.get('natureza'))}",
            f"  - tipo de necessidade: {texto(arg.get('tipo_de_necessidade'))}",
            f"  - nível de operação: {texto(arg.get('nivel_de_operacao'))}",
            f"  - fundamenta: {juntar_lista_simples(arg.get('fundamenta'))}",
            f"  - pressupostos ontológicos: {juntar_lista_simples(arg.get('pressupostos_ontologicos'))}",
            f"  - outputs instalados: {juntar_lista_simples(arg.get('outputs_instalados'))}",
            f"  - operações-chave: {juntar_lista_simples(arg.get('operacoes_chave'))}",
            f"  - premissas: {juntar_lista_simples(arg.get('premissas'))}",
            f"  - deduções necessárias: {juntar_lista_simples(arg.get('deducoes_necessarias'))}",
            f"  - conclusão: {texto(arg.get('conclusao'))}",
            f"  - depende de argumentos: {juntar_lista_simples(arg.get('depende_de_argumentos'))}",
            f"  - prepara argumentos: {juntar_lista_simples(arg.get('prepara_argumentos'))}",
            f"  - back links: {juntar_lista_simples(arg.get('back_links'))}",
            f"  - forward links: {juntar_lista_simples(arg.get('forward_links'))}",
        ]
        blocos.append("\n".join(f"- {linhas[0]}" if i == 0 else linhas[i] for i in range(len(linhas))))

    return "\n\n".join(blocos)


def formatar_capitulos_relacionados(itens: List[Dict[str, Any]], campo_via: str) -> str:
    if not itens:
        return "- —"

    linhas = []
    for item in itens:
        linhas.append(
            f"- {texto(item.get('capitulo_id'))} — {texto(item.get('titulo'))} "
            f"(parte: {texto(item.get('parte_id'))}; ordem: {texto(item.get('ordem'))}; {campo_via}: {texto(item.get(campo_via))})"
        )
    return "\n".join(linhas)


def formatar_argumentos_relacionados(itens: List[Dict[str, Any]]) -> str:
    if not itens:
        return "- —"

    linhas = []
    for item in itens:
        linhas.append(
            f"- {texto(item.get('argumento_id'))} "
            f"(capítulo: {texto(item.get('capitulo_id'))}; conceito-alvo: {texto(item.get('conceito_alvo'))})"
        )
    return "\n".join(linhas)


def formatar_subzonas(subzonas: List[Dict[str, Any]]) -> str:
    if not subzonas:
        return "- —"

    blocos = []
    for sub in subzonas:
        linhas = [
            f"**{texto(sub.get('subzona'))}**",
            f"  - total de fragmentos: {texto(sub.get('total_fragmentos'))}",
            f"  - fortes: {texto(sub.get('fortes'))}",
            f"  - prováveis: {texto(sub.get('provaveis'))}",
            f"  - fracos: {texto(sub.get('fracos'))}",
            f"  - indefinidos: {texto(sub.get('indefinidos'))}",
            f"  - argumentos canónicos: {juntar_lista_simples(sub.get('argumentos_canonicos'))}",
            f"  - trabalhos no sistema: {juntar_lista_simples(sub.get('trabalhos_no_sistema'))}",
            f"  - destinos editoriais finos: {juntar_lista_simples(sub.get('destinos_editoriais_finos'))}",
        ]

        exemplos = normalizar_lista(sub.get("fragmentos_exemplo"))
        if exemplos:
            linhas.append("  - fragmentos-exemplo:")
            for ex in exemplos:
                linhas.append(
                    f"    - {texto(ex.get('fragment_id'))} | "
                    f"grau={texto(ex.get('grau_de_pertenca_ao_indice'))} | "
                    f"arg={texto(ex.get('argumento_canonico_relacionado'))} | "
                    f"trabalho={texto(ex.get('trabalho_no_sistema'))} | "
                    f"score={texto(ex.get('score'))} | "
                    f"{texto(ex.get('descricao_funcional_curta'))}"
                )

        blocos.append("\n".join(f"- {linhas[0]}" if i == 0 else linhas[i] for i in range(len(linhas))))

    return "\n\n".join(blocos)


def formatar_resumo_fragmentos(resumo: Dict[str, Any]) -> str:
    if not resumo:
        return "- —"

    linhas = [
        f"- total de fragmentos prioritários: {texto(resumo.get('total_fragmentos_prioritarios'))}",
        f"- fortes: {texto(resumo.get('fortes'))}",
        f"- prováveis: {texto(resumo.get('provaveis'))}",
        f"- fracos: {texto(resumo.get('fracos'))}",
        f"- indefinidos: {texto(resumo.get('indefinidos'))}",
        f"- reconstruíveis: {texto(resumo.get('reconstruiveis'))}",
        f"- argumentos em esboço: {texto(resumo.get('argumentos_em_esboco'))}",
        f"- formulações pré-argumentativas: {texto(resumo.get('formulacoes_pre_argumentativas'))}",
        f"- prioridade alta: {texto(resumo.get('prioridade_alta'))}",
        f"- prioridade média: {texto(resumo.get('prioridade_media'))}",
    ]
    return "\n".join(linhas)


def formatar_fragmentos_prioritarios(fragmentos: List[Dict[str, Any]]) -> str:
    if not fragmentos:
        return "- —"

    linhas = []
    for f in fragmentos:
        linhas.append(
            f"- {texto(f.get('fragment_id'))} | origem={texto(f.get('origem_id'))} | "
            f"ordem={texto(f.get('ordem_no_ficheiro'))} | "
            f"grau={texto(f.get('grau_de_pertenca_ao_indice'))} | "
            f"modo={texto(f.get('modo_de_pertenca'))} | "
            f"arg={texto(f.get('argumento_canonico_relacionado'))} | "
            f"estado={texto(f.get('estado_argumentativo'))} | "
            f"reconstruível={texto(f.get('argumento_reconstruivel'))} | "
            f"subzona={texto(f.get('subcapitulo_ou_zona_interna'))} | "
            f"destino={texto(f.get('destino_editorial_fino'))} | "
            f"prioridade={texto(f.get('prioridade_de_aproveitamento'))} | "
            f"score={texto(f.get('score'))} | "
            f"{texto(f.get('descricao_funcional_curta'))}"
        )
    return "\n".join(linhas)


def formatar_apoio_percurso(apoio: Dict[str, Any]) -> str:
    if not apoio:
        return "- —"

    linhas = [
        f"- caps_ids no percurso: {juntar_lista_simples(apoio.get('caps_ids_no_percurso'))}",
        f"- percursos base: {juntar_lista_simples(apoio.get('percursos_base'))}",
        f"- resumo: {json.dumps(apoio.get('resumo', {}), ensure_ascii=False, indent=2)}",
    ]
    return "\n".join(linhas)


# ============================================================
# GERAÇÃO DO DOCUMENTO
# ============================================================

def construir_secao_estrutura_global(mapa: Dict[str, Any]) -> str:
    estrutura = mapa.get("estrutura_global", {})
    cobertura = mapa.get("resumo_cobertura", {})

    partes = normalizar_lista(estrutura.get("partes"))
    partes_txt = []
    for p in partes:
        partes_txt.append(
            f"- {texto(p.get('parte_id'))} (ordem: {texto(p.get('ordem'))}) "
            f"-> capítulos: {juntar_lista_simples(p.get('capitulos_ids'))}"
        )

    linhas = [
        linha_titulo_md(1, "Mapa Integral do Índice"),
        "Documento legível gerado a partir de `mapa_integral_do_indice.json`.\n",
        linha_titulo_md(2, "Estrutura global"),
        f"- total de capítulos: {texto(estrutura.get('total_capitulos'))}",
        f"- total de argumentos: {texto(estrutura.get('total_argumentos'))}",
        f"- total de fragmentos tratados: {texto(estrutura.get('total_fragmentos_tratados'))}",
        f"- total de fragmentos fortes: {texto(estrutura.get('total_fragmentos_fortes'))}",
        f"- total de fragmentos prováveis: {texto(estrutura.get('total_fragmentos_provaveis'))}",
        f"- total de fragmentos fracos: {texto(estrutura.get('total_fragmentos_fracos'))}",
        f"- total de fragmentos indefinidos: {texto(estrutura.get('total_fragmentos_indefinidos'))}",
        f"- total de fragmentos reconstruíveis: {texto(estrutura.get('total_fragmentos_reconstruiveis'))}",
        "",
        linha_titulo_md(2, "Partes"),
        formatar_lista_bullets(partes_txt),
        "",
        linha_titulo_md(2, "Cobertura"),
        f"- capítulos sem argumentos: {texto(cobertura.get('total_capitulos_sem_argumentos'))}",
        f"- capítulos sem fragmentos: {texto(cobertura.get('total_capitulos_sem_fragmentos'))}",
        f"- capítulos com cobertura forte: {texto(cobertura.get('total_capitulos_com_cobertura_forte'))}",
        f"- capítulos com cobertura apenas provável: {texto(cobertura.get('total_capitulos_com_cobertura_apenas_provavel'))}",
        "",
        linha_titulo_md(3, "Listas de cobertura"),
        f"**Capítulos sem argumentos**\n{formatar_lista_bullets([texto(x) for x in normalizar_lista(cobertura.get('capitulos_sem_argumentos'))])}",
        "",
        f"**Capítulos sem fragmentos**\n{formatar_lista_bullets([texto(x) for x in normalizar_lista(cobertura.get('capitulos_sem_fragmentos'))])}",
        "",
        f"**Capítulos com cobertura forte**\n{formatar_lista_bullets([texto(x) for x in normalizar_lista(cobertura.get('capitulos_com_cobertura_forte'))])}",
        "",
        f"**Capítulos com cobertura apenas provável**\n{formatar_lista_bullets([texto(x) for x in normalizar_lista(cobertura.get('capitulos_com_cobertura_apenas_provavel'))])}",
        "",
    ]

    return "\n".join(linhas)


def construir_secao_capitulo(cap: Dict[str, Any]) -> str:
    trans = cap.get("transicoes_narrativas", {})
    resumo_fragmentos = cap.get("resumo_fragmentos_prioritarios", {})
    apoio_percurso = cap.get("apoio_percurso", {})

    linhas = [
        linha_titulo_md(3, f"{texto(cap.get('capitulo_id'))} — {texto(cap.get('titulo'))}"),
        f"- parte: {texto(cap.get('parte_id'))}",
        f"- ordem: {texto(cap.get('ordem'))}",
        f"- nível: {texto(cap.get('nivel'))}",
        f"- campos: {juntar_lista_simples(cap.get('campos'))}",
        f"- regime principal: {texto(cap.get('regime_principal'))}",
        f"- regimes secundários: {juntar_lista_simples(cap.get('regimes_secundarios'))}",
        f"- percurso axial: {texto(cap.get('percurso_axial'))}",
        f"- percursos participantes: {juntar_lista_simples(cap.get('percursos_participantes'))}",
        f"- estado de instalação: {texto(cap.get('estado_instalacao'))}",
        f"- observações: {juntar_lista_simples(cap.get('observacoes'))}",
        "",
        "#### Apoio do percurso",
        formatar_apoio_percurso(apoio_percurso),
        "",
        "#### Capítulos anteriores pressupostos",
        formatar_capitulos_relacionados(normalizar_lista(cap.get("capitulos_anteriores_pressupostos")), "via_percurso"),
        "",
        "#### Capítulos seguintes preparados",
        formatar_capitulos_relacionados(normalizar_lista(cap.get("capitulos_seguintes_preparados")), "via_argumento"),
        "",
        "#### Transições narrativas",
        "**Depende de argumentos**",
        formatar_argumentos_relacionados(normalizar_lista(trans.get("depende_de_argumentos"))),
        "",
        "**Prepara argumentos**",
        formatar_argumentos_relacionados(normalizar_lista(trans.get("prepara_argumentos"))),
        "",
        "**Capítulos anteriores referidos**",
        formatar_capitulos_relacionados(normalizar_lista(trans.get("capitulos_anteriores_referidos")), "via_argumento"),
        "",
        "**Capítulos seguintes referidos**",
        formatar_capitulos_relacionados(normalizar_lista(trans.get("capitulos_seguintes_referidos")), "via_argumento"),
        "",
        "#### Argumentos canónicos",
        formatar_argumentos(normalizar_lista(cap.get("argumentos_canonicos"))),
        "",
        "#### Subzonas provisórias",
        formatar_subzonas(normalizar_lista(cap.get("subzonas_provisorias"))),
        "",
        "#### Resumo dos fragmentos prioritários",
        formatar_resumo_fragmentos(resumo_fragmentos),
        "",
        "#### Fragmentos prioritários de exemplo",
        formatar_fragmentos_prioritarios(normalizar_lista(cap.get("fragmentos_prioritarios_exemplo"))),
        "",
    ]

    return "\n".join(linhas)


def construir_documento_markdown(mapa: Dict[str, Any]) -> str:
    capitulos = normalizar_lista(mapa.get("capitulos"))
    capitulos_por_parte: Dict[str, List[Dict[str, Any]]] = {}

    for cap in capitulos:
        parte_id = texto(cap.get("parte_id"))
        capitulos_por_parte.setdefault(parte_id, []).append(cap)

    for parte_id in capitulos_por_parte:
        capitulos_por_parte[parte_id].sort(
            key=lambda c: (c.get("ordem", 9999), texto(c.get("capitulo_id"), "ZZZ"))
        )

    estrutura = mapa.get("estrutura_global", {})
    partes_ordenadas = normalizar_lista(estrutura.get("partes"))

    blocos = [construir_secao_estrutura_global(mapa)]

    blocos.append(linha_titulo_md(2, "Leitura integral por partes"))

    for parte in partes_ordenadas:
        parte_id = texto(parte.get("parte_id"))
        blocos.append(linha_titulo_md(2, f"Parte {texto(parte.get('ordem'))} — {parte_id}"))

        caps = capitulos_por_parte.get(parte_id, [])
        if not caps:
            blocos.append("- Sem capítulos nesta parte.\n")
            continue

        for cap in caps:
            blocos.append(construir_secao_capitulo(cap))

    return "\n".join(blocos).strip() + "\n"


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    if not CAMINHO_MAPA.exists():
        raise FileNotFoundError(f"Não encontrei o ficheiro: {CAMINHO_MAPA}")

    mapa = carregar_json(CAMINHO_MAPA)
    markdown = construir_documento_markdown(mapa)
    guardar_texto(CAMINHO_SAIDA, markdown)

    print("=" * 100)
    print("MAPA INTEGRAL DO ÍNDICE — VERSÃO LEGÍVEL")
    print("=" * 100)
    print(f"Input:  {CAMINHO_MAPA}")
    print(f"Output: {CAMINHO_SAIDA}")
    print("=" * 100)


if __name__ == "__main__":
    main()