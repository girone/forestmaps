// Copyright 2013: Jonas Sternisko
#include <vector>
#include "./DirectedGraph.h"
#include "./Util.h"
#include "./EdgeAttractivenessModel.h"


using std::unordered_map;
using std::vector;


const int kPARAM_MAX_FOREST_TIME = 120 * 60;  // tour time in seconds


void print_usage() {
  std::cout <<
  "Usage: ./Program <ForestGraphFile> <ForestEntries> <ForestEntryPopulation>"
            << std::endl;
}

// _____________________________________________________________________________
int main(int argc, char** argv) {
  if (argc != 4) {
    print_usage();
    exit(1);
  }
  // Read the data
  RoadGraph forestGraph;
  forestGraph.read_in(argv[1]);
  vector<int> forestEntries = util::read_column_file<int>(argv[2])[0];
  vector<float> entryPopulation = util::read_column_file<float>(argv[3])[0];

  ViaEdgeApproach algorithm(forestGraph, forestEntries, entryPopulation,
                            kPARAM_MAX_FOREST_TIME);

  const vector<float> result = algorithm.compute_edge_attractiveness();
  util::dump_vector(result, "edge_attractiveness.txt");
  return 0;
}