''' Contains code for graph contraction.

    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
'''

class SimpleContractionAlgorithm(object):
  ''' A node is contracted by removing it and its adjacent edges from the graph
      and adding shortcuts between its neighbors such that the connectivity of
      the neighbors is maintained.
      
      This class performs a very simple contraction to the graph: All nodes with
      adjacent edges of 'length' shorter than @cost_threshold are successively
      contracted.
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
        TODO(Jonas): Implement something here.
    '''
    return old_candidates

  def contract_node(self, node):
    ''' Contracts a node using the graphs method. '''
    self.graph.contract_node(node)

  def contract_graph(self, exclude_nodes=None):
    ''' Performs the contraction. Algorithm entry point. '''
    candidates = self.compute_candidates()
    if exclude_nodes:
      candidates -= set(exclude_nodes)
    print candidates
    print "%d candidates will be contracted" % len(candidates)
    while candidates:
      c = candidates.pop()
      new_shortcuts = self.contract_node(c)
      candidates = self.update_candidates(candidates, new_shortcuts)


def main():
  import visual_grid
  import pickle



if __name__ == '__main__':
  main()
