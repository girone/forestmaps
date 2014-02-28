''' graph.py

    Contains classes for Graphs, Edges and Nodes.

    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
    Copyright 2013: Jonas Sternisko
'''
from collections import defaultdict

class Edge:
  def __init__(self, cost):
    self.cost = cost

class Graph:
  def __init__(self):
    self.edges = defaultdict(dict)
    self.nodes = set()

  def add_edge(self, s, t, c):
    ''' Adds an edge from s to t with cost c. '''
    self.nodes.add(s)
    self.nodes.add(t)
    try:
      if self.edges[s][t].cost > c:
        self.edges[s][t] = Edge(c)
    except KeyError:
      self.edges[s][t] = Edge(c)


