// Copyright 2013, Chair of Algorithms and Datastructures.

#ifndef SRC_DIRECTEDGRAPH_H_
#define DIRECTEDGRAPH_H_

#include <sstream>
#include <string>
#include <vector>

// Straight forward graph class which is simple to use. For shortest path
// computation use CompactDirectedGraph.
template<class N, class A>
class DirectedGraph {
 public:
  DirectedGraph() {}
  std::string getSummaryString() const;
  std::vector<N> nodes;
  std::vector<std::vector<A> > outArcLists;  // size = #nodes.
};

template <class N, class A>
std::string DirectedGraph<N, A>::getSummaryString() const {
  std::ostringstream os;
  os << "{" << nodes.size() << ", ";
  for (auto it = outArcLists.begin(); it != outArcLists.end(); ++it) {
    if (it != outArcLists.begin()) os << ", ";
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

#endif  // DIRECTEDGRAPH_H_
