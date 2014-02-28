// Copyright 2013: Chair of Algorithms and Datastructures.
// Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

// Contains code to compute the largest connected component.

#ifndef SRC_LCC_H_
#define SRC_LCC_H_

#include <cassert>
#include <algorithm>
#include <vector>

using std::vector;

#include "./DirectedGraph.h"

namespace graph_utils {

// Computes the largest connected component of a graph.
template<class Graph>
Graph lcc(const Graph& g);

// Restrict a graph to a given subset of its node indices.
template<class Graph>
Graph restrictToIndices(const Graph& g,
    const std::vector<uint>& node_indices_subset);

}  // namespace


// TEMPLATE DEFINITIONS GO BELOW //

// _____________________________________________________________________________
// Assumes that the graph is bidirectional.
template<class Graph>
Graph graph_utils::lcc(const Graph& g) {
  printf("Determining LCC by BFS...\n");
  vector<bool> node_marks(g.size(), false);
  vector<uint> nodes_in_lcc;
  uint source_node = 0;
  while (source_node < g.size()) {
    // Settle all nodes reachable from source_node in a BFS.
    vector<uint> queue = {source_node};
    node_marks[source_node] = 1;
    for (size_t i = 0; i < queue.size(); ++i) {
      const uint node = queue[i];
      for (const auto& arc: g.arcs(node)) {
        if (!node_marks[arc.headNodeId]) {
          queue.push_back(arc.headNodeId);
          node_marks[arc.headNodeId] = true;
        }
      }
    }
    // Compare with the current LCC.
    if (queue.size() > nodes_in_lcc.size())
      nodes_in_lcc = queue;
    // Find the next source node.
    while (source_node < g.size() && node_marks[source_node])
      ++source_node;
  }
  return restrictToIndices(g, nodes_in_lcc);
}

// _____________________________________________________________________________
template<class Graph>
Graph graph_utils::restrictToIndices(const Graph& g,
    const vector<uint>& node_indices) {
  typedef typename Graph::Node_t Node;
  typedef typename Graph::Arc_t Arc;
  // Create indicator and index-shift function.
  vector<uint> remove(g.size(), 1);
  vector<uint> index_shift(remove.size());
  for (uint i: node_indices) {
    assert(i < g.size());
    remove[i] = 0;
  }
  std::partial_sum(remove.begin(), remove.end(), index_shift.begin());

  // Filter and assign new indices.
  vector<Node> filtered_nodes;
  vector<vector<Arc>> filtered_arcs;
  for (size_t i = 0; i < remove.size(); ++i) {
    if (!remove[i]) {
      filtered_nodes.push_back(g.node(i));
      filtered_arcs.push_back(vector<Arc>());
      for (const Arc& arc: g.arcs(i)) {
        if (!remove[arc.headNodeId]) {
          Arc shifted = arc;
          shifted.headNodeId -= index_shift[shifted.headNodeId];
          filtered_arcs.back().push_back(shifted);
        }
      }
    }
  }
  Graph res(filtered_nodes, filtered_arcs);
  printf("Removed %lu nodes. %lu remain.\n", g.size() - res.size(), res.size());
  return res;
}


#endif  // SRC_LCC_H_
