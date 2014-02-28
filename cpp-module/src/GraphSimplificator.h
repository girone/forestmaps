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
  const unordered_map<int, vector<int>>& edges_contained_in_shortcut_map() const;
  // Returns the index shift for each node.
  const vector<int>& index_shift() const;

 private:
  // Contracts a node, if possible. That depends on an internal check. Returns
  // true if it contracted the node.
  bool try_to_contract_node(size_t node, const vector<bool>& contractedFlags);

  // Initializes the mapping from arc id to represented fids.
  void initialize_mapping();

  // Builds the simplified graph from the uncontracted part of the graph.
  SimplificationGraph extract_simplified_graph(const vector<bool>& contracted);

  // Pointer to the input. Shortcuts are added to this graph.
  SimplificationGraph* _input;

  // Stores the edge indices represented by non-obsolete shortcuts.
  unordered_map<int, vector<int>> _representedIds;

  // The index shift value for each node.
  vector<int> _indexShift;

  // Count the number of arcs.
  size_t _arcCount;

  FRIEND_TEST(GraphSimplificatorTest, try_to_contract_node);
};



typedef SimplificationGraph::Arc_t Arc;
struct ArcFactory {
  static Arc create(int source, int target, int c, int w, int fid);
};

#endif  // SRC_SIMPLIFYGRAPH_H_
