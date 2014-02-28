// Copyright 2013: Jonas Sternisko

#ifndef SRC_NODESANDEDGES_H_
#define SRC_NODESANDEDGES_H_

#include <sstream>
#include <vector>


using std::string;

// ARCS GO BELOW

// Contains only the target node id and its cost.
class CostArc {
 public:
  CostArc(int t, int c) : target(t), cost(c) { }
  int get_cost() const { return cost; }
  int target;
  int cost;
};


// An arc between to nodes index s (source) and t (target), with a cost value.
class SourceTargetCostArc {
 public:
  SourceTargetCostArc() : source(-1), target(-1), cost(0) { }
  SourceTargetCostArc(int s, int t, int c) : source(s), target(t), cost(c) { }
  int get_cost() const { return cost; }
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

// An arc between to nodes index s (source) and t (target), with multiple value
// costs. The template argument CostDescriptor is a struct with the constant
// field ::count that determines the cardinality of the cost vector, a constant
// field ::costField that determines the position of the major cost component,
// and a constant field ::default_ with the default value for the cost vector.
// See below for an example.
template<class CostDescriptor>
class SourceTargetMultipleCostArc {
 public:
  SourceTargetMultipleCostArc()
    : source(-1), target(-1), cost(CostDescriptor::default_) { }
  SourceTargetMultipleCostArc(const SourceTargetCostArc& other)
    : source(other.source), target(other.target), cost(CostDescriptor::default_)
  {
    cost[CostDescriptor::costField] = other.cost;
  }
  /*SourceTargetMultipleCostArc(int s, int t, const vector<int>& c)
    : source(s), target(t), cost(c) { }*/
  int get_cost() const { return cost[CostDescriptor::costField]; }
  void from_stream(std::istream& is) {  // TODO(Jonas): Put to template defs below.
    is >> source >> target;
    for (size_t i = 0; i < CostDescriptor::count; ++i) {
      string s;
      std::stringstream ss;
      is >> s;
      ss << s;
      ss >> cost[i];
    }
  }
  string to_string() const {
    std::stringstream ss;
    ss << "(" << source << "," << target << "," << "[";
    for (auto it = cost.begin(); it != cost.end(); ++it) {
      if (it != cost.begin())
        ss << ",";
      ss << *it;
    }
    ss << "])";
    return ss.str();
  }

  int source;
  int target;
  std::vector<int> cost;
};


struct N2 {
 public:
  static const size_t count = 2;
  static const size_t costField = 0;
  static const std::vector<int> default_;
};


// This graph has edge with (cost, weight) tuples.
typedef SourceTargetMultipleCostArc<N2> SourceTargetTwoCostsArc;


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


// TEMPLATE DEFINITIONS BELOW




#endif  // SRC_NODESANDEDGES_H_

