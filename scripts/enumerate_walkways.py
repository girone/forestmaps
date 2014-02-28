''' enumerate_forest_walkways

    Copyright 2013:
    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
'''
import Queue

DEBUG = False

''' test_funcs go below '''
def true(*args):
  return True

def arc_repetition(arcs_so_far, next_arc):
  ''' TODO(Jonas): Allow a less strict variant. E.g., allow 5% of arcs along a
      path to have duplicates within the same path.
  '''
  return next_arc in arcs_so_far


''' action_funcs go below '''
def noop(*args):
  pass

def prune(tree_node):
  tree_node.pruned = True
  for s in tree_node.successors:
    prune(s)


class WayTreeNode(object):
  ''' Has one parent, a cost on the way so far and 0...many successors. '''
  def __init__(self, node, parent=None, cost=0):
    self.node = node
    self.parent = parent  # WayTreeNode
    self.cost = cost
    self.successors = []  # list of WayTreeNode
    self.pruned = False

  def create_successor(self, successor, cost):
    return WayTreeNode(successor, self, self.cost + cost)

  def traverse(self, collect, result):
    ''' Recursively descends the tree, collecting things and testing. '''
    if not self.successors:
      result.append((self, collect)) # save the collection for the next traverse
      pass
    else:
      for successor in self.successors:
        if successor.pruned:
          continue
        if arc_repetition(collect, (self.node, successor.node)):
          prune(self)
        else:
          copy = collect.copy()
          copy.add((self.node, successor.node))
          successor.traverse(copy, result)


class WayTree(object):
  ''' A tree structure representing a set of ways. '''
  def __init__(self, node_idx):
    self.root = WayTreeNode(node_idx)
    self.nodes = [self.root]
    self.prune_state = None

  def detect_cycle(self, start_tree_node, node_id, depth):
    ''' Returns true, if @node_id is among the ids of the @depth last nodes. '''
    tree_node = start_tree_node
    contains_cycle = False
    while tree_node and depth > 0 and not contains_cycle:
      contains_cycle = (tree_node.node == node_id)
      depth -= 1
      tree_node = tree_node.parent
    return contains_cycle

  def expand(self, tree_node, edges, depth):
    ''' @depth: Local sequences without repetitions of the same node_id '''
    ext = []
    for succ, edge in edges.items():
      if self.detect_cycle(tree_node, succ, depth):
        continue
      self.nodes.append(tree_node.create_successor(succ, edge.cost))
      ext.append(len(self.nodes) - 1)
      tree_node.successors.append(self.nodes[-1])
    if DEBUG:
      print len(self.nodes)
      print self.nodes[-1].cost
    return ext

  def prune_cycle_subgraphs(self, max_arc_repeat=0):
    ''' Traverses the graph and removes subgraphs which repeat an arc for more
        than @max_arc_repeat times.
        TODO(Jonas): Implement the parameter.
        Returns the 'prune_state', information which can be reused in the next
        pruning operation.
    '''
    new_prune_state = []
    if not self.prune_state:
      traversed_edges = set()
      self.root.traverse(traversed_edges, new_prune_state)
    else:
      for (node, traversed_edges) in self.prune_state:
        node.traverse(traversed_edges, new_prune_state)
    self.prune_state = new_prune_state
    return self.prune_state


class WayGenerator(object):
  ''' The enumeration algorithm. '''
  def __init__(self, way_tree, graph):
    self.tree = way_tree
    self.graph = graph

  def run(self, start_node, cost_limit=10, local_cycle_depth=2,  \
      prune_after=None):
    ''' Generates ways until all open ways exceed the @cost_limit. 
        @local_cycle_depth : 
    '''
    assert self.tree.root.node == start_node
    q = Queue.Queue()
    q.put(0)  # index of tree root
    count = 0
    while not q.empty():
      i = q.get()
      tree_node = self.tree.nodes[i]
      if not tree_node.pruned:
        count += 1
        if prune_after and count % prune_after == 0:
          self.tree.prune_cycle_subgraphs()
          print 'Tree has %d nodes.' % len(self.tree.nodes)
        if tree_node.cost < cost_limit:
          node_idx = tree_node.node
          ext = self.tree.expand(tree_node, self.graph.edges[node_idx], \
              local_cycle_depth)
          for e in ext:
            q.put(e)
    print 'Expanded %d tree nodes.' % count

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
    
  def trace(self, targets=None):
    ''' Backtracks paths from leaves of the generated WayTree back to the root.
    '''
    if targets:
      leaves = [node for node in self.tree.nodes if node.node in targets] 
    else:
      leaves = [node for node in self.tree.nodes if node.successors == []]
    leaves = [leaf for leaf in leaves if not leaf.pruned]
    return [self.backtrack_path(leaf) for leaf in leaves \
            if leaf is not self.tree.root]


