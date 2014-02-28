// Copyright 2014: Jonas Sternisko

#include <gmock/gmock.h>
#include <vector>
#include "../src/ForestUtil.h"
#include "../src/Util.h"

using std::vector;
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

  EXPECT_TRUE(forest::check_preferences(preferences));
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

  ASSERT_DEATH(forest::check_preferences(preferences), ".*");
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

  ASSERT_DEATH(forest::check_preferences(preferences), ".*");
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

  ASSERT_DEATH(forest::check_preferences(preferences), ".*");
}
