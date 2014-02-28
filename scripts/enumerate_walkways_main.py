'''
    Entry point.

    For every WEP, this enumerates walkways in the forest which fulfill a set of
    conditions.

    Usage:
'''
USAGE = \
    'enumerate_forest_walkways.py <WEPS> <OSM_ID_MAP> <FOREST_NODE_IDS> ' \
    '<GRAPH> <NODEINFO> [<LIMIT>]'

import pickle
import sys
import os.path
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from enumerate_walkways import WayTree, WayGenerator, enumerate_walkways
import visual_grid
import edgedistance
from contraction import SimpleContractionAlgorithm, ClusterContractionAlgorithm


def main():
  if len(sys.argv) < 6:
    print USAGE
    exit(1)
  weps = pickle.load(open(sys.argv[1]))
  osm_id_map = pickle.load(open(sys.argv[2]))
  forest_nodes_osm_ids = pickle.load(open(sys.argv[3]))
  g = pickle.load(open(sys.argv[4]))
  nodeinfo = pickle.load(open(sys.argv[5]))

  ''' Set parameters '''
  if len(sys.argv) > 6:
    limit = int(sys.argv[-1]) * 60.
  else:
    limit = 10*60
    print "Using time limit 10min for walkway generation."

  wep_nodes = [osm_id_map[osm_id] for osm_id in weps]
  wep_nodes_set = set(wep_nodes)

  print ''' Concentrate way generation on forests '''
  n = len(g.nodes)
  outside_nodes = g.nodes - set([osm_id_map[id] for id in forest_nodes_osm_ids])
  outside_nodes -= wep_nodes_set
  g.remove_partition(outside_nodes)
  print n, len(g.nodes)

  print ''' Contract binary nodes except WEPs. '''
  n = len(g.nodes)
  g.contract_binary_nodes(exclude=wep_nodes)
  print n, len(g.nodes)

  #1 print ''' Simplify the graph by contraction of nodes with only short arcs. '''
  #1 n = len(g.nodes)
  #1 c = SimpleContractionAlgorithm(g, 20.0)  # 10.0 seconds @ 5 km/h ~= 14m
  #1 c.contract_graph(exclude_nodes=wep_nodes)
  #1 print n, len(g.nodes)
  print ''' Simplify the graph (solves the maze-problem). '''
  n = len(g.nodes)
  c = ClusterContractionAlgorithm(g, [nodeinfo[id].pos for id in g.nodes])
  c.contract_graph(exclude_nodes=set(wep_nodes))
  print n, len(g.nodes)

  ''' Compute the distance to the edge of the woods (or load it) '''
  print 'Computing edge distance...'
  name = os.path.splitext(os.path.splitext(sys.argv[1])[0])[0] + '.' + \
      str(int(limit/60)) + '.edge_distance.out'
  print name
  if os.path.exists(name):
    d_edge = pickle.load(open(name))
  else:
    d_edge = edgedistance.compute_edge_distance(g, wep_nodes, limit/2)
    try:
      pickle.dump(d_edge, open(name, 'w'))
    except:
      print 'Error while trying to write to ' + name
      exit(1)
  print 'Done!'


  print ''' Generate the walkways from every wep...'''
  count = 0
  import time
  t0 = time.clock()
  total_walkways = 0
  for node in wep_nodes[0:3]:
    count += 1
    walkways_and_distances = enumerate_walkways(g, node, 
        target_nodes=wep_nodes_set, cost_limit=limit, local_cycle_depth=5, 
        edge_distance=d_edge)
    print "%d of %d ways generated" % (count, len(wep_nodes))
    #print walkways
    print " %d  ways found with cost limit %.1f min." % \
        (len(walkways_and_distances), limit/60.)
    total_walkways += len(walkways_and_distances)
    if len(walkways_and_distances) < 2:
      continue

    ''' Evaluate the walkways (compute attractiveness), sort by distance. '''
    walkways = walkways_and_distances
    walkways = [(w,d) for (d,w) in sorted([(d,w) for (w,d) in walkways])]
    ma = walkways[0][1]
    mi = walkways[-1][1]
    su = sum([d for (w,d) in walkways])

    ''' Distribute the population weight over the paths. '''
    n_bins = 50
    bin_size = (ma - mi) / float(n_bins - 1.0)
    distance_distr = np.zeros(n_bins)
    #distance_distr[[(d - mi) / bin_size for (w, d) in walkways]] += 1.0
    for (w,d) in walkways:
      distance_distr[(d-mi)/bin_size] += 1.0
    #plt.bar(np.arange(n_bins), distance_distr)
    #plt.show()
    #spread = signal.gaussian(n_bins, std=5)  #  TODO(Jonas): Use sth. senseful.
    #spread[0:-1] *= 1. / sum(spread)  # normalize 
    #result = distance_distr * spread
    #normalizer = float(len(walkways)) / sum(result)  # normalize the joint distribution
    #result[0:-1] *= normalizer

    #plt.bar(np.arange(n_bins), result)
    #plt.show()
    #s = raw_input("Press ENTER for next cycle.")

  delta_t = time.clock() - t0
  print "Generated %d walkways from %d WEs, %.1f in average." % (total_walkways,
      len(weps), float(total_walkways) / len(weps))
  print "Limit was %d min." % (limit / 60)
  print "The graph had %d nodes and %d arcs." % (len(g.nodes),
      sum([len(edges) for edges in g.edges.values()]))
  print "This took %.2fs." % delta_t


if __name__ == '__main__':
  main()

