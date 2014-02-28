import pickle
import graph
from enumerate_walkways import enumerate_walkways

weps = pickle.load(open("../data/saarland-130822.5kmh.weps.out"))
osm_id_map = pickle.load(open("../data/saarland-130822.5kmh.id_map.out"))
forest_nodes_osm_ids = pickle.load(open("../data/saarland-130822.5kmh.forest_ids.out"))
g = pickle.load(open("../data/saarland-130822.5kmh.graph.out"))
nodeinfo = pickle.load(open("../data/saarland-130822.5kmh.nodeinfo.out"))

forest_polygons = pickle.load(open("../data/saarland-130822.forest_polygons.out"))
d_edge = pickle.load(open("../data/saarland-130822.edge_distance.out"))

# ...
wep_nodes = [osm_id_map[osm_id] for osm_id in weps]
wep_nodes_set = set(wep_nodes)

n = len(g.nodes)
outside_nodes = g.nodes - set([osm_id_map[id] for id in forest_nodes_osm_ids])
outside_nodes -= wep_nodes_set
g.remove_partition(outside_nodes)
print n, len(g.nodes)

''' Contract binary nodes except WEPs. '''
n = len(g.nodes)
g.contract_binary_nodes(exclude=wep_nodes)
print n, len(g.nodes)

#walkways = enumerate_walkways(g, node, target_nodes=wep_nodes_set, \
    #    cost_limit=limit, local_cycle_depth=5, edgedistance=d_edge)

