// Copyright 2014: Jonas Sternisko

#include "./GraphConverter.h"
#include <vector>
#include "./DirectedGraph.h"
#include "./AdjacencyGraph.h"

using std::vector;

typedef AdjacencyListGraph<ForestRoadGraph::Node_t, ForestRoadGraph::Arc_t>
    SimplificationGraph;
typedef ForestRoadGraph::Arc_t ForestArc;

// _____________________________________________________________________________
template<>
SimplificationGraph convert_graph(const ForestRoadGraph& input) {
  vector<vector<ForestArc> > adjacencyLists(input.num_nodes());
  for (size_t node = 0; node < input.num_nodes(); ++node) {
    for (const ForestArc& arc: input.arcs(node)) {
      adjacencyLists[node].push_back(arc);
    }
  }
  return SimplificationGraph(input.nodes(), adjacencyLists);
}

// _____________________________________________________________________________
// inverse construction
template<>
ForestRoadGraph convert_graph(const SimplificationGraph& input) {
  vector<ForestArc> arclist;
  vector<size_t> offsets = {0};
  for (size_t node = 0; node < input.num_nodes(); ++node) {
    for (const ForestArc& arc: input.arcs(node)) {
      arclist.push_back(arc);
    }
    offsets.push_back(arclist.size());
  }
  return ForestRoadGraph(arclist, offsets, input.get_nodes());
}

// _____________________________________________________________________________
// inverse construction
template<>
RoadGraph convert_graph(const SimplificationGraph& input) {
  vector<RoadGraph::Arc_t> arclist;
  vector<size_t> offsets = {0};
  for (size_t node = 0; node < input.num_nodes(); ++node) {
    for (const ForestArc& arc: input.arcs(node)) {
      RoadGraph::Arc_t roadArc;
      roadArc.source = arc.source;
      roadArc.target = arc.target;
      roadArc.cost = arc.get_cost();
      arclist.push_back(roadArc);
    }
    offsets.push_back(arclist.size());
  }
  return RoadGraph(arclist, offsets, input.get_nodes());
}

