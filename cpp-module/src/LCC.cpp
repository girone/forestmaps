// Copyright 2013: Chair of Algorithms and Datastructures.
// Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

#include "./LCC.h"
#include <cassert>
#include <algorithm>
#include <vector>

using std::vector;

// _____________________________________________________________________________
// Assumes that the graph is bidirectional.
OSMGraph graph_utils::lcc(const OSMGraph& g) {
  vector<bool> node_marks(g.numNodes(), false);
  vector<uint> nodes_in_lcc;
  uint source_node = 0;
  while (source_node < g.numNodes()) {
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
    while (source_node < g.numNodes() && node_marks[source_node])
      ++source_node;
  }
  return restrictGraphToIndices(g, nodes_in_lcc);
}

// _____________________________________________________________________________
OSMGraph graph_utils::restrictGraphToIndices(const OSMGraph& g,
    const vector<uint>& node_indices) {
  // Create indicator and index-shift function.
  vector<uint> remove(g.numNodes(), 1);
  vector<uint> index_shift(remove.size());
  for (uint i: node_indices) {
    assert(i < g.numNodes());
    remove[i] = 0;
  }
  std::partial_sum(remove.begin(), remove.end(), index_shift.begin());

  // Filter and assign new indices.
  vector<OSMNode> filtered_nodes;
  vector<vector<OSMArc>> filtered_arcs;
  for (size_t i = 0; i < remove.size(); ++i) {
    if (!remove[i]) {
      filtered_nodes.push_back(g.node(i));
      filtered_arcs.push_back(vector<OSMArc>());
      for (const OSMArc& arc: g.arcs(i)) {
        filtered_arcs.back().push_back(
            OSMArc(arc.duration, arc.headNodeId - index_shift[i]));
      }
    }
  }
  OSMGraph res(filtered_nodes, filtered_arcs);
  return res;
}
