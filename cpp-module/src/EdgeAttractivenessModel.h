// Copyright 2013: Jonas Sternisko

#ifndef SRC_EDGEATTRACTIVENESSMODEL_H_
#define SRC_EDGEATTRACTIVENESSMODEL_H_

#include <unordered_map>
#include <vector>
#include "./Dijkstra.h"
#include "./DirectedGraph.h"
#include "Util.h"

using std::unordered_map;
using std::vector;


class EdgeAttractivenessModel {
 public:
  // C'tor.
  EdgeAttractivenessModel(const RoadGraph& g,
                          const vector<int>& feps,
                          const vector<float>& popularities,
                          const int maxCost)
    : _graph(g)
    , _forestEntries(feps)
    , _maxCost(maxCost)
    , _aggregatedEdgeAttractivenesses(g.num_arcs(), 0.f) {
    assert(feps.size() == popularities.size());
    for (size_t i = 0; i < feps.size(); ++i) {
      _popularities[feps[i]] = popularities[i];
    }
  }
  // D'tor.
  virtual ~EdgeAttractivenessModel() { };
  // Computes the model. Pure virtual method.
  virtual vector<float> compute_edge_attractiveness() = 0;
  // Returns the result.
  vector<float> result() const { return _aggregatedEdgeAttractivenesses; }

 protected:
  const RoadGraph& _graph;
  const vector<int>& _forestEntries;
  unordered_map<int, float> _popularities;
  const int _maxCost;
  vector<float> _aggregatedEdgeAttractivenesses;
};


// Computes the edge attractiveness using the via-edge approach.
class FloodingModel : public EdgeAttractivenessModel {
 public:
  FloodingModel(const RoadGraph& g,
                const vector<int>& feps,
                const vector<float>& popularities,
                const int maxCost);
  // Computes the model.
  virtual vector<float> compute_edge_attractiveness();
};


// Computes the edge attractiveness using the via-edge approach.
class ViaEdgeApproach : public EdgeAttractivenessModel {
 public:
  // C'tor.
  ViaEdgeApproach(const RoadGraph& g,
                  const vector<int>& feps,
                  const vector<float>& popularities,
                  const int maxCost);
  // Computes the model.
  virtual vector<float> compute_edge_attractiveness();
  // Evaluates the cost vectors computed by Djkstra's from an edge s --> t.
  void evaluate(
      const int edgeIndex,
      const int s,
      const int t,
      const int c,
      const vector<int>& costsS,
      const vector<int>& costsT);

 private:
  // Stores pairwise distances between forest entries.
  unordered_map<int, unordered_map<int, int> > _distances;
};


// _____________________________________________________________________________
FloodingModel::FloodingModel(
    const RoadGraph& g,
    const vector<int>& feps,
    const vector<float>& popularities,
    const int maxCost)
  : EdgeAttractivenessModel(g, feps, popularities, maxCost) {
}

// _____________________________________________________________________________
std::vector< float > FloodingModel::compute_edge_attractiveness() {
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
      float gain = popularity / cost;  // TODO(Jonas): Some scaling or prefactor could/should be added.
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
ViaEdgeApproach::ViaEdgeApproach(
    const RoadGraph& g,
    const vector<int>& feps,
    const vector<float>& popularities,
    const int maxCost)
  : EdgeAttractivenessModel(g, feps, popularities, maxCost) {
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
    evaluate(arcIndex, s, t, c, bwd.get_costs(), fwd.get_costs());

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
    const int s,
    const int t,
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
      if (fep1 == fep2) {
        gain = _popularities[fep1] / costsFep2;
      } else {
        const float popularity = std::min(_popularities[fep1], _popularities[fep2]);
        const int distance = _distances[fep1][fep2];
        assert(totalCost > 0);
        gain = popularity * distance / totalCost;
      }
      _aggregatedEdgeAttractivenesses[edgeIndex] += gain;
    }
  }
}


#endif  // SRC_EDGEATTRACTIVENESSMODEL_H_
