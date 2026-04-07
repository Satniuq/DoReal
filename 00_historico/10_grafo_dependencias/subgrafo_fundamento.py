import json
import os
from collections import defaultdict, deque, Counter

# ========= PATHS =========
PATH_DEFINICOES = r"../09_Prompt/config/definicoes.json"
PATH_PROPOSICOES = r"../09_Prompt/data/extracao_ontologica_final.json"

OUT_DIR = r"data/subgrafos"
OUT_DOT = os.path.join(OUT_DIR, "subgrafo_fundamento.dot")
OUT_GRAPHML = os.path.join(OUT_DIR, "subgrafo_fundamento.graphml")
OUT_RESUMO = os.path.join(OUT_DIR, "subgrafo_fundamento_resumo.txt")

RAIZ = "D_REAL"

# ========= GRAFO =========
class Digrafo:
    def __init__(self):
        self.adj = defaultdict(set)
        self.rev = defaultdict(set)
        self.nodes = {}

    def add_node(self, n, **attrs):
        if n not in self.nodes:
            self.nodes[n] = {}
        self.nodes[n].update(attrs)

    def add_edge(self, u, v):
        if not isinstance(u, str) or not isinstance(v, str):
            return
        self.add_node(u)
        self.add_node(v)
        self.adj[u].add(v)
        self.rev[v].add(u)

    def edges(self):
        for u, vs in self.adj.items():
            for v in vs:
                yield (u, v)

# ========= UTIL =========
def ler_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ========= CONSTRUÇÃO =========
def construir_grafo():
    defs = ler_json(PATH_DEFINICOES)
    props = ler_json(PATH_PROPOSICOES)

    g = Digrafo()
    id_por_campo = {}

    for d in defs:
        did = d["id"]
        campo = d.get("campo", did)
        id_por_campo[campo] = did
        g.add_node(did, type="def", nivel=d.get("nivel", ""), label=f"{did}:{campo}")

    for d in defs:
        did = d["id"]
        for dep in d.get("depende_de", []):
            dep_id = id_por_campo.get(dep, dep)
            g.add_edge(did, dep_id)

    for p in props:
        pid = p.get("id_proposicao")
        if not pid:
            continue

        lv = p.get("localizacao_vertical", {})
        cp = lv.get("campo_principal")
        nivel = lv.get("nivel", "")

        g.add_node(pid, type="prop", nivel=nivel, label=pid)

        if cp:
            g.add_edge(pid, cp)

        for campo in ["dependencias", "gera", "degeneracao_possivel", "reintegracao"]:
            for dep in (p.get(campo) or []):
                g.add_edge(pid, dep)

    return g

# ========= SUBGRAFO =========
def subgrafo_ancestrais(g, raiz):
    visitados = set()
    stack = [raiz]

    while stack:
        n = stack.pop()
        if n in visitados:
            continue
        visitados.add(n)
        for anterior in g.rev.get(n, []):
            stack.append(anterior)

    sg = Digrafo()

    for n in visitados:
        sg.add_node(n, **g.nodes.get(n, {}))

    for u, v in g.edges():
        if u in visitados and v in visitados:
            sg.add_edge(u, v)

    return sg

# ========= EXPORT =========
def export_dot(g, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("digraph G {\n")
        f.write('  rankdir="LR";\n')
        for n, attrs in g.nodes.items():
            label = attrs.get("label", n)
            f.write(f'  "{n}" [label="{label}"];\n')
        for u, v in g.edges():
            f.write(f'  "{u}" -> "{v}";\n')
        f.write("}\n")

def export_graphml(g, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n')
        f.write('<graph edgedefault="directed">\n')

        for n in g.nodes:
            f.write(f'<node id="{n}"/>\n')

        i = 0
        for u, v in g.edges():
            f.write(f'<edge id="e{i}" source="{u}" target="{v}"/>\n')
            i += 1

        f.write('</graph></graphml>\n')

def resumo(g):
    total_nodes = len(g.nodes)
    total_edges = sum(len(vs) for vs in g.adj.values())

    tipos = Counter(attrs.get("type", "??") for attrs in g.nodes.values())

    return f"""SUBGRAFO FUNDAMENTO

Nós: {total_nodes}
Arestas: {total_edges}
Tipos: {dict(tipos)}
"""

# ========= MAIN =========
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    g = construir_grafo()
    sg = subgrafo_ancestrais(g, RAIZ)

    export_dot(sg, OUT_DOT)
    export_graphml(sg, OUT_GRAPHML)

    with open(OUT_RESUMO, "w", encoding="utf-8") as f:
        f.write(resumo(sg))

    print("Subgrafo Fundamento gerado com sucesso.")

if __name__ == "__main__":
    main()
