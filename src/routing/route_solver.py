import networkx as nx

from src.routing.imbalance import *
from src.routing.transportation import *
from src.routing.utils import *
from src.routing.connectivity import *
from src.routing.tour.tour import *
from src.routing.force_balance import *
from src.routing.split_routes import *

# F = Full road network
# G = Route-First -> Network after regulations, Cluster-First -> Network of one cluster
def solve_route(F, G, route_time):
    imbalance = compute_node_imbalance(G)

    # Solve transportation problem and make all nodes in G balanced (H can include streets from outside of G network)
    H, info = make_balanced_H(G, F, imbalance, weight_attr="cost")

    ensure_node_coordinates(H, F)

    components = get_weak_components(H)

    E = connect_components_to_form_E(H, F, components, weight_attr="cost")

    force_balance(E, F)

    tour, cycles = generate_subcycle_tour(E)

    # print("[INFO] subcycles:", len(cycles))
    # print("[INFO] tour edges:", len(tour))

    max_route_time = route_time * 3600
    routes = split_giant_tour(E, tour, max_route_time)

    return E, H, routes, tour
