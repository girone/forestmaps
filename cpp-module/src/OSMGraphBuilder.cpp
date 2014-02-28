// Copyright 2013, Chair of Algorithms and Datastructures.

#include <boost/algorithm/string/predicate.hpp>

#include <assert.h>

#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <unordered_map>  // NOLINT
#include <utility>
#include <vector>

#include "./OSMGraphBuilder.h"
#include "./utils.h"

using std::string;
using std::unordered_map;
using std::vector;

// _____________________________________________________________________________
OSMGraphBuilder OSMGraphBuilder::CarGraphBuilder(OSMGraph* g) {
  auto wayTypeToSpeedFn = [] (const string& wayType) {
    // Declaration outside of lambda function would be more efficient but does
    // not work with gcc 4.6.3.
    unordered_map<string, size_t> roadTypeToSpeed;
    roadTypeToSpeed["motorway"]       = 110;
    roadTypeToSpeed["trunk"]          = 110;
    roadTypeToSpeed["primary"]        = 70;
    roadTypeToSpeed["secondary"]      = 60;
    roadTypeToSpeed["tertiary"]       = 50;
    roadTypeToSpeed["motorway_link"]  = 50;
    roadTypeToSpeed["trunk_link"]     = 50;
    roadTypeToSpeed["primary_link"]   = 50;
    roadTypeToSpeed["secondary_link"] = 50;
    roadTypeToSpeed["road"]           = 40;
    roadTypeToSpeed["unclassified"]   = 40;
    roadTypeToSpeed["residential"]    = 30;
    roadTypeToSpeed["unsurfaced"]     = 30;
    roadTypeToSpeed["living_street"]  = 10;
    roadTypeToSpeed["service"]        = 5;
    roadTypeToSpeed["OTHER"]          = 0;
    return (roadTypeToSpeed.count(wayType) ? roadTypeToSpeed[wayType] :
        roadTypeToSpeed["OTHER"]);
  };
  return OSMGraphBuilder(g, wayTypeToSpeedFn);
}

// _____________________________________________________________________________
OSMGraphBuilder OSMGraphBuilder::WalkingGraphBuilder(OSMGraph* g) {
  // TODO(mirko): Check how much more arcs are added when the road types are
  // ignored.
  auto wayTypeToSpeedFn = [] (const string& wayType) {
    const size_t walkingSpeed = 5;
    unordered_map<string, size_t> roadTypeToSpeed;
    roadTypeToSpeed["motorway"]       = walkingSpeed;
    roadTypeToSpeed["trunk"]          = walkingSpeed;
    roadTypeToSpeed["primary"]        = walkingSpeed;
    roadTypeToSpeed["secondary"]      = walkingSpeed;
    roadTypeToSpeed["tertiary"]       = walkingSpeed;
    roadTypeToSpeed["motorway_link"]  = walkingSpeed;
    roadTypeToSpeed["trunk_link"]     = walkingSpeed;
    roadTypeToSpeed["primary_link"]   = walkingSpeed;
    roadTypeToSpeed["secondary_link"] = walkingSpeed;
    roadTypeToSpeed["road"]           = walkingSpeed;
    roadTypeToSpeed["unclassified"]   = walkingSpeed;
    roadTypeToSpeed["residential"]    = walkingSpeed;
    roadTypeToSpeed["unsurfaced"]     = walkingSpeed;
    roadTypeToSpeed["living_street"]  = walkingSpeed;
    roadTypeToSpeed["service"]        = walkingSpeed;
    roadTypeToSpeed["OTHER"]          = 0;
    return (roadTypeToSpeed.count(wayType) ? roadTypeToSpeed[wayType] :
        roadTypeToSpeed["OTHER"]);
  }; // NOLINT
  return OSMGraphBuilder(g, wayTypeToSpeedFn);
}

// _____________________________________________________________________________
OSMGraphBuilder::OSMGraphBuilder(
    OSMGraph* g, const wayTypeToSpeedFn_t& wayTypeToSpeedFn) :
  _g(g), _wayTypeToSpeedFn(wayTypeToSpeedFn) {}

