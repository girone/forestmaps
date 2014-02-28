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
#include "./ForestUtil.h"

#define SQR(x) ((x)*(x))

// The user studies revealed these numbers:
const float kUserShareBicycle = 13 / 124.f;
const float kUserShareWalking = 71 / 124.f;
const float kUnmappedPeople = 1.f - (kUserShareWalking - kUserShareBicycle);

// We combined the extraction of travel costs for bike and walking by assuming
// the average bike speed being at a constant factor from the walking speed:
const float kWalkingToBikeSpeedFactor = 4.f;

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
//
// graph       - The road graph with edge costs being the walking (!) time.
// preferences - We assume the same user preferences for walking and biking, but
//               the provided times refer to walking. Biking times are derived
//               using the constant factor above.
vector<float> reachability_analysis(
    const RoadGraph& graph,
    const vector<int>& fepIndices,
    const vector<float>& populations,
    const vector<int>& populationIndices,
    const vector<vector<float> >& preferences) {
  // Get the buckets from the user preferences.
  const vector<float>& upperBounds = preferences[0];
  const vector<float>& shares = preferences[1];
  vector<int> bucketCostBounds;
  for (float val: upperBounds) { bucketCostBounds.push_back(60 * val); }
  vector<int> bucketCostBoundsBike;
  const float f = kWalkingToBikeSpeedFactor;
  for (float val: bucketCostBounds) { bucketCostBoundsBike.push_back(f * val); }
  // As cost limit we use the maximum biking time.
  const float costLimitWalking = bucketCostBounds.back();
  const float costLimitBike = costLimitWalking * kWalkingToBikeSpeedFactor;

  assert(populations.size() == populationIndices.size());
  vector<bool> reachesForestByWalking(populations.size(), false);
  vector<bool> reachesForestByBicycle(populations.size(), false);
  Dijkstra<RoadGraph> dijkstra(graph);
  dijkstra.set_cost_limit(costLimitBike);

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
      populations.size(), vector<float>(bucketCostBounds.size(), 0.f));
  vector<vector<float>> bucketsBike = buckets;
  for (int index: fepIndices) {
    dijkstra.reset();
    dijkstra.shortestPath(index, Dijkstra<RoadGraph>::no_target);
    const vector<int>& costs = dijkstra.get_costs();
    const vector<bool>& settled = dijkstra.get_settled_flags();
    for (size_t i = 0; i < populationIndices.size(); ++i) {
      int popIndex = populationIndices[i];
      if (settled[popIndex]) {
        int cost = costs[popIndex];
        // biking: no need to divide by the speed factor here
        uint b = determine_bucket_index(cost, bucketCostBoundsBike);
        bucketsBike[i][b]++;
        // walking
        if (cost <= costLimitWalking) {
          uint bb = determine_bucket_index(cost, bucketCostBounds);
          buckets[i][bb]++;
        }
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
  for (size_t i = 0; i < populations.size(); ++i) {
    float sumOfCosts = 0.f;
    float sumOfCostsBike = 0.f;
    for (size_t b = 0; b < buckets[i].size(); ++b) {
      sumOfCosts += buckets[i][b] * bucketCostBounds[b];  // TODO(Jonas): Maybe better use the average instead of the upper bound.
      sumOfCostsBike += bucketsBike[i][b] * bucketCostBoundsBike[b];
    }
    if (sumOfCosts > 0) {  // ==> sumOfCostsBike > 0 as well
      for (size_t b = 0; b < buckets[i].size(); ++b) {
        // walking
        if (bucketCostBounds[b] < sumOfCosts) {
          buckets[i][b] = 1.f - bucketCostBounds[b] / sumOfCosts;
        } else {
          // small hack for values which would be negative without this
          buckets[i][b] = 1.f / SQR(b+1);
        }
        // biking
        if (bucketCostBoundsBike[b] < sumOfCostsBike) {
          bucketsBike[i][b] = 1.f - bucketCostBoundsBike[b] / sumOfCostsBike;
        } else {
          bucketsBike[i][b] = 1.f / SQR(b+1);
        }
      }
    }
  }

  // Second round of Dijkstras: Use buckets as likelihood to distribute the
  // population according to the reachable forest entries and their distance.
  vector<float> fepPop(fepIndices.size(), 0.f);
  vector<float> fepPopBike(fepIndices.size(), 0.f);
  for (size_t i = 0; i < fepIndices.size(); ++i) {
    dijkstra.reset();
    dijkstra.shortestPath(fepIndices[i], Dijkstra<RoadGraph>::no_target);
    const vector<int>& costs = dijkstra.get_costs();
    const vector<bool>& settled = dijkstra.get_settled_flags();
    for (size_t j = 0; j < populationIndices.size(); ++j) {
      int popIndex = populationIndices[j];
      //std::cout << "i,j=" << i << "," << j << " shape.size()=" << shares.size() << std::endl;
      if (settled[popIndex]) {
        int cost = costs[popIndex];
        //std::cout << "costs: " << cost << " c.size: " << costs.size() << " popIndex: " << popIndex << " j: " << j << " pI.size " << populationIndices.size() << std::endl;
        // biking
        uint b = determine_bucket_index(cost, bucketCostBoundsBike);
        //printf("b: %d, bB.size: %d, shares.size: %d, populations.size: %d, j: %d\n",
        //       b, bucketsBike[i].size(), shares.size(), populations.size(), j);
        fepPopBike[i] += bucketsBike[i][b] * shares[b] * populations[j];
        reachesForestByBicycle[j] = true;
        // walking
        if (cost < costLimitWalking) {
          uint bb = determine_bucket_index(cost, bucketCostBounds);
          fepPop[i] += buckets[i][bb] * shares[bb] * populations[j];
          reachesForestByWalking[j] = true;
        }
      }
    }

    done++;
    if ((clock() - timestamp) / CLOCKS_PER_SEC > 2) {
      timestamp = clock();
      printf("Progress: %d of %d, this is %5.1f%% \r\n",
             done, total, done * 100.f / total);
    }
  }

  // Normalize the population numbers:
  // - For population points which can reach the forest within <limit> time, all
  //   people are distributed over the reachable forest entries.
  // - For population points which cannot reach any forest entry, the bike and
  //   walking population is distributed over all entries such that their weight
  //   factor remains the same.
  // The car share is considered separately (return the numbers, such that they
  // can be mapped to the parking lots) =: TODO(Jonas)
  float sumFepPop = accumulate(fepPop.begin(), fepPop.end(), 0.f);
  float mappedPopulation = 0;
  for (size_t i = 0; i < populations.size(); ++i) {
    mappedPopulation += reachesForestByWalking[i] * populations[i] * kUserShareWalking;
  }
  float normalizer = sumFepPop / mappedPopulation;
  for (size_t i = 0; i < fepPop.size(); ++i) {
    fepPop[i] /= normalizer;
  }
  // biking
  float sumFepPopBike = accumulate(fepPopBike.begin(), fepPopBike.end(), 0.f);
  float mappedPopulationBike = 0;
  for (size_t i = 0; i < populations.size(); ++i) {
    mappedPopulationBike += reachesForestByBicycle[i] * populations[i] * kUserShareBicycle;
  }
  normalizer = sumFepPopBike / mappedPopulationBike;
  for (size_t i = 0; i < fepPop.size(); ++i) {
    fepPopBike[i] /= normalizer;
  }

  // Map those (bicycle+walking) who are not yet assigned to any forest entry.
  float unmapped = 0;
  for (size_t i = 0; i < populations.size(); ++i) {
    unmapped += (!reachesForestByWalking[i] * kUserShareWalking +
                 !reachesForestByBicycle[i] * kUserShareBicycle) * populations[i];
  }
  float mapped = mappedPopulation + mappedPopulationBike;
  for (size_t i = 0; i < fepIndices.size(); ++i) {
    float share = (fepPop[i] + fepPopBike[i]) / mapped;
    fepPop[i] += share * unmapped;
  }

  std::cout << "mapped/unmapped: " << mapped << " " << unmapped << std::endl;

  float totalPopulation = accumulate(populations.begin(), populations.end(), 0.f);
  if ((1.f - kUserShareWalking - kUserShareBicycle) *  totalPopulation != totalPopulation - (mapped + unmapped)) {
    std::cout << "Populations (1) differ: "
              << (1.f - kUserShareWalking - kUserShareBicycle) * totalPopulation
              << " vs. "
              << totalPopulation - (mapped + unmapped) << std::endl;
    //assert(false && "See stdout above.");
  }
  if ((kUserShareWalking + kUserShareBicycle) * totalPopulation
      != mapped + unmapped) {
    std::cout << "Populations (2) differ: "
              << (kUserShareWalking + kUserShareBicycle) * totalPopulation
              << " vs. "
              << mapped + unmapped << std::endl;
    //assert(false && "See stdout above.");
  }
  // TODO(Jonas): Return car population or do that elsewhere.
  const float kUserShareCar = 1.f - kUserShareWalking - kUserShareBicycle;
  return fepPop;
}


void print_usage() {
  std::cout <<
  "Usage: ./NAME <GraphFile> <ForestEntries> <PopulationNodes> <Preferences> <OutputFile>\n"
  "  GraphFile -- ...\n"
  "  ForestEntries -- ...\n"
  "  PopulationNodes -- ...\n"
  "  Preferences -- User study data as 2-column text file. First column contains upper bounds (in minutes), its last value denotes the cost limit for searches. The second column contains shares in [0,1], which sum up to at most 1.\n"
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

  // Read in the user preferences and convert them. The resulting shares
  // consider users which accept longer times to get to the forest also for
  // nearby forest entries. For example, 40% of the users accept 1h traveling
  // to reach the forest and 60% accept at most 30 min. Then 100% of users will
  // be considered for forest entries within 30 min, and 40% for those within
  // between 0.5h and 1h.
  vector<vector<float>> preferences = util::read_column_file<float>(prefFile);
  assert(forest::check_preferences(preferences));
  float cumsum = 0;
  for (auto it = preferences[1].rbegin(); it != preferences[1].rend(); ++it) {
    cumsum += *it;
    *it = cumsum;
  }
  assert(cumsum <= 1.f);


  // Reachability analysis
  vector<float> fepPopulations = reachability_analysis(
      graph, fepNodeIndices, population, populationNodeIndices, preferences);
  string filename = outfile;  // "forest_entries_popularity.tmp.txt";
  std::cout << "Writing entry point popularity to " << filename << std::endl;
  util::dump_vector(fepPopulations, filename);

  return 0;
}
