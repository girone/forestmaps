// Copyright 2013: Chair of Algorithms and Datastructures.
// Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

#include <gmock/gmock.h>
#include <ostream>
#include <string>
#include <vector>
#include "./GraphTestUtils.h"
#include "../src/CompactDirectedGraph.h"
#include "../src/CompactDirectedGraphIterator.h"

using std::ostream;
using std::vector;

// Define some arc class.
class Arc {
 public:
  Arc(size_t id) : headNodeId(id) { }  // NOLINT
  std::string string() const { return std::to_string(headNodeId); }
 private:
  size_t headNodeId;
};

// _____________________________________________________________________________
// This is not a real unit-test, but rather a demonstration of the functionality
// of CompactDirectedGraph<T>::arcs(node), _AccessMediator, the Iterators and
// string-conversion using the mediator.
TEST(CompactDirectedGraphIteratorTest, range_based_for_loop) {
  // Create a totally sound graph.
  vector<Arc> arcs      = {   11, 12, 13, 21, 22, 41, 42, 43};
  vector<size_t> offset = { 0, 0,          3,  5,  5,        8};
  typedef CompactDirectedGraph<Arc> Graph;
  Graph g = forst::test::GraphComposer<Graph>::compose(arcs, offset);

  for (int i: {0, 1, 2, 3, 4}) {
    for (const Arc& arc: g.arcs(i)) {
//       std::cout << arc.string() << std::endl;
    }
  }
  EXPECT_EQ("", g.arcs(0).string());
  EXPECT_EQ("11, 12, 13", g.arcs(1).string());
  EXPECT_EQ("21, 22", g.arcs(2).string());
  EXPECT_EQ("", g.arcs(3).string());
  EXPECT_EQ("41, 42, 43", g.arcs(4).string());
}
