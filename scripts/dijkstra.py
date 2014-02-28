''' dijkstra.py

    Implementation of Dijkstra's algorithm for shortest paths in graphs. 

    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
    Copyright 2013: Jonas Sternisko
'''
import sys
from Queue import PriorityQueue

class Dijkstra:
  def __init__(self, graph):
    self.graph = graph
    self.inf = sys.maxint
    self.cost_limit = None
    self.forbidden_edges = None

  def set_cost_limit(self, cost):
    ''' Sets an optional cost limit. Algorithm will stop when current pq-elem
        has higher costs.
    '''
    self.cost_limit = cost

  def set_forbidden_edges(self, edges):
    ''' Sets an optional set of edges which must not be used by the search. '''
    self.forbidden_edges = edges

  def run(self, start_node):
    ''' Runs Dijkstra's algorithm from @start_node. '''
    def relax_arc(target, new_cost):
      if new_cost < self.tentative_costs[target]:
        self.tentative_costs[target] = new_cost
        self.pq.put((new_cost, target))
    self.pq = PriorityQueue()
    self.pq.put((0, start_node))
    num_nodes = self.graph.size()
    self.settled = [False] * num_nodes
    self.tentative_costs = [self.inf] * num_nodes
    self.tentative_costs[start_node] = 0
    self.final_costs = [self.inf] * num_nodes
    while not self.pq.empty():
      cost, node = self.pq.get()
      if self.cost_limit and cost > self.cost_limit:
        break
      if not self.settled[node]:
        for to, edge in self.graph.edges[node].items():
          if not self.forbidden_edges or (node, to) not in self.forbidden_edges:
            relax_arc(to, cost + edge.cost)
        self.settled[node] = True
        self.final_costs[node] = cost
    return self.final_costs


import unittest 
class TestDijkstra(unittest.TestCase):
  def test_dijkstra(self):
    from graph import Graph
    A, B, C, D, E = 0, 1, 2, 3, 4
    g = Graph()
    g.add_edge(A, B, 4)
    g.add_edge(A, C, 2)
    g.add_edge(C, D, 1)
    g.add_edge(D, B, 1)
    g.add_edge(B, E, 1)
    d1 = Dijkstra(g)
    sp = d1.run(A)
    print sp == [0, 4, 2, 3, 5]
    
    d2 = Dijkstra(g)
    d2.set_cost_limit(4)
    sp = d2.run(A)
    print sp == [0, 4, 2, 3, self.inf]


def main():
  ''' Tests this module. '''
  unittest.main()

if __name__ == '__main__':
  main()
