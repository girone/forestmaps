// Copyright 2013: Jonas Sternisko

#include <gmock/gmock.h>
#include "../src/EdgeAttractivenessModel.h"
#include "../src/Util.h"

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


// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, user_shares_functions) {
  ::testing::FLAGS_gtest_death_test_style = "threadsafe";

  vector<vector<float> > preferences =
      {{ 15,   30,  60,  120},
       {0.5, 0.25, 0.2, 0.05}};
  RoadGraph g;
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

using std::endl;

// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, check_preferences) {
  std::string filename = "test-input.0.tmp.txt";
  std::ofstream ofs(filename);
  ofs << "15 0.5" << endl
      << "30 0.25" << endl
      << "60 0.2" << endl
      << "120 0.05" << endl;
  ofs.close();
  vector<vector<float> > preferences = util::read_column_file<float>(filename);
  ASSERT_EQ(2, preferences.size());

  EXPECT_TRUE(EdgeAttractivenessModel::check_preferences(preferences));
}

// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, check_preferences1) {
  ::testing::FLAGS_gtest_death_test_style = "threadsafe";
  std::string filename = "test-input.1.tmp.txt";
  std::ofstream ofs(filename);
  ofs << "15 0.5" << endl
      << "14 0.25" << endl  // <<<<<<<<<<<<< KEYS ARE NOT ASCENDING
      << "60 0.2" << endl
      << "120 0.05" << endl;
  ofs.close();
  vector<vector<float> > preferences = util::read_column_file<float>(filename);
  ASSERT_EQ(2, preferences.size());

  ASSERT_DEATH(EdgeAttractivenessModel::check_preferences(preferences), ".*");
}

// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, check_preferences2) {
  ::testing::FLAGS_gtest_death_test_style = "threadsafe";
  std::string filename = "test-input.2.tmp.txt";
  std::ofstream ofs(filename);
  ofs << "15 0.5" << endl
      << "30 0.25" << endl
      << "60 1.2" << endl  // <<<<<<<<<<<<< SHARE IS NOT IN [0,1]
      << "120 0.05" << endl;
  ofs.close();
  vector<vector<float> > preferences = util::read_column_file<float>(filename);
  ASSERT_EQ(2, preferences.size());

  ASSERT_DEATH(EdgeAttractivenessModel::check_preferences(preferences), ".*");
}

// _____________________________________________________________________________
TEST(EdgeAttractivenessModelTest, check_preferences3) {
  ::testing::FLAGS_gtest_death_test_style = "threadsafe";
  std::string filename = "test-input.3.tmp.txt";
  std::ofstream ofs(filename);
  ofs << "15 0.5" << endl
      << "30 0.25" << endl
      << "60 0.2" << endl
      << "120 0.5" << endl;  // <<<<<<<<<<<<< SUM IS NOT IN [0,1]
  ofs.close();
  vector<vector<float> > preferences = util::read_column_file<float>(filename);
  ASSERT_EQ(2, preferences.size());

  ASSERT_DEATH(EdgeAttractivenessModel::check_preferences(preferences), ".*");
}

