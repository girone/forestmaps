""" graph.py -- Contains classes for Graphs, Edges and Nodes.

Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
Copyright 2013: Jonas Sternisko

"""
from collections import defaultdict
import numpy as np


class Edge(object):
  def __init__(self, cost):
    self.cost = cost

  def __eq__(self, other):
    return self.cost == other.cost

  def __repr__(self):
    return "c=" + str(self.cost)


class NodeInfo(object):
  def __init__(self, osm_id=None, pos=None):
    self.osm_id = osm_id
    self.pos = pos

  def __repr__(self):
    return '"' + str(self.osm_id) + '" ' + str(self.pos)


class Graph(object):
  def __init__(self, maxNumNodes):
    """Requires the maximum number of nodes to be known."""
    self.edges = defaultdict(dict)  # {node : {successor : Edge}}
    #self.nodes = set()
    self.nodes = np.zeros(maxNumNodes, dtype=np.uint8)

  def __repr__(self):
    return str(self.nodes) + "\n" + str(self.edges) + "\n"

  def __eq__(self, other):
    return self.nodes == other.nodes and self.edges == other.edges

  def __ne__(self, other):
    return self.nodes != other.nodes or self.edges != other.edges

  def get_nodes(self):
      """Returns defined nodes."""
      return np.flatnonzero(self.nodes)

  def copy(self):
    """Returns a hard copy of the graph."""
    copy = Graph()
    copy.edges = self.edges.copy()
    copy.nodes = self.nodes.copy()
    return copy

  def size(self):
    return len(self.edges)

  def add_edge(self, s, t, c):
    """ Adds an edge from s to t with cost c. """
    self.nodes[s] = 1
    self.nodes[t] = 1
    try:
      if self.edges[s][t].cost > c:
        self.edges[s][t] = Edge(c)
    except KeyError:
      self.edges[s][t] = Edge(c)

  def remove_partition(self, node_ids):
    """ Removes nodes in @node_ids and incident arcs from the graph. """
    node_ids = set(node_ids)
    self.nodes[node_ids] = 0
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
    """ Determines the component (set of connected nodes) of @node such that
        every node of the component is contained in @nodes.
    """
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
    """ Filters the @nodes such that only those which form a connected component
        in the @graph of size larger than @threshold remain.
    """
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
    """ Returns the largest connected component of @self. """
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

  def contract_binary_nodes(self, exclude=set()):
    """Contracts nodes which have only two successors.

    On the graph's scope, this eliminates chains of nodes:
        \                     /              \                     /
         o -- o -- o -- o -- o       ===>     o ----------------- o
        /                     \              /                     \

    Parameter @exclude determines nodes which will not be contracted.
    Returns the contraction order.

    """
    contracted = np.zeros(len(self.nodes))
    contraction_list = []
    for node, bit in enumerate(self.nodes):
      edges = self.edges[node]
      if node not in exclude and len(edges) == 2:
        neighbors = edges.keys()
        # avoid loss of information, code assumes symmetric graph
        if neighbors[0] not in self.edges[neighbors[1]]:
          res = self.contract_node(node, remove=False)
          assert len(res) == 2  # supports only binary contraction
          contraction_list.extend(res)
          contracted[node] = 1
    self.nodes = self.nodes - contracted * self.nodes
    return contraction_list

  def contract_node(self, node, remove=True):
    """Contracts a node.

    This removes the node from the node set and connects its neighbors. Assumes
    that the graph is bidirectional.

    """
    new_edges = []
    contraction_list = []
    for neighborA, edgeA in self.edges[node].items():
      for neighborB, edgeB in self.edges[node].items():
        if neighborA is neighborB:
          continue
        new_cost = edgeA.cost + edgeB.cost
        if neighborB not in self.edges[neighborA] or \
            self.edges[neighborA][neighborB].cost > new_cost:
          new_edges.append((neighborA, neighborB, new_cost))
          contraction_list.append( ((neighborA, node), (node, neighborB)) )
    for (a, b, cost) in new_edges:
      self.add_edge(a, b, cost)
    if remove:
      self.nodes[node] = 0
    for neighbor in self.edges[node].keys():
      self.edges[neighbor].pop(node, None)
    self.edges.pop(node, None)
    return contraction_list

  def undo_contraction(self, contractionOrder):
    """Undoes a previous contraction. Distributes edge weights.

    Parameter @contractionOrder is a list of tuples
      ((A,C), (C,B))  # (A,B) is the result of contracting C
    starting with the first contraction. Supports only binary contraction.

    """
    for uncontractedArcs in reversed(contractionOrder):
      assert len(uncontractedArcs) == 2
      ((a, c), (_, b)) = uncontractedArcs
      self.nodes[c] = 1
      cost = self.edges[a][b].cost
      self.add_edge(a, c, cost)
      self.add_edge(c, b, cost)
      self.edges[a].pop(b, None)



