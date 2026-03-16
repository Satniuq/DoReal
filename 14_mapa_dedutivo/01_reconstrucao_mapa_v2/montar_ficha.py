from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# CONFIGURAÇÃO DE PATHS
# ============================================================

PASTA_SCRIPT = Path(__file__).resolve().parent

FICHEIROS_CORREDOR = [
    "corredor_P25_P30_organizado.json",
    "corredor_P33_P37_organizado.json",
    "corredor_P42_P48_organizado.json",
    "corredor_P50_organizado.json",
]

LIMITES_POR_CATEGORIA = {
    "fragmentos_justificativos": 12,
    "fragmentos_mediacionais": 8,
    "fragmentos_de_bloqueio": 8,
    "fragmentos_ilustrativos": 6,
}

VERSAO_SCRIPT = "montar_fichas_v2_v1"


# ============================================================
# UTILITÁRIOS GERAIS
# ============================================================


def ler_json(caminho: Path) -> Dict[str, Any]:
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)



def escrever_json(caminho: Path, dados: Dict[str, Any]) -> None:
    with caminho.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)



def utc_agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")



def limpar_lista_textos(valores: Optional[List[Any]]) -> List[str]:
    if not isinstance(valores, list):
        return []

    vistos = set()
    saida: List[str] = []
    for valor in valores:
        if valor is None:
            continue
        texto = str(valor).strip()
        if not texto:
            continue
        chave = texto.casefold()
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append(texto)
    return saida



def limpar_lista_ids(valores: Optional[List[Any]]) -> List[str]:
    return limpar_lista_textos(valores)



def escolher_primeiro_texto(*valores: Any) -> Optional[str]:
    for valor in valores:
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return None



def limitar_lista(lista: List[Any], limite: int) -> List[Any]:
    return lista[:limite] if limite >= 0 else list(lista)



def resumo_distribuicao(fragmentos: List[Dict[str, Any]]) -> Dict[str, int]:
    saida = {
        "alta": 0,
        "media": 0,
        "baixa": 0,
        "muito_provisorio_ou_instavel": 0,
    }
    for frag in fragmentos:
        tratamento = frag.get("tratamento_filosofico") or {}
        prioridade = str(tratamento.get("prioridade_de_aproveitamento") or "").strip().lower()
        estabilizacao = str(tratamento.get("grau_de_estabilizacao") or "").strip().lower()
        clareza = str(tratamento.get("clareza_atual") or "").strip().lower()

        if prioridade == "alta":
            saida["alta"] += 1
        elif prioridade == "media":
            saida["media"] += 1
        else:
            saida["baixa"] += 1

        if estabilizacao in {"muito_provisorio", "provisorio"} or clareza in {"instavel", "muito_instavel"}:
            saida["muito_provisorio_ou_instavel"] += 1
    return saida



def extrair_objecoes_dos_fragmentos(materiais: Dict[str, Any]) -> List[str]:
    return limpar_lista_textos(materiais.get("objecoes_que_ajudam_a_bloquear"))



def extrair_mediacoes_em_falta(prop: Dict[str, Any]) -> List[str]:
    base = prop.get("base_dedutiva_existente") or {}
    academico = prop.get("mapa_base_origem", {}).get("tratamento_academico", {}) or {}
    existentes = limpar_lista_textos(base.get("mediacoes_em_falta_no_mapa"))
    existentes += limpar_lista_textos(academico.get("mediacoes_em_falta"))

    diagnostico = prop.get("diagnostico_estrutural") or {}
    necessidade = str(diagnostico.get("necessidade_principal") or "").strip().lower()
    dependencias = limpar_lista_ids(prop.get("depende_de"))
    prepara = limpar_lista_ids(prop.get("prepara"))

    inferidas: List[str] = []
    if necessidade == "explicitar_mediacoes":
        if dependencias:
            inferidas.append(
                f"Explicitar a ponte dedutiva entre {', '.join(dependencias)} e {prop.get('proposicao_id')}."
            )
        if prepara:
            inferidas.append(
                f"Explicitar a passagem de {prop.get('proposicao_id')} para {', '.join(prepara)}."
            )
    elif necessidade == "reformular":
        inferidas.append("Reformular a proposição sem perder o núcleo que o material já sustenta.")
    elif necessidade == "densificar":
        inferidas.append("Densificar a justificação interna e tornar explícitos os seus pressupostos imediatos.")

    med_fornecidas = limpar_lista_textos((prop.get("materiais_de_reconstrucao") or {}).get("mediacoes_que_fornecem"))
    if med_fornecidas:
        inferidas.append("Aproveitar as mediações já sinalizadas nos fragmentos e separar as fortes das apenas expositivas.")

    return limpar_lista_textos(existentes + inferidas)



