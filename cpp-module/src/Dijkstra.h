// Copyright 2011-2013: Jonas Sternisko

#ifndef SRC_DIJKSTRA_H_
#define SRC_DIJKSTRA_H_

#include <cstdlib>
#include <limits>
#include <queue>
#include <utility>
#include <vector>
#include "./DirectedGraph.h"

using std::numeric_limits;
using std::vector;

typedef unsigned int uint;


// Dijkstra's algorithm on a bidirectional graph.
template<class Graph_t>
class Dijkstra {
 public:
   // Dijkstra priority queue elements: <cost, node>
  typedef std::pair<int, uint> pq_elem;
  typename Graph_t::Node_t N;
  typename Graph_t::Arc_t A;
  static const int infinity;
  static const uint no_target;

  // Constructor.
  Dijkstra(const Graph_t& graph);

  // Sets and initializes the member arrays according to the size of the network
  void resetMemberArraysFull();
  // Resets the member arrays after a limited shortest path search. Uses the
  // indices of nodes reached by the preceeding search. Faster than full reset.
  void resetMemberArraysAfterLimitedShortestPath();
  // Short alias for the method above.
  void reset() { resetMemberArraysAfterLimitedShortestPath(); }

  // Computes the shortest path from a node s to a node t.
  int shortestPath(uint s, uint t=no_target);
  // Alias for shortestPath(s, t)
  int run(uint s, uint t=no_target) { return shortestPath(s, t); }
  // Computes the shortest path from a set of nodes S to a node t. Returns the
  // total costs of the shortest path. Returns Dijkstra::infinity if there is no
  // path from S to t.
  int shortestPath(const vector<uint>& S, uint t=no_target);

  // Set the vector indicating which nodes have to be settled and the number of
  // these nodes.
  void setNodesToBeSettledMarks(const vector<bool>* nodesToBeSettledMarks,
                                const size_t numNodesToBeSettled);
  // Sets the indicators for nodes which should be ignored during the search.
  void set_nodes_to_ignore(const vector<bool>* ignore);
  // Set the cost limit.
  void set_cost_limit(const int cost);
  // Set the hop limit.
  void setHopLimit(const size_t maxHops);

  // Get the costs to each node settled by Dijkstra. If a node was not settled,
  // the costs equal Dijkstra::infinity.
  const vector<int>& get_costs() const;
  // Get the parent node of every settled node.
  const vector<uint>& getOrigins() const;
  // Returns true if a node was settled, false otherwise.
  bool isSettled(uint node) const;
  // Gets the number off settled nodes.
  size_t getNumSettledNodes() const;
  // Get the vector of settled nodes in the last limited search.
  const vector<uint>& get_settled_node_indices() const;
  // Get the settled node flags.
  const vector<bool>& get_settled_flags() const;
  // Get the vector of touched nodes in limited searches.
  const vector<uint>& getTouchedNodeIndices() const;

 private:
  // The graph.
  const Graph_t& _graph;

  // A pointer to a vector indicating which nodes Dijkstra has to settle. If all
  // these nodes are settled, Dijkstra aborts.
  const vector<bool>* _nodesToBeSettledMarks;
  // The number of nodes to be settled. Used to avoid large reinitialisation.
  size_t _numNodesToBeSettled;
  // Pointer to indicator for ignored nodes.
  const vector<bool>* _ignore;
  // A pointer to a number indicating the largest cost of a node to be settled.
  // If set, the Dijkstra search aborts after a node with tentative costs larger
  // than this value is removed from the priority queue.
  int _costLimit;
  // The limit of hops for Dijkstra searches. A limit of 0 means no limit.
  size_t _hopLimit;


  // A vector storing the costs on the shortest path for each node.
  vector<int> _costs;
  // A vector indicating for each node the parent node on the shortest path.
  vector<uint> _origins;
  // A vector with a flag for each node whether or not is has been settled.
  vector<bool> _settled;
  // Number of settled nodes. For statistics and optimization.
  size_t _numSettledNodes;
  // A vector storing the indices of nodes settled or touched by the Dijkstra
  // search. Used for resetting after limited searches.
  vector<uint> _settledNodes;
  vector<uint> _touchedNodes;
};


// _____________________________________________________________________________
// TEMPLATE DEFINITIONS GO BELOW

template<class G>
const int Dijkstra<G>::infinity = std::numeric_limits<int>::max();
template<class G>
const uint Dijkstra<G>::no_target = std::numeric_limits<unsigned int>::max();

template<class G>
Dijkstra<G>::Dijkstra(const G& graph) : _graph(graph) {
  _nodesToBeSettledMarks = NULL;
  _numNodesToBeSettled   = 0;
  _ignore                = NULL;
  _costLimit             = infinity;
  _hopLimit              = 0;
  // init member arrays
  resetMemberArraysFull();
  _numSettledNodes = 0;
}

template<class G>
void Dijkstra<G>::resetMemberArraysFull() {
  _costs.assign(_graph.num_nodes(), infinity);
  _origins.assign(_graph.num_nodes(), no_target);
  _settled.assign(_graph.num_nodes(), false);
}

