// Copyright 2013, Chair of Algorithms and Datastructures.
// Author: Mirko Brodesser <mirko.brodesser@gmail.com>

#ifndef SRC_OSMGRAPHBUILDER_H_
#define SRC_OSMGRAPHBUILDER_H_

#include <boost/tokenizer.hpp>

#include <string>
#include <unordered_map>  // NOLINT

#include "./OSMGraph.h"


// Builds a symmetric OSMGraph from .osm file.
class OSMGraphBuilder {
  typedef boost::tokenizer<boost::char_separator<char>,
          std::istreambuf_iterator<char> > tokenizer_t;
  typedef std::function<size_t (const std::string& wt)> wayTypeToSpeedFn_t;
 public:
  static OSMGraphBuilder CarGraphBuilder(OSMGraph* g);
  static OSMGraphBuilder WalkingGraphBuilder(OSMGraph* g);
  // This includes all roads and paths accessible to a car driver (including
  // when he leaves his car).
  static OSMGraphBuilder RoadGraphBuilder(OSMGraph* g);
  void build(const std::string& fileName);

 private:
  // From wayTypeToSpeedFn speed should be returned in km/h.
  OSMGraphBuilder(OSMGraph* g, const wayTypeToSpeedFn_t& wayTypeToSpeedFn);
  void addNode(int osmId, float lat, float lon);
  void addArc(size_t fromId, size_t toId, size_t duration);
  void parseNode();
  void parseWay();
  // Returns pos after first occurance of sub in s, std::npos if sub not in s.
  inline size_t findPos(const std::string& s, const std::string& sub) const;
  // Car and walking graphs.
  OSMGraph* _g;
  wayTypeToSpeedFn_t _wayTypeToSpeedFn;
  std::unordered_map<int, size_t> _osmIdToId;
  tokenizer_t::const_iterator _tokenIt;
  tokenizer_t::const_iterator _tokensEnd;
};

#endif  // SRC_OSMGRAPHBUILDER_H_
