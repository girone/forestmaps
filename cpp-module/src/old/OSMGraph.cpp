// Copyright 2013, Chair of Algorithms and Datastructures.
// Author: Mirko Brodesser <mirko.brodesser@gmail.com>

#include <sstream>
#include <string>

#include "./OSMGraph.h"

// _____________________________________________________________________________
std::string OSMNode::string() const {
  std::ostringstream os;
  os << "(" << lat << ", " << lon << ")";
  return os.str();
}

// _____________________________________________________________________________
std::string OSMArc::string() const {
  std::ostringstream os;
  os << "(" << duration << ", " << headNodeId << ")";
  return os.str();
}