template<class G>
inline void Dijkstra<G>::resetMemberArraysAfterLimitedShortestPath() {
  // 'untouch' the nodes
  vector<uint>::const_iterator it;
  for (it = _settledNodes.begin(); it != _settledNodes.end(); ++it)
    _settled[*it] = false;
  for (it = _touchedNodes.begin(); it != _touchedNodes.end(); ++it) {
    _costs[*it]   = infinity;
    _origins[*it] = no_target;
  }
  _settledNodes.clear();
  _touchedNodes.clear();
}

template<class G>
void Dijkstra<G>::setNodesToBeSettledMarks(
    const vector<bool>* nodesToBeSettledMarks,
    const size_t numNodesToBeSettled) {
  _nodesToBeSettledMarks = nodesToBeSettledMarks;
  // count the nodes that the Dijkstra has to settle
  _numNodesToBeSettled = numNodesToBeSettled;
  /*_numNodesToBeSettled = 0;
  for (size_t i = 0; i < _nodesToBeSettledMarks->size(); ++i)
    if (_nodesToBeSettledMarks->at(i))
      ++_numNodesToBeSettled;*/
}

template<class G>
void Dijkstra<G>::set_nodes_to_ignore(const vector<bool>* ignore) {
  assert(ignore->size() == _graph.num_nodes());
  _ignore = ignore;
}

template<class G>
void Dijkstra<G>::set_cost_limit(const int cost) {
  _costLimit = cost;
}

template<class G>
void Dijkstra<G>::setHopLimit(const size_t maxHops) {
  _hopLimit = maxHops;
}

template<class G>
const vector<int>& Dijkstra<G>::get_costs() const {
  return _costs;
}

template<class G>
const vector<uint>& Dijkstra<G>::getOrigins() const {
  return _origins;
}

template<class G>
bool Dijkstra<G>::isSettled(uint node) const {
  assert(node < _graph.num_nodes());
  return _settled[node];
}

template<class G>
size_t Dijkstra<G>::getNumSettledNodes() const {
  return _numSettledNodes;
}

template<class G>
const vector<uint>& Dijkstra<G>::get_settled_node_indices() const {
  return _settledNodes;
}

template<class G>
const vector<bool>& Dijkstra<G>::get_settled_flags() const {
  return _settled;
}

template<class G>
const vector<uint>& Dijkstra<G>::getTouchedNodeIndices() const {
  return _touchedNodes;
}

template<class G>
int Dijkstra<G>::shortestPath(uint s, uint t) {
  vector<uint> S;
  S.push_back(s);
  return shortestPath(S, t);
}

template<class G>
int Dijkstra<G>::shortestPath(const vector<uint>& S, uint t) {
  const bool limited = (_nodesToBeSettledMarks || _costLimit != infinity ||
      _hopLimit);
  if (limited) {
    // reset arrays using the indices of the last touched nodes
    resetMemberArraysAfterLimitedShortestPath();
  } else {
    // initialization of Dijkstra's algorithm for large searches
    if (_numSettledNodes > 0)  resetMemberArraysFull();
  }
  _numSettledNodes = 0;

  // add starting set to priority queue
  std::priority_queue<pq_elem, vector<pq_elem>, std::greater<pq_elem> > pq;
  for (size_t i = 0; i < S.size(); i++) {
    pq.push(pq_elem(0, S[i]));
    _costs[S[i]] = 0;
    _origins[S[i]] = S[i];
    if (limited) { _touchedNodes.push_back(S[i]); }
  }

  // optionally keep track of the number of nodes to be settled
  size_t numSelectedNodesUnsettled = 0;
  if (_nodesToBeSettledMarks != NULL)
    numSelectedNodesUnsettled = _numNodesToBeSettled;

  while (!pq.empty()) {
    // Get the node with the lowest tentative distance.
    pq_elem x = pq.top();
    const uint xIndex   = x.second;
    const int xCosts = x.first;
    pq.pop();
    // Quit search, if the cost limit is reached.
    if (xCosts > _costLimit) { break; }
    // Skip nodes that are already settled.
    if (_settled[xIndex]) { continue; }
    _settled[xIndex] = true;
    if (limited) { _settledNodes.push_back(xIndex); }
    ++_numSettledNodes;
    // Quit the search, if all marked nodes are settled.
    if (_nodesToBeSettledMarks != NULL && _nodesToBeSettledMarks->at(xIndex)) {
      numSelectedNodesUnsettled--;
      if (numSelectedNodesUnsettled == 0) { break; }
    }
    // Quit the search, if the target is reached.
    if (xIndex == t) { break; }


    // Relax the outgoing arcs xIndex --> yIndex.
    for (const auto& arc: _graph.arcs(xIndex)) {
      uint yIndex = arc.target;
      if (_ignore && _ignore->at(yIndex)) { continue; }
      if (!_settled[yIndex]) {
        // Compute the tentative distance.
        int g = _costs[xIndex] + arc.get_cost();
        int h = 0;
        int f = g + h;
        if (_costs[yIndex] > g) {
          _costs[yIndex] = g;
          pq.push(pq_elem(f, yIndex));
          _origins[yIndex] = xIndex;  // remember origin node
          if (limited) { _touchedNodes.push_back(yIndex); }
        }
      }
    }
  }
  return (t < _costs.size()) ? _costs[t] : infinity;
}


#endif  // SRC_DIJKSTRA_H_
