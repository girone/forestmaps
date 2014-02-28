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
  "Usage: ./Program <ForestGraphFile> <EntriesXYRF> <EntryPopulation> <Approach>\n"
  "  ForestGraphFile -- ...\n"
  "  EntriesXYRF -- ...\n"
  "  EntryPopulation -- ...\n"
  "  Approach -- selects the attractiveness modelling approach. 0 for Flooding, 1 for Via-Edge\n"
            << std::endl;
}

// _____________________________________________________________________________
int main(int argc, char** argv) {
  if (argc != 5) {
    print_usage();
    exit(1);
  }
  // Read the data
  RoadGraph forestGraph;
  forestGraph.read_in(argv[1]);
  vector<int> forestEntries = util::read_column_file<int>(argv[2])[3];
  vector<float> entryPopulation = util::read_column_file<float>(argv[3])[0];
  int approach = util::convert<int>(argv[4]);

  EdgeAttractivenessModel* algorithm;
  if (approach == 0) {
    algorithm = new FloodingModel(
        forestGraph, forestEntries, entryPopulation, kPARAM_MAX_FOREST_TIME);
    std::cout << "Selected Flooding Approach." << std::endl;
  } else if (approach == 1) {
    algorithm = new ViaEdgeApproach(
        forestGraph, forestEntries, entryPopulation, kPARAM_MAX_FOREST_TIME);
    std::cout << "Selected Via Edge Approach." << std::endl;
  } else {
    std::cout << "Invalid approach selector." << std::endl;
    exit(1);
  }


  const vector<float> result = algorithm->compute_edge_attractiveness();
  string filename = "edge_weights.tmp.txt";
  std::cout << "Writing the attractivenesses to " << filename << std::endl;
  util::dump_vector(result, filename);
  delete algorithm;
  return 0;
}
