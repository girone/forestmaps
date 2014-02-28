''' Loads everything needed for debugging with saarland. '''
import pickle
import graph
import visual_grid
g = pickle.load(open("../data/saarland-130822.5kmh.graph.out"))
osm_id_map = pickle.load(open("../data/saarland-130822.5kmh.id_map.out"))
weps = pickle.load(open("../data/saarland-130822.5kmh.weps.out"))
forest_polygons = \
    pickle.load(open("../data/saarland-130822.forest_polygons.out"))
nodeinfo = pickle.load(open("../data/saarland-130822.5kmh.nodeinfo.out"))
#visual_grid.visualize_nodes(g, nodeinfo, set([316033, 59860, 139821]), \
#    inset=1.0, forest=forest_polygons)