// _____________________________________________________________________________
void OSMGraphBuilder::build(const string& fileName) {
  std::cout << "Building OSM Graph ... " << std::endl;
  // According to http://wiki.openstreetmap.org/wiki/OSM_XML nodes come before
  // ways.
  std::ifstream fs(fileName);
  assert(fs.good());
  std::istreambuf_iterator<char> fsit(fs);
  std::istreambuf_iterator<char> fsitEnd;

  boost::char_separator<char> tokenSeparator("<");
  tokenizer_t tkzer(fsit, fsitEnd, tokenSeparator);
  // Parse nodes and arcs.
  _tokensEnd = tkzer.end();
  for (_tokenIt = tkzer.begin(); _tokenIt != tkzer.end(); ++_tokenIt) {
    if (boost::starts_with(*_tokenIt, "node")) {
      parseNode();
    } else if (boost::starts_with(*_tokenIt, "way")) {
      parseWay();
    }
  }

  // Fill graph with nodes and arcs.
  fs.close();
  std::cout << "done" << std::endl;
}

// _____________________________________________________________________________
void OSMGraphBuilder::parseNode() {
  const string& token = *_tokenIt;
  size_t pos = findPos(token, "id=\"");
  assert(pos != string::npos);
  int id = atoi(token.c_str() + pos);

  pos = findPos(token, "lat=\"");
  assert(pos != string::npos);
  float lat = atof(token.c_str() + pos);

  pos = findPos(token, "lon=\"");
  assert(pos != string::npos);
  float lon = atof(token.c_str() + pos);
  addNode(id, lat, lon);
}

// _____________________________________________________________________________
void OSMGraphBuilder::parseWay() {
  const string& NO_WAY_TYPE = "";
  const string& TAG_KEY_HIGHWAY = "tag k=\"highway\" v=\"";
  vector<int> wayIds;
  string wayType = NO_WAY_TYPE;
  while (_tokenIt != _tokensEnd) {
    const string& token = *_tokenIt;
    if (boost::starts_with(token, "nd")) {
      size_t pos = findPos(token, "ref=\"");
      int id = atoi(token.c_str() + pos);
      wayIds.push_back(id);
    }
    if (boost::starts_with(token, TAG_KEY_HIGHWAY)) {
      size_t pos = findPos(token, TAG_KEY_HIGHWAY);
      wayType = token.substr(pos);
      // Get pos of quote.
      pos = wayType.find("\"");
      wayType = wayType.substr(0, pos);
    }
    if (boost::starts_with(token, "/way")) break;
    ++_tokenIt;
  }
  const size_t speed = _wayTypeToSpeedFn(wayType);
  if (speed > 0) {
    // Add arcs in both directions.
    for (size_t i = 1; i < wayIds.size(); ++i) {
      const int fromOsmId = wayIds[i - 1];
      const int toOsmId = wayIds[i];
      assert(_osmIdToId.count(fromOsmId));
      assert(_osmIdToId.count(toOsmId));
      const size_t fromId = _osmIdToId[fromOsmId];
      const size_t toId = _osmIdToId[toOsmId];
      const OSMNode& f = _g->nodes[fromId];
      const OSMNode& t = _g->nodes[toId];
      const size_t distance = utils::distance(f.lat, f.lon, t.lat, t.lon);
      const size_t duration = std::ceil((distance * 3.6) / speed);
      addArc(fromId, toId, duration);
      addArc(toId, fromId, duration);
    }
  } else {
    std::cout << "Ignored way without type." << std::endl;
  }
}

// _____________________________________________________________________________
size_t OSMGraphBuilder::findPos(const string& s,
    const string& sub) const {
  size_t pos = s.find(sub);
  return pos == string::npos ? string::npos : pos + sub.length();
}


// _____________________________________________________________________________
void OSMGraphBuilder::addNode(int osmId, float lat, float lon) {
  assert(_osmIdToId.count(osmId) == 0);
  size_t id = _g->nodes.size();
  _g->nodes.push_back(OSMNode(lat, lon));
  _osmIdToId.insert(std::make_pair(osmId, id));
  _g->outArcLists.push_back(vector<OSMArc>());
}

// _____________________________________________________________________________
void OSMGraphBuilder::addArc(size_t fromId, size_t toId, size_t duration) {
  assert(fromId < _g->outArcLists.size());
  assert(toId < _g->outArcLists.size());
  _g->outArcLists[fromId].push_back(OSMArc(duration, toId));
}
