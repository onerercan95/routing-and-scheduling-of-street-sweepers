from src.routing.tour.pair import *
from src.routing.tour.subcycle import *

def generate_subcycle_tour(E):
    pairing = compute_local_pairings(E)
    cycles = enumerate_subcycles(E, pairing)
    tour = merge_subcycles(cycles)

    return tour, cycles