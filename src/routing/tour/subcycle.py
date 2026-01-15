def enumerate_subcycles(E, pairing):
    unused = set(E.edges(keys=True))
    cycles = []

    while unused:
        start = next(iter(unused))
        cycle = []
        e = start

        while True:
            if e not in unused:
                break

            unused.remove(e)
            cycle.append(e)

            u, v, k = e
            next_e = pairing.get((u, v, k), None)
            if next_e is None:
                raise RuntimeError(f"No pairing found for incoming edge {e} at node {v}")

            e = next_e

            if e == start:
                break

        cycles.append(cycle)

    return cycles

def _cycle_nodes(edge_cycle):
    nodes = [edge_cycle[0][0]]
    for u, v, k in edge_cycle:
        nodes.append(v)
    return nodes


def _rotate_cycle_to_start_at_node(edge_cycle, node):
    nodes = _cycle_nodes(edge_cycle)
    m = len(edge_cycle)

    for t in range(m):
        if edge_cycle[t][0] == node:
            return edge_cycle[t:] + edge_cycle[:t]

    for t in range(m):
        if nodes[t] == node:
            return edge_cycle[t % m:] + edge_cycle[:t % m]
    raise ValueError("Node not found in cycle")


def merge_subcycles(cycles):
    if not cycles:
        return []

    tour = cycles[0]
    remaining = cycles[1:]

    while remaining:
        tour_nodes = set(_cycle_nodes(tour))

        merged = False
        for idx, cy in enumerate(remaining):
            cy_nodes = set(_cycle_nodes(cy))
            common = tour_nodes.intersection(cy_nodes)
            if not common:
                continue

            x = next(iter(common))  # pick any common node
            tour_rot = _rotate_cycle_to_start_at_node(tour, x)
            cy_rot = _rotate_cycle_to_start_at_node(cy, x)

            tour = tour_rot[:1] + cy_rot + tour_rot[1:]
            remaining.pop(idx)
            merged = True
            break

        if not merged:
            raise RuntimeError(
                "Could not merge remaining subcycles: no common nodes found. "
                "This suggests cycles lie in disjoint node sets."
            )

    return tour