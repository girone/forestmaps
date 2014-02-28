// Copyright 2013, Chair of Algorithms and Datastructures.
// Author: Mirko Brodesser <mirko.brodesser@gmail.com>,
//         Jonas Sternisko <sternis@informatik.uni-freiburg.de>

#ifndef SRC_DIRECTEDGRAPH_H_
#define SRC_DIRECTEDGRAPH_H_

#include <cassert>
#include <sstream>
#include <string>
#include <vector>

// _____________________________________________________________________________
// Straight forward graph class which is simple to use. For shortest path
// computation use CompactDirectedGraph.
template<class N, class A>
class DirectedGraph {
 public:
  DirectedGraph() {}
  DirectedGraph(const std::vector<N>& nodes,
      const std::vector<std::vector<A>>& arcs);
  size_t numNodes() const { return _arcs.size(); }
  const N& node(uint node) const;
  std::string getSummaryString() const;
  const std::vector<A>& arcs(uint node) const;
 protected:
  std::vector<std::vector<A> > _arcs;  // size = #nodes.
  std::vector<N> _nodes;

  friend class OSMGraphBuilder;
};

// _____________________________________________________________________________
// TEMPLATE DEFINITIONS BELOW //

// DirectedGraph

template<class N, class A>
const std::vector<A>& DirectedGraph<N, A>::arcs(uint node) const {
  assert(node < numNodes());
  return _arcs[node];
}


template<class N, class A>
DirectedGraph<N, A>::DirectedGraph(
    const std::vector<N>& nodes, const std::vector<std::vector<A>>& arcs)
  : _arcs(arcs)
  , _nodes(nodes) {
  assert(arcs.size() == nodes.size());
}


template<class N, class A>
const N& DirectedGraph<N, A>::node(uint node) const {
  assert(node < numNodes());
  return _nodes[node];
}


template <class N, class A>
std::string DirectedGraph<N, A>::getSummaryString() const {
  std::ostringstream os;
  os << "{" << _nodes.size() << ", ";
  for (auto it = _arcs.begin(); it != _arcs.end(); ++it) {
    if (it != _arcs.begin()) os << ", ";
    os << "[";
    const auto& arcs = *it;  // NOLINT
    for (auto arcIt = arcs.begin(); arcIt != arcs.end(); ++arcIt) {
      if (arcIt != arcs.begin()) os << ", ";
      os << (*arcIt).getSummaryString();
    }
    os << "]";
  }
  os << "}";
  return os.str();
}

#endif  // SRC_DIRECTEDGRAPH_H_
