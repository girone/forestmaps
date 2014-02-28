""" Compute the distance to the edge of the wood.

Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

"""
from dijkstra import Dijkstra
import sys

def compute_edge_distance(graph, border_node_ids, maximum_distance=0):
  """Computes the distance to the border of the forest for each node of graph.

  Returns a list of lenght |graph| with the distances.

  @maximum_distance : This is used to improve the computation time. All
  nodes with distance larger than this parameter are considered unreachable.

  """
  dmin = [sys.maxint] * graph.size()
  for i, id in enumerate(border_node_ids):
    print " %d of %d" % (i+1, len(border_node_ids))
    alg = Dijkstra(graph)
    if maximum_distance > 0:
      alg.set_cost_limit(maximum_distance)
    d = alg.run(id)
    for index, value in enumerate(d):
      if value < dmin[index]:
        dmin[index] = value
  return dmin

