import warnings
import urllib3
import time
import os
from src.data_loading.data_loader import *
from src.visualizing.visualizer import *
from src.routing.route_solver import *
from src.routing.utils import *
from src.subnetwork.subnetwork import *
from src.data_loading.json_loader import *


if __name__ == "__main__":
    warnings.filterwarnings(action="ignore")
    warnings.simplefilter(action="ignore", category=FutureWarning)

    config = load_config()

    place = config["place"]
    schedule = config["schedule"]

    folder = "out/maps/" + place
    if os.path.exists(folder):
        for file in os.listdir(folder):
            os.remove(os.path.join(folder, file))

    F = load_street_network(place)

    """
    print("Weak components:", nx.number_weakly_connected_components(F))
    print("Strong components:", nx.number_strongly_connected_components(F))
    """
    blockIndex = 0
    for block in schedule:
        days = block["days"]
        start, end = block["time_window"]
        allowed_roads = set(block["road_types"])

        output_path_f = folder + "/" + str(blockIndex) + "_01-Full Street Network-F.html"
        output_path_k = folder + "/" + str(blockIndex) + "_02-Subnetwork-K.html"
        output_path_tour = folder + "/" + str(blockIndex) + "_03-Tour.html"
        output_path_route_first = folder + "/" + str(blockIndex) + "_04-Route First Routes.html"
        output_path_imbalance_k = folder + "/" + str(blockIndex) + "_05-imbalance_K.html"
        output_path_imbalance_h = folder + "/" + str(blockIndex) + "_06-imbalance_H.html"
        output_path_imbalance_e = folder + "/" + str(blockIndex) + "_07-imbalance_E.html"

        diag_start_t = time.perf_counter()
        K = extract_K(F, allowed_roads)
        G = K

        for u,v,k in G.edges(keys=True):
            G[u][v][k]["mode"] = "SWEEP"

        route_time = hours_between(start, end)
        E, H, routes, tour = solve_route(F, G, route_time)
        diag_end_t = time.perf_counter()
        
        plot_interactive_roads_hierarchical(F, output_path=output_path_f)
        plot_F_and_K(F, K, output_path=output_path_k)
        visualize_tour_and_routes(E, tour, routes, output_path_route_first)
        visualize_giant_tour(E, tour, output_path_tour)
        print(f"[INFO] {days} {start}-{end} → {allowed_roads} - Runtime ({diag_end_t - diag_start_t:.6f}s)")

        """
        print("F edges:", F.number_of_edges())
        print("K edges:", K.number_of_edges())
        print("G edges:", G.number_of_edges())
        print("E edges:", E.number_of_edges())
        print("Tour edges:", len(tour))
        print("Sweep edges:", sum(1 for u,v,k in E.edges(keys=True) if E[u][v][k].get("mode")=="SWEEP"))
        print("Deadhead edges:", sum(1 for u,v,k in E.edges(keys=True) if E[u][v][k].get("mode")=="DEADHEAD"))
        
        missing = set(E.edges(keys=True)) - set(tour)
        print("Missing:", len(missing))
        print(list(missing)[:10])
        """

        imbalance_K = compute_node_imbalance(K)
        plot_H_node_imbalance(K, imbalance_K, output_path=output_path_imbalance_k)

        imbalance_H = compute_node_imbalance(H)
        plot_H_node_imbalance(H, imbalance_H, output_path=output_path_imbalance_h)

        imbalance_E = compute_node_imbalance(E)
        plot_H_node_imbalance(E, imbalance_E, output_path=output_path_imbalance_e)
        
        summary, route_rows = compute_stats(E, routes)

        write_stats_html(
            summary,
            route_rows,
            title=f"{blockIndex}_Statistics",
            output_path=f"{folder}/{blockIndex}_Statistics.html"
        )
        """
        for i,r in enumerate(routes):
            print("Route",i+1, route_stats(E,r))
        print(compute_fleet_requirements(E, routes))
        """
        blockIndex += 1