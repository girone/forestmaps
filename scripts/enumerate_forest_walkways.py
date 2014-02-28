''' enumerate_forest_walkways

    For every WEP, this enumerates walkways in the forest which fulfill a set of
    conditions.

    Usage:
      python enumerate_forest_walkways.py <WEPS> <OSM_ID_MAP> <FOREST_NODE_IDS>
          <GRAPH>

    Copyright 2013:
    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
'''

class WayTreeNode(object):
  ''' Has one parent, a cost on the way so far and 0...many successors. '''
  def __init__(self, parent=None, cost=0):
    self.parent = parent  # WayTreeNode
    self.cost = 0
    self.successors = []  # list of WayTreeNode

  def create_successor(self, edge):
    return WayTreeNode(self, self.cost + edge.cost)
  


class WayTree(object):
  ''' A tree structure representing a set of ways. '''
  def __init__(self, osm_id):
    self.root = WayTreeNode(osm_id)
    self.nodes = [self.root]

  def expand(self, tree_node, edges):
    for e in edges:
      if tree.node.cost + e.cost < self.cost_limit:
        self.nodes.append(tree_node.create_successor(e))
        tree_node.successors.append(self.nodes[-1])


def enumerate_walkways(graph, start_node):
  ''' Enumerates walkways beginning at @start_node.
     
      Admissible walkways start at a WEP and end at a WEP. Start and end may
      equal. Walkways are required to have a total cost within [cmin, cmax]. 

      TODO(Jonas): Restrict to real walkways by osm tag.
      TODO(Jonas): Remove ways which have bad cycles.
      TODO(Jonas): Use some tree structure to represent the walkways.
      TODO(Jonas): Add online-filtering.
  '''
  ways = [] 
  
  # create the tree node until limit cmax

  # collect ways which end at an WEP and have cost >= cmin


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



if __name__ == '__main__':
  main()