def gerar_funcao_no_percurso(prop: Dict[str, Any]) -> str:
    proposicao = prop.get("proposicao") or prop.get("mapa_base_origem", {}).get("proposicao") or ""
    bloco = prop.get("bloco_titulo") or "bloco não identificado"
    depende = limpar_lista_ids(prop.get("depende_de"))
    prepara = limpar_lista_ids(prop.get("prepara"))

    partes = [f"No {bloco}, esta proposição fixa que {proposicao[:1].lower() + proposicao[1:] if proposicao else 'este passo deve ser mantido'}"]
    if depende:
        partes.append(f"Recebe apoio imediato de {', '.join(depende)}")
    if prepara:
        partes.append(f"e prepara {', '.join(prepara)}")
    return "; ".join(partes) + "."



def gerar_nucleo_que_se_mantem(prop: Dict[str, Any]) -> str:
    base = prop.get("base_dedutiva_existente") or {}
    tese = escolher_primeiro_texto(base.get("tese_minima"), prop.get("proposicao")) or ""
    justificacao = escolher_primeiro_texto(base.get("justificacao_interna_do_passo"))
    estabilidade = str((prop.get("diagnostico_estrutural") or {}).get("estabilidade") or "").strip()

    partes = [f"Mantém-se o núcleo segundo o qual {tese[:1].lower() + tese[1:] if tese else 'a proposição continua válida'}"]
    if justificacao:
        partes.append(f"A justificação mínima já presente é: {justificacao}")
    if estabilidade:
        partes.append(f"O diagnóstico estrutural atual é '{estabilidade}'")
    return ". ".join(partes).strip() + "."



def gerar_defice_principal(prop: Dict[str, Any]) -> str:
    diagnostico = prop.get("diagnostico_estrutural") or {}
    base = prop.get("base_dedutiva_existente") or {}
    falta = escolher_primeiro_texto(
        base.get("o_que_falta_provar_ou_explicitar"),
        prop.get("mapa_base_origem", {}).get("tratamento_academico", {}).get("o_que_falta_provar_ou_explicitar"),
    )
    necessidade = str(diagnostico.get("necessidade_principal") or "").strip().lower()

    prefixo = {
        "reformular": "O défice principal é de formulação e fecho dedutivo.",
        "explicitar_mediacoes": "O défice principal é de mediação dedutiva explícita.",
        "densificar": "O défice principal é de densidade justificativa.",
        "verificar_manual": "O défice principal é de validação manual do passo.",
    }.get(necessidade, "O défice principal exige revisão filosófica localizada.")

    if falta:
        return f"{prefixo} Falta ainda: {falta}"
    return prefixo



def gerar_ponte(prop: Dict[str, Any], direcao: str) -> Optional[str]:
    ids = limpar_lista_ids(prop.get("depende_de") if direcao == "anterior" else prop.get("prepara"))
    if not ids:
        return None

    tese = escolher_primeiro_texto(prop.get("proposicao"), prop.get("base_dedutiva_existente", {}).get("tese_minima")) or "esta proposição"

    if direcao == "anterior":
        return f"Mostrar como {', '.join(ids)} desemboca(m) em '{tese}' sem salto categorial nem compressão excessiva."
    return f"Mostrar como '{tese}' abre legitimamente a passagem para {', '.join(ids)}, explicitando o elo intermédio quando necessário."



