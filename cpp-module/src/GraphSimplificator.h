// Copyright 2014: Jonas Sternisko

#ifndef SRC_SIMPLIFYGRAPH_H_
#define SRC_SIMPLIFYGRAPH_H_

#include <gtest/gtest_prod.h>
#include <set>
#include <unordered_map>
#include <vector>
#include "./DirectedGraph.h"
#include "./AdjacencyGraph.h"

using std::set;
using std::unordered_map;
using std::vector;

typedef AdjacencyListGraph<ForestRoadGraph::Node_t, ForestRoadGraph::Arc_t>
    SimplificationGraph;

// Simplyfies a graph by 'contracting' nodes of along non-branching chains.
// Remembers for each shortcut which arcs of the original graph it representd.
//
class GraphSimplificator {
 public:
  GraphSimplificator(SimplificationGraph* input);
  // Builds and returns the simplified version of the input. Adds shortcuts to
  // the input, so it grows in size. Assumes the input has only bidirectional
  // arcs.
  SimplificationGraph simplify(const set<uint>* doNotContract=NULL);

  // returns the mapping.
  const unordered_map<int, vector<int>>& edgeIndexToFidsMap() const;

 private:
  // Contracts a node, if possible. That depends on an internal check. Returns
  // true if it contracted the node.
  bool contract_node(size_t node, const vector<bool>& contractedFlags);

  // Initializes the mapping from arc id to represented fids.
  void initialize_mapping();

  // Builds the simplified graph from the uncontracted part of the graph.
  SimplificationGraph extract_simplified_graph(const vector<bool>& contracted)
      const;

  // Pointer to the input. Shortcuts are added to this graph.
  SimplificationGraph* _input;

  // Stores the FIDs represented by arcs to non-contracted nodes.
  unordered_map<int, vector<int>> _representedFids;

  // Count the number of arcs.
  size_t _arcCount;

  FRIEND_TEST(GraphSimplificatorTest, contract_node);
};



typedef SimplificationGraph::Arc_t Arc;
struct ArcFactory {
  static Arc create(int source, int target, int c, int w, int fid);
};

#endif  // SRC_SIMPLIFYGRAPH_H_
