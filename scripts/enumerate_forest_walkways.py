''' enumerate_forest_walkways

    For every WEP, this enumerates walkways in the forest which fulfill a set of
    conditions.

    Usage:
      python enumerate_forest_walkways.py <WEPS> <OSM_ID_MAP> <FOREST_NODE_IDS>
          <GRAPH>

    Copyright 2013:
    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
'''
import Queue

class WayTreeNode(object):
  ''' Has one parent, a cost on the way so far and 0...many successors. '''
  def __init__(self, node, parent=None, cost=0):
    self.node = node
    self.parent = parent  # WayTreeNode
    self.cost = cost
    self.successors = []  # list of WayTreeNode

  def create_successor(self, successor, cost):
    return WayTreeNode(successor, self, self.cost + cost)


class WayTree(object):
  ''' A tree structure representing a set of ways. '''
  def __init__(self, node_idx):
    self.root = WayTreeNode(node_idx)
    self.nodes = [self.root]

  def detect_cycle(self, start_tree_node, node_id, depth=2):
    ''' Returns true, if @node_id is among the ids of the @depth last nodes. '''
    tree_node = start_tree_node
    contains_cycle = False
    while tree_node and depth > 0 and not contains_cycle:
      contains_cycle = (tree_node.node == node_id)
      depth -= 1
      tree_node = tree_node.parent
    return contains_cycle

  def expand(self, tree_node, edges):
    ext = []
    for succ, edge in edges.items():
      if self.detect_cycle(tree_node, succ, depth=2):
        continue
      self.nodes.append(tree_node.create_successor(succ, edge.cost))
      ext.append(len(self.nodes) - 1)
      tree_node.successors.append(self.nodes[-1])
    return ext


class WayGenerator(object):
  ''' The enumeration algorithm. '''
  def __init__(self, way_tree, graph):
    self.tree = way_tree
    self.graph = graph

  def run(self, start_node, cost_limit=10):
    ''' Generates ways until all open ways exceed the @cost_limit. '''
    ''' TODO(Jonas): Avoid trivial cycles a-b-a-b-a-b-... in the bigraph. '''
    assert self.tree.root.node == start_node
    q = Queue.Queue()
    q.put(0)  # index of tree root
    while not q.empty():
      i = q.get()
      tree_node = self.tree.nodes[i]
      if tree_node.cost < cost_limit:
        node_idx = tree_node.node
        ext = self.tree.expand(tree_node, self.graph.edges[node_idx])
        for e in ext:
          q.put(e)

  def backtrack_path(self, leaf_node):
    ''' Backtracks a path from a node to the root, returns a node sequence. '''
    parent = leaf_node.parent
    path = [leaf_node.node]
    while parent:
      node = parent
      path.append(node.node)
      parent = node.parent
    path.reverse()
    return path
    
  def trace(self):
    ''' Backtracks paths from leaves of the generated WayTree back to the root.
    '''
    leaves = [node for node in self.tree.nodes if node.successors == []]
    return [self.backtrack_path(leaf) for leaf in leaves]


def enumerate_walkways(graph, start_node, cost_limit=9):
  ''' Enumerates walkways beginning at @start_node.
     
      Admissible walkways start at a WEP and end at a WEP. Start and end may
      equal. Walkways are required to have a total cost within [cmin, cmax]. 

      TODO(Jonas): Restrict to real walkways by osm tag.
      TODO(Jonas): Remove ways which have bad cycles.
      TODO(Jonas): Use some tree structure to represent the walkways.
      TODO(Jonas): Add online-filtering.
  '''
  # create the tree node until limit cmax
  tree = WayTree(start_node)
  gen = WayGenerator(tree, graph)
  gen.run(start_node, cost_limit)

  # collect ways which end at an WEP and have cost >= cmin
  ways = gen.trace()
  return ways


def main():
  g = Graph()
  osm_id_map = {}
  weps = []
  forest_nodes_osm_ids = []

  ''' concentrate on the inner forests '''
  outside_nodes = g.nodes - set([osm_id_map[id] for id in forest_nodes_osm_ids])
  g.remove_partition(outside_nodes)

  ''' '''
  for osm_id in weps:
    node = osm_id_map[osm_id]
    walkways = enumerate_walkways(g, node)


from unittest import TestCase
class WalkwayEnumerationTest(TestCase):
  def test_1(self):
    from graph import Graph
    A, B, C = range(3)
    g = Graph()
    g.add_edge(A, B, 3)
    g.add_edge(B, A, 3)
    g.add_edge(B, C, 5)
    g.add_edge(C, B, 5)
    g.add_edge(C, A, 2)
    g.add_edge(A, C, 2)
    g.add_edge(A, A, 4)

    ways = enumerate_walkways(g, A)
    for w in ways:
      print w


if __name__ == '__main__':
  import unittest
  unittest.main()
  #main()

