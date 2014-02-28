// Copyright 2013: Chair of Algorithms and Datastructures.
// Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

// Constructs a OSM graph from a osm directory in the arguments.

#include <string>
#include "./OSMGraphBuilder.h"
#include "./LCC.h"

using std::string;

int main(int argc, char** argv) {
  assert(argc > 1 && "No osm-path given.");
  const string filename = argv[1];

  OSMGraph g;
  OSMGraphBuilder builder = OSMGraphBuilder::RoadGraphBuilder(&g);
  builder.build(filename);
  g = graph_utils::lcc(g);
}
