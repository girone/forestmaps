// Copyright 2013, Chair of Algorithms and Datastructures.

#include <sstream>
#include <string>

#include "./OSMGraph.h"

// _____________________________________________________________________________
std::string OSMNode::getSummaryString() const {
  std::ostringstream os;
  os << "(" << lat << ", " << lon << ")";
  return os.str();
}

// _____________________________________________________________________________
std::string OSMArc::getSummaryString() const {
  std::ostringstream os;
  os << "(" << duration << ", " << headNodeId << ")";
  return os.str();
}
