// Copyright 2011-2012: Jonas Stegraphisko, Jendrik Seipp, Philip Stahl
// This file contains tests for Dijkstra with and without AStar using either
// straight line or landmark heuristic.
#include <gtest/gtest.h>
#include "../src/Dijkstra.h"

typedef Dijkstra<RoadGraph> RoadDijkstra;


// _____________________________________________________________________________
TEST(DijkstraTest, computeShortestPath) {
  string s = "[8,10,{(6,1)(2,5)(5,1)},{},{(3,1)},{(4,1)},{(1,1)},"
             "{(1,12)(7,1)},{(7,2)},{(1,8)}]";

  RoadGraph graph;
  graph.from_string(s);
  RoadDijkstra dijkstra(graph);
  EXPECT_EQ(8, dijkstra.shortestPath(0, 1));

  vector<uint> origins = dijkstra.getOrigins();
  EXPECT_EQ(4, origins[1]);
  EXPECT_EQ(3, origins[4]);
  EXPECT_EQ(2, origins[3]);
  EXPECT_EQ(0, origins[2]);
}


// _____________________________________________________________________________
/*
 *    2
 *    ^
 *    |
 *    |
 *    |
 *    |
 *    0-->1
 *
 */
TEST(DijkstraTest, computeShortestPathThreeNodes) {
  RoadGraph graph;
  graph.from_string("[3,2,{(1,3)(2,5)},{},{}]");

  RoadDijkstra dijkstra(graph);
  EXPECT_EQ(5, dijkstra.shortestPath(0, 2));
  EXPECT_TRUE(dijkstra.isSettled(0));
  EXPECT_TRUE(dijkstra.isSettled(1));
  EXPECT_TRUE(dijkstra.isSettled(2));
}


// _____________________________________________________________________________
/*
 *    2
 *    ^
 *    |\
 *  4 | \ 5
 *    |  \
 *    0-->1
 *      3
 *
 */
TEST(DijkstraTest, computeShortestPathThreeArcs) {
  RoadGraph graph;
  graph.from_string("[3,3,{(1,3)(2,4)},{(2,5)},{}]");

  RoadDijkstra dijkstraStd(graph);
  EXPECT_EQ(4, dijkstraStd.shortestPath(0, 2));
  EXPECT_TRUE(dijkstraStd.isSettled(0));
  EXPECT_TRUE(dijkstraStd.isSettled(1));
  EXPECT_TRUE(dijkstraStd.isSettled(2));
  // make sure multiple calls of shortest path behave properly (array reset)
  EXPECT_EQ(5, dijkstraStd.shortestPath(1, 2));
  EXPECT_FALSE(dijkstraStd.isSettled(0));
  EXPECT_TRUE(dijkstraStd.isSettled(1));
  EXPECT_TRUE(dijkstraStd.isSettled(2));
  dijkstraStd.shortestPath(0,1);
  EXPECT_TRUE(dijkstraStd.isSettled(0));
  EXPECT_TRUE(dijkstraStd.isSettled(1));
  EXPECT_FALSE(dijkstraStd.isSettled(2));

}


// _____________________________________________________________________________
/*
 *       2
 *      / \
 *    7/   \5
 *    /     \
 *   0-------1
 *       1
 * When we settle all nodes from 2, make sure origin(0) == 1 and != 2.
 */
TEST(DijkstraTest, origins) {
  RoadGraph graph;
  graph.from_string("[3,6,"
                   "{(1,1)(2,7)},"
                   "{(0,1)(2,5)},"
                   "{(0,7)(1,5)}]");
  RoadDijkstra dijkstra(graph);
  dijkstra.shortestPath(2, std::numeric_limits<int>::max());

  EXPECT_EQ(1, dijkstra.getOrigins()[0]);
}


// _____________________________________________________________________________
/*
 *    0 <--> 1 <--> 2              each arc has cost 3
 */
// Examines if limited versions of the dijkstra work properly and if the
// algorithm's reset works.
TEST(DijkstraTest, limitedDijkstraReset) {
  RoadGraph graph;
  graph.from_string("[3,4,{(1,3)},{(2,3),(0,3)},{(1,3)}]");
  RoadDijkstra dijkstra(graph);
//   // check it for hop limit
//   dijkstra.setHopLimit(1);
//   dijkstra.shortestPath(0, RoadDijkstra::no_target);
//   EXPECT_TRUE(dijkstra.isSettled(0));
//   EXPECT_TRUE(dijkstra.isSettled(1));
//   EXPECT_FALSE(dijkstra.isSettled(2));
//   dijkstra.shortestPath(2, RoadDijkstra::no_target);
//   EXPECT_FALSE(dijkstra.isSettled(0));
//   EXPECT_TRUE(dijkstra.isSettled(1));
//   EXPECT_TRUE(dijkstra.isSettled(2));

  // check for cost limit
  dijkstra.set_cost_limit(4);
  dijkstra.shortestPath(0, RoadDijkstra::no_target);
  EXPECT_TRUE(dijkstra.isSettled(0));
  EXPECT_TRUE(dijkstra.isSettled(1));
  EXPECT_FALSE(dijkstra.isSettled(2));
  dijkstra.shortestPath(2, RoadDijkstra::no_target);
  EXPECT_FALSE(dijkstra.isSettled(0));
  EXPECT_TRUE(dijkstra.isSettled(1));
  EXPECT_TRUE(dijkstra.isSettled(2));

  // check for nodes to be settled
  dijkstra.set_cost_limit(RoadDijkstra::infinity);
  vector<bool> nodesToSettle(3, false);
  nodesToSettle[1] = true;
  dijkstra.setNodesToBeSettledMarks(&nodesToSettle, 1);
  dijkstra.shortestPath(0, RoadDijkstra::no_target);
  EXPECT_TRUE(dijkstra.isSettled(0));
  EXPECT_TRUE(dijkstra.isSettled(1));
  EXPECT_FALSE(dijkstra.isSettled(2));
  dijkstra.shortestPath(2, RoadDijkstra::no_target);
  EXPECT_FALSE(dijkstra.isSettled(0));
  EXPECT_TRUE(dijkstra.isSettled(1));
  EXPECT_TRUE(dijkstra.isSettled(2));
}


// _____________________________________________________________________________
/*
 *       2
 *      / \
 *    7/   \5
 *    /     \
 *   0-------1
 *       1
 * Ignore a node during search.
 */
TEST(DijkstraTest, ignore_nodes) {
  RoadGraph graph;
  graph.from_string("[3,6,"
                   "{(1,1)(2,7)},"
                   "{(0,1)(2,5)},"
                   "{(0,7)(1,5)}]");
  // Without ignoring a node.
  RoadDijkstra dijkstra(graph);
  dijkstra.shortestPath(0, RoadDijkstra::no_target);
  EXPECT_EQ(1, dijkstra.getOrigins()[2]);
  EXPECT_EQ(6, dijkstra.get_costs()[2]);

  // Ignore node 1.
  vector<bool> ignoreIndicators = {false, true, false};
  dijkstra.set_nodes_to_ignore(&ignoreIndicators);
  dijkstra.shortestPath(0, RoadDijkstra::no_target);
  EXPECT_EQ(0, dijkstra.getOrigins()[2]);
  EXPECT_EQ(7, dijkstra.get_costs()[2]);
}
