// Copyright 2013: Jonas Stegraphisko

#include <gtest/gtest.h>
#include <gtest/gtest_prod.h>
#include <vector>
#include "../src/AdjacencyGraph.h"
#include "../src/GraphConverter.h"
#include "../src/GraphSimplificator.h"
#include "../src/Util.h"

using std::string;
using std::vector;

// A test node.
class TestNode {
 public:
  void from_stream(std::istream& is) {
    is >> value;
  }
  string to_string() const {
    std::stringstream ss;
    ss << value;
    return ss.str();
  }
  float value;
};

// A test arc.
class TestArc {
 public:
  //TestArc() : source(-1), target(-1), cost(0) { }
  //TestArc(int s, int t, int c) : source(s), target(t), cost(c) { }
  void from_stream(std::istream& is) {
    is >> source >> target >> cost;
  }
  string to_string() const {
    std::stringstream ss;
    ss << "(" << source << "," << target << "," << cost << ")";
    return ss.str();
  }

  int source;
  int target;
  int cost;
};

typedef AdjacencyListGraph<TestNode, TestArc> TestGraph;


// _____________________________________________________________________________
TEST(AdjacencyListGraphTest, to_string) {
  {
    TestGraph graph;
    ASSERT_EQ("[0,0,]", graph.to_string());

    graph._nodes.assign(3, TestGraph::Node_t());
    graph._arcs = vector<vector<TestGraph::Arc_t>>(3);
    EXPECT_EQ("[3,0,{},{},{}]", graph.to_string());
  }
}

/*
// _____________________________________________________________________________
TEST(AdjacencyListGraphTest, from_string) {
  {
    OffsetListGraph<SourceTargetCostArc> graph;
    graph.from_string("[3,2,{(1,3)},{},{(2,5)}]");

    ASSERT_EQ(3, graph.size());
    ASSERT_EQ(2, graph.num_arcs());

    EXPECT_EQ(1, graph.arcs(0).begin()->target);
    EXPECT_EQ(3, graph.arcs(0).begin()->cost);
    EXPECT_EQ(0, graph.arcs(1).size());
    EXPECT_EQ(2, graph.arcs(2).begin()->target);
    EXPECT_EQ(5, graph.arcs(2).begin()->cost);
  }
  {
    TestGraph graph;
    graph.from_string("[3,2,{(1,3)},{},{(2,5)}]");
    EXPECT_EQ("[3,2,{(1,3)},{},{(2,5)}]", graph.to_string());

    ASSERT_EQ(3, graph.size());
    ASSERT_EQ(2, graph.num_arcs());

    EXPECT_EQ(1, graph.arcs(0).begin()->target);
    EXPECT_EQ(3, graph.arcs(0).begin()->cost);
    EXPECT_EQ(0, graph.arcs(1).size());
    EXPECT_EQ(2, graph.arcs(2).begin()->target);
    EXPECT_EQ(5, graph.arcs(2).begin()->cost);
  }
}

// _____________________________________________________________________________
TEST(AdjacencyListGraphTest, one_more_test) {
  {
    OffsetListGraph<SourceTargetCostArc> graph;
    graph.from_string("[4,2,{},{(1,3)(2,5)},{},{}]");
    EXPECT_EQ(4, graph.num_nodes());
    EXPECT_EQ(2, graph.num_arcs());
    EXPECT_EQ("[4,2,{},{(1,3)(2,5)},{},{}]", graph.to_string());
  }
  {
    TestGraph graph;
    graph.from_string("[4,2,{},{(1,3)(2,5)},{},{}]");
    EXPECT_EQ("[4,2,{},{(1,3)(2,5)},{},{}]", graph.to_string());
  }
}*/

// _____________________________________________________________________________
TEST(AdjacencyListGraphTest, read_in) {
  {
    // Check nodes
    std::stringstream ss;
    ss << "12  " << std::endl;
    TestGraph::Node_t n;
    n.from_stream(ss);
    EXPECT_EQ(12, n.value);
    EXPECT_EQ("12", n.to_string());
  }

  {
    // Check arcs
    std::stringstream ss;
    ss << "5    7  42";
    TestGraph::Arc_t arc;
    arc.from_stream(ss);
    EXPECT_EQ(5, arc.source);
    EXPECT_EQ(7, arc.target);
    EXPECT_EQ(42, arc.cost);
    EXPECT_EQ("(5,7,42)", arc.to_string());
  }

  {
    string filename = "from_stream.tmp.txt";
    std::ofstream ofs(filename);
    ofs << "9" << std::endl;
    ofs << "10" << std::endl;

    // Nodes
    ofs << "42 42" << std::endl;
    ofs << "42 42" << std::endl;
    ofs << "42 42" << std::endl;
    ofs << "42 42" << std::endl;
    ofs << "42 42" << std::endl;
    ofs << "42 42" << std::endl;
    ofs << "42 42" << std::endl;
    ofs << "42 42" << std::endl;
    ofs << "42 42" << std::endl;

    // Arcs
    ofs << "0 7  0" << std::endl;
    ofs << "0 8  0" << std::endl;
    ofs << "0 10 0" << std::endl;
    ofs << "1 3  0 99 55 77" << std::endl;  // Works with unregular input?
    ofs << "1 10 0" << std::endl;
    ofs << "2 9  0" << std::endl;
    ofs << "2 9  0" << std::endl;
    ofs << "2 4  0" << std::endl;
    ofs << "5 8  0" << std::endl;
    ofs << "7 8  0" << std::endl;
  }

  {
    TestGraph graph;
    graph.read_in("from_stream.tmp.txt");

    EXPECT_EQ("[9,10,{(0,7,0)(0,8,0)(0,10,0)},{(1,3,0)(1,10,0)},{(2,4,0)(2,9,0)"
               "(2,9,0)},{},{},{(5,8,0)},{},{(7,8,0)},{}]",
              graph.to_string());
  }
}

// _____________________________________________________________________________
// These arcs store also an FIDs (reference to the original shape in ArcGIS).
TEST(AdjacencyListGraphTest, forest_graph_from_file_with_fids) {
  const string filename = "test.forest_graph_from_file.tmp.txt";
  {
    std::ofstream ofs(filename);
    using std::endl;
    ofs << "3" << endl
        << "5" << endl
        << "4.5 4.2 " << endl
        << "5.5 5.2" << endl
        << "6.5 6.2" << endl
        << "0 1 10.1 1 1" << endl
        << "1 0 5.5 5 2" << endl
        << "1 2 4.2 0 3" << endl
        << "2 1 4.2 10 4" << endl
        << "0 2 4.2 45 5" << endl;
  }

  {
    SimplificationGraph fg;
    fg.read_in(filename);
    EXPECT_EQ(
     "[3,5,{(0,1,[10,1,1])(0,2,[4,45,5])},{(1,0,[5,5,2])(1,2,[4,0,3])},"
     "{(2,1,[4,10,4])}]",
     fg.to_string()
    );
  }
}