def seleccionar_fragmentos(fragmentos: List[Dict[str, Any]], limite: int) -> List[Dict[str, Any]]:
    def chave_ordenacao(frag: Dict[str, Any]) -> Tuple[int, int, int, str]:
        tratamento = frag.get("tratamento_filosofico") or {}
        prioridade = str(tratamento.get("prioridade_de_aproveitamento") or "").lower()
        forca = str(tratamento.get("forca_logica_estimada") or "").lower()
        precisa_reescrita = bool(tratamento.get("requer_reescrita"))

        peso_prioridade = {"alta": 3, "media": 2, "baixa": 1}.get(prioridade, 0)
        peso_forca = {"alta": 3, "media": 2, "baixa": 1}.get(forca, 0)
        penalizacao = 0 if not precisa_reescrita else -1
        return (-peso_prioridade, -peso_forca, -penalizacao, str(frag.get("fragment_id") or ""))

    ordenados = sorted(fragmentos, key=chave_ordenacao)
    escolhidos = limitar_lista(ordenados, limite)

    saida: List[Dict[str, Any]] = []
    for frag in escolhidos:
        tratamento = frag.get("tratamento_filosofico") or {}
        saida.append(
            {
                "fragment_id": frag.get("fragment_id"),
                "origem_id": frag.get("origem_id"),
                "resumo_local_no_corredor": frag.get("resumo_local_no_corredor"),
                "justificacao_local_no_corredor": frag.get("justificacao_local_no_corredor"),
                "categoria_primaria": frag.get("categoria_primaria"),
                "categorias_secundarias": frag.get("categorias_secundarias") or [],
                "prioridade_de_aproveitamento": tratamento.get("prioridade_de_aproveitamento"),
                "forca_logica_estimada": tratamento.get("forca_logica_estimada"),
                "estado_argumentativo": tratamento.get("estado_argumentativo"),
                "forma_de_inferencia": tratamento.get("forma_de_inferencia"),
                "requer_reescrita": tratamento.get("requer_reescrita"),
                "requer_densificacao": tratamento.get("requer_densificacao"),
                "necessita_reconstrucao_forte": tratamento.get("necessita_reconstrucao_forte"),
                "descricao_funcional_curta": tratamento.get("descricao_funcional_curta"),
            }
        )
    return saida



def recolher_fragmentos_bloqueio(prop: Dict[str, Any]) -> List[Dict[str, Any]]:
    blocos: List[Dict[str, Any]] = []
    for chave in ("fragmentos_justificativos", "fragmentos_mediacionais", "fragmentos_ilustrativos"):
        for frag in (prop.get("reconstrucao_v2") or {}).get(chave, []) or []:
            secundarias = frag.get("categorias_secundarias") or []
            if "bloqueio" in secundarias or frag.get("categoria_primaria") == "bloqueio":
                blocos.append(frag)
    # remover duplicados por fragment_id
    vistos = set()
    unicos: List[Dict[str, Any]] = []
    for frag in blocos:
        fid = frag.get("fragment_id")
        if not fid or fid in vistos:
            continue
        vistos.add(fid)
        unicos.append(frag)
    return unicos



def gerar_observacoes_trabalho(prop: Dict[str, Any]) -> List[str]:
    diagnostico = prop.get("diagnostico_estrutural") or {}
    organizacao = prop.get("organizacao_fragmentos_por_funcao") or {}
    necessidade = str(diagnostico.get("necessidade_principal") or "").strip().lower()
    acao = str(diagnostico.get("acao_estrutural_recomendada") or "").strip().lower()

    obs: List[str] = []
    if necessidade == "reformular":
        obs.append("Reescrever a proposição com maior precisão canónica, mas sem mexer desnecessariamente na posição do passo no corredor.")
    elif necessidade == "explicitar_mediacoes":
        obs.append("Abrir explicitamente as mediações internas entre a tese atual e o passo seguinte.")
    elif necessidade == "densificar":
        obs.append("Densificar a justificação e transformar apoio fragmentário disperso em argumento corrido.")
    elif necessidade == "verificar_manual":
        obs.append("Confirmar manualmente se a falta de fragmentos é contingente ou se o passo tem mesmo apoio indireto apenas arquitetónico.")

    if acao == "reformular":
        obs.append("A ação recomendada não é só acrescentar material: é corrigir formulação e clarificar o alcance do passo.")
    elif acao == "densificar":
        obs.append("A ação recomendada dominante é densificar, não dividir o mapa nem criar novos passos sem necessidade.")

    dist = organizacao.get("distribuicao_categorias_primarias") or {}
    if dist.get("mediacional", 0) == 0 and dist.get("justificativo", 0) > 0:
        obs.append("Há muito apoio justificativo, mas pouca mediação primária identificada; convém fabricar a ponte dedutiva na escrita v2.")
    if organizacao.get("fragmentos_sem_tratamento_filosofico"):
        obs.append("Há fragmentos sem tratamento filosófico prévio; convém revê-los antes do fecho do corredor.")

    return limpar_lista_textos(obs)



