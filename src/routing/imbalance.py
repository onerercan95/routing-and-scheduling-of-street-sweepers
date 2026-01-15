import networkx as nx

# Finds imbalances in graph and returns a dictionary of nodes whose imbalance info are stored.
def compute_node_imbalance(G):
    imbalance = {}

    for node in G.nodes:
        in_deg = G.in_degree(node)
        out_deg = G.out_degree(node)
        diff = in_deg - out_deg

        if diff == 0:
            node_type = "balanced"
        elif diff > 0:
            node_type = "supply"
        else:
            node_type = "demand"

        imbalance[node] = {
            "in": in_deg,
            "out": out_deg,
            "imbalance": diff,
            "type": node_type
        }

    return imbalance