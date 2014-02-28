''' graph.py

    Contains classes for Graphs, Edges and Nodes.

    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
    Copyright 2013: Jonas Sternisko
'''
from collections import defaultdict

class Edge():
  def __init__(self, cost):
    self.cost = cost

  def __repr__(self):
    return str(self.cost)

class Graph(object):
  def __init__(self):
    self.edges = defaultdict(dict)
    self.nodes = set()

  def size(self):
    return max(self.nodes) + 1

  def add_edge(self, s, t, c):
    ''' Adds an edge from s to t with cost c. '''
    self.nodes.add(s)
    self.nodes.add(t)
    try:
      if self.edges[s][t].cost > c:
        self.edges[s][t] = Edge(c)
    except KeyError:
      self.edges[s][t] = Edge(c)

  def remove_partition(self, node_ids):
    ''' Removes nodes in @node_ids and incident arcs from the graph. '''
    node_ids = set(node_ids)
    self.nodes -= node_ids
    for id in node_ids:
      self.edges.pop(id, None)
    for key, edges in self.edges.items():
      remove = []
      for node in edges.keys():
        if node in node_ids:
          remove.append(node)
      for elem in remove:
        edges.pop(elem, None)

## class OsmGraph(Graph):
##   ''' Adds a mapping from osm-id to node id to the graph. '''
##   def __init__(self):
##     super(OsmGraph, self).__init__()
##     self.osm_id_map = {}
##     self.inv_osm_id_map = {}
## 
##   def add_osm_edge(self, s, t, c):
##     if s not in self.osm_id_map:
##       ids = len(self.osm_id_map)
##       self.osm_id_map[s] = ids
##       self.inv_osm_id_map[ids] = s
##     else:
##       ids = self.osm_id_map[s]
##     if t not in self.osm_id_map:
##       idt = len(self.osm_id_map)
##       self.osm_id_map[t] = idt
##       self.inv_osm_id_map[idt] = t
##     else:
##       idt = self.osm_id_map[t]
##     super(OsmGraph, self).add_edge(ids, idt, c)
    


import unittest
class TestGraph(unittest.TestCase):
  def test_base(self):
    A, B, C, D, E = 0, 1, 2, 3, 4
    g = Graph()
    g.add_edge(A, B, 4)
    g.add_edge(A, C, 2)
    g.add_edge(C, D, 1)
    g.add_edge(D, B, 1)
    g.add_edge(B, E, 1)
    self.assertEqual(g.nodes, set([0, 1, 2, 3, 4]))
    self.assertEqual(str(g.edges), \
        "defaultdict(<type 'dict'>, {0: {1: 4, 2: 2}, " \
        "1: {4: 1}, 2: {3: 1}, 3: {1: 1}})")

    g.remove_partition([B])
    self.assertEqual(g.nodes, set([0, 2, 3, 4]))
    self.assertEqual(str(g.edges), "defaultdict(<type 'dict'>, {0: {2: 2}, " \
        "2: {3: 1}, 3: {}})")

    ##  def test_osmgraph(self):
    ##    A, B, C = 599, 132, 17
    ##    g = OsmGraph()
    ##    g.add_osm_edge(A, B, 5)
    ##    g.add_osm_edge(A, C, 10)
    ##    g.add_osm_edge(B, C, 2)
    ##    print g.nodes
    ##    print g.edges
    ##    print g.osm_id_map


def main():
  ''' Test this module. '''
  unittest.main()

if __name__ == '__main__':
  main()

