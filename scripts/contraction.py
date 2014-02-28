''' Contains code for graph contraction.

    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
    A node is contracted by removing it and its adjacent edges from the graph
    and adding shortcuts between its neighbors such that the connectivity of
    the neighbors is maintained.
      
'''
import numpy as np
from forestentrydetection import great_circle_distance


class SimpleContractionAlgorithm(object):
  ''' This class performs a very simple contraction to the graph: All nodes with
      only adjacent edges of 'length' shorter than @cost_threshold are
      successively contracted.
  '''
  def __init__(self, graph, cost_threshold):
    self.graph = graph
    self.cost_threshold = cost_threshold
    self.contracted_flags = [False] * graph.size()
  
  def compute_candidates(self):
    ''' Computes the candidates for contraction. All nodes with only edges of
        cost < threshold will be selected.
    '''
    candidates = set()
    for node in self.graph.nodes:
      candidate = True
      for other_node, edge in self.graph.edges[node].items():
        if edge.cost > self.cost_threshold:
          candidate = False
          break
      if candidate:
        candidates.add(node)
    return candidates

  def update_candidates(self, old_candidates, new_shortcuts):
    ''' This updates the candidates. I.e., new shortcuts of length >
        self.threshold to node A should result in node A being removed from the
        set of candidates.
        TODO(Jonas): Implement this behaviour.
    '''
    return old_candidates

  def contract_graph(self, exclude_nodes=None):
    ''' Performs the contraction. Algorithm entry point. '''
    candidates = self.compute_candidates()
    if exclude_nodes:
      candidates -= set(exclude_nodes)
    print candidates
    print "%d candidates will be contracted" % len(candidates)
    while candidates:
      c = candidates.pop()
      new_shortcuts = self.graph.contract_node(c)
      candidates = self.update_candidates(candidates, new_shortcuts)


class Cluster(object):
  def __init__(self, node_id, node_pos):
    ''' Creates a cluster from one node and its position (given as numpy.array).
    '''
    self.nodes = set([node_id])
    self.centroid = node_pos

  def __repr__(self):
    return str(self.nodes) + " centroid@" + str(self.centroid)

  def join(self, other):
    lengths = [len(self.nodes), len(other.nodes)]
    a, b = [float(l) / sum(lengths) for l in lengths]
    self.centroid = (a * self.centroid[0] + b * other.centroid[0],
        a * self.centroid[1] + b * other.centroid[1])
    self.nodes = self.nodes.union(other.nodes)
    other.nodes.clear()

  def distance(self, other):
    ''' Returns the great-circle-distance to the centroid of another cluster.
    '''
    return great_circle_distance(self.centroid, other.centroid)

  def determine_border_nodes(self, graph):
    ''' Returns the border nodes, i.e. nodes inside of the cluster which have
        arcs to nodes outside of the cluster.
    '''
    border_nodes = set([])
    for node in self.nodes:
      for other_node in graph.edges[node]:
        if other_node not in self.nodes:
          border_nodes.add(node)
    return border_nodes


INTRA_CLUSTER_DISTANCE_THRESHOLD = 15.0  # meters 
INTER_CLUSTER_DISTANCE_THRESHOLD = 50.0


