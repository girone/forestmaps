// Copyright 2013, Chair of Algorithms and Datastructures.

#ifndef COMPACTDIRECTEDGRAPH_H_
#define COMPACTDIRECTEDGRAPH_H_

#include <vector>

// Space and cache efficient graph representation using concatenated adjacency
// lists.
class CompactDirectedGraph {
 public:
  CompactDirectedGraph() {}
  std::vector<N> nodes;
  std::vector<A> outArcs;  // size = #arcs.
  // For each node the offset where its arcs begin.
  std::vector<size_t> outArcOffsets;  // size = #nodes.
};

#endif  // COMPACTDIRECTEDGRAPH_H_
