''' wep_weight_computation.py

    Entry point for the weight computation for WEPs.

    Copyright 2013: 
    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
'''
import sys
import os.path
import pickle
from graph import Graph
from dijkstra import Dijkstra


def load_data(osmfile):
  filename = os.path.splitext(osmfile)[0]
  f = open(filename + ".weps.out")
  weps = pickle.load(f)
  f.close()
  f = open(filename + ".forestal_ids.out")
  forestal_highway_nodes = pickle.load(f)
  f.close()
  f = open(filename + ".population.out")
  population_points = pickle.load(f)
  f.close()
  f = open(filename + ".graph.out")
  graph = pickle.load(f)
  f.close()
  f = open(filename + ".osm_id_map.out")
  osm_id_map = pickle.load(f)
  f.close()
  return weps, forestal_highway_nodes, population_points, graph, osm_id_map


def main():
  if len(sys.argv) != 2 or os.path.splitext(sys.argv[1])[1] != '.osm':
    print ''' No osm file specified! '''
    exit(1)
  osmfile = sys.argv[1]

  print '''Loading data...'''
  weps, forestal_highway_nodes, population, graph, osm_id_map = \
      load_data(osmfile)

  print '''Restrict the graph to non-forest nodes. '''
  graph.remove_partition([osm_id_map[id] for id in forestal_highway_nodes])

  print '''Compute Dijkstra from every WEP. '''
  avg = 0
  for count, node in enumerate(weps):
    print 'Running time-restricted Dijkstra %d of %d...' % (count+1, len(weps))
    search = Dijkstra(graph)
    search.set_cost_limit(60 * 60)  # 1 hour
    res = search.run(osm_id_map[node])
    print "Settled %d of %d nodes." % \
        (len(res) - res.count(sys.maxint), len(res))
    avg += len(res) - res.count(sys.maxint)  # non-infty (reached) nodes
  avg /= len(weps)
  print 'In average, %f of %d nodes have been settled.' \
      % (avg, len(graph.nodes))


if __name__ == '__main__':
  ''' Run this module. '''
  main()

