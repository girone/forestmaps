// Copyright 2013: Jonas Sternisko

#ifndef SRC_NODESANDEDGES_H_
#define SRC_NODESANDEDGES_H_

#include <sstream>

using std::string;

// ARCS GO BELOW

// Contains only the target node id and its cost.
class CostArc {
 public:
  CostArc(int t, int c) : target(t), cost(c) { }
  int target;
  int cost;
};


// An arc between to nodes index s (source) and t (target), with cost.
class SourceTargetCostArc {
 public:
  SourceTargetCostArc() : source(-1), target(-1), cost(0) { }
  SourceTargetCostArc(int s, int t, int c) : source(s), target(t), cost(c) { }
  void from_stream(std::istream& is) {
    is >> source >> target >> cost;
  }
  string to_string() const {
    std::stringstream ss;
    ss << "(" << /*source << "," <<*/ target << "," << cost << ")";
    return ss.str();
  }

  int source;
  int target;
  int cost;
};


// NODES GO BELOW

// A geo position.
class GeoPosition {
 public:
  void from_stream(std::istream& is) {
    is >> x >> y;
  }
  string to_string() const {
    std::stringstream ss;
    ss << x << " " << y;
    return ss.str();
  }

  float x;
  float y;
};



#endif  // SRC_NODESANDEDGES_H_
