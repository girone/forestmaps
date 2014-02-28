// Copyright 2014: Jonas Sternisko

#include "./EdgeAttractivenessModel.h"
#include <ctime>
#include <algorithm>
#include <iostream>
#include "./Dijkstra.h"
#include "./Util.h"

using std::accumulate;
using std::lower_bound;
using std::upper_bound;
using std::cout;
using std::endl;


// _____________________________________________________________________________
FloodingModel::FloodingModel(
    const RoadGraph& g,
    const vector<int>& feps,
    const vector<float>& popularities,
    const vector<vector<float>>& preferences,
    const int maxCost)
  : EdgeAttractivenessModel(g, feps, popularities, preferences, maxCost) {
}

// _____________________________________________________________________________
vector<float> FloodingModel::compute_edge_attractiveness() {
  // Prepare progress information
  size_t total = 2 * _forestEntries.size();
  size_t done = 0;
  clock_t timestamp = clock();

  // Collect node attractivenesses.
  vector<float> nodeAttractiveness(_graph.num_nodes(), 0.f);
  Dijkstra<RoadGraph> dijkstra(_graph);
  dijkstra.set_cost_limit(_maxCost / 2);  // half way forth and back
  for (int fep: _forestEntries) {
    dijkstra.reset();
    dijkstra.run(fep);
    const vector<int>& costs = dijkstra.get_costs();
    const vector<uint>& settledNodes = dijkstra.get_settled_node_indices();
    float popularity = _popularities[fep];
    for (uint node: settledNodes) {
      int cost = costs[node];
      assert(cost != Dijkstra<RoadGraph>::infinity);
      if (cost < 1) { cost = 1; }
      // Map cost * 2 with the preferences, adjust popularity share accordingly.
      float share = sum_of_user_shares_after(2.f * cost);
      // TODO(Jonas): Some scaling factor could/should be added below:
      float gain = popularity * share / cost;
      nodeAttractiveness[node] += gain;
    }

    // Progress
    done++;
    if ((clock() - timestamp) / static_cast<float>(CLOCKS_PER_SEC) > 0.00001) {
      timestamp = clock();
      printf("Progress: %d of %d, this is %5.1f%% \r\n",
             done, total, done * 100.f / total);
    }
  }

  // Convert to arc attractivenesses: Each arc gets the attractiveness of its target.
  const vector<RoadGraph::Arc_t>& arcs = _graph.arclist();
  for (size_t i = 0; i < arcs.size(); ++i) {
    _aggregatedEdgeAttractivenesses[i] = nodeAttractiveness[arcs[i].target];
  }
  return result();
}

// _____________________________________________________________________________
float EdgeAttractivenessModel::user_share(const float tif) const {
  assert(tif <= _preferences[0].back());
  // Do a binary search in the user preferences.
  auto it = lower_bound(_preferences[0].begin(), _preferences[0].end(), tif);
  if (it == _preferences[0].end()) { it--; }
  size_t offset = it - _preferences[0].begin();
  return _preferences[1][offset];
}

// _____________________________________________________________________________
float EdgeAttractivenessModel::sum_of_user_shares_after(const float tif) const {
  assert(tif <= _preferences[0].back());
  // Do a binary search in the user preferences.
  auto it = lower_bound(_preferences[0].begin(), _preferences[0].end(), tif);
  if (it == _preferences[0].end()) { it--; }
  size_t offset = it - _preferences[0].begin();
  return accumulate(_preferences[1].begin()+offset, _preferences[1].end(), 0.f);
}

// _____________________________________________________________________________
ViaEdgeApproach::ViaEdgeApproach(
    const RoadGraph& g,
    const vector<int>& feps,
    const vector<float>& popularities,
    const vector<vector<float>>& preferences,
    const int maxCost)
  : EdgeAttractivenessModel(g, feps, popularities, preferences, maxCost) {
  // Compute pairwise distances between forest entries.
  Dijkstra<RoadGraph> dijkstra(g);
  dijkstra.set_cost_limit(maxCost);
  for (int fep1: feps) {
    dijkstra.reset();
    dijkstra.run(fep1);
    const vector<int>& costs = dijkstra.get_costs();
    for (int fep2: feps) {
      _distances[fep1][fep2] = costs[fep2];
    }
  }
}

