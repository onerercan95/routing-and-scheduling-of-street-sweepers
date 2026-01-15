import networkx as nx

def make_balanced_H(G, F, imbalance_data, weight_attr="cost"):
    # Make sure that weight_attr is stored in edges. Some might not have it.
    ensure_edge_weight(F, weight_attr=weight_attr)
    ensure_edge_weight(G, weight_attr=weight_attr)

    # Extract supply and demand nodes
    supplies, demands = build_supply_demand(imbalance_data)

    # If there are no supply or demand nodes, G is already balanced.
    if not supplies and not demands:
        return G.copy(), {"transport_cost": 0}

    # Calculate all possible shortest paths
    dist, paths = calculate_supply_to_demand_paths(F, supplies, demands, weight_attr=weight_attr)

    # Check unreachable supply and demand nodes
    un_s, un_d = check_reachability(supplies, demands, dist)
    
    # Solve minimum cost flow problem for supply and demand nodes
    cost, flow_dict = solve_transportation_min_cost_flow(supplies, demands, dist)

    # Build H graph from given flow G, F and flow dictionary
    H = build_H_from_flow(G, F, flow_dict, paths, weight_attr=weight_attr)

    return H, {"transport_cost": cost, "supplies": supplies, "demands": demands}

def build_H_from_flow(G, F, flow, paths, weight_attr="cost"):
    H = G.copy()

    # Iterate through every entry in flow dict
    for s_node in flow:
        # Make sure that it is a supply node
        if not (isinstance(s_node, tuple) and s_node[0] == "S"):
            continue
        s = s_node[1]

        # Go through each demand node
        for d_node, amount in flow[s_node].items():
            # Make sure demand is positive
            if amount <= 0:
                continue

            # Make sure it is a demand node
            if not (isinstance(d_node, tuple) and d_node[0] == "D"):
                continue
            d = d_node[1]

            # Nodes from s to d
            node_path = paths[s][d]

            # Add edges from s to d for given amount
            for _ in range(amount):
                # [A, B, C, D] -> [(A,B) (B,C) (C,D)]
                for a, b in zip(node_path[:-1], node_path[1:]):
                    # Get the min cost edge. There might be multiple parallel edges so we need the min cost one
                    k = pick_min_cost_edge_key(F, a, b, weight_attr=weight_attr)

                    # Copy the data of cheapest edge
                    data = F[a][b][k].copy()

                    # Mark the edge data as deadhead
                    data["mode"] = "DEADHEAD"
                    data["is_deadhead_added"] = True

                    # Add the edge even if its parallel
                    H.add_edge(a, b, **data)

    return H


def pick_min_cost_edge_key(F, u, v, weight_attr="cost"):
    best_k = None
    best_w = float("inf")
    for k, data in F[u][v].items():
        w = float(data.get(weight_attr, data.get("length", 1.0)))
        if w < best_w:
            best_w = w
            best_k = k
    return best_k

def solve_transportation_min_cost_flow(supplies, demands, dist):
    # Get all supply-demand node pairs that are in shortest dist list
    reachable_pairs = []

    for s in supplies:
        for d in demands:
            if d in dist.get(s, {}):
                reachable_pairs.append((s, d))

    # All unique supply nodes in reachable pairs
    reachable_supplies = {s for s, _ in reachable_pairs}

    # All unique demand nodes in reachable pairs
    reachable_demands = {d for _, d in reachable_pairs}

    # Transportation graph. networx.network_simplex(T) function requires a graph that includes
    # nodes and edges with certain attributes. Nodes have to include "demand" attribute.
    # Negative demand means it is a supply node and positive demand means it is a demand node.
    # Edges requite weight and capacity. Weight is the cost of the path from s to d. Capacity
    # is there to limit how many times we can use this path for transportation problem.
    # I made capaciy 10**9 so that it is basically unlimited.
    T = nx.DiGraph()

    for s, amount in supplies.items():
        if s in reachable_supplies:
            T.add_node(("S", s), demand=-amount)

    for d, amount in demands.items():
        if d in reachable_demands:
            T.add_node(("D", d), demand=amount)

    for s, d in reachable_pairs:
        T.add_edge(
            ("S", s),
            ("D", d),
            weight=int(dist[s][d]),
            capacity=10**9,
        )

    # Calculates total cost and gives a flot dictionary. 
    # Ex: 
    # T.add_edge("A","B", weight=5)
    # T.add_edge("B","C", weight=2)
    # flow_dict = {"A": {"B": 3},"B": {"C": 3}}
    # cost = 5 * 3 + 2 * 3 = 21
    cost, flow_dict = nx.network_simplex(T)
    return cost, flow_dict

# Calculates and returns shortest distances and path nodes from all nodes to all nodes in F
# Returns: dists and paths matrices. Ex: dists[s][d], paths[s][d]
def calculate_supply_to_demand_paths(F, supplies, demands, weight_attr="cost"):
    demand_nodes = list(demands.keys())

    dists = {} # Shortest path cost from s to d. dists[s][d]
    paths = {} # Nodes that form tha path s to d. paths[s][d]

    # Iterate over supply nodes
    for s in supplies.keys():
        # This calculates the shortest distance and paths from node s to each node in F
        dists_s, paths_s = nx.single_source_dijkstra(F, source=s, weight=weight_attr)

        dists[s] = {}
        paths[s] = {}

        # Iterate over demand nodes and record distance and path nodes if the path exists from s to d
        for d in demand_nodes:
            if d in dists_s:
                dists[s][d] = dists_s[d]
                paths[s][d] = paths_s[d]

    return dists, paths


def build_supply_demand(imbalance_data):
    supplies = {}
    demands = {}

    for node, info in imbalance_data.items():
        diff = info["imbalance"]
        if diff > 0:
            supplies[node] = diff
        elif diff < 0:
            demands[node] = -diff

    return supplies, demands

# Checks if there are unreachable supply and demand nodes.
# Returns: Uncreachable supply and demand node lists
def check_reachability(supplies, demands, dist):
    unreachable_supplies = []
    unreachable_demands = []

    for s in supplies:
        if s not in dist or len(dist[s]) == 0:
            unreachable_supplies.append(s)

    for d in demands:
        if not any(d in dist.get(s, {}) for s in supplies):
            unreachable_demands.append(d)

    return unreachable_supplies, unreachable_demands

# Adds weight_attr data if it does not exist in edges
def ensure_edge_weight(G, weight_attr="cost"):
    for u, v, k, data in G.edges(keys=True, data=True):
        if weight_attr not in data:
            data[weight_attr] = float(data.get("length", 1.0))