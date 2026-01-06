import networkx as nx

G = nx.Graph()

for f in data:
    G.add_node(f["id"])

for d in [conceitos, eixos, teses, tensoes]:
    for f, items in d.items():
        for other, other_items in d.items():
            if f != other and items & other_items:
                G.add_edge(f, other)

nx.write_gexf(G, "../output/grafo.gexf")
