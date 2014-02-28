// Copyright 2013: Jonas Sternisko
#include <vector>
#include "./DirectedGraph.h"
#include "./Util.h"
#include "./ForestUtil.h"
#include "./EdgeAttractivenessModel.h"


using std::unordered_map;
using std::vector;


const int kPARAM_MAX_FOREST_TIME = 120 * 60;  // tour time in seconds


void print_usage() {
  std::cout <<
  "Usage: ./Program <ForestGraphFile> <EntriesXYRF> <EntryPopulation> <Preferences> <Approach> <OutputFile>\n"
  "  ForestGraphFile -- ...\n"
  "  EntriesXYRF -- ...\n"
  "  EntryPopulation -- ...\n"
  "  Preferences -- 2-column table with time intervals (upper bounds) and share in [0,1]. The last interval bound also defines the maximum search radius.\n"
  "  Approach -- selects the attractiveness modelling approach. 0 for Flooding, 1 for Via-Edge\n"
  "  OutputFile -- Is what you think it is.\n"
            << std::endl;
}
/*
 *
 * TODO(Jonas): Have population counts as output.
 *
 * Proceed as follows: Store for each edge a list of pairs with possible tour
 * starting forest entry points and the according weight of the edge in the
 * tour. After the selected approach has finished, sort the list of each edge
 * by the weights, and normalize all weights relative to their maximum. Then
 * the populations of the forest entries is distributed according to the
 * normalized weights.
 *
 * TODO(Jonas): Talk to Hannah about this later on.
 */

// _____________________________________________________________________________
int main(int argc, char** argv) {
  if (argc != 7) {
    print_usage();
    exit(1);
  }
  // Read the data
  ForestRoadGraph forestGraph;
  forestGraph.read_in(argv[1]);
  vector<int> forestEntries = util::read_column_file<int>(argv[2])[3];
  vector<float> entryPopulation = util::read_column_file<float>(argv[3])[0];
  vector<vector<float> > preferences = util::read_column_file<float>(argv[4]);
  int approach = util::convert<int>(argv[5]);
  string outfile = argv[6];

  // Check preferences & convert from minutes to seconds.
  assert(forest::check_preferences(preferences));
  std::for_each(preferences[0].begin(), preferences[0].end(),
                [](float& x) { x*=60; });
  const int costLimit = preferences[0].back();

  EdgeAttractivenessModel* algorithm;
  if (approach == 0) {
    std::cout << "Selected Flooding Approach." << std::endl;
    algorithm = new FloodingModel(
        forestGraph, forestEntries, entryPopulation, preferences, costLimit);
  } else if (approach == 1) {
    std::cout << "Selected Via Edge Approach." << std::endl;
    algorithm = new ViaEdgeApproach(
        forestGraph, forestEntries, entryPopulation, preferences, costLimit);
  } else {
    std::cout << "Invalid approach selector." << std::endl;
    exit(1);
  }

  const vector<float> result = algorithm->compute_edge_attractiveness();

  string filename = outfile;  // "edge_weights.tmp.txt";
  std::cout << "Writing the attractivenesses to " << filename << std::endl;
  util::dump_vector(result, filename);
  delete algorithm;

  // Message to exernal callers which can't fetch the return code.
  std::cout << std::endl << "OK" << std::endl;
  return 0;
}
