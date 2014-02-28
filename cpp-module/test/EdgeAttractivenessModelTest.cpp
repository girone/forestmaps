// Copyright 2013-14: Jonas Sternisko

#include <gmock/gmock.h>
#include <unordered_map>
#include "../src/EdgeAttractivenessModel.h"
#include "../src/Util.h"

using std::unordered_map;
using ::testing::Each;
using ::testing::Gt;


const vector<vector<float> > preferences = {{150, 300},
                                            { 50,  50}};

// A and D are forest entries:
//   A -- B -- C -- D
// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, FloodingApproachTrivial) {
  ForestRoadGraph graph;
  graph.from_string(
      "[4,6,{(1,7)},{(0,7)(2,7)},{(1,7)(3,7)},{(2,7)}]"
  );
  EXPECT_EQ(
      "[4,6,{(0,1,[7,1])},{(1,0,[7,1])(1,2,[7,1])},{(2,1,[7,1])(2,3,[7,1])},{(3,2,[7,1])}]",
      graph.to_string()
  );

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
  ForestRoadGraph graph;
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
      const ForestRoadGraph::Arc_t& arc = arcs[i];
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
  ForestRoadGraph graph;
  graph.from_string(
      "[4,6,{(1,7)},{(0,7)(2,7)},{(1,7)(3,7)},{(2,7)}]"
  );
  EXPECT_EQ(
      "[4,6,{(0,1,[7,1])},{(1,0,[7,1])(1,2,[7,1])},{(2,1,[7,1])(2,3,[7,1])},{(3,2,[7,1])}]",
      graph.to_string()
  );

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
  ForestRoadGraph graph;
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
      const ForestRoadGraph::Arc_t& arc = arcs[i];
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


// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, user_shares_functions) {
  ::testing::FLAGS_gtest_death_test_style = "threadsafe";

  vector<vector<float> > preferences =
      {{ 15,   30,  60,  120},
       {0.5, 0.25, 0.2, 0.05}};
  ForestRoadGraph g;
  const vector<int> feps = {};
  const vector<float> popularities = {};
  FloodingModel model(g, feps, popularities, preferences, 0);

  EXPECT_FLOAT_EQ(0.5, model.user_share(0));
  EXPECT_FLOAT_EQ(0.5, model.user_share(15));
  EXPECT_FLOAT_EQ(0.25, model.user_share(20));
  EXPECT_FLOAT_EQ(0.25, model.user_share(30));
  EXPECT_FLOAT_EQ(0.2, model.user_share(31));
  EXPECT_FLOAT_EQ(0.05, model.user_share(120));
  ASSERT_DEATH(model.user_share(121), ".*");

  EXPECT_FLOAT_EQ(1., model.sum_of_user_shares_after(0));
  EXPECT_FLOAT_EQ(1., model.sum_of_user_shares_after(15));
  EXPECT_FLOAT_EQ(0.5, model.sum_of_user_shares_after(16));
  EXPECT_FLOAT_EQ(0.5, model.sum_of_user_shares_after(30));
  EXPECT_FLOAT_EQ(0.25, model.sum_of_user_shares_after(31));
  EXPECT_FLOAT_EQ(0.25, model.sum_of_user_shares_after(60));
  EXPECT_FLOAT_EQ(0.05, model.sum_of_user_shares_after(61));
  EXPECT_FLOAT_EQ(0.05, model.sum_of_user_shares_after(120));
  ASSERT_DEATH(model.sum_of_user_shares_after(121), ".*");
}

// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, normalize_contributions) {
  ViaEdgeApproach::MapMap map;
  map[0][0] = 1;
  map[0][1] = 2;
  map[0][2] = 5;
  map[0][3] = 0;

  map[1][0] = 0.10;
  map[1][2] = 0.5;
  map[1][6] = 0.5;
  map[1][8] = 0.5;

  ViaEdgeApproach::normalize_contributions(&map);

  EXPECT_FLOAT_EQ(0.2, map[0][0]);
  EXPECT_FLOAT_EQ(0.4, map[0][1]);
  EXPECT_FLOAT_EQ(1.0, map[0][2]);
  EXPECT_FLOAT_EQ(0.0, map[0][3]);
  EXPECT_FLOAT_EQ(0.2, map[1][0]);
  EXPECT_FLOAT_EQ(1.0, map[1][2]);
  EXPECT_FLOAT_EQ(1.0, map[1][6]);
  EXPECT_FLOAT_EQ(1.0, map[1][8]);
}

// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, distribute_contribution) {
  ForestRoadGraph g;
  g.from_string("[5,4,"                  // NOTE(Jonas): This is a dummy graph
                "{(1,0)},"               // with unidirectional arcs only.
                "{(2,0)},"
                "{(3,0),(4,0)},"
                "{},"
                "{}]");
  const vector<int> f = {};
  const vector<float> p = {};
  vector<vector<float> > pref =
      {{ 15,   30,  60,  120},
       {0.5, 0.25, 0.2, 0.05}};
  ViaEdgeApproach model(g, f, p, pref, 0);
  unordered_map<int, float> populations;
  populations[0] = 10;
  populations[1] = 15;
  populations[2] = 5;
  ViaEdgeApproach::MapMap contributions;
  contributions[0][0] = 1.;
  contributions[0][1] = 0.8;
  contributions[0][2] = 0.5;
  contributions[0][3] = 0.1;

  contributions[1][0] = 0.;
  contributions[1][1] = 0.8;
  contributions[1][2] = 1.;
  contributions[1][3] = 0.4;

  contributions[2][1] = 0.5;
  contributions[2][2] = 0.5;
  contributions[2][3] = 1.;

  vector<float> attractivenesses(g.num_arcs(), 0.f);
  model.distribute(populations, contributions, &attractivenesses);
  EXPECT_FLOAT_EQ(1.0 * 10, attractivenesses[0]);
  EXPECT_FLOAT_EQ(0.8 * 10 + 0.8 * 15 + 0.5 * 5, attractivenesses[1]);
  EXPECT_FLOAT_EQ(0.5 * 10 + 1.0 * 15 + 0.5 * 5, attractivenesses[2]);
  EXPECT_FLOAT_EQ(0.1 * 10 + 0.4 * 15 + 1.0 * 5, attractivenesses[3]);
}