def montar_ficha_proposicao(prop: Dict[str, Any], corredor_nome: str) -> Dict[str, Any]:
    recon = deepcopy(prop.get("reconstrucao_v2") or {})
    materiais = prop.get("materiais_de_reconstrucao") or {}
    base = prop.get("base_dedutiva_existente") or {}
    diagnostico = prop.get("diagnostico_estrutural") or {}

    just = recon.get("fragmentos_justificativos") or []
    med = recon.get("fragmentos_mediacionais") or []
    ilust = recon.get("fragmentos_ilustrativos") or []
    bloq = recon.get("fragmentos_de_bloqueio") or []
    if not bloq:
        bloq = recolher_fragmentos_bloqueio(prop)

    ficha = {
        "proposicao_id": prop.get("proposicao_id"),
        "numero": prop.get("numero"),
        "corredor": corredor_nome,
        "bloco_id": prop.get("bloco_id"),
        "bloco_titulo": prop.get("bloco_titulo"),
        "proposicao_atual": prop.get("proposicao"),
        "descricao_curta": prop.get("descricao_curta"),
        "depende_de": limpar_lista_ids(prop.get("depende_de")),
        "prepara": limpar_lista_ids(prop.get("prepara")),
        "funcao_no_percurso": gerar_funcao_no_percurso(prop),
        "estado_estrutural_atual": {
            "estabilidade": diagnostico.get("estabilidade"),
            "necessidade_principal": diagnostico.get("necessidade_principal"),
            "acao_estrutural_recomendada": diagnostico.get("acao_estrutural_recomendada"),
            "diagnostico_textual": diagnostico.get("diagnostico_textual"),
        },
        "nucleo_que_se_mantem": gerar_nucleo_que_se_mantem(prop),
        "defice_principal": gerar_defice_principal(prop),
        "justificacao_atual": escolher_primeiro_texto(base.get("justificacao_interna_do_passo")),
        "mediacoes_em_falta": extrair_mediacoes_em_falta(prop),
        "objecoes_a_bloquear": limpar_lista_textos(
            list(base.get("objecoes_tipicas_a_bloquear") or []) + extrair_objecoes_dos_fragmentos(materiais)
        ),
        "fragmentos_justificativos": seleccionar_fragmentos(just, LIMITES_POR_CATEGORIA["fragmentos_justificativos"]),
        "fragmentos_mediacionais": seleccionar_fragmentos(med, LIMITES_POR_CATEGORIA["fragmentos_mediacionais"]),
        "fragmentos_de_bloqueio": seleccionar_fragmentos(bloq, LIMITES_POR_CATEGORIA["fragmentos_de_bloqueio"]),
        "fragmentos_ilustrativos": seleccionar_fragmentos(ilust, LIMITES_POR_CATEGORIA["fragmentos_ilustrativos"]),
        "decisao_editorial_v2": {
            "acao_recomendada": diagnostico.get("acao_estrutural_recomendada"),
            "necessidade_principal": diagnostico.get("necessidade_principal"),
            "estado_provisorio": diagnostico.get("estabilidade"),
        },
        "formulacao_v2_provisoria": escolher_primeiro_texto(
            recon.get("nova_formulacao_v2_provisoria"),
            prop.get("nova_formulacao_provisoria"),
        ),
        "ponte_com_passo_anterior": gerar_ponte(prop, "anterior"),
        "ponte_com_passo_seguinte": gerar_ponte(prop, "seguinte"),
        "observacoes_de_trabalho": gerar_observacoes_trabalho(prop),
        "resumo_fragmentario": {
            "total_fragmentos_relacionados": (prop.get("organizacao_fragmentos_por_funcao") or {}).get("total_fragmentos_relacionados"),
            "distribuicao_categorias_primarias": (prop.get("organizacao_fragmentos_por_funcao") or {}).get("distribuicao_categorias_primarias") or {},
            "distribuicao_justificativos": resumo_distribuicao(just),
            "distribuicao_mediacionais": resumo_distribuicao(med),
            "distribuicao_bloqueio": resumo_distribuicao(bloq),
            "distribuicao_ilustrativos": resumo_distribuicao(ilust),
        },
        "materiais_de_referencia": {
            "teses_principais": limpar_lista_textos(materiais.get("teses_principais_dos_fragmentos")),
            "justificacoes_novas": limpar_lista_textos(materiais.get("justificacoes_novas_que_fornecem")),
            "propostas_de_nova_formulacao": limpar_lista_textos(materiais.get("propostas_de_nova_formulacao")),
            "observacoes_finais": limpar_lista_textos(materiais.get("observacoes_finais")),
        },
    }
    return ficha



