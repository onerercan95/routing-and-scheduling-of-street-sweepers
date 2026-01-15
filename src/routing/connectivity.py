import networkx as nx
from src.routing.transportation import *
from src.routing.utils import *

def get_weak_components(H):
    return list(nx.weakly_connected_components(H))

def choose_representatives(components):
    return [next(iter(comp)) for comp in components]

def build_component_graph(F, reps, weight_attr="cost"):
    CG = nx.Graph()

    for r in reps:
        CG.add_node(r)

    for i in range(len(reps)):
        for j in range(i + 1, len(reps)):
            u, v = reps[i], reps[j]
            try:
                dist = nx.shortest_path_length(F, u, v, weight=weight_attr)
                CG.add_edge(u, v, weight=dist)
            except nx.NetworkXNoPath:
                pass

    return CG

def connect_components_to_form_E(H, F, components, weight_attr="cost"):

    if len(components) <= 1:
        return H.copy()

    reps = choose_representatives(components)
    CG = build_component_graph(F, reps, weight_attr=weight_attr)

    MST = nx.minimum_spanning_tree(CG, weight="weight")

    E = H.copy()

    for u, v in MST.edges():
        path = nx.shortest_path(F, u, v, weight=weight_attr)
        for a, b in zip(path[:-1], path[1:]):
            k = pick_min_cost_edge_key(F, a, b, weight_attr=weight_attr)
            data = F[a][b][k].copy()
            data["mode"] = "DEADHEAD"
            data["is_component_connector"] = True
            E.add_edge(a, b, **data)

    ensure_node_coordinates(E, F)

    return E