''' dijkstra.py

    Implementation of Dijkstra's algorithm for shortest paths in graphs. 

    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
    Copyright 2013: Jonas Sternisko
'''
import sys

class Dijkstra:
  def __init__(self, graph):
    self.graph = graph
    self.cost_limit = None

  def set_cost_limit(self, cost):
    ''' Sets an optional cost limit. Algorithm will stop when current pq-elem
        has higher costs.
    '''
    self.cost_limit = cost

  def run(self, start_node):
    ''' Runs Dijkstra's algorithm from @start_node. '''
    def relax_arc(target, new_cost, tentative_costs, priority_queue):
      if new_cost < tentative_costs[target]:
        tentative_costs[target] = new_cost
        priority_queue.put((new_cost, target))
    from Queue import PriorityQueue
    pq = PriorityQueue()
    pq.put((0, start_node))
    settled = [False] * len(self.graph.nodes)
    tentative_costs = [sys.maxint] * len(self.graph.nodes)
    tentative_costs[start_node] = 0
    final_costs = [sys.maxint] * len(self.graph.nodes)
    while not pq.empty():
      cost, node = pq.get()
      if self.cost_limit and self.cost_limit < cost:
        break
      print cost, node
      if not settled[node]:
        for to, edge in self.graph.edges[node].items():
          relax_arc(to, cost + edge.cost, tentative_costs, pq)
        settled[node] = True
        final_costs[node] = cost
    return final_costs

def main():
  ''' Tests this module. '''
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
  print sp == [0, 4, 2, 3, sys.maxint]

if __name__ == '__main__':
  main()
