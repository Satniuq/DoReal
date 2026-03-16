#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
06_preparar_fecho_manual_corredor.py

Objetivo
--------
A partir de um ficheiro `fichas_v2_corredor_*.json`, gerar um ficheiro
`fecho_manual_corredor_*.json` mais enxuto e diretamente utilizável para
fecho filosófico manual do corredor.

O script:
- lê um ou vários ficheiros `fichas_v2_corredor_*.json`;
- reduz cada ficha ao núcleo de decisão final;
- transporta automaticamente o que já foi consolidado nas fichas v2;
- cria campos vazios para preenchimento manual;
- gera também um resumo global da preparação do fecho manual.

Uso típico
----------
    python 06_preparar_fecho_manual_corredor.py

Ou então:
    python 06_preparar_fecho_manual_corredor.py /caminho/para/fichas_v2_corredor_P33_P37.json

Saídas
------
- fecho_manual_corredor_P33_P37.json
- fecho_manual_corredor_P25_P30.json
- fecho_manual_corredor_P42_P48.json
- fecho_manual_corredor_P50.json
- resumo_preparacao_fecho_manual.json
"""

from __future__ import annotations

import json
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSAO_SCRIPT = "1.0.0"
ENCODING = "utf-8"


# ============================================================
# Utilitários base
# ============================================================

def agora_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def carregar_json(path: Path) -> Any:
    with path.open("r", encoding=ENCODING) as f:
        return json.load(f)



def guardar_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=ENCODING) as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")



def normalizar_lista(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []



def normalizar_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}



def texto_limpo(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()



def slugify(texto: str) -> str:
    texto = texto_limpo(texto).lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    texto = re.sub(r"_+", "_", texto).strip("_")
    return texto or "sem_nome"



def inferir_corredor_do_nome(path: Path) -> str:
    m = re.search(r"(P\d+(?:_P\d+)?)", path.stem)
    return m.group(1) if m else path.stem


def sanitizar_nome_corredor(valor: str) -> str:
    v = texto_limpo(valor)
    if not v:
        return ""
    m = re.search(r"(P\d+(?:_P\d+)?)", v)
    if m:
        return m.group(1)
    v = re.sub(r"^corredor_", "", v, flags=re.IGNORECASE)
    v = re.sub(r"_organizado$", "", v, flags=re.IGNORECASE)
    return v


# ============================================================
# Lógica de redução / seleção
# ============================================================

def score_fragmento(fragmento: Dict[str, Any]) -> int:
    prioridade = texto_limpo(fragmento.get("prioridade_de_aproveitamento")).lower()
    forca = texto_limpo(fragmento.get("forca_logica_estimada")).lower()
    estado = texto_limpo(fragmento.get("estado_argumentativo")).lower()
    precisa_reescrita = bool(fragmento.get("requer_reescrita"))
    precisa_densificacao = bool(fragmento.get("requer_densificacao"))
    reconstrucao_forte = bool(fragmento.get("necessita_reconstrucao_forte"))

    score = 0

    mapa_prioridade = {
        "alta": 40,
        "media": 20,
        "baixa": 5,
        "muito_provisorio_ou_instavel": 0,
    }
    mapa_forca = {
        "alta": 25,
        "media": 15,
        "baixa": 5,
    }

    score += mapa_prioridade.get(prioridade, 0)
    score += mapa_forca.get(forca, 0)

    if "argumento" in estado:
        score += 10
    elif "formulacao" in estado:
        score += 6
    elif "exploracao" in estado:
        score += 2

    if not precisa_reescrita:
        score += 5
    if not precisa_densificacao:
        score += 4
    if not reconstrucao_forte:
        score += 3

    # presença de resumo local ou justificação local ajuda muito no fecho manual
    if texto_limpo(fragmento.get("resumo_local_no_corredor")):
        score += 4
    if texto_limpo(fragmento.get("justificacao_local_no_corredor")):
        score += 6

    return score



def reduzir_fragmento(fragmento: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "fragment_id": texto_limpo(fragmento.get("fragment_id")),
        "origem_id": texto_limpo(fragmento.get("origem_id")),
        "prioridade_de_aproveitamento": texto_limpo(fragmento.get("prioridade_de_aproveitamento")),
        "forca_logica_estimada": texto_limpo(fragmento.get("forca_logica_estimada")),
        "estado_argumentativo": texto_limpo(fragmento.get("estado_argumentativo")),
        "forma_de_inferencia": texto_limpo(fragmento.get("forma_de_inferencia")),
        "descricao_funcional_curta": texto_limpo(fragmento.get("descricao_funcional_curta")),
        "resumo_local_no_corredor": texto_limpo(fragmento.get("resumo_local_no_corredor")),
        "justificacao_local_no_corredor": texto_limpo(fragmento.get("justificacao_local_no_corredor")),
        "requer_reescrita": bool(fragmento.get("requer_reescrita")),
        "requer_densificacao": bool(fragmento.get("requer_densificacao")),
        "necessita_reconstrucao_forte": bool(fragmento.get("necessita_reconstrucao_forte")),
    }



def selecionar_fragmentos(lista: List[Dict[str, Any]], max_itens: int = 8) -> List[Dict[str, Any]]:
    vistos = set()
    ordenados = sorted(
        [x for x in lista if isinstance(x, dict)],
        key=lambda x: (-score_fragmento(x), texto_limpo(x.get("fragment_id"))),
    )

    saida: List[Dict[str, Any]] = []
    for frag in ordenados:
        frag_id = texto_limpo(frag.get("fragment_id"))
        if not frag_id or frag_id in vistos:
            continue
        vistos.add(frag_id)
        saida.append(reduzir_fragmento(frag))
        if len(saida) >= max_itens:
            break
    return saida



def lista_textual_limpa(itens: Any) -> List[str]:
    saida: List[str] = []
    if not isinstance(itens, list):
        return saida
    for item in itens:
        t = texto_limpo(item)
        if t:
            saida.append(t)
    return saida



def construir_ficha_fecho_manual(ficha: Dict[str, Any]) -> Dict[str, Any]:
    justificativos = normalizar_lista(ficha.get("fragmentos_justificativos"))
    mediacionais = normalizar_lista(ficha.get("fragmentos_mediacionais"))
    bloqueio = normalizar_lista(ficha.get("fragmentos_de_bloqueio"))
    ilustrativos = normalizar_lista(ficha.get("fragmentos_ilustrativos"))
    resumo_fragmentario = normalizar_dict(ficha.get("resumo_fragmentario"))
    materiais_ref = normalizar_dict(ficha.get("materiais_de_referencia"))

    numero = ficha.get("numero")
    proposicao_id = texto_limpo(ficha.get("proposicao_id")) or f"P{numero}"
    corredor = sanitizar_nome_corredor(texto_limpo(ficha.get("corredor")))

    return {
        "proposicao_id": proposicao_id,
        "numero": numero,
        "corredor": corredor,
        "bloco_id": texto_limpo(ficha.get("bloco_id")),
        "bloco_titulo": texto_limpo(ficha.get("bloco_titulo")),
        "proposicao_atual": texto_limpo(ficha.get("proposicao_atual")),
        "descricao_curta": texto_limpo(ficha.get("descricao_curta")),
        "depende_de": normalizar_lista(ficha.get("depende_de")),
        "prepara": normalizar_lista(ficha.get("prepara")),
        "estado_estrutural_atual": texto_limpo(ficha.get("estado_estrutural_atual")),
        "funcao_no_percurso": texto_limpo(ficha.get("funcao_no_percurso")),
        "nucleo_que_se_mantem": texto_limpo(ficha.get("nucleo_que_se_mantem")),
        "defice_principal": texto_limpo(ficha.get("defice_principal")),
        "justificacao_atual": texto_limpo(ficha.get("justificacao_atual")),
        "mediacoes_em_falta": lista_textual_limpa(ficha.get("mediacoes_em_falta")),
        "objecoes_a_bloquear": lista_textual_limpa(ficha.get("objecoes_a_bloquear")),
        "decisao_editorial_v2": texto_limpo(ficha.get("decisao_editorial_v2")),
        "formulacao_v2_provisoria": texto_limpo(ficha.get("formulacao_v2_provisoria")),
        "ponte_com_passo_anterior_base": texto_limpo(ficha.get("ponte_com_passo_anterior")),
        "ponte_com_passo_seguinte_base": texto_limpo(ficha.get("ponte_com_passo_seguinte")),
        "observacoes_de_trabalho": texto_limpo(ficha.get("observacoes_de_trabalho")),
        "resumo_fragmentario": resumo_fragmentario,
        "materiais_de_referencia": {
            "teses_principais": lista_textual_limpa(materiais_ref.get("teses_principais")),
            "justificacoes_novas": lista_textual_limpa(materiais_ref.get("justificacoes_novas")),
            "propostas_de_nova_formulacao": lista_textual_limpa(materiais_ref.get("propostas_de_nova_formulacao")),
            "observacoes_finais": lista_textual_limpa(materiais_ref.get("observacoes_finais")),
        },
        "fragmentos_selecionados": {
            "justificativos": selecionar_fragmentos(justificativos, max_itens=8),
            "mediacionais": selecionar_fragmentos(mediacionais, max_itens=6),
            "de_bloqueio": selecionar_fragmentos(bloqueio, max_itens=6),
            "ilustrativos": selecionar_fragmentos(ilustrativos, max_itens=4),
        },
        "campos_para_fecho_manual": {
            "formulacao_v2_final": "",
            "justificacao_expandida_final": [],
            "ponte_entrada": "",
            "ponte_saida": "",
            "objecoes_bloqueadas_final": [],
            "fragmentos_selecionados_finais": {
                "justificativos": [],
                "mediacionais": [],
                "de_bloqueio": [],
                "ilustrativos": [],
            },
            "nota_editorial_final": "",
        },
    }


# ============================================================
# Processamento de ficheiros
# ============================================================

def encontrar_inputs(args: List[str], base_dir: Path) -> List[Path]:
    if args:
        paths = [Path(a).expanduser().resolve() for a in args]
        return [p for p in paths if p.is_file()]

    candidatos = sorted(base_dir.glob("fichas_v2_corredor_*.json"))
    return [p.resolve() for p in candidatos if p.is_file()]



def nome_saida_para(path_input: Path, meta: Dict[str, Any]) -> str:
    corredor = sanitizar_nome_corredor(texto_limpo(meta.get("corredor"))) or inferir_corredor_do_nome(path_input)
    return f"fecho_manual_corredor_{corredor}.json"



def processar_ficheiro(path_input: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    data = carregar_json(path_input)
    if not isinstance(data, dict):
        raise ValueError(f"O ficheiro {path_input.name} não contém um objeto JSON no topo.")

    meta = normalizar_dict(data.get("meta"))
    resumo = normalizar_dict(data.get("resumo"))
    fichas = normalizar_lista(data.get("fichas"))

    fichas_fecho = [construir_ficha_fecho_manual(f) for f in fichas if isinstance(f, dict)]

    corredor = sanitizar_nome_corredor(texto_limpo(meta.get("corredor"))) or inferir_corredor_do_nome(path_input)
    titulo = texto_limpo(meta.get("titulo")) or f"Corredor {corredor}"

    total_fragmentos_selecionados = 0
    for ficha in fichas_fecho:
        sel = normalizar_dict(ficha.get("fragmentos_selecionados"))
        total_fragmentos_selecionados += sum(len(normalizar_lista(v)) for v in sel.values())

    saida = {
        "meta": {
            "gerado_em_utc": agora_utc_iso(),
            "versao_script": VERSAO_SCRIPT,
            "ficheiro_origem": path_input.name,
            "corredor": corredor,
            "titulo": titulo,
            "descricao": f"Ficheiro de fecho manual preparado a partir de {path_input.name}.",
            "objetivo": "Separar o núcleo de decisão filosófica final do material já preparado nas fichas v2.",
        },
        "resumo": {
            "total_fichas": len(fichas_fecho),
            "total_fragmentos_selecionados": total_fragmentos_selecionados,
            "distribuicao_necessidade_principal": deepcopy(normalizar_dict(resumo.get("distribuicao_necessidade_principal"))),
            "distribuicao_acao_recomendada": deepcopy(normalizar_dict(resumo.get("distribuicao_acao_recomendada"))),
            "top_proposicoes_por_carga_fragmentaria": deepcopy(normalizar_lista(resumo.get("top_proposicoes_por_carga_fragmentaria"))),
        },
        "instrucoes_de_preenchimento": [
            "Preencher 'formulacao_v2_final' com a formulação canónica já estabilizada da proposição.",
            "Usar 'justificacao_expandida_final' para listar, em frases curtas, o encadeamento justificativo final.",
            "Preencher 'ponte_entrada' e 'ponte_saida' como transições dedutivas explícitas entre passos.",
            "Em 'objecoes_bloqueadas_final', listar apenas as objeções efetivamente tratadas no fecho final.",
            "Em 'fragmentos_selecionados_finais', escolher apenas os fragmentos que entram na redação ou na sustentação estrutural final.",
            "Usar 'nota_editorial_final' para decidir se a proposição entra como núcleo, mediação ou apoio expositivo.",
        ],
        "fichas": fichas_fecho,
    }

    resumo_local = {
        "ficheiro_origem": path_input.name,
        "ficheiro_saida": nome_saida_para(path_input, meta),
        "corredor": corredor,
        "total_fichas": len(fichas_fecho),
        "total_fragmentos_selecionados": total_fragmentos_selecionados,
    }
    return saida, resumo_local



def main() -> int:
    base_dir = Path(__file__).resolve().parent
    inputs = encontrar_inputs(sys.argv[1:], base_dir)

    if not inputs:
        print("Nenhum ficheiro 'fichas_v2_corredor_*.json' encontrado.")
        return 1

    resumo_global = {
        "gerado_em_utc": agora_utc_iso(),
        "versao_script": VERSAO_SCRIPT,
        "ficheiros_processados": [],
        "total_corredores": 0,
        "total_fichas": 0,
        "total_fragmentos_selecionados": 0,
    }

    for path_input in inputs:
        saida, resumo_local = processar_ficheiro(path_input)
        nome_saida = resumo_local["ficheiro_saida"]
        path_saida = path_input.with_name(nome_saida)
        guardar_json(path_saida, saida)

        resumo_global["ficheiros_processados"].append(resumo_local)
        resumo_global["total_corredores"] += 1
        resumo_global["total_fichas"] += int(resumo_local["total_fichas"])
        resumo_global["total_fragmentos_selecionados"] += int(resumo_local["total_fragmentos_selecionados"])

        print(f"[OK] {path_input.name} -> {path_saida.name}")

    guardar_json(base_dir / "resumo_preparacao_fecho_manual.json", resumo_global)
    print(f"[OK] resumo_preparacao_fecho_manual.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
