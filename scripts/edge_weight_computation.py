'''
File: edge_weight_computation.py
Author: Jonas Sternisko
Description:
This file contains code which computes the weight of edges e=(s,t) in the graph
by conducting one Dijkstra from s and t respectively.

'''

from collections import defaultdict
from dijkstra import Dijkstra
from util import Progress

MAX_COST = 60*60  # 1 hour

def find_feasible_entrypoints_for_each_edge(edges, graph, fep_nodes,
                                            cost_limit):
  """Determines shortest paths from entry to exit via edge.

  For each edge, this finds all pairs of forest entry/exit between which a
  shortest path via the edge with costs less than some limit exists.

  """
  def find_reached_fep_nodes(distances):
    return [node for node, cost in enumerate(distances) if cost != dijkstra.inf
            and node in fep_nodes]  # TODO(Jonas): use list intersection here
  entrypoints_to_edges = defaultdict(lambda : defaultdict(lambda : {}))
  print "cost limit is", cost_limit
  dijkstra = Dijkstra(graph)
  progress = Progress("Forest trips via Dijkstra", len(edges))
  for (s,t) in edges:
    edge_cost = graph.edges[s][t].cost
    dijkstra.set_cost_limit(cost_limit - edge_cost)
    dijkstra.set_forbidden_edges(set([(s,t), (t,s)]))
    dist1 = dijkstra.run(s)
    dijkstra.set_cost_limit(cost_limit - min(dist1) - edge_cost)
    dist2 = dijkstra.run(t)
    dijkstra.set_forbidden_edges(None)
    reached_entry_nodes = find_reached_fep_nodes(dist1)
    reached_exit_nodes = find_reached_fep_nodes(dist2)
    for entry in reached_entry_nodes:
      for exit in reached_exit_nodes:
        path_cost = dist1[entry] + edge_cost + dist2[exit]
        print "{0} + {1} + {2} = {3} <=? {4}".format(dist1[entry], edge_cost,
            dist2[exit], path_cost, cost_limit)
        if path_cost <= cost_limit:
          entrypoints_to_edges[entry][exit][(s,t)] = path_cost
    progress.step()
  return entrypoints_to_edges


def distribute_entrypoint_weight(fep_nodes, fep_population,
                                 entrypoints_to_edges):
  """Distribute entry point weight to edges on feasible round trips."""
  edge_population = defaultdict(float)
  no_paths_found = 0
  for entry in fep_nodes:
    num_paths_at_fep = sum([len(v) for v in entrypoints_to_edges[entry].values()])
    if num_paths_at_fep > 0:
      average_weight = fep_population[entry] / float(num_paths_at_fep)
      for exit, feasible_edges in entrypoints_to_edges[entry].items():
        for (s,t) in feasible_edges:
          edge_population[(s,t)] += average_weight
    else:
      no_paths_found += 1
  print "For {0} entries no trips have been found.".format(no_paths_found)
  return edge_population
  #return dict(edge_population)


def compute_edge_weight(graph, fep_nodes, fep_population, cost_limit=MAX_COST):
  """ """
  edges = set([(s,t) for s in graph.edges.keys() for t in graph.edges[s].keys()])
  entrypoints_to_edges = find_feasible_entrypoints_for_each_edge(
      edges, graph, fep_nodes, cost_limit)
  edge_population = distribute_entrypoint_weight(
      fep_nodes, fep_population, entrypoints_to_edges)
  return edge_population


import unittest
class TestModule(unittest.TestCase):

  def test1(self):
    from graph import Graph
    A, B, C, D, E = 0, 1, 2, 3, 4
    g = Graph()
    g.add_edge(A, B, 4)
    g.add_edge(A, C, 2)
    g.add_edge(C, D, 1)
    g.add_edge(D, B, 1)
    g.add_edge(B, E, 1)
    feps = [A, E]
    fep_population = {A: 100, E: 10}
    r = compute_edge_weight(g, feps, fep_population)


def main():
  ''' Run unit tests. '''
  unittest.main()

if __name__ == '__main__':
  main()

