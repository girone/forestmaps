// Copyright 2011-2013: Jonas Sternisko

#include <ctime>
#include <numeric>
#include <string>
#include <vector>
#include "./Dijkstra.h"
#include "./DirectedGraph.h"
#include "./EdgeAttractivenessModel.h"
#include "./Tree2d.h"
#include "./Util.h"

#define SQR(x) ((x)*(x))

// _____________________________________________________________________________
// Returns the bucket index for a cost.
uint determine_bucket_index(int cost, const vector<int>& bucketCostBounds) {
  uint b = 0;
  while (b < bucketCostBounds.size() && cost > bucketCostBounds[b]) { b++; }
  assert(b < bucketCostBounds.size());
  return b;
}

// _____________________________________________________________________________
// From each FEP, do a limited backwards Dijkstra on the graph (note that
// direction does not matter if we are using a bidirectional graph). Remember
// visited nodes, and store buckets for these. Repeat the search and use the
// buckets as a likelihood for distributing the population of nodes to which
// population has been mapped.
vector<float> reachability_analysis(
    const RoadGraph& graph,
    const vector<int>& fepIndices,
    const vector<float>& population,
    const vector<int>& populationIndices,
    const vector<vector<float> >& preferences) {
  // Get the buckets from the user preferences.
  const vector<float>& upperBounds = preferences[0];
  const vector<float>& shares = preferences[1];
  vector<int> bucketCostBounds;
  for (float bound: upperBounds) { bucketCostBounds.push_back(60 * bound); }
  const float costLimit = bucketCostBounds.back();

  assert(population.size() == populationIndices.size());
  Dijkstra<RoadGraph> dijkstra(graph);
  dijkstra.set_cost_limit(costLimit);

  // Prepare progress information
  size_t total = 2 * fepIndices.size();
  size_t done = 0;
  clock_t timestamp = clock();

  // First round of Dijkstras: Analize reachability and determine frequency of
  // forest distance categories for each population point. For each population
  // grid point a set of buckets is mainted. After the first round of Dijkstra
  // each bucket contains the number of forest entries that can be reached from
  // the population point in less that the time bound in the corresponding slot
  // of bucketCostBounds.
  vector<vector<float>> buckets(
      population.size(), vector<float>(bucketCostBounds.size(), 0.f));
  for (int index: fepIndices) {
    dijkstra.reset();
    dijkstra.shortestPath(index, Dijkstra<RoadGraph>::no_target);
    const vector<int>& costs = dijkstra.get_costs();
    const vector<bool>& settled = dijkstra.get_settled_flags();
    for (size_t i = 0; i < populationIndices.size(); ++i) {
      int popIndex = populationIndices[i];
      if (settled[popIndex]) {
        int cost = costs[popIndex];
        assert(cost != Dijkstra<RoadGraph>::infinity);
        uint b = determine_bucket_index(cost, bucketCostBounds);
        buckets[i][b]++;
      }
    }

    done++;
    if ((clock() - timestamp) / CLOCKS_PER_SEC > 2) {
      timestamp = clock();
      printf("Progress: %d of %d, this is %5.1f%% \r\n",
             done, total, done * 100.f / total);
    }
  }

  // Evaluate the buckets: Compute likelihood, store it in place.
  for (size_t i = 0; i < population.size(); ++i) {
    float sumOfCosts = 0.f;
    for (size_t b = 0; b < buckets[i].size(); ++b) {
      sumOfCosts += buckets[i][b] * bucketCostBounds[b];  // TODO(Jonas): Maybe better use the average instead of the upper bound.
    }
    if (sumOfCosts > 0) {
      for (size_t b = 0; b < buckets[i].size(); ++b) {
        if (bucketCostBounds[b] < sumOfCosts) {
          buckets[i][b] = 1.f - bucketCostBounds[b] / sumOfCosts;
        } else {
          // small hack for values which would be negative without this
          buckets[i][b] = 1.f / SQR(b+1);
        }
      }
    }
  }

  // Second round of Dijkstras: Use buckets as likelihood to distribute the
  // population according to the reachable forest entries and their distance.
  vector<float> fepPop(fepIndices.size(), 0.f);
  for (size_t i = 0; i < fepIndices.size(); ++i) {
    dijkstra.reset();
    dijkstra.shortestPath(fepIndices[i], Dijkstra<RoadGraph>::no_target);
    const vector<int>& costs = dijkstra.get_costs();
    const vector<bool>& settled = dijkstra.get_settled_flags();
    for (size_t j = 0; j < populationIndices.size(); ++j) {
      int popIndex = populationIndices[j];
      if (settled[popIndex]) {
        int cost = costs[popIndex];
        assert(cost != Dijkstra<RoadGraph>::infinity);
        uint b = determine_bucket_index(cost, bucketCostBounds);
        fepPop[i] += buckets[i][b] * shares[b] * population[j];  // TODO(Jonas): Users which accept long distances to forests will also use entries in the vicinity.
      }
    }

    done++;
    if ((clock() - timestamp) / CLOCKS_PER_SEC > 2) {
      timestamp = clock();
      printf("Progress: %5.1f%%\n", done * 100.f / total);
    }
  }

  // Normalize the population numbers: Sum must equal the sum before.
  float normalizer = std::accumulate(fepPop.begin(), fepPop.end(), 0.f) /
                     std::accumulate(population.begin(), population.end(), 0.f);
  for (size_t i = 0; i < fepPop.size(); ++i) {
    fepPop[i] /= normalizer;
  }

  return fepPop;
}


