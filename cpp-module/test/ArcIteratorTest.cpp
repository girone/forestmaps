// Copyright 2013: Chair of Algorithms and Datastructures.
// Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

#include <gmock/gmock.h>
#include <ostream>
#include <string>
#include <vector>
#include "./GraphTestUtils.h"
#include "../src/DirectedGraph.h"
#include "../src/ArcIterator.h"

using std::ostream;
using std::vector;

// Define simple arc class. Only information if the head node.
class SimpleArc {
 public:
  SimpleArc(size_t id) : headNodeId(id) { }  // NOLINT
  std::string string() const { return std::to_string(headNodeId); }
 private:
  size_t headNodeId;
};

// _____________________________________________________________________________
// NOTE: This is not a real unit-test, but rather a demonstration of the
// functionality of OffsetArcGraph<T>::arcs(node), _AccessMediator, the
// Iterators and string-conversion using the mediator.
TEST(ArcIteratorTest, range_based_for_loop) {
  // Create a totally sound graph.
  vector<SimpleArc> arcs = {   11, 12, 13, 21, 22, 41, 42, 43};
  vector<size_t> offset = { 0, 0,          3,  5,  5,        8};
  typedef OffsetListGraph<SimpleArc> Graph;
  Graph g = forst::test::GraphComposer<Graph>::compose(arcs, offset);

//   for (int i: {0, 1, 2, 3, 4}) {
//     for (const SimpleArc& arc: g.arcs(i)) {
//       std::cout << arc.string() << std::endl;
//     }
//   }

  EXPECT_EQ(0, g.arcs(0).size());
  EXPECT_EQ(3, g.arcs(1).size());
  EXPECT_EQ(2, g.arcs(2).size());
  EXPECT_EQ(0, g.arcs(3).size());
  EXPECT_EQ(3, g.arcs(4).size());

  EXPECT_EQ("", g.arcs(0).string());
  EXPECT_EQ("11, 12, 13", g.arcs(1).string());
  EXPECT_EQ("21, 22", g.arcs(2).string());
  EXPECT_EQ("", g.arcs(3).string());
  EXPECT_EQ("41, 42, 43", g.arcs(4).string());
}
