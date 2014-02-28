// Copyright 2013: Chair of Algorithms and Datastructures.
// Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>


#ifndef SRC_GRAPHTESTUTILS_H_
#define SRC_GRAPHTESTUTILS_H_

#include <vector>

using std::vector;

namespace forst {
namespace test {

// This class allows to construct a graph from its parts.
template<class Graph>
class GraphComposer {
 public:
  static
  Graph compose(const vector<typename Graph::Arc_t>& arcs, const vector<size_t>& offset);
};


// TEMPLATE DEFINITIONS //

template<class Graph>
Graph GraphComposer<Graph>::compose(const vector<typename Graph::Arc_t>& arcs,
    const vector< size_t >& offset) {
  Graph g(arcs, offset);
  return g;
}


}  // namespace
}  // namespace

#endif  // SRC_GRAPHTESTUTILS_H_
