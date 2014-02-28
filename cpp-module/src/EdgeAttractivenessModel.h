// Copyright 2013: Jonas Sternisko

#ifndef SRC_EDGEATTRACTIVENESSMODEL_H_
#define SRC_EDGEATTRACTIVENESSMODEL_H_

#include <unordered_map>
#include <vector>
#include <gtest/gtest_prod.h>
#include "./DirectedGraph.h"
#include "./Dijkstra.h"

using std::unordered_map;
using std::vector;


// Base class.
// The algorithms count duplicates forest entries (due to mapping) twice.
class EdgeAttractivenessModel {
 public:
  typedef unordered_map<int32_t, unordered_map<int32_t, float> > MapMap;
  typedef unordered_map<int32_t, float> Map;
  // C'tor.
  EdgeAttractivenessModel(const ForestRoadGraph& g,
                          const vector<int>& feps,
                          const vector<float>& popularities,
                          const vector<vector<float>>& preferences,
                          const int maxCost)
    : _graph(g)
    , _forestEntries(feps)
    , _preferences(preferences)
    , _maxCost(maxCost)
    , _aggregatedEdgeAttractivenesses(g.num_arcs(), 0.f) {
    assert(feps.size() == popularities.size());
    for (size_t i = 0; i < feps.size(); ++i) {
      _popularities[feps[i]] = popularities[i];
    }
    assert(_preferences.size() == 2);
    assert(_preferences[0].size() > 0);
    assert(_preferences[0].size() == _preferences[1].size());
    std::sort(_forestEntries.begin(), _forestEntries.end());
  }
  // D'tor.
  virtual ~EdgeAttractivenessModel() { };
  // Computes the model. Pure virtual method.
  virtual vector<float> compute_edge_attractiveness() = 0;
  // Returns the result.
  vector<float> result() const { return _aggregatedEdgeAttractivenesses; }
  // Normalize the contributions of each entrypoint s.t. the maximum is 1.0
  static void normalize_contributions(MapMap* c);
  // Distributes the entry points' populations according to their contributions.
  void distribute(const Map& pop, const MapMap& cont, vector<float>* att) const;

 protected:
  const ForestRoadGraph& _graph;
  vector<int> _forestEntries;
  const vector<vector<float>>& _preferences;
  Map _popularities;
  const int _maxCost;
  vector<float> _aggregatedEdgeAttractivenesses;

  // Returns the share of users preferring a specific TIF.
  float user_share(const float tif) const;
  // Returns the sum of user shares which spend @tif or more time in the forest.
  float sum_of_user_shares_after(const float tif) const;
  FRIEND_TEST(EdgeAttractivenessModelTest, user_shares_functions);
};


// Computes the edge attractiveness using the via-edge approach.
class FloodingModel : public EdgeAttractivenessModel {
 public:
  FloodingModel(const ForestRoadGraph& g,
                const vector<int>& feps,
                const vector<float>& popularities,
                const vector<vector<float>>& preferences,
                const int maxCost);
  // Computes the model.
  virtual vector<float> compute_edge_attractiveness();
 private:
  // Distributes the edge weights to the adjacent nodes. Selects the maximum.
  vector<int> compute_node_from_arc_weights(const ForestRoadGraph& graph) const;
};


// Computes the edge attractiveness using the via-edge approach.
class ViaEdgeApproach : public EdgeAttractivenessModel {
 public:
  // C'tor.
  ViaEdgeApproach(const ForestRoadGraph& g,
                  const vector<int>& feps,
                  const vector<float>& popularities,
                  const vector<vector<float>>& preferences,
                  const int maxCost);
  // Computes the model.
  virtual vector<float> compute_edge_attractiveness();
  // Evaluates the cost vectors computed by Djkstra's from an edge s --> t
  // and computes the contribution of the forest entries participating in the
  // routes.
  void evaluate(
      const int edgeIndex,
      const int c,
      const int w,
      const Dijkstra<ForestRoadGraph>& bwd,
      const Dijkstra<ForestRoadGraph>& fwd,
      MapMap* contributions);

 private:
  // Stores pairwise distances between forest entries.
  MapMap _distances;
};

#endif  // SRC_EDGEATTRACTIVENESSMODEL_H_
