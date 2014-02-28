// Copyright 2014: Jonas Sternisko

#include "./NodesAndEdges.h"
#include <vector>

// These have to be defined out of class:
const std::vector<int> N2::default_ = {0, 1};
const std::vector<int> N3::default_ = {0, 1, -1};

bool operator==(const SourceTargetThreeLabelsArc& lhs,
                const SourceTargetThreeLabelsArc& rhs) {
  return lhs.source == rhs.source && lhs.target == rhs.target &&
         lhs.labels == rhs.labels;
}