class ClusterContractionAlgorithm(object):
  ''' This algorithm consists of two steps. 
      First, nodes are clustered agglomeratively such that dense local regions
      with good internal connectivity are created. 
      In a second step, these clusters are contracted such that only the border
      nodes of the clusters remain, with arcs corresponding to the shortest
      paths in the original graph between them.

      Clusters are defined by: ...
  '''

  def __init__(self, graph, positions,
      intra_dist=INTRA_CLUSTER_DISTANCE_THRESHOLD, 
      inter_dist=INTER_CLUSTER_DISTANCE_THRESHOLD):
    self.graph = graph
    self.node_positions = positions
    self._intra_dist_thresh = intra_dist
    self._inter_dist_thresh = inter_dist

  def cluster(self, graph, node_positions):
    ''' Agglomerative clutering. '''
    def merge_clusters(id_a, id_b, clusters, cluster_labels):
      nodes_of_b = list(clusters[id_b].nodes)
      clusters[id_a].join(clusters[id_b])
      clusters.pop(id_b, None)
      cluster_labels[nodes_of_b] = id_a

    clusters = {id : Cluster(node, pos) for id, (node, pos) in
        enumerate(zip(graph.nodes, node_positions))}
    cluster_labels = np.ones(graph.size()) * -1
    cluster_labels[list(graph.nodes)] = range(len(graph.nodes))
    # sort arcs by distances
    #arcs = set()
    #for a in graph.nodes:
    #  for b in graph.edges[a]:
    #    if a < b:
    #      arcs.add((a,b))
    arcs = set([(a,b) for a in graph.nodes for b in graph.edges[a] if a < b])
    cost_and_arc = sorted([(graph.edges[a][b].cost, (a, b)) for (a,b) in arcs])

    # merge from shortest to longest (until arc-cost > inter cluster distance)
    cost_and_arc.reverse()
    while (len(cost_and_arc) > 0 and 
        cost_and_arc[-1][0] < self._intra_dist_thresh):
      cost, (a,b) = cost_and_arc.pop()
      cluster_id_a = cluster_labels[a]
      cluster_id_b = cluster_labels[b]
      if cluster_id_a != cluster_id_b:
        cluster_a = clusters[cluster_id_a]
        cluster_b = clusters[cluster_id_b]
        if cluster_a.distance(cluster_b) < self._inter_dist_thresh:
          merge_clusters(cluster_id_a, cluster_id_b, clusters, cluster_labels)
    return clusters.values()

  def contract_graph(self, exclude_nodes=None):
    ''' Performs the contraction. '''
    for cluster in self.cluster(self.graph, self.node_positions):
      nodes = cluster.nodes
      border_nodes = cluster.determine_border_nodes(self.graph)
      if exclude_nodes: border_nodes = border_nodes.union(exclude_nodes)
      for node in nodes - border_nodes:
        self.graph.contract_node(node)


import unittest
import copy
from graph import Graph, add_biedge, Edge
class TestClusterContraction(unittest.TestCase):
  def setUp(self):
    ''' Create this graph:
        A --- C
        |     |   
        B --- D
    '''
    A, B, C, D = range(4)
    self.g = Graph()
    add_biedge(self.g, A, B, 1)
    add_biedge(self.g, A, C, 3)
    add_biedge(self.g, B, D, 3)
    add_biedge(self.g, C, D, 1)
    self.pos = [(0, 0), (0, 0.0001), (1, 0), (1, 0.0001)]

  def test_merge_cluster(self):
    A, B, C, D = range(4)
    clusters = [Cluster(i, p) for i, p in zip([A, B, C, D], self.pos)]
    reference = clusters[0].distance(clusters[1])
    self.assertLess(abs(reference - clusters[2].distance(clusters[3])), 1)
    self.assertAlmostEqual(reference, clusters[2].distance(clusters[3]), 2)
    ''' Merge A, B and C, D '''
    reference = clusters[0].distance(clusters[2])
    clusters[0].join(clusters[1])
    clusters[2].join(clusters[3])
    clusters = [clusters[0], clusters[2]]
    self.assertEqual(clusters[0].distance(clusters[1]), reference)

  def test_contract_graph1(self):
    ''' Nothing should happen here, because all nodes are border nodes. '''
    reference = copy.deepcopy(self.g)
    c = ClusterContractionAlgorithm(self.g, self.pos)
    c.contract_graph()
    self.assertEqual(self.g, reference)

  def test_contract_graph2(self):
    ''' Extend the graph:
        A --- C
       /|     |\ 
      X |     | Y   contracts to (A, B), (C, D)
       \|     |/
        B --- D
    '''
    A, B, C, D, X, Y = range(6)
    add_biedge(self.g, X, A, 1)
    add_biedge(self.g, X, B, 1)
    add_biedge(self.g, Y, C, 1)
    add_biedge(self.g, Y, D, 1)
    self.pos.append((0, 0.00005))
    self.pos.append((1, 0.00005))
    reference = copy.deepcopy(self.g)
    ''' Cluster and contract...'''
    c = ClusterContractionAlgorithm(self.g, self.pos)
    c.contract_graph()
    self.assertNotEqual(self.g, reference)

  def test_contract_graph3(self):
    ''' Another graph:
    A
    |\ 
    | C ---- D
    |/
    B
    '''
    g = Graph()
    A, B, C, D = range(4)
    add_biedge(g, A, B, 1)
    add_biedge(g, A, C, 1)
    add_biedge(g, B, C, 1)
    add_biedge(g, C, D, 5)
    pos = [(0., 0.0001), (0.0001, 0.), (0., 0.), (10., 0.)]
    c = ClusterContractionAlgorithm(g, pos)
    c.contract_graph()
    self.assertEqual(g.nodes, set([C, D]))
    self.assertEqual(g.edges.items(), [(2, {3 : Edge(5)}), (3, {2 : Edge(5)})])


def main():
  unittest.main()


if __name__ == '__main__':
  main()
