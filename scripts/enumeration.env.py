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

import contraction
positions = [nodeinfo[id].pos for id in g.nodes]
c = contraction.ClusterContractionAlgorithm(g, positions,
    intra_dist=30.0, inter_dist=50.)
c.contract_graph(exclude_nodes=set(wep_nodes))
print n, len(g.nodes)

import visual_grid
osm_ids = [459952293,459952291,459952290,459952288,459952285,459952284,459952283,459952281,459952280,369977243,369977242,369977241,369977239,369977237,369977236,369977226,369977225,369977223,369977222,369977221,369977220,369977219,369977218,369977217,369977216,369977215,369977214,369977213,369977212,369977211,369977210,369977209,369977208,369977207,369977206,369977205,369977204,369977203,369977197,369977195,369977194,2392004676,2392004675,2392004674,2392004673,2392004672,2392004671,2392004670,2392004669,2392004668,2392004667,2392004666,2392004665,2392004664,2392004663,2392004662,2392004661,2392004660,2392004659,2392004658,2392004657,2392004656,2392004655,2392004654,2392004653,2392004652,2392004651,2392004650,2392004649,2392004648,2392004647,2392004646,2392004645,2392004644,2392004643,2392004642,2392004641,2392004640,2392004639,2392004638,2392004637,2392004636,2392004635,2392004634,2392004633,2392004632,2392004631,369977193,369977224,369977228,369977229,369977230,369977231,369977232,369977233,369977234,369977235,459952287,789509393,369977192,369977190,2392004678,2392004677,789509390,789509391,323717865,683448368,323717859,369977186,683448370,369977191,369977279]
a = [osm_id_map[id] for id in osm_ids]
visual_grid.visualize_nodes(g, nodeinfo, set(a), inset=0.0, forest=forest_polygons)

#walkways = enumerate_walkways(g, node, target_nodes=wep_nodes_set, \
    #    cost_limit=limit, local_cycle_depth=5, edgedistance=d_edge)

