// Copyright 2013: Chair of Algorithms and Datastructures.
// Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

#include <gmock/gmock.h>
#include <string>
#include <vector>
#include "../src/LCC.h"
#include "../src/OSMGraph.h"

using std::string;
using std::vector;

class TestNode {
 public:
  TestNode(int id) : id(id) { }  // NOLINT
  int id;
};

class TestArc {
 public:
  TestArc(int head) : headNodeId(head) { }  // NOLINT
  int headNodeId;
  const string getSummaryString() const { return std::to_string(headNodeId); }
};

/*    A ---- B      F      G
 *    |             |
 *    |             |
 *    C ---- D      E
 *
 * */
class GraphUtilTest : public ::testing::Test {
 public:
  GraphUtilTest() {
    vector<TestNode> nodes = {A, B, C, D, E, F, G};
    vector<vector<TestArc>> arcs = {{B, C}, {A}, {A, D}, {C}, {F}, {E}, {}};
    g = DirectedGraph<TestNode, TestArc>(nodes, arcs);
  }
 protected:
  enum {A ,B, C, D, E, F, G};
  typedef DirectedGraph<TestNode, TestArc> TestGraph;
  TestGraph g;
};

// _____________________________________________________________________________
TEST_F(GraphUtilTest, self_test) {
  EXPECT_EQ("{7, [1, 2], [0], [0, 3], [2], [5], [4], []}",
            g.getSummaryString());
}

// _____________________________________________________________________________
TEST_F(GraphUtilTest, restrictGraph) {
  TestGraph a = graph_utils::restrictToIndices(g, {A ,B, C, D, E, F, G});
  EXPECT_EQ("{7, [1, 2], [0], [0, 3], [2], [5], [4], []}",
            a.getSummaryString());

  TestGraph b = graph_utils::restrictToIndices(g, {G});
  EXPECT_EQ("{1, []}", b.getSummaryString());

  TestGraph c = graph_utils::restrictToIndices(g, {E, F});
  EXPECT_EQ("{2, [1], [0]}", c.getSummaryString());

  TestGraph d = graph_utils::restrictToIndices(g, {A, C, E});
  EXPECT_EQ("{3, [1], [0], []}", d.getSummaryString());

  TestGraph e = graph_utils::restrictToIndices(g, {});
  EXPECT_EQ("{0, }", e.getSummaryString());

  TestGraph f = graph_utils::restrictToIndices(g, {A, B, C, D});
  EXPECT_EQ("{4, [1, 2], [0], [0, 3], [2]}", f.getSummaryString());
}

// _____________________________________________________________________________
TEST_F(GraphUtilTest, lcc) {
  TestGraph a = graph_utils::lcc(g);
  EXPECT_EQ("{4, [1, 2], [0], [0, 3], [2]}", a.getSummaryString());
}
