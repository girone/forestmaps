// Copyright 2013, Chair of Algorithms and Datastructures.
// Author: Mirko Brodesser <mirko.brodesser@gmail.com>

#include <gtest/gtest.h>
#include <fstream>
#include <string>

#include "../src/OSMGraph.h"
#include "../src/OSMGraphBuilder.h"

using std::string;


const char TEST_FILE_NAME[] = "tmp/OSMGraphBuilderTest.TMP.osm";

// _____________________________________________________________________________
void writeTestFile() {
  std::ofstream os(TEST_FILE_NAME);
  os <<
    "<node id=\"42432091\" lat=\"40.7163940\" lon=\"-73.9845360\"/>"
    "<node id=\"42432093\" lat=\"40.7166310\" lon=\"-73.9853230\"/>"
    "<node id=\"42432094\" lat=\"40.7168990\" lon=\"-73.9862000\"/>"
    "<way id=\"39662324\">"
    " <nd ref=\"42432094\"/>"
    " <nd ref=\"42432093\"/>"
    " <nd ref=\"42432091\"/>"
    " <tag k=\"highway\" v=\"residential\"/>"
    " <tag k=\"name\" v=\"Broome Street\"/>"
    "</way>";
  os.close();
}

// _____________________________________________________________________________
TEST(OSMGraphBuilder, build_various) {
  writeTestFile();
  OSMGraph cg, wg;
  OSMGraphBuilder cgBuilder = OSMGraphBuilder::CarGraphBuilder(&cg);
  cgBuilder.build(TEST_FILE_NAME);
  ASSERT_EQ(
      "{3, (40.7164, -73.9845):[(9, 1)], "
      "(40.7166, -73.9853):[(10, 2), (9, 0)], (40.7169, -73.9862):[(10, 1)]}",
      cg.string());
  OSMGraphBuilder wgBuilder = OSMGraphBuilder::WalkingGraphBuilder(&wg);
  wgBuilder.build(TEST_FILE_NAME);
  ASSERT_EQ(
      "{3, (40.7164, -73.9845):[(52, 1)], "
      "(40.7166, -73.9853):[(57, 2), (52, 0)], (40.7169, -73.9862):[(57, 1)]}",
      wg.string());
}

// _____________________________________________________________________________
TEST(OSMGraphBuilder, compact_graph) {
  writeTestFile();
  OSMGraph cg;
  OSMGraphBuilder cgBuilder = OSMGraphBuilder::CarGraphBuilder(&cg);
  cgBuilder.build(TEST_FILE_NAME);

  CompactOSMGraph compact = OSMGraphBuilder::compact(cg);
  EXPECT_EQ(cg.string(), compact.string());
}
