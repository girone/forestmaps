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


def main():
  ''' Test this module. '''
  unittest.main()

if __name__ == '__main__':
  main()

