''' fep_weight_computation.py

    Forest entry point weight computation.

    Usage:
    python fep_weight_computation.py <OSMFile> [<MAXSPEED>]

    Copyright 2013: 
    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
'''
import sys
import os.path
import pickle
import time
from collections import defaultdict

from graph import Graph
from dijkstra import Dijkstra
from arcutil import Progress


def load_data(osmfile, maxspeed):
  filename = os.path.splitext(osmfile)[0] + "." + str(maxspeed) + "kmh"
  f = open(filename + ".feps.out")
  feps = pickle.load(f)
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
  return feps, forestal_highway_nodes, population_points, graph, osm_id_map, \
      nodes


def connect_population_to_graph(population, graph, coords, index_to_node_id):
  ''' Creates nodes for coordinates and connects them to the graph. 'coords'
  gives the coordinates for the graph nodes. The last
  argument is a funtion which yields the node id for every index in coords.
  '''
  from scipy.spatial import KDTree
  tree = KDTree(coords)
  population_node_ids = []
  for p in population:
    (d, index) = tree.query(p)
    population_node_ids.append(graph.size())
    node_id = index_to_node_id(index)
    graph.add_edge(node_id, population_node_ids[-1], 0)
  return population_node_ids


def reachability_analysis(graph, sources, targets, cost_limit=60*60):
  ''' Conducts Dijkstra's algorithm for every node in sources and returns for
  each node in targets the subset of sources from which it can be reached and
  the according distance.
  '''
  reachable_targets = defaultdict(list)
  avg = 0.
  p = Progress("Reachability analysis.", len(sources))
  search = Dijkstra(graph)
  search.set_cost_limit(cost_limit)
  print "Reachability cost limit:", cost_limit
  for count, node in enumerate(sources):
    res = search.run(node)
    for id in targets:
      if res[id] != sys.maxint:
        reachable_targets[id].append((node, res[id]))  # (source, dist)
    avg += len(res) - res.count(sys.maxint)  # non-infty (reached) nodes
    p.progress()
  print ''
  avg /= len(sources)
  print 'In average, %.1f of %d nodes have been settled.' \
      % (avg, len(graph.nodes))
  return reachable_targets


def main():
  if len(sys.argv) < 2 or os.path.splitext(sys.argv[1])[1] != '.osm':
    print ''' No osm file specified! '''
    exit(1)
  osmfile = sys.argv[1]
  maxspeed = int(sys.argv[2]) if len(sys.argv) > 2 else 130

  print '''Loading data...'''
  feps, forestal_highway_nodes, population, graph, osm_id_map, nodes = \
      load_data(osmfile, maxspeed)

  print '''Restrict the graph to non-forest nodes. '''
  graph.remove_partition([osm_id_map[id] for id in forestal_highway_nodes])

  print 'The graph has %d nodes and %d arcs.' % (len(graph.nodes),
      sum([len(outgoing) for outgoing in graph.edges.values()]))

  print '''Adding and connecting the population points to the graph. '''
  def index_to_node_id_func(index):
    return osm_id_map[osm_nodes.keys()[index]]
  population_node_ids = connect_population_to_graph(population, graph,
                                                    nodes.values(), 
                                                    index_to_node_id_func)

  print '''Contracting 2-nodes in the graph.'''
  graph.contract_binary_nodes(exclude=feps)

  print 'There are %d WEs.' % len(feps)
  print 'The graph has %d nodes and %d arcs.' % (len(graph.nodes),
      sum([len(outgoing) for outgoing in graph.edges.values()]))

  print '''Computing Dijkstra from every FEP...'''
  t0 = time.clock()
  sources = [osm_id_map[fep] for fep in feps]
  reachable_feps = reachability_analysis(graph, sources, population_node_ids)
  delta_t = time.clock() - t0
  print 'Dijkstra\'s took %.2fs, in average %.2fs per WE.' % (delta_t, 
      delta_t / len(feps))

  print '''Evaluating reachability result...'''
  population_at_fep = defaultdict(int)
  population_per_gridpoint = [500] * len(reachable_feps)
  for index, id in enumerate(reachable_feps.keys()):
    for fep, dist in reachable_feps[id]:
      population_at_fep[fep] += population_per_gridpoint[index] /  \
          float(len(reachable_feps[id]))

  pickle.dump(population_at_fep,  
      open(os.path.splitext(osmfile)[0] + '.population_at_fep.out', 'w'))
  for key, value in population_at_fep.items():
      print "FEP %d has population %d" % (key, value)



if __name__ == '__main__':
  ''' Run this module. '''
  main()