def resumir_fichas(fichas: List[Dict[str, Any]]) -> Dict[str, Any]:
    dist_necessidade: Dict[str, int] = {}
    dist_acao: Dict[str, int] = {}
    top_fragmentos: List[Dict[str, Any]] = []

    for ficha in fichas:
        estado = ficha.get("estado_estrutural_atual") or {}
        necessidade = str(estado.get("necessidade_principal") or "nao_indicado")
        acao = str(estado.get("acao_estrutural_recomendada") or "nao_indicado")
        dist_necessidade[necessidade] = dist_necessidade.get(necessidade, 0) + 1
        dist_acao[acao] = dist_acao.get(acao, 0) + 1

        top_fragmentos.append(
            {
                "proposicao_id": ficha.get("proposicao_id"),
                "numero": ficha.get("numero"),
                "total_fragmentos_relacionados": ficha.get("resumo_fragmentario", {}).get("total_fragmentos_relacionados") or 0,
                "necessidade_principal": necessidade,
                "acao_recomendada": acao,
            }
        )

    top_fragmentos.sort(key=lambda x: (-int(x["total_fragmentos_relacionados"]), int(x["numero"] or 0)))

    return {
        "total_fichas": len(fichas),
        "distribuicao_necessidade_principal": dist_necessidade,
        "distribuicao_acao_recomendada": dist_acao,
        "top_proposicoes_por_carga_fragmentaria": top_fragmentos[:10],
    }



def processar_corredor(caminho: Path) -> Optional[Tuple[Path, Dict[str, Any]]]:
    if not caminho.exists():
        print(f"[AVISO] Ficheiro não encontrado: {caminho.name}")
        return None

    dados = ler_json(caminho)
    props = dados.get("proposicoes") or []
    fichas = [montar_ficha_proposicao(prop, caminho.stem) for prop in props if isinstance(prop, dict)]

    saida = {
        "meta": {
            "gerado_em_utc": utc_agora_iso(),
            "versao_script": VERSAO_SCRIPT,
            "ficheiro_origem": str(caminho),
            "corredor": caminho.stem,
            "titulo": (dados.get("meta") or {}).get("titulo"),
            "descricao": (dados.get("meta") or {}).get("descricao"),
            "objetivo": "Converter o corredor organizado em fichas v2 de trabalho por proposição, já reduzidas e orientadas para reconstrução dedutiva controlada.",
        },
        "resumo": resumir_fichas(fichas),
        "fichas": fichas,
    }

    nome_saida = caminho.name.replace("_organizado.json", "")
    caminho_saida = caminho.with_name(f"fichas_v2_{nome_saida}.json")
    escrever_json(caminho_saida, saida)
    return caminho_saida, saida



def main() -> None:
    resultados: List[Tuple[Path, Dict[str, Any]]] = []

    for nome in FICHEIROS_CORREDOR:
        resultado = processar_corredor(PASTA_SCRIPT / nome)
        if resultado is not None:
            resultados.append(resultado)

    resumo_global = {
        "meta": {
            "gerado_em_utc": utc_agora_iso(),
            "versao_script": VERSAO_SCRIPT,
            "observacao": "As fichas v2 são um instrumento de trabalho. Não substituem a decisão filosófica humana sobre formulação final e ordem dedutiva.",
        },
        "ficheiros_gerados": [
            {
                "corredor": dados.get("meta", {}).get("corredor"),
                "ficheiro": str(caminho),
                "total_fichas": dados.get("resumo", {}).get("total_fichas"),
            }
            for caminho, dados in resultados
        ],
        "resumo_por_corredor": {
            dados.get("meta", {}).get("corredor", caminho.stem): dados.get("resumo", {})
            for caminho, dados in resultados
        },
    }

    escrever_json(PASTA_SCRIPT / "resumo_montagem_fichas_v2.json", resumo_global)

    print("[OK] Fichas v2 geradas com sucesso.")
    for caminho, _ in resultados:
        print(f" - {caminho.name}")
    print(" - resumo_montagem_fichas_v2.json")


if __name__ == "__main__":
    main()
