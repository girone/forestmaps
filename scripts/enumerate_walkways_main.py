'''
    Entry point.

    For every WEP, this enumerates walkways in the forest which fulfill a set of
    conditions.

    Usage:
'''
USAGE = \
    'enumerate_forest_walkways.py <WEPS> <OSM_ID_MAP> <FOREST_NODE_IDS> ' \
    '<GRAPH> <NODEINFO>'

import pickle
import sys
import os.path
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from enumerate_walkways import WayTree, WayGenerator, enumerate_walkways
import visual_grid
import edgedistance
from contraction import SimpleContractionAlgorithm


def main():
  if len(sys.argv) < 6:
    print USAGE
    exit(1)
  weps = pickle.load(open(sys.argv[1]))
  osm_id_map = pickle.load(open(sys.argv[2]))
  forest_nodes_osm_ids = pickle.load(open(sys.argv[3]))
  g = pickle.load(open(sys.argv[4]))
  nodeinfo = pickle.load(open(sys.argv[5]))

  forest_polygons = pickle.load(open("data/saarland-130822.forest_polygons.out"))

  ''' Set parameters '''
  limit = 20*60

  wep_nodes = [osm_id_map[osm_id] for osm_id in weps]
  wep_nodes_set = set(wep_nodes)

  ''' Concentrate way generation on forests '''
  n = len(g.nodes)
  outside_nodes = g.nodes - set([osm_id_map[id] for id in forest_nodes_osm_ids])
  outside_nodes -= wep_nodes_set
  g.remove_partition(outside_nodes)
  print n, len(g.nodes)

  ''' Contract binary nodes except WEPs. '''
  n = len(g.nodes)
  g.contract_binary_nodes(exclude=wep_nodes)
  print n, len(g.nodes)

  ''' Simplify the graph by contraction of nodes with only short arcs. '''
  n = len(g.nodes)
  c = SimpleContractionAlgorithm(g, 20.0)  # 10.0 seconds @ 5 km/h ~= 14m
  c.contract_graph(exclude_nodes=wep_nodes)
  print n, len(g.nodes)

  ''' Compute the distance to the edge of the woods (or load it) '''
  print 'Computing edge distance...'
  name = "data/saarland-130822.edge_distance.out"
  if os.path.exists(name):
    d_edge = pickle.load(open(name))
  else:
    d_edge = edgedistance.compute_edge_distance(g, wep_nodes, limit/2)
    pickle.dump(d_edge, open(name, 'w'))
  print 'Done!'


  ''' Generate the walkways from every wep to all weps (within distance) '''
  count = 0
  for node in wep_nodes:
    count += 1
    walkways_and_distances = enumerate_walkways(g, node, target_nodes=wep_nodes_set, 
        cost_limit=limit, local_cycle_depth=5, edge_distance=d_edge)
    print "%d of %d ways generated" % (count, len(wep_nodes))
    #print walkways
    print " %d  ways found with cost limit %.1f min." % (len(walkways_and_distances), limit/60.)
    if len(walkways_and_distances) == 0:
      continue

    ''' Evaluate the walkways (compute attractiveness), sort by distance. '''
    #metric = evaluate(walkways)
    walkways = \
        [(w,d) for (d,w) in sorted([(d,w) for (w,d) in walkways_and_distances])]
    ma = max([d for (w,d) in walkways])
    mi = min([d for (w,d) in walkways])
    su = sum([d for (w,d) in walkways])

    ''' Distribute the population weight over the paths. '''
    n_bins = 50
    bin_size = (ma - mi) / float(n_bins - 1.0)
    distance_distr = np.zeros(n_bins)
    for (w,d) in walkways:
      print (d-mi)/bin_size, n_bins
      distance_distr[(d-mi)/bin_size] += 1.0
    plt.bar(np.arange(n_bins), distance_distr)
    plt.show()
    spread = signal.gaussian(n_bins, std=5)  #  TODO(Jonas): Use sth. senseful.
    spread[0:-1] *= 1. / sum(spread)  # normalize 
    result = distance_distr * spread
    normalizer = float(su) / sum(result)  # normalize the joint distribution
    result[0:-1] *= normalizer

    plt.bar(np.arange(n_bins), result)
    plt.show()
    s = raw_input("Press ENTER for next cycle.")







if __name__ == '__main__':
  main()

