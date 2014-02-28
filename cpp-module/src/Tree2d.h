// Copyright 2013: Jonas Sternisko

#ifndef SRC_TREE2D_H_
#define SRC_TREE2D_H_

#include <kdtree++/kdtree.hpp>
#include <vector>
#include "./DirectedGraph.h"


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
Tree2D build_kdtree(const RoadGraph& graph);

// Builds a 2d tree from a set of coordinates.
Tree2D build_kdtree(const vector<vector<float> >& coords);

// Maps (x,y) coordinates to the closest node referenced by the kdtree.
// Returns the index of the closest node for every row of x and y.
vector<int> map_xy_locations_to_closest_node(
    const vector<float>& x, const vector<float>& y, const RoadGraph& graph);

// Returns the X nearest neightbors within Y meters of the reference node.
// The distance function has to be provided: distance(x0, y0, x1, y1).
vector<TreeNode> get_nearest_X_within_Y(
    const Tree2D& t, const TreeNode& ref, const unsigned int X, const float Y,
    float (*dist_func)(float, float, float, float));


#endif  // SRC_TREE2D_H_