// _____________________________________________________________________________
vector<float> ViaEdgeApproach::compute_edge_attractiveness() {
  Dijkstra<RoadGraph> fwd(_graph), bwd(_graph);
  // During the search from s and t, ignore the respective other node.
  vector<bool> nodesToIgnoreBwd(_graph.num_nodes(), false);
  vector<bool> nodesToIgnoreFwd(_graph.num_nodes(), false);
  bwd.set_nodes_to_ignore(&nodesToIgnoreBwd);
  fwd.set_nodes_to_ignore(&nodesToIgnoreFwd);

  // Iterate over all forest edges s --> t.
  // For each edge, do a forward Dijkstra from t and a backward Dijkstra from s.#
  const vector<RoadGraph::Arc_t>& arcs = _graph.arclist();
  // Prepare progress information
  size_t total = arcs.size();
  size_t done = 0;
  clock_t timestamp = clock();
  for (size_t arcIndex = 0; arcIndex < arcs.size(); ++arcIndex) {
    // Set up
    const RoadGraph::Arc_t& arc = arcs[arcIndex];
    int s = arc.source;
    int t = arc.target;
    int c = arc.cost;
    bwd.set_cost_limit(_maxCost - c);
    fwd.set_cost_limit(_maxCost - c);
    nodesToIgnoreBwd[t] = true;
    nodesToIgnoreFwd[s] = true;

    bwd.run(s, Dijkstra<RoadGraph>::no_target);
    fwd.run(t, Dijkstra<RoadGraph>::no_target);
    evaluate(arcIndex, c,
             bwd.get_costs(), bwd.get_settled_flags(),
             fwd.get_costs(), fwd.get_settled_flags());

    // Clean up
    nodesToIgnoreBwd[t] = false;
    nodesToIgnoreFwd[s] = false;

    // Progress
    done++;
    if ((clock() - timestamp) / CLOCKS_PER_SEC > 2) {
      timestamp = clock();
      printf("Progress: %d of %d, this is %5.1f%% \r\n",
             done, total, done * 100.f / total);
    }
  }
  // ^^ TODO(Jonas): put to separate method

  normalize_contributions(&_fepContribution);

  distribute(_popularities, _fepContribution);

  return result();
}

// _____________________________________________________________________________
// Evaluates the cost vectors computed by Djkstra's from an edge s --> t.
void ViaEdgeApproach::evaluate(
    const int edgeIndex,
    const int c,
    const vector<int>& costsS,
    const vector<bool>& settledS,
    const vector<int>& costsT,
    const vector<bool>& settledT) {
  // Evaluate routes fep1 -->* s --> t --> fep2.
  for (int fep1: _forestEntries) {
    if (!settledS[fep1]) { continue; }
    const int costsFep1 = costsS[fep1];
    for (int fep2: _forestEntries) {
      if (!settledT[fep2]) { continue; }
      const int costsFep2 = costsT[fep2];
      const int routeCostViaThisEdge = costsFep1 + c + costsFep2;
      if (routeCostViaThisEdge > _maxCost) { continue; }
      float gain = 0;
      const float share = sum_of_user_shares_after(routeCostViaThisEdge);
      if (fep1 == fep2) {
        gain = share * 1.f / (costsFep2 + 1);
      } else {
        const float distance = _distances[fep1][fep2];
        gain = share * distance / (routeCostViaThisEdge + 1);
      }
      _fepContribution[fep1][edgeIndex] = gain;
    }
  }
}

typedef std::pair<int, float> ElementType;
struct LessSecond {
  bool operator()(const ElementType& lhs, const ElementType& rhs) const {
    return lhs.second < rhs.second;
  }
} cmp;

// _____________________________________________________________________________
void ViaEdgeApproach::normalize_contributions(MapMap* contributions) {
  for (auto it = contributions->begin(); it != contributions->end(); ++it) {
    // Normalize by the max.
    Map* cc = &(it->second);
    float max = std::max_element(cc->begin(), cc->end(), cmp)->second;
    assert(max != 0. && "Avoid zero-division.");
    float normalizer = 1. / max;
    for (auto itit = cc->begin(); itit != cc->end(); ++itit) {
      itit->second *= normalizer;
    }
  }
}

// _____________________________________________________________________________
void ViaEdgeApproach::distribute(const Map& popu, const MapMap& contr) {
  for (auto it = popu.begin(); it != popu.end(); ++it) {
    const int entryPoint = it->first;
    const float population = it->second;
    auto fit = contr.find(entryPoint);
    // Use an empty map if the entry point does not contribute to any edge.
    const Map& shares = (fit == contr.end()) ? Map() : fit->second;
    for (auto it2 = shares.begin(); it2 != shares.end(); ++it2) {
      const int edgeIndex = it2->first;
      const float share = it2->second;
      assert(edgeIndex < _aggregatedEdgeAttractivenesses.size());
      _aggregatedEdgeAttractivenesses[edgeIndex] += share * population;
    }
  }
}
