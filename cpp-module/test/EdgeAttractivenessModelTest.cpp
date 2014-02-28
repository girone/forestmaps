// Copyright 2013: Jonas Sternisko

#include <gmock/gmock.h>
#include "../src/EdgeAttractivenessModel.h"

using ::testing::Each;
using ::testing::Gt;


const vector<vector<float> > preferences = {{150, 300},
                                            { 50,  50}};

// A and D are forest entries:
//   A -- B -- C -- D
// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, FloodingApproachTrivial) {
  RoadGraph graph;
  graph.from_string(
      "[4,6,{(1,7)},{(0,7)(2,7)},{(1,7)(3,7)},{(2,7)}]"
  );
  EXPECT_EQ("[4,6,{(1,7)},{(0,7)(2,7)},{(1,7)(3,7)},{(2,7)}]",
            graph.to_string());

  {
    // No entry points.
    vector<int> forestEntries = {};
    vector<float> entryPopularity = {};
    FloodingModel algorithm(graph, forestEntries, entryPopularity, preferences, 300);
    const vector<float> result = algorithm.compute_edge_attractiveness();
    ASSERT_EQ(result.size(), graph.num_arcs());
    EXPECT_THAT(result, Each(0.f));
  }

  {
    // No population.
    vector<int> forestEntries = {0, 3};
    vector<float> entryPopularity = {0.f, 0.f};
    FloodingModel algorithm(graph, forestEntries, entryPopularity, preferences, 300);
    const vector<float> result = algorithm.compute_edge_attractiveness();
    ASSERT_EQ(result.size(), graph.num_arcs());
    EXPECT_THAT(result, Each(0.f));
  }

  {
    // To hard Dijkstra limit.
    vector<int> forestEntries = {0, 3};
    vector<float> entryPopularity = {200.f, 200.f};
    FloodingModel algorithm(graph, forestEntries, entryPopularity, preferences, -3);
    const vector<float> result = algorithm.compute_edge_attractiveness();
    ASSERT_EQ(result.size(), graph.num_arcs());
    EXPECT_THAT(result, Each(0.f));
  }

  {
    // Realistic setting.
    vector<int> forestEntries = {0, 3};
    vector<float> entryPopularity = {100.f, 12.f};
    FloodingModel algorithm(graph, forestEntries, entryPopularity, preferences, 300);
    const vector<float> result = algorithm.compute_edge_attractiveness();
    ASSERT_EQ(result.size(), graph.num_arcs());
    EXPECT_THAT(result, Each(Gt(0.f)));
  }
}

// More elaborate example:
//  A ––– B
//  |  \  |   A-D is shortest path of cost 7.
//  C ––– D
// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, FloodingApproach) {
  RoadGraph graph;
  graph.from_string(
      "[4,10,{(1,6)(2,9)(3,7)},{(0,6)(3,6)},{(0,9)(3,9)},{(0,7)(1,6)(2,9)}]"
  );

  {
    // No entry points.
    vector<int> forestEntries = {0, 3};
    vector<float> entryPopularity = {100.f, 100.f};
    FloodingModel algorithm(graph, forestEntries, entryPopularity, preferences, 300);
    const vector<float> result = algorithm.compute_edge_attractiveness();
    ASSERT_EQ(result.size(), graph.num_arcs());
    EXPECT_THAT(result, Each(Gt(0.f)));

    const auto& arcs = graph.arclist();
    std::stringstream ss;
    for (size_t i = 0; i < arcs.size(); ++i) {
      const RoadGraph::Arc_t& arc = arcs[i];
      ss << arc.source << " " << arc.target << " " << result[i]
                << std::endl;
    }
    EXPECT_EQ("0 1 75\n"
              "0 2 50\n"
              "0 3 100\n"
              "1 0 72.619\n"
              "1 3 72.619\n"
              "2 0 53.1746\n"
              "2 3 53.1746\n"
              "3 0 100\n"
              "3 1 75\n"
              "3 2 50\n", ss.str());
  }
}


// A and D are forest entries:
//   A -- B -- C -- D
// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, ViaEdgeApproachTrivial) {
  RoadGraph graph;
  graph.from_string(
      "[4,6,{(1,7)},{(0,7)(2,7)},{(1,7)(3,7)},{(2,7)}]"
  );
  EXPECT_EQ("[4,6,{(1,7)},{(0,7)(2,7)},{(1,7)(3,7)},{(2,7)}]",
            graph.to_string());

  {
    // No entry points.
    vector<int> forestEntries = {};
    vector<float> entryPopularity = {};
    ViaEdgeApproach algorithm(graph, forestEntries, entryPopularity, preferences, 300);
    const vector<float> result = algorithm.compute_edge_attractiveness();
    ASSERT_EQ(result.size(), graph.num_arcs());
    EXPECT_THAT(result, Each(0.f));
  }

  {
    // No population.
    vector<int> forestEntries = {0, 3};
    vector<float> entryPopularity = {0.f, 0.f};
    ViaEdgeApproach algorithm(graph, forestEntries, entryPopularity, preferences, 300);
    const vector<float> result = algorithm.compute_edge_attractiveness();
    ASSERT_EQ(result.size(), graph.num_arcs());
    EXPECT_THAT(result, Each(0.f));
  }

  {
    // To hard Dijkstra limit.
    vector<int> forestEntries = {0, 3};
    vector<float> entryPopularity = {200.f, 200.f};
    ViaEdgeApproach algorithm(graph, forestEntries, entryPopularity, preferences, 3);
    const vector<float> result = algorithm.compute_edge_attractiveness();
    ASSERT_EQ(result.size(), graph.num_arcs());
    EXPECT_THAT(result, Each(0.f));
  }

  {
    // Realistic setting.
    vector<int> forestEntries = {0, 3};
    vector<float> entryPopularity = {100.f, 12.f};
    ViaEdgeApproach algorithm(graph, forestEntries, entryPopularity, preferences, 300);
    const vector<float> result = algorithm.compute_edge_attractiveness();
    ASSERT_EQ(result.size(), graph.num_arcs());
    EXPECT_THAT(result, Each(Gt(0.f)));
  }
}

// More elaborate example:
//  A ––– B
//  |  \  |   A-D is shortest path of cost 7.
//  C ––– D
// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, ViaEdgeApproach) {
  RoadGraph graph;
  graph.from_string(
      "[4,10,{(1,6)(2,9)(3,7)},{(0,6)(3,6)},{(0,9)(3,9)},{(0,7)(1,6)(2,9)}]"
  );

  {
    // No entry points.
    vector<int> forestEntries = {0, 3};
    vector<float> entryPopularity = {100.f, 100.f};
    ViaEdgeApproach algorithm(graph, forestEntries, entryPopularity, preferences, 300);
    const vector<float> result = algorithm.compute_edge_attractiveness();
    ASSERT_EQ(result.size(), graph.num_arcs());
    EXPECT_THAT(result, Each(Gt(0.f)));

    const auto& arcs = graph.arclist();
    std::stringstream ss;
    for (size_t i = 0; i < arcs.size(); ++i) {
      const RoadGraph::Arc_t& arc = arcs[i];
      ss << arc.source << " " << arc.target << " " << result[i]
                << std::endl;
    }
    EXPECT_EQ("0 1 75\n"
              "0 2 50\n"
              "0 3 100\n"
              "1 0 72.619\n"
              "1 3 72.619\n"
              "2 0 53.1746\n"
              "2 3 53.1746\n"
              "3 0 100\n"
              "3 1 75\n"
              "3 2 50\n", ss.str());
  }
}
