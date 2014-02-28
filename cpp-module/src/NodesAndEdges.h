// Copyright 2013: Jonas Sternisko

#ifndef SRC_NODESANDEDGES_H_
#define SRC_NODESANDEDGES_H_

#include <sstream>
#include <string>
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
// labels. The template argument LabelDescriptor is a struct with the constant
// field ::count that determines the cardinality of the cost vector, a constant
// field ::costField that determines the position of the major cost component,
// and a constant field ::default_ with the default value for the cost vector.
// See below for an example.
template<class LabelDescriptor>
class SourceTargetLabelsArc {
 public:
  SourceTargetLabelsArc()
    : source(-1), target(-1), labels(LabelDescriptor::default_) {
    }
  SourceTargetLabelsArc(const SourceTargetCostArc& other)  // NOLINT
    : source(other.source)
    , target(other.target)
    , labels(LabelDescriptor::default_) {
    labels[LabelDescriptor::costField] = other.cost;
  }
  /*SourceTargetMultipleCostArc(int s, int t, const vector<int>& c)
    : source(s), target(t), labels(c) { }*/
  int get_cost() const { return labels[LabelDescriptor::costField]; }
  void from_stream(std::istream& is);
  string to_string() const;

  int source;
  int target;
  std::vector<int> labels;
};


struct N2 {
  static const size_t count = 2;
  static const size_t costField = 0;
  static const std::vector<int> default_;
};

struct N3 {
  static const size_t count = 3;
  static const size_t costField = 0;
  static const std::vector<int> default_;
};


// These edges have (cost, weight) tuples.
typedef SourceTargetLabelsArc<N2> SourceTargetTwoCostsArc;

// These edges have (cost, weight, label) triples.
typedef SourceTargetLabelsArc<N3> SourceTargetThreeLabelsArc;

// Comparator
template<class A>
struct CompareArcs {
  bool operator()(const A& lhs, const A& rhs) const {
    return lhs.source < rhs.source ||
          (lhs.source == rhs.source && lhs.target < rhs.target);
  }
};

// Check for equality
bool operator==(const SourceTargetThreeLabelsArc& lhs,
                const SourceTargetThreeLabelsArc& rhs);


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

// _____________________________________________________________________________
template<class LabelDescriptor>
void SourceTargetLabelsArc<LabelDescriptor>::from_stream(std::istream& is) {
  is >> source >> target;
  for (size_t i = 0; i < LabelDescriptor::count; ++i) {
    string s;
    std::stringstream ss;
    is >> s;
    ss << s;
    ss >> labels[i];
  }
}

// _____________________________________________________________________________
template<class LabelDescriptor>
string SourceTargetLabelsArc<LabelDescriptor>::to_string() const {
  std::stringstream ss;
  ss << "(" << source << "," << target << "," << "[";
  for (auto it = labels.begin(); it != labels.end(); ++it) {
    if (it != labels.begin())
      ss << ",";
    ss << *it;
  }
  ss << "])";
  return ss.str();
}

#endif  // SRC_NODESANDEDGES_H_

