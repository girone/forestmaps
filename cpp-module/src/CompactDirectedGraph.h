// Copyright 2013, Chair of Algorithms and Datastructures.
// Authors: Mirko Brodesser <mirko.brodesser@gmail.com>,
//          Jonas Sternisko <sternis@informatik.uni-freiburg.de>

#ifndef SRC_COMPACTDIRECTEDGRAPH_H_
#define SRC_COMPACTDIRECTEDGRAPH_H_

#include <vector>
#include "./CompactDirectedGraphIterator.h"

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
  CompactDirectedGraph() {}

  // Grants read-access to the adjacent arcs of a node.
  const _AccessMediator<A> arcs(const size_t node) const;

 protected:
  std::vector<A> _arcList;  // size = #arcs.
  // For each node the offset where its arcs begin.
  std::vector<size_t> _offset;  // size = #nodes + 1.

  friend class forst::test::GraphComposer<CompactDirectedGraph<A> >;
};

// _____________________________________________________________________________
// Compact graph representation with explicit information about nodes.
template<class A, class N>
class CompactDirectedGraphWithNodes : public CompactDirectedGraph<A> {
 public:
  CompactDirectedGraphWithNodes();

 protected:
  std::vector<N> nodes;
};

// _____________________________________________________________________________
// TEMPLATE DEFINITIONS GO BELOW //

template<class A>
const _AccessMediator<A> CompactDirectedGraph<A>::arcs(const size_t node)
    const {
  assert(node < _arcList.size());
  return _AccessMediator<A>(&this->_arcList, _offset[node], _offset[node+1]);
}


#endif  // SRC_COMPACTDIRECTEDGRAPH_H_
