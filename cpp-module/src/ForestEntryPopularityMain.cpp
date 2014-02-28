// Copyright 2013-2014: Jonas Sternisko

#include <algorithm>
#include <set>
#include <string>
#include <utility>
#include <vector>
#include "./Dijkstra.h"
#include "./DirectedGraph.h"
#include "./EdgeAttractivenessModel.h"
#include "./GraphSimplificator.h"
#include "./GraphConverter.h"
#include "./Util.h"
#include "./ForestUtil.h"
#include "./Timer.h"
#include "./Tree2d.h"

using std::pair;
using std::cout;
using std::endl;

#define SQR(x) ((x)*(x))

// The user studies revealed these numbers:
const float kUserShareBicycle = 13 / 124.f;
const float kUserShareWalking = 71 / 124.f;
const float kUserShareCar = 1.f - (kUserShareWalking + kUserShareBicycle);

// We combined the extraction of travel costs for bike and walking by assuming
// the average bike speed being at a constant factor from the walking speed:
const float kWalkingToBikeSpeedFactor = 4.f;

// _____________________________________________________________________________
// Returns true if the differnce is more than 1% of a.
bool differ(const double a, const double b, double deviation = 0.01) {
  return fabs(a - b) > fabs(deviation * a);
}

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
// Returns the population of each entry point and the number of unmapped people.
//
// graph       - The road graph with edge costs being the walking (!) time.
// preferences - We assume the same user preferences for walking and biking, but
//               the provided times refer to walking. Biking times are derived
//               using the constant factor above.
int reachability_analysis(const RoadGraph& graph,
                          const vector<int>& fepIndices,
                          const vector<float>& populations,
                          const vector<int>& populationIndices,
                          const vector<vector<float> >& preferences,
                          float userShareWalking,
                          float userShareBicycle,
                          float userShareCar,
                          vector<double>* fepPopulationOut) {
  // TODO(Jonas): Split this method into multiple submethods.
  //
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
  Timer t;
  t.start();

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
    if (t.intermediate() / 1000 > 2) {
      printf("Progress: %i of %i, this is %5.1f%% \r\n",
             done, total, done * 100.f / total);
      t.stop();
      t.start();
    }
  }

  // Evaluate the buckets: Compute likelihood, store it in place.
  for (size_t i = 0; i < populations.size(); ++i) {
    float sumOfCosts = 0.f;
    float sumOfCostsBike = 0.f;
    for (size_t b = 0; b < buckets[i].size(); ++b) {
      sumOfCosts += buckets[i][b] * bucketCostBounds[b];
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
          bucketsBike[i][b] = 1.f / SQR(b + 1);
        }
      }
    }
  }

  // Second round of Dijkstras: Use buckets as likelihood to distribute the
  // population according to the reachable forest entries and their distance.
  vector<double> fepPop(fepIndices.size(), 0.f);
  vector<double> fepPopBike(fepIndices.size(), 0.f);
  for (size_t i = 0; i < fepIndices.size(); ++i) {
    dijkstra.reset();
    dijkstra.shortestPath(fepIndices[i], Dijkstra<RoadGraph>::no_target);
    const vector<int>& costs = dijkstra.get_costs();
    const vector<bool>& settled = dijkstra.get_settled_flags();
    for (size_t j = 0; j < populationIndices.size(); ++j) {
      int popIndex = populationIndices[j];
      if (settled[popIndex]) {
        int cost = costs[popIndex];
        // biking
        uint b = determine_bucket_index(cost, bucketCostBoundsBike);
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
    if (t.intermediate() / 1000 > 2) {
      printf("Progress: %i of %i, this is %5.1f%% \r\n",
             done, total, done * 100.f / total);
      t.stop();
      t.start();
    }
  }

  // Normalize the population numbers:
  // - For population points which can reach the forest within <limit> time, all
  //   people are distributed over the reachable forest entries.
  // - For population points which cannot reach any forest entry, the bike and
  //   walking population is distributed over all entries such that their weight
  //   factor remains the same.
  float sumFepPop = util::sum(fepPop);
  float mappedPopulation = 0;
  for (size_t i = 0; i < populations.size(); ++i) {
    mappedPopulation += reachesForestByWalking[i] * populations[i]
        * userShareWalking;
  }
  float normalizer = sumFepPop / mappedPopulation;
  for (size_t i = 0; i < fepPop.size(); ++i) {
    fepPop[i] /= normalizer;
  }
  // biking
  float sumFepPopBike = util::sum(fepPopBike);
  float mappedPopulationBike = 0;
  for (size_t i = 0; i < populations.size(); ++i) {
    mappedPopulationBike += reachesForestByBicycle[i] * populations[i]
        * userShareBicycle;
  }
  normalizer = sumFepPopBike / mappedPopulationBike;
  for (size_t i = 0; i < fepPop.size(); ++i) {
    fepPopBike[i] /= normalizer;
  }

  // Map those (bicycle+walking) who are not yet assigned to any forest entry.
  float unmapped = 0;
  for (size_t i = 0; i < populations.size(); ++i) {
    unmapped += (!reachesForestByWalking[i] * userShareWalking +
                 !reachesForestByBicycle[i] * userShareBicycle)
        * populations[i];
  }
  float mapped = mappedPopulation + mappedPopulationBike;
  for (size_t i = 0; i < fepIndices.size(); ++i) {
    float share = (fepPop[i] + fepPopBike[i]) / mapped;
    fepPop[i] += share * unmapped;
  }

  // Add bicycle to walking populations.
  for (size_t i = 0; i < fepIndices.size(); ++i) {
    fepPop[i] = fepPop[i] + fepPopBike[i];
  }

  // Some post-checks of the calculations. Do the number match roughly?
  float totalPopulation = util::sum(populations);
  if (differ(totalPopulation * (1.f - userShareWalking - userShareBicycle),
             totalPopulation - (mapped + unmapped))) {
    cout << "Remaining unmapped populations differ from quota: "
              << (1.f - userShareWalking - userShareBicycle) * totalPopulation
              << " vs. "
              << totalPopulation - (mapped + unmapped) << endl;
    // assert(false && "See stdout above.");
  }
  if (differ(totalPopulation * (userShareWalking + userShareBicycle),
             mapped + unmapped)) {
    cout << "Mapped walking and biking populations differ from quota: "
              << (userShareWalking + userShareBicycle) * totalPopulation
              << " vs. "
              << mapped + unmapped << endl;
    // assert(false && "See stdout above.");
  }

  // Calculate the car share. It is considered separately.
  float carPopulation = 0.f;
  for (size_t i = 0; i < populations.size(); ++i) {
    carPopulation += userShareCar * populations[i];
  }
  /*{
    std::ofstream ofs(carPopulationFile);
    ofs << carPopulation << endl;
    cout << "Car population written to '" << carPopulationFile << "'."
              << endl;
  }*/
  fepPopulationOut->swap(fepPop);
  return carPopulation;
}

// Returns the Euclidean distance between two points (x0,y0) and (x1,y1).
float euclid(float x0, float y0, float x1, float y1) {
  return sqrt(SQR(x1-x0) + SQR(y1-y0));
}

// _____________________________________________________________________________
// Distributes the total car population to a set of parking lots described by
// coordinates. Returns the populations as vector corresponding to the input.
vector<float> distribute_car_population(
    const int population,
    const vector<vector<float> >& parkingLots) {
  assert(parkingLots.size() == 4);
  assert(parkingLots[0].size() == parkingLots[1].size());
  assert(parkingLots[1].size() == parkingLots[2].size());
  assert(parkingLots[2].size() == parkingLots[3].size());
  // The population is distributed over all parking spaces.
  size_t numParkingLots = parkingLots[0].size();
  assert(numParkingLots > 0);
  vector<float> parkingPopulations(numParkingLots, 0);
  const vector<float>& ranks = parkingLots[2];
  float sumOfRanks = util::sum(ranks);
  if (sumOfRanks == 0)
    sumOfRanks = 1;
  for (size_t i = 0; i < numParkingLots; ++i) {
    parkingPopulations[i] = population * ranks[i] / sumOfRanks;
  };

  float mappedParkingPopulation = util::sum(parkingPopulations);
  if (differ(population, mappedParkingPopulation)) {
    cout << "Input population for parking differs from mapped population: "
              << population << " vs. "
              << mappedParkingPopulation << endl;
  }
  return parkingPopulations;
}

// _____________________________________________________________________________
RoadGraph read_and_simplify_graph(const string& filename,
                                  vector<int>* entryNodeIds) {
  // Read the original graph
  SimplificationGraph input;
  input.read_in(filename);

  // Simplify the graph.
  GraphSimplificator simplificator(&input);
  set<uint> doNotContract(entryNodeIds->begin(), entryNodeIds->end());
  SimplificationGraph simplified = simplificator.simplify(&doNotContract);

  // Shift the forest entry indices.
  const vector<int>& shift = simplificator.index_shift();
  std::transform(entryNodeIds->begin(), entryNodeIds->end(),
                 entryNodeIds->begin(),
                 [shift](int i) { return i - shift[i]; });

  // Return the converted graph.
  return convert_graph<SimplificationGraph, RoadGraph>(simplified);
}

// _____________________________________________________________________________
void print_usage() {
  cout <<
  "Usage: ./NAME <GraphFile> <ForestEntriesAndParkingXYRF> <PopulationNodes> "
  "<Preferences> <ParkingLots> <OutputFile>\n"
  "  GraphFile -- ...\n"
  "  ForestEntriesAndParkingXYRF -- Forest entries and parking lots with "
  "latitude, longitude, Road graph index, Forest graph index\n"
  "  PopulationNodes -- ...\n"
  "  Preferences -- User study data as 2-column text file. First column "
  "contains upper bounds (in minutes), its last value denotes the cost limit "
  "for searches. The second column contains shares in [0,1], which sum up to "
  "at most 1.\n"
  "  ParkingLots -- Location (latitude, longitude), rank and population of "
  "the parking lots.\n"
  "  OutputFile -- Path and name of the ouput file for populations.\n"
  "  User share {walking, bicycle, car} (floating numbers, three or none) -- \n"
  "The share of the population that uses the respective mean of transport.\n"
       << endl;
}

// _____________________________________________________________________________
int main(int argc, char** argv) {
  if (argc != 7 || argc != 10) {
    print_usage();
    exit(0);
  }
  string graphFile = argv[1];
  string fepAndParkingFile = argv[2];
  string popFile = argv[3];
  string prefFile = argv[4];
  string parkFile = argv[5];
  string outfile = argv[6];
  float userShareWalking =
      (argc == 10) ? util::convert<float>(argv[7]) : kUserShareWalking;
  float userShareBicycle =
      (argc == 10) ? util::convert<float>(argv[8]) : kUserShareBicycle;
  float userShareDriving =
      (argc == 10) ? util::convert<float>(argv[9]) : kUserShareCar;


  // Read in the parking lots. Format is:
  //  lat0 lon0 rank0 population0
  //  lat1 lon1 rank1 population1
  //  ...
  vector<vector<float> > parkingLots = util::read_column_file<float>(parkFile);
  assert(parkingLots.size() == 4);
  int numParking = parkingLots[0].size();

  // Read the forest entries. The file has the format
  //  lat0 lon0 nodeId0
  //  lat1 lon1 nodeId1
  //  ...
  // with N lines of which the first are forest entries and the last N-M are
  // parking lots, where M = |parkFile|.
  vector<vector<float> > fepAndParkingCols =
      util::read_column_file<float>(fepAndParkingFile);
  assert(fepAndParkingCols.size() > 2);
  vector<int> fepNodeIndices(fepAndParkingCols[2].begin(),
                             fepAndParkingCols[2].end() - numParking);

  // Read the graph. The file has the graph format
  //  #nodes
  //  #edges
  //  x y (node0)
  //  x y (node1)
  //  ...
  //  source target cost (arc0)
  //  source target cost (arc1)
  //  ...
  // Internally, the graph is simplified and the entry indices are shifted.
//   RoadGraph graph = read_and_simplify_graph(graphFile, &fepNodeIndices);
  // NOTE(Jonas): The simplification is still buggy in this part. Some index
  // problem remains. The speed advantage is not that large, so I leave it out.
  RoadGraph graph;
  graph.read_in(graphFile);

  // Read the population nodes. The file has the format:
  //  lat0 lon0 population0
  //  lat1 lon1 population1
  //  ...
  // We map the population to the closest node.
  vector<vector<float>> popColumns = util::read_column_file<float>(popFile);
  assert(popColumns.size() == 3);
  const vector<float>& lat = popColumns[0];
  const vector<float>& lon = popColumns[1];
  const vector<float>& population = popColumns[2];

  vector<int> populationNodeIndices =
      map_xy_locations_to_closest_node(lat, lon, graph);

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

  // > The actual reachability analysis <
  vector<double> fepPopulation;
  int carPopulation = reachability_analysis(
      graph, fepNodeIndices, population, populationNodeIndices, preferences,
      userShareWalking, userShareBicycle, userShareDriving, &fepPopulation);

  // PARKING LOTS

  // The population of parking lots is computed separately from the regular
  // forest entries: With higher rank they get a higher share of the car
  // population. Optionally the population can be used as given in the input.
  // Finally, the population of the parking lots is added to nodes of the graph,
  // such as if they were regular forest entries.

  bool useParkingLotPopulationFromInput = true;
  vector<float> parkingPopulations;
  if (useParkingLotPopulationFromInput) {
    parkingPopulations = parkingLots[3];
  } else {
    parkingPopulations = distribute_car_population(carPopulation, parkingLots);
  }

  // Add the parking populations to the forest entry population.
  fepPopulation.insert(fepPopulation.end(),
                       parkingPopulations.begin(), parkingPopulations.end());

  // Output.
  cout << "Writing entry point popularity to " << outfile << endl;
  util::dump_vector(fepPopulation, outfile);

  // Message to external callers which can't fetch the return code.
  cout << endl << "OK" << endl;
  return 0;
}
