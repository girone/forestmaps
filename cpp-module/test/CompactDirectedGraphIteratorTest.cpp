// Copyright 2013: Jonas Sternisko

#include <gmock/gmock.h>
#include <vector>
#include "./GraphTestUtils.h"
#include "../src/CompactDirectedGraph.h"
#include "../src/CompactDirectedGraphIterator.h"

using std::vector;

// Define any arc class.
class Arc {
 public:
  Arc(size_t id) : headNodeId(id) { }
  std::string debugStr() const { return std::to_string(headNodeId); }
 private:
  size_t headNodeId;
};


TEST(CompactDirectedGraphIteratorTest, range_based_for_loop) {
  // Create a totally sound graph.
  vector<Arc> arcs        = {   11, 12, 13, 21, 22, 41, 42, 43};
  vector<size_t> offset   = { 0, 0,          3,  5,  5,        8};
  CompactDirectedGraph<Arc> g =
      forst::test::GraphComposer<CompactDirectedGraph<Arc>>::compose(arcs, offset);



  for (int i: {0, 1, 2, 3, 4}) {
    for (const Arc& arc: g.arcs(i)) {
      std::cout << arc.debugStr() << std::endl;
    }
  }
}

