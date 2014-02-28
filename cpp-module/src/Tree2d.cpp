// Copyright 2014: Jonas Sternisko

#include "./Tree2d.h"
#include <algorithm>
#include <utility>
#include <vector>

using std::pair;

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
// Builds a 2d tree from a set of coordinates.
Tree2D build_kdtree(const vector<vector<float> >& coords) {
  assert(coords.size() >= 2);
  assert(coords[0].size() == coords[1].size());
  Tree2D tree;
  for (size_t i = 0; i < coords[0].size(); ++i) {
    const float lat = coords[0][i];
    const float lon = coords[1][i];
    tree.insert(TreeNode(lat, lon, i));
  }
  return tree;
}

// _____________________________________________________________________________
// Maps (x,y) coordinates to the closest node referenced by the kdtree.
// Returns the index of the closest node for every row of x and y.
vector<int> map_xy_locations_to_closest_node(const vector<float>& x,
    const vector<float>& y, const RoadGraph& graph) {
  Tree2D tree = build_kdtree(graph);
  vector<int> closestNodeIndices(x.size(), -1);
  assert(x.size() == y.size());
  for (size_t i = 0; i < x.size(); ++i) {
    TreeNode pos(x[i], y[i], -1);
    std::pair<Tree2D::const_iterator, float> res = tree.find_nearest(pos);
    assert(res.first != tree.end());
    closestNodeIndices[i] = res.first->refNodeIndex;
  }
  return closestNodeIndices;
}

// _____________________________________________________________________________
// Returns the X nearest neightbors within Y meters of the reference node.
vector<TreeNode> get_nearest_X_within_Y(
    const Tree2D& t, const TreeNode& ref, const unsigned int X, const float Y,
    float (*dist_fun)(float, float, float, float)) {
  // Get everything within Y meters.
  vector<TreeNode> rangeQueryResults;
  t.find_within_range(ref, Y, std::back_inserter(rangeQueryResults));
  // Compute the actual great circle distances
  vector<pair<float, unsigned> > distanceAndIndex;
  unsigned index = 0;
  for (const TreeNode& node: rangeQueryResults) {
    distanceAndIndex.emplace_back(dist_fun(ref[0], ref[1], node[0], node[1]),
                                  index++);
  }
  // Sort and truncate to the top X.
  unsigned int k = X < rangeQueryResults.size() ? X : rangeQueryResults.size();
  std::partial_sort(distanceAndIndex.begin(), distanceAndIndex.begin() + k,
                    distanceAndIndex.end());
  const vector<TreeNode>& r = rangeQueryResults;
  vector<TreeNode> result;
  std::transform(distanceAndIndex.begin(), distanceAndIndex.begin() + k,
                 std::back_inserter(result),
                 [r](const pair<float, unsigned>& e) { return r[e.second]; });
  return result;
}
