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
  const std::string string() const { return std::to_string(id); }
};

class TestArc {
 public:
  TestArc(int head) : headNodeId(head) { }  // NOLINT
  int headNodeId;
  const std::string string() const { return std::to_string(headNodeId); }
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
  EXPECT_EQ("{7, 0:[1, 2], 1:[0], 2:[0, 3], 3:[2], 4:[5], 5:[4], 6:[]}",
            g.string());
}

// _____________________________________________________________________________
TEST_F(GraphUtilTest, restrictGraph) {
  TestGraph a = graph_utils::restrictToIndices(g, {A ,B, C, D, E, F, G});
  EXPECT_EQ("{7, 0:[1, 2], 1:[0], 2:[0, 3], 3:[2], 4:[5], 5:[4], 6:[]}",
            a.string());

  TestGraph b = graph_utils::restrictToIndices(g, {G});
  EXPECT_EQ("{1, 6:[]}", b.string());

  TestGraph c = graph_utils::restrictToIndices(g, {E, F});
  EXPECT_EQ("{2, 4:[1], 5:[0]}", c.string());

  TestGraph d = graph_utils::restrictToIndices(g, {A, C, E});
  EXPECT_EQ("{3, 0:[1], 2:[0], 4:[]}", d.string());

  TestGraph e = graph_utils::restrictToIndices(g, {});
  EXPECT_EQ("{0, }", e.string());

  TestGraph f = graph_utils::restrictToIndices(g, {A, B, C, D});
  EXPECT_EQ("{4, 0:[1, 2], 1:[0], 2:[0, 3], 3:[2]}", f.string());
}

// _____________________________________________________________________________
TEST_F(GraphUtilTest, lcc) {
  TestGraph a = graph_utils::lcc(g);
  EXPECT_EQ("{4, 0:[1, 2], 1:[0], 2:[0, 3], 3:[2]}", a.string());
}
