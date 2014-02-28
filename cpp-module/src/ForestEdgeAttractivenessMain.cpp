// Copyright 2013: Jonas Sternisko

#include <algorithm>
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
using std::max;
using std::max_element;


// _____________________________________________________________________________
// Reads a grapha and simplifies it.  Every node except forest entries can be
// contracted. Returns the simple graph, the number of edges in the original
// graph, a map {arc : represented edge indices} and the shifted indices of the
// forest entries.
ForestRoadGraph read_and_simplify(
    const string& filename,
    const vector<int>& forestEntries,
    unordered_map<int, vector<int>>* containedEdgeIds,
    vector<int>* newForestEntries) {
  // Read the adjacency list graph from file.
  SimplificationGraph adjGraph;
  adjGraph.read_in(filename);

  // Simplify chains of nodes.
  GraphSimplificator simplifier(&adjGraph);
  set<uint> doNotContract(forestEntries.begin(), forestEntries.end());
  SimplificationGraph simple = simplifier.simplify(&doNotContract);

  *containedEdgeIds = simplifier.edges_contained_in_shortcut_map();
  const vector<int>& shift = simplifier.index_shift();
  newForestEntries->clear();
  std::transform(forestEntries.begin(), forestEntries.end(),
                 std::back_inserter(*newForestEntries),
                 [shift](int index) { return index - shift[index]; });
  // Convert to a compact graph representation.
  adjGraph.clear();
  return convert_graph<SimplificationGraph, ForestRoadGraph>(simple);
}

// _____________________________________________________________________________
// Write the output to a file. The simplification is undone: Each edge of the
// graph has an id which represents a set of edges in the original graph. These
// correspondences are restored using the mapping.
void write_output(const string& filename,
                  const vector<float>& result,
                  const ForestRoadGraph& simplifiedGraph,
                  const unordered_map<int, vector<int>>& representedEdgeIds) {
  // Set up the vector of edge weights. Its size is: max({edgeIndex})
  int maxEdgeIndex = -1;
  for (const auto& entry: representedEdgeIds) {
    const vector<int>& ids = entry.second;
    if (ids.size()) {
      maxEdgeIndex = max(maxEdgeIndex, *max_element(ids.begin(), ids.end()));
    } else {
      cout << " entry for " << entry.first << " is empty. " << endl;
    }
  }
  assert(maxEdgeIndex > 0);

  vector<float> unpackedResult(maxEdgeIndex + 1, 0.f);
  // TODO(Jonas): is the correspondence here correct? Index in
  // offsetgraph._arclist to index in result?
  assert(result.size() == simplifiedGraph.arclist().size());
  int index = 0;
  for (const Arc& arc: simplifiedGraph.arclist()) {
    const float weight = result[index++];
    if (weight > 0.f) {
      const int id = arc.labels[2];
      auto it = representedEdgeIds.find(id);
      if (it != representedEdgeIds.end()) {
        for (const int edgeId: it->second) {
          unpackedResult[edgeId] = weight;
        }
      }
    }
  }

  util::dump_vector(unpackedResult, filename);
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

  unordered_map<int, vector<int>> containedEdgeIds;
  vector<int> forestEntriesInSimplifiedGraph;
  ForestRoadGraph simplifiedGraph = read_and_simplify(
      argv[1], forestEntries, &containedEdgeIds, &forestEntriesInSimplifiedGraph);
  assert(forestEntriesInSimplifiedGraph.size() == forestEntries.size());

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
    algorithm = new FloodingModel(simplifiedGraph,
                                  forestEntriesInSimplifiedGraph,
                                  entryPopulation, preferences, costLimit);
  } else if (approach == 1) {
    cout << "Selected Via Edge Approach." << endl;
    algorithm = new ViaEdgeApproach(simplifiedGraph,
                                    forestEntriesInSimplifiedGraph,
                                    entryPopulation, preferences, costLimit);
  } else {
    cout << "Invalid approach selector." << endl;
    exit(1);
  }

  const vector<float> result = algorithm->compute_edge_attractiveness();

  cout << "Writing the attractivenesses to " << outfile << endl;
  write_output(outfile, result, simplifiedGraph, containedEdgeIds);

  delete algorithm;

  // Message to external callers which can't fetch the return code.
  cout << endl << "OK" << endl;
  return 0;
}

