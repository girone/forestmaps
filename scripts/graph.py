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

  def __repr__(self):
    return str(self.nodes) + "\n" + str(self.edges) + "\n"

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

  def connected_component(self, node, nodes):
    ''' Determines the component (set of connected nodes) of @node such that
        every node of the component is contained in @nodes. 
    '''
    component = set()
    queue = [node]
    while len(queue):
      top = queue.pop()
      component.add(top)
      for adjacent_node in self.edges[top].keys():
        if adjacent_node in nodes and adjacent_node not in component:
          queue.append(adjacent_node)
    assert len(component) == len(set(component))
    return component

  def filter_components(self, nodes, threshold):
    ''' Filters the @nodes such that only those which form a connected component
        in the @graph of size larger than @threshold remain.
    '''
    node_set = set(nodes)
    remaining = []
    removed = []
    while len(node_set):
      node = node_set.pop()
      component = self.connected_component(node, node_set)
      node_set -= component
      if len(component) >= threshold:
        remaining.extend(component)
      else:
        removed.extend(component)
    assert len(remaining) == len(set(remaining))
    return set(remaining), removed

  def lcc(self):
    ''' Returns the largest connected component of @self. '''
    node_set = set(range(self.size()))
    largest_component = set()
    while len(node_set):
      node = node_set.pop()
      component = self.connected_component(node, node_set)
      node_set -= component
      if len(component) >= len(largest_component):
        largest_component = component
    lcc = Graph()
    for x in largest_component:
      for y, edge in self.edges[x].items():
        lcc.add_edge(x, y, edge.cost)
    return lcc


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

  def test_lcc(self):
    A, B, C, D, E = 0, 1, 2, 3, 4
    g = Graph()
    g.add_edge(A, B, 4)
    g.add_edge(B, A, 4)
    g.add_edge(C, D, 2)
    g.add_edge(D, C, 2)
    g.add_edge(D, E, 1)
    g.add_edge(E, D, 1)
    expect = Graph()
    expect.add_edge(C, D, 2)
    expect.add_edge(D, C, 2)
    expect.add_edge(D, E, 1)
    expect.add_edge(E, D, 1)
    self.assertEqual(str(g.lcc()), str(expect))


def main():
  ''' Test this module. '''
  unittest.main()

if __name__ == '__main__':
  main()

