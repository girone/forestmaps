// Copyright 2013: Jonas Sternisko

#include "../src/Util.h"
#include <gtest/gtest.h>
#include <string>
#include <vector>

using std::string;
using std::vector;

// _____________________________________________________________________________
TEST(UtilTest, convert) {
  {
    EXPECT_EQ(3, util::convert<int>("3"));
    EXPECT_FLOAT_EQ(3, util::convert<int>("3.9"));
    EXPECT_EQ("3", util::convert<string>(3));
    EXPECT_FLOAT_EQ(3.1, util::convert<float>("3.1"));
    EXPECT_EQ("3.1", util::convert<string>("3.1"));
    EXPECT_EQ("3.1", util::convert<string>(3.1));
  }
}

// _____________________________________________________________________________
TEST(UtilTest, read_column_file) {
  {
    // Start with a neat formatted input (no double spaces).
    std::ofstream ofs("util.tmp.txt");
    ofs << "3.2 1.2 4.0" << std::endl;
    ofs << "1.0 1.0 4.0" << std::endl;
    ofs << "2.8 3.7 4.2" << std::endl;
  }
  {
    // Test float entries
    vector<vector<float> > columns = util::read_column_file<float>("util.tmp.txt");
    ASSERT_EQ(3, columns.size());
    ASSERT_EQ(3, columns[0].size());
    ASSERT_EQ(3, columns[1].size());
    ASSERT_EQ(3, columns[2].size());

    EXPECT_FLOAT_EQ(3.2, columns[0][0]);
    EXPECT_FLOAT_EQ(1.0, columns[0][1]);
    EXPECT_FLOAT_EQ(2.8, columns[0][2]);

    EXPECT_FLOAT_EQ(1.2, columns[1][0]);
    EXPECT_FLOAT_EQ(1.0, columns[1][1]);
    EXPECT_FLOAT_EQ(3.7, columns[1][2]);

    EXPECT_FLOAT_EQ(4.0, columns[2][0]);
    EXPECT_FLOAT_EQ(4.0, columns[2][1]);
    EXPECT_FLOAT_EQ(4.2, columns[2][2]);
  }

  {
    // Now some more complicated input.
    std::ofstream ofs("util.tmp.txt");
    ofs << "3.2 1.2  4.0  " << std::endl;
    ofs << "1.0 1.0 4.0 " << std::endl;
    ofs << "2.8  3.7 4.2" << std::endl;
  }
  {
    // Test float entries
    vector<vector<float> > columns = util::read_column_file<float>("util.tmp.txt");
    ASSERT_EQ(3, columns.size());
    ASSERT_EQ(3, columns[0].size());
    ASSERT_EQ(3, columns[1].size());
    ASSERT_EQ(3, columns[2].size());

    EXPECT_FLOAT_EQ(3.2, columns[0][0]);
    EXPECT_FLOAT_EQ(1.0, columns[0][1]);
    EXPECT_FLOAT_EQ(2.8, columns[0][2]);

    EXPECT_FLOAT_EQ(1.2, columns[1][0]);
    EXPECT_FLOAT_EQ(1.0, columns[1][1]);
    EXPECT_FLOAT_EQ(3.7, columns[1][2]);

    EXPECT_FLOAT_EQ(4.0, columns[2][0]);
    EXPECT_FLOAT_EQ(4.0, columns[2][1]);
    EXPECT_FLOAT_EQ(4.2, columns[2][2]);
  }
  {
    // Test with integer conversion
    vector<vector<int> > columns = util::read_column_file<int>("util.tmp.txt");
    ASSERT_EQ(3, columns.size());
    EXPECT_EQ(vector<int>({3, 1, 2}), columns[0]);
    EXPECT_EQ(vector<int>({1, 1, 3}), columns[1]);
    EXPECT_EQ(vector<int>({4, 4, 4}), columns[2]);
  }
}


