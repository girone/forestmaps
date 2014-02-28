// Copyright 2013: Jonas Sternisko
#include <set>
#include <vector>
#include "./DirectedGraph.h"
#include "./Util.h"
#include "./ForestUtil.h"
#include "./EdgeAttractivenessModel.h"
#include "./GraphConverter.h"
#include "./AdjacencyGraph.h"
#include "./GraphSimplificator.h"

using std::set;
using std::vector;
using std::cout;
using std::endl;


// _____________________________________________________________________________
// Reads a graph, simplifies it and returns a map {arc : represented FIDs}.
// Everything but forest entries can be contracted.
unordered_map<int, vector<int>> read_and_simplify(
    const string& filename,
    const vector<int>& forestEntries,
    ForestRoadGraph* out) {
  // Read the adjacency list graph from file.
  SimplificationGraph adjGraph;
  adjGraph.read_in(filename);

  // Simplify chains of nodes.
  GraphSimplificator simplifier(&adjGraph);
  set<uint> doNotContract(forestEntries.begin(), forestEntries.end());
  SimplificationGraph simple = simplifier.simplify(&doNotContract);

  // Convert to a compact graph representation.
  adjGraph.clear();
  *out = convert_graph<SimplificationGraph, ForestRoadGraph>(simple);
  return simplifier.edgeIndexToFidsMap();
}

// _____________________________________________________________________________
void print_usage() {
  cout <<
  "Usage: ./Program <ForestGraphFile> <EntryAndParkingXYRF> <EntryPopulation> "
  "<Preferences> <Approach> <OutputFile>\n"
  "  ForestGraphFile -- ...\n"
  "  EntryAndParkingXYRF -- Contains position (X,Y) and graph node indices "
  "(Road, Forest) for forest entries and parking lots. Both are treated "
  "equally by this module.\n"
  "  EntryPopulation -- Population numbers of the forest entries and parking "
  "lots.\n"
  "  Preferences -- 2-column table with time intervals (upper bounds) and "
  "share in [0,1]. The last interval bound also defines the maximum search "
  "radius.\n"
  "  Approach -- selects the attractiveness modelling approach. 0 for "
  "Flooding, 1 for Via-Edge\n"
  "  OutputFile -- Is what you think it is.\n"
            << endl;
}

// _____________________________________________________________________________
int main(int argc, char** argv) {
  if (argc != 7) {
    print_usage();
    exit(1);
  }
  cout << "Reading the data..." << endl;
  vector<int> forestEntries = util::read_column_file<int>(argv[2])[3];

  ForestRoadGraph forestGraph;
  unordered_map<int, vector<int>> edgeIdToFids = read_and_simplify(
      argv[1], forestEntries, &forestGraph);
  forestGraph.read_in(argv[1]);

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
    cout << "Selected Flooding Approach." << endl;
    algorithm = new FloodingModel(
        forestGraph, forestEntries, entryPopulation, preferences, costLimit);
  } else if (approach == 1) {
    cout << "Selected Via Edge Approach." << endl;
    algorithm = new ViaEdgeApproach(
        forestGraph, forestEntries, entryPopulation, preferences, costLimit);
  } else {
    cout << "Invalid approach selector." << endl;
    exit(1);
  }

  const vector<float> result = algorithm->compute_edge_attractiveness();

  string filename = outfile;  // "edge_weights.tmp.txt";
  cout << "Writing the attractivenesses to " << filename << endl;
  util::dump_vector(result, filename);
  delete algorithm;

  // Message to external callers which can't fetch the return code.
  cout << endl << "OK" << endl;
  return 0;
}

