// Copyright 2013: Jonas Sternisko

#ifndef SRC_EDGEATTRACTIVENESSMODEL_H_
#define SRC_EDGEATTRACTIVENESSMODEL_H_

#include <unordered_map>
#include <vector>
#include <gtest/gtest_prod.h>
#include "./DirectedGraph.h"

using std::unordered_map;
using std::vector;


class EdgeAttractivenessModel {
 public:
  // C'tor.
  EdgeAttractivenessModel(const RoadGraph& g,
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
  }
  // D'tor.
  virtual ~EdgeAttractivenessModel() { };
  // Computes the model. Pure virtual method.
  virtual vector<float> compute_edge_attractiveness() = 0;
  // Returns the result.
  vector<float> result() const { return _aggregatedEdgeAttractivenesses; }

  // Checks the user preferences read from a text file for correct values.
  static bool check_preferences(const vector<vector<float> >& preferences);


 protected:
  const RoadGraph& _graph;
  const vector<int>& _forestEntries;
  const vector<vector<float>>& _preferences;  // User preferences for time in forest (tif)
  unordered_map<int, float> _popularities;
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
  FloodingModel(const RoadGraph& g,
                const vector<int>& feps,
                const vector<float>& popularities,
                const vector<vector<float>>& preferences,
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
                  const vector<vector<float>>& preferences,
                  const int maxCost);
  // Computes the model.
  virtual vector<float> compute_edge_attractiveness();
  // Evaluates the cost vectors computed by Djkstra's from an edge s --> t.
  void evaluate(
      const int edgeIndex,
      const int c,
      const vector<int>& costsS,
      const vector<int>& costsT);

 private:
  // Stores pairwise distances between forest entries.
  unordered_map<int, unordered_map<int, float> > _distances;
};

#endif  // SRC_EDGEATTRACTIVENESSMODEL_H_
