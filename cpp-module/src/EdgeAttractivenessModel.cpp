// Copyright 2014: Jonas Sternisko

#include "./EdgeAttractivenessModel.h"
#include <algorithm>
#include <utility>
#include "./Util.h"
#include "./Timer.h"

using std::accumulate;
using std::lower_bound;
using std::upper_bound;
using std::cout;
using std::endl;
using std::pair;
using std::make_pair;


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

typedef std::pair<int, float> ElementType;
struct LessSecond {
  bool operator()(const ElementType& lhs, const ElementType& rhs) const {
    return lhs.second < rhs.second;
  }
} cmp;

// _____________________________________________________________________________
void EdgeAttractivenessModel::normalize_contributions(MapMap* contributions) {
  for (auto it = contributions->begin(); it != contributions->end(); ++it) {
    // Normalize s.t. the maxium contribution becomes 1.
    Map* cc = &(it->second);
    if (cc->size()) {
      float max = std::max_element(cc->begin(), cc->end(), cmp)->second;
      if (max > 0.f) {
        assert(max != 0. && "Avoid zero-division.");
        float normalizer = 1. / max;
        for (auto itit = cc->begin(); itit != cc->end(); ++itit) {
          itit->second *= normalizer;
        }
      }
    }
  }
}

// _____________________________________________________________________________
void EdgeAttractivenessModel::distribute(
    const Map& popu,
    const MapMap& contr,
    vector<float>* attractivenesses) const {
  for (auto it = popu.begin(); it != popu.end(); ++it) {
    const int entryPoint = it->first;
    const float population = it->second;
    auto fit = contr.find(entryPoint);
    // Use an empty map if the entry point does not contribute to any edge.
    const Map& shares = (fit == contr.end()) ? Map() : fit->second;
    for (auto it2 = shares.begin(); it2 != shares.end(); ++it2) {
      const int edgeIndex = it2->first;
      const float share = it2->second;
      assert(static_cast<size_t>(edgeIndex) < attractivenesses->size());
      (*attractivenesses)[edgeIndex] += share * population;
    }
  }
}

// _____________________________________________________________________________
FloodingModel::FloodingModel(
    const ForestRoadGraph& g,
    const vector<int>& feps,
    const vector<float>& popularities,
    const vector<vector<float>>& preferences,
    const int maxCost)
  : EdgeAttractivenessModel(g, feps, popularities, preferences, maxCost) {
}

// _____________________________________________________________________________
vector<int> FloodingModel::compute_node_from_arc_weights(
    const ForestRoadGraph& graph) const {
  vector<int> weights(graph.num_nodes(), 0);
  for (const auto& arc: graph.arclist()) {
    uint s = arc.source;
    uint t = arc.target;
    int w = arc.labels[1];
    assert(s < weights.size());
    assert(t < weights.size());
    weights[s] = std::max(weights[s], w);
    weights[t] = std::max(weights[t], w);
  }
  return weights;
}

// _____________________________________________________________________________
vector<float> FloodingModel::compute_edge_attractiveness() {
  cout << "Starting..." << endl;
  // Prepare progress information
  size_t total = _forestEntries.size();
  size_t done = 0;
  Timer t;
  t.start();

  vector<int> nodeWeights = compute_node_from_arc_weights(_graph);

  // Collect contribution of forest entries to node attractivenesses.
  MapMap contribution;
  Dijkstra<ForestRoadGraph> dijkstra(_graph);
  dijkstra.set_cost_limit(_maxCost / 2);  // half way forth and back
  for (const uint fep: _forestEntries) {
    dijkstra.reset();
    dijkstra.run(fep);
    const vector<int>& costs = dijkstra.get_costs();
    const vector<uint>& settledNodes = dijkstra.get_settled_node_indices();
    for (const uint node: settledNodes) {
      int cost = costs[node];
      assert(cost != Dijkstra<ForestRoadGraph>::infinity);
      if (cost < 1) { cost = 1; }
      // Map cost * 2 with the preferences, adjust popularity share accordingly.
      float share = sum_of_user_shares_after(2.f * cost);
      // NOTE(Jonas): As a first scaling variant, increase the gain to minutes.
      // NOTE(Jonas): Try also division by (cost + 60).
      float gain = share / (cost + 60);
      int w = nodeWeights[node];
      float value = w * gain;
      if (value != 0.f) {
        contribution[fep][node] = value;
      }
    }

    // Progress
    done++;
    if (t.intermediate() / 1000 > 2) {
      printf("Progress: %i of %i, this is %5.1f%% \r\n",
             done, total, done * 100.f / total);
      t.stop();
      t.start();
    }
  }

  cout << "Normalizing and distributing the contributions..." << endl;
  // Collect node attractivenesses.
  normalize_contributions(&contribution);
  vector<float> nodeAttractiveness(_graph.num_nodes(), 0.f);
  distribute(_popularities, contribution, &nodeAttractiveness);

  // Node -> Arc: Each arc gets the attractiveness of its target node.
  const vector<ForestRoadGraph::Arc_t>& arcs = _graph.arclist();
  for (size_t i = 0; i < arcs.size(); ++i) {
    _aggregatedEdgeAttractivenesses[i] = nodeAttractiveness[arcs[i].target];
  }
  return result();
}

