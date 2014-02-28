// Copyright 2014: Jonas Sternisko

#include <gtest/gtest.h>
#include <string>
#include <fstream>
#include "../src/GraphConverter.h"
#include "../src/DirectedGraph.h"
#include "../src/GraphSimplificator.h"

using std::string;
using std::endl;

// _____________________________________________________________________________
TEST(GraphConvertedTest, offset_adjacency_offset) {
  {
    // Create a graph file
    string filename = "offset_graph.tmp.txt";
    std::ofstream ofs(filename);
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

  // Read the offset graph
  ForestRoadGraph input;
  input.read_in("offset_graph.tmp.txt");

  // Check if it is ok.
  ASSERT_EQ("[3,5,{(0,1,[10,1,-1])(0,2,[4,45,-1])},"
            "{(1,0,[5,5,-1])(1,2,[4,0,-1])},{(2,1,[4,10,-1])}]",
            input.to_string());
  ASSERT_EQ(3, input.num_nodes());
  ASSERT_EQ(5, input.num_arcs());

  {
    // Convert to adjacency graph
    SimplificationGraph adjacencyGraph =
        convert_graph<ForestRoadGraph, SimplificationGraph>(input);

    // Check if it is ok
    EXPECT_EQ(3, adjacencyGraph.num_nodes());
    EXPECT_EQ(5, adjacencyGraph.count_arcs());
    EXPECT_EQ("[3,5,{(0,1,[10,1,-1])(0,2,[4,45,-1])},"
              "{(1,0,[5,5,-1])(1,2,[4,0,-1])},{(2,1,[4,10,-1])}]",
              adjacencyGraph.to_string());

    // Convert back to offset graph
    ForestRoadGraph restoredGraph =
        convert_graph<SimplificationGraph, ForestRoadGraph>(adjacencyGraph);

    // Should be the same as before
    EXPECT_EQ("[3,5,{(0,1,[10,1,-1])(0,2,[4,45,-1])},"
              "{(1,0,[5,5,-1])(1,2,[4,0,-1])},{(2,1,[4,10,-1])}]",
              restoredGraph.to_string());
  }
}

// _____________________________________________________________________________
TEST(GraphConvertedTest, adjacency_offset_adjacency) {
  {
    // Create a graph file
    string filename = "adjacency_graph.tmp.txt";
    std::ofstream ofs(filename);
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

  // Read the adjacency graph
  SimplificationGraph input;
  input.read_in("adjacency_graph.tmp.txt");

  // Check if it is ok.
  ASSERT_EQ("[3,5,{(0,1,[10,1,-1])(0,2,[4,45,-1])},"
            "{(1,0,[5,5,-1])(1,2,[4,0,-1])},{(2,1,[4,10,-1])}]",
            input.to_string());

  {
    // Convert to offset graph
    ForestRoadGraph offsetGraph =
        convert_graph<SimplificationGraph, ForestRoadGraph>(input);

    // Check if it is ok
    EXPECT_EQ("[3,5,{(0,1,[10,1,-1])(0,2,[4,45,-1])},"
              "{(1,0,[5,5,-1])(1,2,[4,0,-1])},{(2,1,[4,10,-1])}]",
              offsetGraph.to_string());

    // Convert back to adjacency graph
    SimplificationGraph restored =
        convert_graph<ForestRoadGraph, SimplificationGraph>(offsetGraph);

    // Should be the same as before
    EXPECT_EQ("[3,5,{(0,1,[10,1,-1])(0,2,[4,45,-1])},"
              "{(1,0,[5,5,-1])(1,2,[4,0,-1])},{(2,1,[4,10,-1])}]",
              restored.to_string());
  }
}

// _____________________________________________________________________________
TEST(GraphConvertedTest, adjacency_to_road_graph) {
  {
    // Create a graph file
    string filename = "adjacency_graph.tmp.txt";
    std::ofstream ofs(filename);
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

  // Read the adjacency graph
  SimplificationGraph input;
  input.read_in("adjacency_graph.tmp.txt");

  // Check if it is ok.
  ASSERT_EQ("[3,5,{(0,1,[10,1,-1])(0,2,[4,45,-1])},"
            "{(1,0,[5,5,-1])(1,2,[4,0,-1])},{(2,1,[4,10,-1])}]",
            input.to_string());

  {
    // Convert to offset graph
    RoadGraph offsetGraph =
        convert_graph<SimplificationGraph, RoadGraph>(input);

    // Check if it is ok
    EXPECT_EQ("[3,5,{(1,10)(2,4)},"
              "{(0,5)(2,4)},{(1,4)}]",
              offsetGraph.to_string());
  }
}
