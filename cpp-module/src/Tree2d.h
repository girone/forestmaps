// Copyright 2013: Jonas Sternisko

#ifndef SRC_TREE2D_H_
#define SRC_TREE2D_H_

#include <kdtree++/kdtree.hpp>
#include "./DirectedGraph.h"

// TODO(jonas): Split into header and source file.

// _____________________________________________________________________________
// Reference of a graph node in a 2dtree.
class TreeNode {
 public:
  typedef float value_type;
  // Construct a kdtree node for a graph node and its index.
  TreeNode(const RoadGraph::Node_t& node, int index)
    : refNodeIndex(index) {
    pos[0] = node.x;
    pos[1] = node.y;
  }
  // Construct a kdtree node for a tuple of coordinates.
  TreeNode(const float lat, const float lon, int index)
    : refNodeIndex(index) {
    pos[0] = lat;
    pos[1] = lon;
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
// Builds a 2d tree from a set of coordinates.
Tree2D build_kdtree(const vector<vector<float>>& coords) {
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

#endif  // SRC_TREE2D_H_
