// Copyright 2011-2013: Jonas Sternisko

#include <kdtree++/kdtree.hpp>
#include <numeric>
#include <string>
#include <vector>
#include "./Dijkstra.h"
#include "./DirectedGraph.h"
#include "./Util.h"


// _____________________________________________________________________________
// Reference of a graph node in a 2dtree.
class TreeNode {
 public:
  typedef float value_type;
  // Construct a kdtree node for a graph node and its index.
  explicit TreeNode(const RoadGraph::Node_t& node, int index)
    : refNodeIndex(index) {
    pos[0] = node.x;
    pos[1] = node.y;
  }
  value_type operator[](size_t i) const {
    assert(i < 2);
    return pos[i];
  }
  int refNodeIndex;
  value_type pos[2];
};

typedef KDTree::KDTree<2, TreeNode> Tree2D;

// _____________________________________________________________________________
// Builds a 2d tree from a road graph.
Tree2D build_kdtree(const RoadGraph& graph) {
  Tree2D tree;
  for (size_t i = 0; i < graph.nodes().size(); ++i) {
    const RoadGraph::Node_t& node = graph.nodes()[i];
    tree.insert(TreeNode(node, i));
  }
  return tree;
}

// _____________________________________________________________________________
// Maps (x,y) coordinates to the closest node referenced by the kdtree.
vector<int> map_population_to_closest_node(const vector<float>& x,
    const vector<float>& y, const RoadGraph& graph) {
  Tree2D tree = build_kdtree(graph);
  vector<int> populationNodeIndices(x.size(), -1);
  assert(x.size() == y.size());
  for (size_t i = 0; i < x.size(); ++i) {
    RoadGraph::Node_t dummy;
    dummy.x = x[i];
    dummy.y = y[i];
    TreeNode pos(dummy, -1);
    std::pair<Tree2D::const_iterator, float> res = tree.find_nearest(pos);
    assert(res.first != tree.end());
    populationNodeIndices[i] = res.first->refNodeIndex;
  }
  return populationNodeIndices;
}

// _____________________________________________________________________________
// Returns the bucket index for a cost.
uint determine_bucket_index(int cost, const vector<int>& bucketCostBounds) {
  uint b = 0;
  while (b < bucketCostBounds.size() && cost > bucketCostBounds[b]) { b++; }
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
    const vector<int>& populationIndices) {
  assert(population.size() == populationIndices.size());
  typedef Dijkstra<RoadGraph::Node_t, RoadGraph::Arc_t> Dijkstra_t;
  Dijkstra_t dijkstra(graph);
  dijkstra.setCostLimit(3*60);

  // First round of Dijkstras: Analyse reachability and determine frequency of
  // forest distances categories for each population point.
  vector<int> bucketCostBounds = {5*60, 10*60, 15*60, 20*60, 25*60};
  vector<vector<float>> buckets(
      population.size(), vector<float>(bucketCostBounds.size() + 1, 0.f));
  for (int index: fepIndices) {
    dijkstra.reset();
    dijkstra.shortestPath(index, Dijkstra_t::no_target);
    const vector<int>& costs = dijkstra.getCosts();
    for (size_t i = 0; i < populationIndices.size(); ++i) {
      int popIndex = populationIndices[i];
      int cost = costs[popIndex];
      if (cost != Dijkstra_t::infinity) {
        uint b = determine_bucket_index(cost, bucketCostBounds);
        buckets[i][b]++;
      }
    }
  }

  // Evaluate the buckets: Compute likelihood, store it in place.
  for (size_t i = 0; i < population.size(); ++i) {
    float sumOfCosts = 0.f;
    for (size_t b = 0; b < buckets[i].size(); ++b) {
      sumOfCosts += buckets[i][b] * bucketCostBounds[b];
    }
    for (size_t b = 0; b < buckets[i].size(); ++b) {
      buckets[i][b] = 1. - bucketCostBounds[b] / sumOfCosts;
    }
  }

  // Second round of Dijkstras: Use buckets as likelihood to distribute the
  // population according to the reachable forest entries and their distance.
  vector<float> fepPop(fepIndices.size(), 0);
  for (size_t i = 0; i < fepIndices.size(); ++i) {
    int index = fepIndices[i];
    dijkstra.reset();
    dijkstra.shortestPath(index, Dijkstra_t::no_target);
    const vector<int>& costs = dijkstra.getCosts();
    for (size_t j = 0; j < populationIndices.size(); ++j) {
      int popIndex = populationIndices[j];
      int cost = costs[popIndex];
      if (cost != Dijkstra_t::infinity) {
        uint b = determine_bucket_index(cost, bucketCostBounds);
        fepPop[i] = fepPop[i] + buckets[i][b] * population[j];
      }
    }
  }

  // Normalize the population numbers: Sum must equal the sum before.
  float normalizer = std::accumulate(fepPop.begin(), fepPop.end(), 0.f) /
                     std::accumulate(population.begin(), population.end(), 0.f);
  for (size_t i = 0; i < fepPop.size(); ++i) {
    fepPop[i] = fepPop[i] / normalizer;
  }

  return fepPop;
}


void print_usage() {
  std::cout << "Usage: ./NAME <GraphFile> <ForestEntries> <PopulationNodes>"
            << std::endl;
}

// _____________________________________________________________________________
int main(int argc, char** argv) {
  if (argc != 4) {
    print_usage();
    exit(0);
  }
  string graphFile = argv[1];
  string fepFile = argv[2];
  string popFile = argv[3];

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
  vector<int> fepNodeIndices = util::read_column_file<int>(fepFile)[0];


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

  vector<int> populationNodeIndices = map_population_to_closest_node(x, y, graph);


  // Reachability analysis
  vector<float> fepPopulations = reachability_analysis(
      graph, fepNodeIndices, population, populationNodeIndices);
  util::dump_vector(fepPopulations, "fepPopulation.txt");

  return 0;
}
