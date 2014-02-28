// Copyright 2012-13: Jonas Sternisko

#ifndef SRC_ROUTINGALGORITHM_H_
#define SRC_ROUTINGALGORITHM_H_


#include "./DirectedGraph.h"


// A virtual base class for routing algorithms.
template<class N, class A>
class RoutingAlgorithm {
public:
//  RoutingAlgorithm();
 RoutingAlgorithm(const Graph<N, A>& g) : _graph(g) { }
 virtual ~RoutingAlgorithm();
 // Get the graph.
 const Graph<N, A>& getGraph() const;
protected:
 const Graph<N, A>& _graph;
};

#endif  // SRC_ROUTINGALGORITHM_H_