def enumerate_walkways(graph, start_node, target_nodes=None, cost_limit=9, \
    local_cycle_depth=2):
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
  gen.run(start_node, cost_limit, local_cycle_depth, prune_after=500)
  # prune bad walkways
  tree.prune_cycle_subgraphs(max_arc_repeat=0)


  # collect ways which end at an WEP and have cost >= cmin
  ways = gen.trace(targets=target_nodes)
  return ways


# def main():
#   g = Graph()
#   osm_id_map = {}
#   weps = []
#   forest_nodes_osm_ids = []
# 
#   ''' concentrate on the inner forests '''
#   outside_nodes = g.nodes - set([osm_id_map[id] for id in forest_nodes_osm_ids])
#   g.remove_partition(outside_nodes)
# 
#   ''' '''
#   for osm_id in weps:
#     node = osm_id_map[osm_id]
#     walkways = enumerate_walkways(g, node)


def add_biedge(graph, s, t, cost):
  graph.add_edge(s, t, cost)
  graph.add_edge(t, s, cost)


from unittest import TestCase
from graph import Graph
A, B, C, D, E, F = range(6)
class WalkwayEnumerationTest(TestCase):
  def setUp(self):
    self.g = Graph()
    add_biedge(self.g, A, B, 3)
    add_biedge(self.g, B, C, 5)
    add_biedge(self.g, C, A, 2)
    add_biedge(self.g, B, D, 4)
    add_biedge(self.g, C, D, 4)
    add_biedge(self.g, D, E, 3)
    add_biedge(self.g, C, F, 3)
    add_biedge(self.g, F, E, 6)

  def test_local_cycle_avoidance(self):
    self.g.remove_partition([D, E, F])
    self.g.add_edge(A, A, 4)
    ways = enumerate_walkways(self.g, A, cost_limit=10, local_cycle_depth=0)
    self.assertTrue([A, A, A, A] in ways)
    ways = enumerate_walkways(self.g, A, cost_limit=10, local_cycle_depth=1)
    self.assertTrue([A, A, A, A] not in ways)
    self.assertTrue([A, B, A, B, A] in ways)
    ways = enumerate_walkways(self.g, A, cost_limit=10, local_cycle_depth=2)
    self.assertTrue([A, B, A, B, A] not in ways)

  def test_traversal_and_pruning(self):
    tree = WayTree(A)
    gen = WayGenerator(tree, self.g)
    gen.run(A, cost_limit=50, local_cycle_depth=5)
    ways1 = gen.trace()
    #for w in ways1:
    #  print w
    ''' Prune subtrees with cycles from the tree. This removes two large
        repetitions. 
    '''
    collect = set()
    tree.root.traverse(collect, arc_repetition, prune)
    ways2 = gen.trace()
    #for w in ways2:
    #  print w
    self.assertLess(len(ways2), len(ways1))

  def test_global_cycle_avoidance(self):
    # create the tree node until limit cmax
    tree = WayTree(A)
    gen = WayGenerator(tree, self.g)
    gen.run(A, cost_limit=50, local_cycle_depth=5)
    # collect ways which end at an WEP and have cost >= cmin
    ways = gen.trace()
    # NEW: prune 
    tree.prune_cycle_subgraphs(max_arc_repeat=0)
    # collect ways which end at an WEP and have cost >= cmin
    ways2 = gen.trace()
    self.assertLess(len(ways2), len(ways))

  def test_target_set(self):
    ways1 = enumerate_walkways(self.g, A, cost_limit=50, local_cycle_depth=5)
    ways2 = enumerate_walkways(self.g, A, cost_limit=50, local_cycle_depth=5, \
        target_nodes=[A, E])
    self.assertNotEqual(ways1, ways2)
    #print "ways1"
    #for w in ways1:
    #  print w
    #print "ways2"
    #for w in ways2:
    #  print w

if __name__ == '__main__':
  import unittest
  unittest.main()

