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
  "Usage: ./Program <ForestGraphFile> <EntriesXYRF> <EntryPopulation> <Preferences> <Approach>\n"
  "  ForestGraphFile -- ...\n"
  "  EntriesXYRF -- ...\n"
  "  EntryPopulation -- ...\n"
  "  Preferences -- 2-column table with time intervals (upper bounds) and share in [0,1]. The last interval bound also defines the maximum search radius.\n"
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
  vector<vector<float> > preferences = util::read_column_file<float>(argv[4]);
  int approach = util::convert<int>(argv[5]);

  // TODO(Jonas): Check input in separate function, ADD UNITTEST (I mean it!)
  for (size_t i = 1; i < preferences[0].size(); ++i) {
    if (preferences[0][i] <= preferences[0][i-1]) {
      std::cout << "Wrong prefence intervals: upper bound " << preferences[0][i]
                << " is less than or equal its predecessor." << std::endl;
      exit(1);
    }
  }
  for (float share: preferences[1]) {
    if (share < 0 || share > 1) {
      std::cout << "Wront preference values: share " << share
                << " is not in [0,1]." << std::endl;
      exit(1);
    }
  }


  EdgeAttractivenessModel* algorithm;
  if (approach == 0) {
    algorithm = new FloodingModel(
        forestGraph, forestEntries, entryPopulation, preferences, kPARAM_MAX_FOREST_TIME);
    std::cout << "Selected Flooding Approach." << std::endl;
  } else if (approach == 1) {
    algorithm = new ViaEdgeApproach(
        forestGraph, forestEntries, entryPopulation, preferences, kPARAM_MAX_FOREST_TIME);
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
