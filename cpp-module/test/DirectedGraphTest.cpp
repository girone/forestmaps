// Copyright 2013: Jonas Stegraphisko

#include <gtest/gtest.h>
#include "../src/DirectedGraph.h"
#include "../src/Util.h"

using std::string;

// _____________________________________________________________________________
TEST(DirectedGraphTest, to_string) {
  {
    RoadGraph graph;
    ASSERT_EQ("[0,0,]", graph.to_string());

    graph._nodes.assign(3, RoadGraph::Node_t());
    graph._offset.assign(3+1, 0);
    graph._arcList = vector<RoadGraph::Arc_t>();
    EXPECT_EQ("[3,0,{},{},{}]", graph.to_string());
  }
}

// _____________________________________________________________________________
TEST(DirectedGraphTest, compute_offsets) {
  typedef RoadGraph::Arc_t Arc;
  {
    vector<Arc> arcList;
    vector<size_t> offsets = compute_offsets(arcList, 0);
    EXPECT_EQ(vector<size_t>({0}), offsets);

    offsets = compute_offsets(arcList, 3);
    EXPECT_EQ(vector<size_t>({0, 0, 0, 0}), offsets);
  }

  {
    int c = 0;  // dummy
    vector<Arc> arcList = {Arc(0, 7, c),
                           Arc(0, 8, c),
                           Arc(0, 10, c),
                           Arc(1, 3, c),
                           Arc(1, 10, c),
                           Arc(2, 9, c),
                           Arc(2, 9, c),
                           Arc(2, 4, c),
                           Arc(5, 9, c),
                           Arc(7, 8, c)};
    std::sort(arcList.begin(), arcList.end(), CompareArcs<Arc>());
    vector<size_t> offsets = compute_offsets(arcList, 8);
    EXPECT_EQ("0,3,5,8,8,8,9,9,10", util::join(",", offsets));
  }

  {
    // [4,2,{},{(1,3)(2,5)},{},{}]
    vector<Arc> arcList = {Arc(1, 1, 3),
                           Arc(1, 2, 5)};
    std::sort(arcList.begin(), arcList.end(), CompareArcs<Arc>());
    vector<size_t> offsets = compute_offsets(arcList, 4);
    EXPECT_EQ("0,0,2,2,2", util::join(",", offsets));
  }
}

// _____________________________________________________________________________
TEST(DirectedGraphTest, from_string) {
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
    RoadGraph graph;
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
TEST(DirectedGraphTest, one_more_test) {
  {
    OffsetListGraph<SourceTargetCostArc> graph;
    graph.from_string("[4,2,{},{(1,3)(2,5)},{},{}]");
    EXPECT_EQ(4, graph.num_nodes());
    EXPECT_EQ(2, graph.num_arcs());
    EXPECT_EQ("[4,2,{},{(1,3)(2,5)},{},{}]", graph.to_string());
  }
  {
    RoadGraph graph;
    graph.from_string("[4,2,{},{(1,3)(2,5)},{},{}]");
    EXPECT_EQ("[4,2,{},{(1,3)(2,5)},{},{}]", graph.to_string());
  }
}

// _____________________________________________________________________________
TEST(DirectedGraphTest, from_stream) {
  {
    // Check nodes
    std::stringstream ss;
    ss << "12  99" << std::endl;
    RoadGraph::Node_t n;
    n.from_stream(ss);
    EXPECT_EQ(12, n.x);
    EXPECT_EQ(99, n.y);
    EXPECT_EQ("12 99", n.to_string());
  }

  {
    // Check arcs
    std::stringstream ss;
    ss << "5    7  42";
    RoadGraph::Arc_t arc;
    arc.from_stream(ss);
    EXPECT_EQ(5, arc.source);
    EXPECT_EQ(7, arc.target);
    EXPECT_EQ(42, arc.cost);
    EXPECT_EQ("(7,42)", arc.to_string());
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
    ofs << "1 3  0" << std::endl;
    ofs << "1 10 0" << std::endl;
    ofs << "2 9  0" << std::endl;
    ofs << "2 9  0" << std::endl;
    ofs << "2 4  0" << std::endl;
    ofs << "5 8  0" << std::endl;
    ofs << "7 8  0" << std::endl;
  }

  {
    RoadGraph graph;
    graph.read_in("from_stream.tmp.txt");

    EXPECT_EQ("[9,10,{(7,0)(8,0)(10,0)},{(3,0)(10,0)},{(4,0)(9,0)(9,0)},{},{},{(8,0)},{},{(8,0)},{}]",  // NOLINT
              graph.to_string());
  }
}

// _____________________________________________________________________________
TEST(DirectedGraphTest, forest_graph_from_file) {
  const string filename = "test.forest_graph_from_file.tmp.txt";
  {
    std::ofstream ofs(filename);
    using std::endl;
    ofs << "3" << endl
        << "5" << endl
        << "4.5 4.2" << endl
        << "5.5 5.2" << endl
        << "6.5 6.2" << endl
        << "0 1 10.1 1" << endl
        << "1 0 5.5 5" << endl
        << "1 2 4.2 0" << endl
        << "2 1 4.2 10" << endl
        << "0 2 4.2 45" << endl;
  }

  {
    ForestRoadGraph fg;
    fg.read_in(filename);
    EXPECT_EQ(
     "[3,5,{(0,1,[10,1])(0,2,[4,45])},{(1,0,[5,5])(1,2,[4,0])},{(2,1,[4,10])}]",
     fg.to_string()
    );
  }
}

// _____________________________________________________________________________
TEST(NodesAndEdgesTest, from_stream) {
  {
    SourceTargetTwoCostsArc arc;
    arc.source = 24;
    arc.target = 42;
    arc.cost = {0, 12};
    EXPECT_EQ("(24,42,[0,12])", arc.to_string());
  }

  {
    std::stringstream s;
    s << "0 1 53 10";
    SourceTargetTwoCostsArc arc;
    arc.from_stream(s);
    EXPECT_EQ("(0,1,[53,10])", arc.to_string());
  }

  {
    std::stringstream s;
    s << "0 1 53.3 10";
    SourceTargetTwoCostsArc arc;
    arc.from_stream(s);
    EXPECT_EQ("(0,1,[53,10])", arc.to_string());
  }
}
