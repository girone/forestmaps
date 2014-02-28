// Copyright 2013, Chair of Algorithms and Datastructures.

#include <gtest/gtest.h>

#include <fstream>
#include <string>

#include "./OSMGraph.h"
#include "./OSMGraphBuilder.h"

using std::string;


const char TEST_FILE_NAME[] = "OSMGraphBuilderTest.TMP.osm";

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
TEST(BuildTest, buildTest) {
  writeTestFile();
  OSMGraph cg, wg;
  OSMGraphBuilder cgBuilder = OSMGraphBuilder::CarGraphBuilder(&cg);
  cgBuilder.build(TEST_FILE_NAME);
  ASSERT_EQ(
      "{3, [(9, 1)], [(10, 2), (9, 0)], [(10, 1)]}",
      cg.getSummaryString());
  OSMGraphBuilder wgBuilder = OSMGraphBuilder::WalkingGraphBuilder(&wg);
  wgBuilder.build(TEST_FILE_NAME);
  ASSERT_EQ(
      "{3, [(52, 1)], [(57, 2), (52, 0)], [(57, 1)]}",
      wg.getSummaryString());
}