// _____________________________________________________________________________
ViaEdgeApproach::ViaEdgeApproach(
    const ForestRoadGraph& g,
    const vector<int>& feps,
    const vector<float>& popularities,
    const vector<vector<float>>& preferences,
    const int maxCost)
  : EdgeAttractivenessModel(g, feps, popularities, preferences, maxCost) {
  compute_counterarc_map(g);
  compute_distance_table(g, feps, maxCost);
}

// _____________________________________________________________________________
void ViaEdgeApproach::compute_distance_table(const ForestRoadGraph& g,
                                             const vector<int>& feps,
                                             const int maxCost) {
  // Compute pairwise distances between forest entries.
  cout << "Setting up entry point distance table..." << endl;
  Dijkstra<ForestRoadGraph> dijkstra(g);
  dijkstra.set_cost_limit(maxCost);
  size_t count = 0;
  for (int fep1: feps) {
    ++count;
    if (count % 5000 == 0) {
      cout << "Progress: " << count << " of " << feps.size()
           << ", this is ";
      printf("%.1f%%.\n", 100. * count / feps.size());
    }

    dijkstra.reset();
    dijkstra.run(fep1);
    const vector<int>& costs = dijkstra.get_costs();
    vector<int> settledEntries = determine_settled_forest_entries(dijkstra);
    for (int fep2: settledEntries) {
      // The distances are symmetric. Exploit this and keep only half of them.
      if (fep1 <= fep2) {
          _distances[fep1][fep2] = costs[fep2];
      }
    }
  }
}

// _____________________________________________________________________________
void ViaEdgeApproach::compute_counterarc_map(const ForestRoadGraph& g) {
  unordered_map<pair<int, int>, vector<int>, util::PairHash> abToArcIndex;
  int index = 0;
  for (const ForestRoadGraph::Arc_t& arc: g.arclist()) {
    abToArcIndex[make_pair(arc.source, arc.target)].push_back(index);
    index++;
  }
  _arcIndexToCounterArcIndex.clear();
  for (const auto& entry: abToArcIndex) {
    int a = entry.first.first;
    int b = entry.first.second;
    auto it = abToArcIndex.find(make_pair(b, a));
    assert(it != abToArcIndex.end() && "Counter-arc(s) is not in the graph?");
    assert(entry.second.size() == it->second.size());
    for (size_t i = 0; i < entry.second.size(); ++i) {
      int index = entry.second[i];
      int counterIndex = it->second[i];
      _arcIndexToCounterArcIndex[index] = counterIndex;
    }
  }
}

// _____________________________________________________________________________
int ViaEdgeApproach::get_counterpart(int arcIndex) const {
  auto it = _arcIndexToCounterArcIndex.find(arcIndex);
  assert(it != _arcIndexToCounterArcIndex.end());
  return it->second;
}

// _____________________________________________________________________________
int ViaEdgeApproach::get_distance(int forestEntry1, int forestEntry2) const {
  int a = forestEntry1 <= forestEntry2 ? forestEntry1 : forestEntry2;
  int b = forestEntry1 >  forestEntry2 ? forestEntry1 : forestEntry2;
  auto it = _distances.find(a);
  assert(it != _distances.end());
  auto it2 = it->second.find(b);
  assert(it2 != it->second.end());
  return it2->second;
}