import unittest

def add_biedge(graph, s, t, cost):
  graph.add_edge(s, t, cost)
  graph.add_edge(t, s, cost)


class TestGraph(unittest.TestCase):
  def test_base(self):
    A, B, C, D, E = 0, 1, 2, 3, 4
    g = Graph()
    g.add_edge(A, B, 4)
    g.add_edge(A, C, 2)
    g.add_edge(C, D, 1)
    g.add_edge(D, B, 1)
    g.add_edge(B, E, 1)
    #self.assertEqual(g.nodes, set([0, 1, 2, 3, 4]))
    self.assertEqual(str(g.edges), \
        "defaultdict(<type 'dict'>, {0: {1: c=4, 2: c=2}, " \
        "1: {4: c=1}, 2: {3: c=1}, 3: {1: c=1}})")

    g.remove_partition([B])
    #self.assertEqual(g.nodes, set([0, 2, 3, 4]))
    self.assertEqual(str(g.edges), "defaultdict(<type 'dict'>, {0: {2: c=2}, "
        "2: {3: c=1}, 3: {}})")

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

  def test_contraction1(self):
    A, B, C = 0, 1, 2
    g = Graph()
    add_biedge(g, A, B, 2)
    add_biedge(g, B, C, 3)
    g.contract_node(B)
    self.assertEqual(str(g.edges), "defaultdict(<type 'dict'>, "\
        "{0: {2: c=5}, 2: {0: c=5}})")

  def test_contraction2(self):
    A, B, C = 0, 1, 2
    g = Graph()
    add_biedge(g, A, B, 2)
    add_biedge(g, B, C, 3)
    g.contract_binary_nodes()
    self.assertEqual(str(g.edges), "defaultdict(<type 'dict'>, "\
        "{0: {2: c=5}, 2: {0: c=5}})")

  def test_contraction3(self):
    A, B, C = 0, 1, 2
    g = Graph()
    add_biedge(g, A, B, 2)
    add_biedge(g, B, C, 3)
    g.contract_binary_nodes(exclude=set([B]))
    self.assertEqual(str(g.edges), "defaultdict(<type 'dict'>, "\
        "{0: {1: c=2}, 1: {0: c=2, 2: c=3}, 2: {1: c=3}})")

  def test_contraction4(self):
    A, B, C = 0, 1, 2
    g = Graph()
    add_biedge(g, A, B, 2)
    add_biedge(g, B, C, 3)
    add_biedge(g, A, C, 4)  # don't contract B, it would cause information loss
    g.contract_binary_nodes()
    self.assertEqual(str(g.edges), "defaultdict(<type 'dict'>, "\
        "{0: {1: c=2, 2: c=4}, 1: {0: c=2, 2: c=3}, 2: {0: c=4, 1: c=3}})")


def main():
  """ Test this module. """
  unittest.main()

if __name__ == '__main__':
  main()

