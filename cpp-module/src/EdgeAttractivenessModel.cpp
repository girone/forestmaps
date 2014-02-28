// Copyright 2014: Jonas Sternisko

#include "./EdgeAttractivenessModel.h"
#include <algorithm>
#include <iostream>
#include "./Dijkstra.h"
#include "./Util.h"

using std::accumulate;
using std::lower_bound;
using std::upper_bound;
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
    evaluate(arcIndex, c, bwd.get_costs(), fwd.get_costs());

    // Clean up
    nodesToIgnoreBwd[t] = false;
    nodesToIgnoreFwd[s] = false;
  }
  return result();
}

// _____________________________________________________________________________
// Evaluates the cost vectors computed by Djkstra's from an edge s --> t.
void ViaEdgeApproach::evaluate(
    const int edgeIndex,
    const int c,
    const vector<int>& costsS,
    const vector<int>& costsT) {
  // Evaluate routes fep1 -->* s --> t --> fep2.
  for (int fep1: _forestEntries) {
    const int costsFep1 = costsS[fep1];
    if (costsFep1 == Dijkstra<RoadGraph>::infinity) { continue; }
    for (int fep2: _forestEntries) {
      const int costsFep2 = costsT[fep2];
      if (costsFep2 == Dijkstra<RoadGraph>::infinity) { continue; }
      const int totalCost = costsFep1 + c + costsFep2;
      if (totalCost > _maxCost) { continue; }
      float gain;
      const float share = sum_of_user_shares_after(totalCost);
      if (fep1 == fep2) {
        gain = share * _popularities[fep1] / costsFep2;
      } else {
        const float popularity = std::min(_popularities[fep1], _popularities[fep2]);
        const float distance = _distances[fep1][fep2];
        assert(totalCost > 0);
        gain = distance / totalCost * (share * popularity);
      }
      _aggregatedEdgeAttractivenesses[edgeIndex] += gain;
    }
  }
}

// _____________________________________________________________________________
bool EdgeAttractivenessModel::check_preferences(
    const vector<vector<float> >& preferences) {
  using std::endl;
  for (size_t i = 1; i < preferences[0].size(); ++i) {
    if (preferences[0][i] <= preferences[0][i-1]) {
      std::cout << "Wrong prefence intervals: upper bound " << preferences[0][i]
                << " is less than or equal its predecessor." << std::endl;
      exit(1);
    }
  }

  for (float share: preferences[1]) {
    if (share < 0 || share > 1) {
      std::cout << "Wrong preference values: share " << share
                << " is not in [0,1]." << std::endl;
      exit(1);
    }
  }

  if (std::accumulate(preferences[1].begin(), preferences[1].end(), 0.f) > 1.) {
    std::cerr << "Sum of preference category shares is greater than 1." << endl;
    exit(1);
  }

  return true;
}
