// Copyright 2013: Chair of Algorithms and Datastructures.
// Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

// Contains code to compute the largest connected component.

#ifndef SRC_LCC_H_
#define SRC_LCC_H_

#include "./OSMGraph.h"

namespace graph_utils {

// Computes the largest connected component of a graph.
OSMGraph lcc(const OSMGraph& g);

// Restrict a graph to a given subset of its node indices.
OSMGraph restrictGraphToIndices(const OSMGraph& g,
    const std::vector<uint>& node_indices_subset);

}  // namespace

#endif  // SRC_LCC_H_
