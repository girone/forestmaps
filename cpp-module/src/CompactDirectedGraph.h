// Copyright 2013, Chair of Algorithms and Datastructures.
// Authors: Mirko Brodesser <mirko.brodesser@gmail.com>,
//          Jonas Sternisko <sternis@informatik.uni-freiburg.de>

#ifndef SRC_COMPACTDIRECTEDGRAPH_H_
#define SRC_COMPACTDIRECTEDGRAPH_H_

#include <cassert>
#include <vector>
#include "./CompactDirectedGraphIterator.h"


using std::vector;

// _____________________________________________________________________________
// Space and cache efficient graph representation using concatenated adjacency
// lists. Nodes are implicit in this graph. Uses _AccessMediator to generate
// iterators over the outgoing arcs from each node, which allows for range-based
// for-loops over these arcs.
template<class A>
class CompactDirectedGraph {
 public:
  typedef A Arc_t;

  // C'tor
  CompactDirectedGraph(const vector<A>& a, const vector<size_t>& o);

  // Grants read-access to the adjacent arcs of a node.
  const _AccessMediator<A> arcs(const size_t node) const;

  // The size of the graph is the number of nodes.
  size_t size() const { return _offset.size() - 1; }

  // Returns a string representation.
  const std::string string() const;

 protected:
  std::vector<A> _arcList;  // size = #arcs.
  // For each node the offset where its arcs begin.
  std::vector<size_t> _offset;  // size = #nodes + 1.

};

// _____________________________________________________________________________
// Compact graph representation with explicit information about nodes.
template<class A, class N>
class CompactDirectedGraphWithNodes : public CompactDirectedGraph<A> {
 public:
  CompactDirectedGraphWithNodes(const vector<A>& a, const vector<size_t>& o,
      const vector<N>& n);

  // Returns a string representation.
  const std::string string() const;

 protected:
  std::vector<N> _nodes;
};

// _____________________________________________________________________________
// TEMPLATE DEFINITIONS GO BELOW //

template<class A>
const _AccessMediator<A> CompactDirectedGraph<A>::arcs(const size_t node)
    const {
  assert(node < _arcList.size());
  return _AccessMediator<A>(&this->_arcList, _offset[node], _offset[node+1]);
}

// _____________________________________________________________________________
template<class A>
CompactDirectedGraph<A>::CompactDirectedGraph(const vector<A>& a,
    const vector<size_t>& o)
  : _arcList(a), _offset(o) {
  assert(1 <= o.size());
  assert(o.back() <= a.size());
}

// _____________________________________________________________________________
template<class A>
const std::string CompactDirectedGraph<A>::string() const {
  std::stringstream s;
  s << "{" << this->size() << ", ";
  for (size_t i = 0; i < this->size(); ++i) {
    if (i != 0) { s << ", "; }
    s << "[";
    for (auto it = this->arcs(i).begin(); it != this->arcs(i).end(); ++it) {
      if (it != this->arcs(i).begin()) { s << ", "; }
      s << (*it).string();
    }
    s << "]";
  }
  return s.str();
}

// _____________________________________________________________________________
template<class A, class N>
CompactDirectedGraphWithNodes<A, N>::CompactDirectedGraphWithNodes(
    const vector<A>& a, const vector<size_t>& o, const vector<N>& n)
  : CompactDirectedGraph<A>(a, o), _nodes(n) { }

// _____________________________________________________________________________
template<class A, class N>
const std::string CompactDirectedGraphWithNodes<A, N>::string() const {
  std::stringstream s;
  s << "{" << this->size() << ", ";
  for (size_t i = 0; i < this->size(); ++i) {
    if (i != 0) { s << ", "; }
    s << _nodes[i].string() << ":[";
    for (auto it = this->arcs(i).begin(); it != this->arcs(i).end(); ++it) {
      if (it != this->arcs(i).begin()) { s << ", "; }
      s << (*it).string();
    }
    s << "]";
  }
  s << "}";
  return s.str();
}

#endif  // SRC_COMPACTDIRECTEDGRAPH_H_

