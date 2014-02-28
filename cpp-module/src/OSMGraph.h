// Copyright 2013, Chair of Algorithms and Datastructures.

#ifndef OSMGRAPH_H_
#define OSMGRAPH_H_

#include <string>

#include "./DirectedGraph.h"


class OSMNode {
 public:
  OSMNode(float lat, float lon) : lat(lat), lon(lon) {}
  std::string getSummaryString() const;
  float lat;
  float lon;
};

class OSMArc {
 public:
  // Duration in seconds.
  OSMArc(size_t duration, size_t headNodeId) :
    duration(duration), headNodeId(headNodeId) {}
  std::string getSummaryString() const;
  size_t duration;
  size_t headNodeId;
};

// No derived class to avoid indirections.
typedef DirectedGraph<OSMNode, OSMArc> OSMGraph;

#endif  // OSMGRAPH_H_