void print_usage() {
  std::cout <<
  "Usage: ./NAME <GraphFile> <ForestEntries> <PopulationNodes> <Preferences>\n"
  "  GraphFile -- ...\n"
  "  ForestEntries -- ...\n"
  "  PopulationNodes -- ...\n"
  "  Preferences -- User study data as 2-column text file. First column contains upper bounds (in minutes), its last value denotes the cost limit for searches. The second column contains shares in [0,1].\n"
  "  OutputFile -- Path and name of the ouput file.\n"
            << std::endl;
}

// _____________________________________________________________________________
int main(int argc, char** argv) {
  if (argc != 6) {
    print_usage();
    exit(0);
  }
  string graphFile = argv[1];
  string fepFile = argv[2];
  string popFile = argv[3];
  string prefFile = argv[4];
  string outfile = argv[5];

  // Read the graph. The file has the graph format
  //  #nodes
  //  #edges
  //  x y (node0)
  //  x y (node1)
  //  ...
  //  source target cost (arc0)
  //  source target cost (arc1)
  //  ...
  RoadGraph graph;
  graph.read_in(graphFile);

  // Read the forest entries. The file has the format
  //  nodeId0
  //  nodeId1
  //  ...
  vector<vector<float> > fepCols = util::read_column_file<float>(fepFile);
  assert(fepCols.size() > 2);
  vector<int> fepNodeIndices(fepCols[2].begin(), fepCols[2].end());


  // Read the population nodes. The file has the format:
  //  x0 y0 population0
  //  x1 y1 population1
  //  ...
  // We map the population to the closest node.
  vector<vector<float>> popColumns = util::read_column_file<float>(popFile);
  assert(popColumns.size() == 3);
  const vector<float>& x = popColumns[0];
  const vector<float>& y = popColumns[1];
  const vector<float>& population = popColumns[2];

  vector<int> populationNodeIndices = map_xy_locations_to_closest_node(x, y, graph);


  vector<vector<float>> preferences = util::read_column_file<float>(prefFile);
  assert(EdgeAttractivenessModel::check_preferences(preferences));


  // Reachability analysis
  vector<float> fepPopulations = reachability_analysis(
      graph, fepNodeIndices, population, populationNodeIndices, preferences);
  string filename = outfile;  // "forest_entries_popularity.tmp.txt";
  std::cout << "Writing entry point popularity to " << filename << std::endl;
  util::dump_vector(fepPopulations, filename);

  return 0;
}
