''' wep_weight_computation.py

    Entry point for the weight computation for WEPs.

    Usage:
    python wep_weight_computation.py <OSMFile> [<MAXSPEED>]

    Copyright 2013: 
    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
'''
import sys
import os.path
import pickle
from scipy.spatial import KDTree
from collections import defaultdict

from graph import Graph
from dijkstra import Dijkstra


def load_data(osmfile, maxspeed):
  filename = os.path.splitext(osmfile)[0] + "." + str(maxspeed) + "kmh"
  f = open(filename + ".weps.out")
  weps = pickle.load(f)
  f.close()
  f = open(filename + ".forest_ids.out")
  forestal_highway_nodes = pickle.load(f)
  f.close()
  f = open(filename + ".population.out")
  population_points = pickle.load(f)
  f.close()
  f = open(filename + ".graph.out")
  graph = pickle.load(f)
  f.close()
  f = open(filename + ".id_map.out")
  osm_id_map = pickle.load(f)
  f.close()
  f = open(filename + ".nodes.out")
  nodes = pickle.load(f)
  f.close()
  return weps, forestal_highway_nodes, population_points, graph, osm_id_map, \
      nodes


def main():
  if len(sys.argv) < 2 or os.path.splitext(sys.argv[1])[1] != '.osm':
    print ''' No osm file specified! '''
    exit(1)
  osmfile = sys.argv[1]
  maxspeed = int(sys.argv[2]) if len(sys.argv) > 2 else 130

  print '''Loading data...'''
  weps, forestal_highway_nodes, population, graph, osm_id_map, nodes = \
      load_data(osmfile, maxspeed)

  print '''Restrict the graph to non-forest nodes. '''
  graph.remove_partition([osm_id_map[id] for id in forestal_highway_nodes])

  # Cannot pickle KDTree.innernode ...
  #kdtree_file_name = os.path.splitext(osmfile)[0] + ".kdtree.out"
  #if not os.path.exists(kdtree_file_name):
  #  print '''Constructing the KDTree from the osm-nodes... '''
  #  coords = nodes.values()
  #  tree = KDTree(coords)
  #  pickle.dump(tree, open(kdtree_file_name, 'w'))
  #else:
  #  print '''Loading the KDTree from file ''' + kdtree_file_name + '...'
  #  tree = pickle.load(open(kdtree_file_name))
  print '''Constructing the KDTree from the osm-nodes... '''
  coords = nodes.values()
  tree = KDTree(coords)

  print '''Adding the population points to the graph. '''
  population_node_ids = []
  for p in population:
    (d, index) = tree.query(p)
    #print " nn-distance = " + str(d)
    osm_id = nodes.keys()[index]  # index in tree input data
    node_id = osm_id_map[osm_id]
    population_node_ids.append(graph.size())
    graph.add_edge(node_id, population_node_ids[-1], 0)
    #print " adding edge from %d to %d" % (node_id, population_node_ids[-1])

  print '''Compute Dijkstra from every WEP. '''
  reachable_weps = defaultdict(list)
  avg = 0
  weps = list(weps)
  for count, node in enumerate(weps):
    print 'Running time-restricted Dijkstra %d of %d...' % (count+1, len(weps))
    search = Dijkstra(graph)
    search.set_cost_limit(60 * 60)  # 1 hour
    res = search.run(osm_id_map[node])
    for id in population_node_ids:
      if res[id] != sys.maxint:
        reachable_weps[id].append((node, res[id]))  # (wep, dist)

    #print "Settled %d of %d nodes." % \
        #    (len(res) - res.count(sys.maxint), len(res))
    avg += len(res) - res.count(sys.maxint)  # non-infty (reached) nodes
  avg /= len(weps)
  print 'In average, %f of %d nodes have been settled.' \
      % (avg, len(graph.nodes))

  print '''Evaluating reachability analysis...'''
  population_at_wep = defaultdict(int)
  population_per_gridpoint = [500] * len(reachable_weps)
  for index, id in enumerate(reachable_weps.keys()):
    for wep, dist in reachable_weps[id]:
      #print ' WEP %d can be reached within %.1f minutes' % (wep, dist / 60.)
      population_at_wep[wep] += population_per_gridpoint[index] /  \
          float(len(reachable_weps[id]))

  pickle.dump(population_at_wep,  
      open(os.path.splitext(osmfile)[0] + '.population_at_wep.out', 'w'))
  for key, value in population_at_wep.items():
    print "WEP %d has population %d" % (key, value)



if __name__ == '__main__':
  ''' Run this module. '''
  main()