// _____________________________________________________________________________
vector<float> ViaEdgeApproach::compute_edge_attractiveness() {
  cout << "Starting..." << endl;
  Dijkstra<ForestRoadGraph> fwd(_graph), bwd(_graph);
  // During the search from s and t, ignore the respective other node.
  vector<bool> nodesToIgnoreBwd(_graph.num_nodes(), false);
  vector<bool> nodesToIgnoreFwd(_graph.num_nodes(), false);
  bwd.set_nodes_to_ignore(&nodesToIgnoreBwd);
  fwd.set_nodes_to_ignore(&nodesToIgnoreFwd);

  // Iterate over all forest edges s --> t.
  // For each edge, do a forward Dijkstra from t and a backward Dijkstra from s.
  const vector<ForestRoadGraph::Arc_t>& arcs = _graph.arclist();
  MapMap contributions;
  // We only have bidirectional arcs. The code avoids to compute everything
  // twice for a-->b and b-->a
  vector<bool> examined(arcs.size(), false);
  // Prepare progress information
  size_t total = arcs.size();
  size_t done = 0;
  Timer timer;
  timer.start();
  for (size_t arcIndex = 0; arcIndex < arcs.size(); ++arcIndex) {
    if (!examined[arcIndex]) {
      // Set up
      const ForestRoadGraph::Arc_t& arc = arcs[arcIndex];
      int s = arc.source;
      int t = arc.target;
      int c = arc.labels[0];
      int w = arc.labels[1];
      bwd.set_cost_limit(_maxCost - c);
      fwd.set_cost_limit(_maxCost - c);
      nodesToIgnoreBwd[t] = true;
      nodesToIgnoreFwd[s] = true;

      // Run two Dijkstras
      bwd.run(s, Dijkstra<ForestRoadGraph>::no_target);
      fwd.run(t, Dijkstra<ForestRoadGraph>::no_target);

      // Evaluate the forward and backward direction in one sweep.
      evaluate(arcIndex, c, w, bwd, fwd, &contributions);
      size_t counterArcIndex = get_counterpart(arcIndex);
      evaluate(counterArcIndex, c, w, fwd, bwd, &contributions);

      // Clean up
      nodesToIgnoreBwd[t] = false;
      nodesToIgnoreFwd[s] = false;

      // Mark a-->b and b-->a as examined.
      examined[arcIndex] = true;
      examined[counterArcIndex] = true;
    }

    // Progress
    done++;
    if (timer.intermediate() / 1000 > 2) {
      printf("Progress: %i of %i, this is %5.1f%% \r\n",
             done, total, done * 100.f / total);
      timer.stop();
      timer.start();
    }
  }

  cout << "Normalizing and distributing contributions..." << endl;
  normalize_contributions(&contributions);

  distribute(_popularities, contributions, &_aggregatedEdgeAttractivenesses);

  return result();
}

// _____________________________________________________________________________
vector<int> ViaEdgeApproach::determine_settled_forest_entries(
    const Dijkstra<ForestRoadGraph>& dijkstra) const {
  // Sort the settled nodes to allow for list intersection.
//   vector<uint> settledNodes = dijkstra.get_settled_node_indices();
//   std::sort(settledNodes.begin(), settledNodes.end());
  const vector<bool>& settledFlags = dijkstra.get_settled_flags();
  vector<uint> settledNodes;
  settledNodes.reserve(dijkstra.get_num_settled_nodes());
  for (auto it = settledFlags.begin(); it != settledFlags.end(); ++it) {
    if (*it) {
      settledNodes.push_back(it - settledFlags.begin());
    }
  }

  const size_t fepsize = _forestEntries.size();
  vector<int> settledForestEntries;
  settledForestEntries.reserve(std::min(settledNodes.size(), fepsize));

  // Assumes the _forestEntries are sorted.
  std::set_intersection(settledNodes.begin(), settledNodes.end(),
                        _forestEntries.begin(), _forestEntries.end(),
                        std::back_inserter(settledForestEntries));
  return settledForestEntries;
}

// _____________________________________________________________________________
// Evaluates the cost vectors computed by Djkstra's from an edge s --> t.
void ViaEdgeApproach::evaluate(
    const int edgeIndex,
    const int c,
    const int w,
    const Dijkstra<ForestRoadGraph>& dijkstraToS,
    const Dijkstra<ForestRoadGraph>& dijkstraFromT,
    MapMap* contributions) const {
  const vector<int>& costsS = dijkstraToS.get_costs();
  const vector<int>& costsT = dijkstraFromT.get_costs();
  vector<int> entriesToS = determine_settled_forest_entries(dijkstraToS);
  vector<int> entriesFromT = determine_settled_forest_entries(dijkstraFromT);

  // Evaluate routes fep1 -->* s --> t --> fep2.
  for (int fep1: entriesToS) {
    //if (!settledS[fep1]) { continue; }
    const int costsFep1 = costsS[fep1];
    for (int fep2: entriesFromT) {
//       if (!settledT[fep2]) { continue; }
//       const int costsFep2 = costsT[fep2];
      const int routeCostViaThisEdge = costsFep1 + c + costsT[fep2];
      if (routeCostViaThisEdge > _maxCost) { continue; }
      float gain = 0;
      const float share = sum_of_user_shares_after(routeCostViaThisEdge);
      if (fep1 == fep2) {
        gain = share / (costsT[fep2] + 60.f);
      } else {
        const float distance = get_distance(fep1, fep2);
        gain = share * distance / (routeCostViaThisEdge + 60.f);
      }
      float increase = w * gain;
      if (increase > 0) {
        (*contributions)[fep1][edgeIndex] += increase;
      }
    }
  }
}
