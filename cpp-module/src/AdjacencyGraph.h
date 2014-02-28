// Copyright 2013-2014, Chair of Algorithms and Datastructures.
// Author: Mirko Brodesser <mirko.brodesser@gmail.com>,
//         Jonas Sternisko <sternis@informatik.uni-freiburg.de>

#ifndef SRC_ADJACENCYGRAPH_H_
#define SRC_ADJACENCYGRAPH_H_

#include <gtest/gtest_prod.h>
#include <cassert>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include "./NodesAndEdges.h"

using std::vector;
using std::string;

// _____________________________________________________________________________
// Straight forward graph class. For shortest path computation use
// CompactDirectedGraph.
template<class N, class A>
class AdjacencyListGraph {
 public:
  typedef N Node_t;
  typedef A Arc_t;

  AdjacencyListGraph() {}
  AdjacencyListGraph(const std::vector<N>& nodes,
      const std::vector<std::vector<A>>& arcs);

  // Reads the graph from a file. The filename has the format
  //  #nodes
  //  #arcs
  //  node0
  //  ...
  //  arc0
  //  ...
  void read_in(const string& filename);

  // Clears the graph, freeing all memory.
  void clear() {
    _arcs.clear();
    _arcs.shrink_to_fit();
    _nodes.clear();
    _nodes.shrink_to_fit();
  }

  // Returns the size (#nodes).
  size_t num_nodes() const { return _nodes.size(); }
  const std::vector<N>& get_nodes() const { return _nodes; }
  const N& node(uint node) const;
  const std::vector<A>& arcs(uint node) const;
  size_t count_arcs() const;

  string to_string() const;

 protected:
  std::vector<std::vector<A> > _arcs;  // size = #nodes.
  std::vector<N> _nodes;

  friend class OSMGraphBuilder;
  friend class GraphSimplificator;
  FRIEND_TEST(AdjacencyListGraphTest, to_string);
  FRIEND_TEST(GraphSimplificatorTest, contract_node);
};

// _____________________________________________________________________________
// TEMPLATE DEFINITIONS BELOW //

// DirectedGraph

template<class N, class A>
const std::vector<A>& AdjacencyListGraph<N, A>::arcs(uint node) const {
  assert(node < this->num_nodes());
  return _arcs[node];
}


template<class N, class A>
AdjacencyListGraph<N, A>::AdjacencyListGraph(
    const std::vector<N>& nodes, const std::vector<std::vector<A>>& arcs)
  : _arcs(arcs)
  , _nodes(nodes) {
  assert(arcs.size() == nodes.size());
}


template<class N, class A>
const N& AdjacencyListGraph<N, A>::node(uint node) const {
  assert(node < this->num_nodes());
  return _nodes[node];
}


template <class N, class A>
string AdjacencyListGraph<N, A>::to_string() const {
  std::stringstream s;
  s << "[" << _nodes.size() << "," << count_arcs() << ",";
  for (auto it = _arcs.begin(); it != _arcs.end(); ++it) {
    if (it != _arcs.begin()) { s << ","; }
//     s << _nodes[it - _arcs.begin()].to_string() << ":[";
    s << "{";
    const auto& arcs = *it;  // NOLINT
    for (auto arcIt = arcs.begin(); arcIt != arcs.end(); ++arcIt) {
//       if (arcIt != arcs.begin()) { s << ","; }
      s << (*arcIt).to_string();
    }
    s << "}";
  }
  s << "]";
  return s.str();
}

template <class N, class A>
size_t AdjacencyListGraph<N, A>::count_arcs() const {
  size_t n = 0;
  for (const auto& list: _arcs) {
    n += list.size();
  }
  return n;
}


// _____________________________________________________________________________
template<class N, class A>
void AdjacencyListGraph<N, A>::read_in(const string& filename) {
  std::ifstream input(filename);
  if (!input.good()) {
    std::cout << "File not found: " << filename << std::endl;
  }
  assert(input.good() && "File not found.");

  size_t numNodes, numArcs;
  input >> numNodes >> numArcs;
  std::cout << "#nodes: " << numNodes << ", #arcs: " << numArcs << std::endl;

  string buffer;
  getline(input, buffer);  // finishes current line
  for (size_t i = 0; i < numNodes; ++i) {
    getline(input, buffer);
    std::stringstream ss;
    ss << buffer;
    N node;
    node.from_stream(ss);
    _nodes.push_back(node);
  }

  vector<vector<A> > arcs(num_nodes());
  for (size_t i = 0; i < numArcs; ++i) {
    getline(input, buffer);
    std::stringstream ss;
    ss << buffer;
    A arc;
    arc.from_stream(ss);
    arcs[arc.source].push_back(arc);
  }
  // Sort
  for (auto it = arcs.begin(); it != arcs.end(); ++it) {
    std::sort(it->begin(), it->end(), CompareArcs<A>());
  }
  std::swap(arcs, _arcs);

  assert(count_arcs() == numArcs);
  assert(num_nodes() == numNodes);
}


#endif  // SRC_ADJACENCYGRAPH_H_
