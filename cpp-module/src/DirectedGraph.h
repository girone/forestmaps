// Copyright 2013, Chair of Algorithms and Datastructures.
// Authors: Mirko Brodesser <mirko.brodesser@gmail.com>,
//          Jonas Sternisko <sternis@informatik.uni-freiburg.de>

#ifndef SRC_COMPACTDIRECTEDGRAPH_H_
#define SRC_COMPACTDIRECTEDGRAPH_H_

#include <gtest/gtest_prod.h>
#include <cassert>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include "./ArcIterator.h"
#include "./NodesAndEdges.h"

using std::string;
using std::stringstream;
using std::vector;

// Space and cache efficient graph representation using concatenated adjacency
// lists. Uses _AccessMediator to generate iterators over the outgoing arcs
// from each node, which allows for range-based for-loops over these arcs.
// Nodes are implicit in this graph, without further information.
template<class A>
class OffsetListGraph {
 public:
  typedef A Arc_t;

  // C'tor
  OffsetListGraph() : _offset(1, 0) { }
  OffsetListGraph(const vector<A>& a, const vector<size_t>& o);

  // Grants read-access to the adjacent arcs of a node.
  const _AccessMediator<A> arcs(const size_t node) const;
  // Returns the arc list.
  const std::vector<A>& arclist() const { return _arcList; }

  // The size of the graph is the number of nodes.
  size_t size() const { return num_nodes(); }
  // Returns the number of nodes.
  size_t num_nodes() const { return _offset.size() - 1; }
  // Returns the number of arcs.
  size_t num_arcs() const { return _arcList.size(); }

  // Returns a string representation of the style "[3,2,{(1,3)(2,5)},{},{}]".
  const std::string to_string() const;

  // Builds the graph from a string of the style "[3,2,{(1,3)(2,5)},{},{}]".
  void from_string(string s);  // NOTE: Only for A = SimpleCostArc

 protected:
  std::vector<A> _arcList;  // size = #arcs.
  // For each node the offset where its arcs begin.
  std::vector<size_t> _offset;  // size = #nodes + 1.

  FRIEND_TEST(DirectedGraphTest, to_string);
};

// Compact graph representation with explicit information about nodes.
template<class N, class A>
class Graph : public OffsetListGraph<A> {
 public:
  typedef N Node_t;
  typedef A Arc_t;

  // Default C'tor.
  Graph() : OffsetListGraph<A>() { }
  // Construct from already known offset vector o.
  Graph(const vector<A>& a, const vector<size_t>& offset, const vector<N>& n);
  // Construct from list of arcs and nodes. Offsets will be calculated.
  Graph(const vector<A>& arc, const vector<N>& nodes);

  // Reads the graph from a file. The filename has the format
  //  #nodes
  //  #arcs
  //  node0
  //  ...
  //  arc0
  //  ...
  void read_in(const string& filename);

  // Returns the nodes.
  const std::vector<N>& nodes() const { return _nodes; }

 protected:
  std::vector<N> _nodes;

  FRIEND_TEST(DirectedGraphTest, to_string);
};


typedef Graph<GeoPosition, SourceTargetCostArc> RoadGraph;


// Computes the offset vector for a sorted list of arcs with source node ids.
template<class A>
vector<size_t> compute_offsets(const vector<A>& sortedArcList, size_t numNodes) {
  vector<size_t> offsets = {0};
  size_t currSource = 0;
  if (sortedArcList.size()) {
    size_t nextSource = currSource;
    for (size_t i = 0; i < sortedArcList.size(); ++i) {
      currSource = nextSource;
      nextSource = sortedArcList[i].source;
      while (currSource != nextSource) {
        offsets.push_back(i);
        ++currSource;
      }
    }
  }
  while (offsets.size() < numNodes+1) {
    offsets.push_back(sortedArcList.size());
  }
  return offsets;
}


// _____________________________________________________________________________
// TEMPLATE DEFINITIONS GO BELOW //

template<class A>
const _AccessMediator<A> OffsetListGraph<A>::arcs(const size_t node) const {
  assert(node < _offset.size() - 1);
  //return _AccessMediator<A>(&this->_arcList, _offset[node], _offset[node+1]);
  return _AccessMediator<A>(&_arcList, _offset[node], _offset[node+1]);
}

// _____________________________________________________________________________
template<class A>
OffsetListGraph<A>::OffsetListGraph(const vector<A>& a,
    const vector<size_t>& o)
  : _arcList(a), _offset(o) {
  assert(1 <= o.size());
  assert(o.back() <= a.size());
}

// _____________________________________________________________________________
template<class A>
const std::string OffsetListGraph<A>::to_string() const {
  std::stringstream s;
  s << "[" << num_nodes() << "," << num_arcs() << ",";
  for (size_t i = 0; i < size(); ++i) {
    if (i != 0) { s << ","; }
    s << "{";
    for (auto it = arcs(i).begin(); it != arcs(i).end(); ++it) {
//       if (it != arcs(i).begin()) { s << ","; }
      s << (*it).to_string();
    }
    s << "}";
  }
  s << "]";
  return s.str();
}

// _____________________________________________________________________________
template<class N, class A>
Graph<N, A>::Graph(
    const vector<A>& a, const vector<size_t>& o, const vector<N>& n)
  : OffsetListGraph<A>(a, o), _nodes(n) { }


template<class A>
struct CompareArcs {
  bool operator()(const A& lhs, const A& rhs) const {
    return lhs.source < rhs.source ||
          (lhs.source == rhs.source && lhs.target < rhs.target);
  }
};

// _____________________________________________________________________________
template<class N, class A>
void Graph<N, A>::read_in(const string& filename) {
  std::ifstream input(filename);
  if (!input.good()) {
    std::cout << "File not found: " << filename << std::endl;
  }
  assert(input.good() && "File not found.");

  size_t numNodes, numArcs;
  input >> numNodes >> numArcs;
  std::cout << numNodes << " " << numArcs << std::endl;

  string buffer;
  getline(input, buffer);  // finishes current line
  vector<N> nodeList;
  for (size_t i = 0; i < numNodes; ++i) {
    getline(input, buffer);
    stringstream ss;
    ss << buffer;
    N node;
    node.from_stream(ss);
    nodeList.push_back(node);
  }

  vector<A> arcList;
  for (size_t i = 0; i < numArcs; ++i) {
    getline(input, buffer);
    stringstream ss;
    ss << buffer;
    A arc;
    arc.from_stream(ss);
    arcList.push_back(arc);
  }

  std::sort(arcList.begin(), arcList.end(), CompareArcs<A>());

  this->_nodes = nodeList;
  this->_arcList = arcList;
  this->_offset = compute_offsets(arcList, numNodes);
}

#endif  // SRC_COMPACTDIRECTEDGRAPH_H_

