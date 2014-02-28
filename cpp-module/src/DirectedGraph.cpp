// Copyright 2013: Jonas Sternisko

#include "./DirectedGraph.h"
#include "./Util.h"


// _____________________________________________________________________________
// Parse a string in the style "[3,2,{(1,3)(2,5)},{},{}]"
template<>
void OffsetListGraph<SourceTargetCostArc>::from_string(string s) {
  // remove whitespace
  std::stringstream ss;
  string::iterator it;
  for (it = s.begin(); it < s.end(); it++) {
    if (!isspace(*it)) ss << *it;
  }
  s = ss.str();

  // read number of nodes
  int numNodes = atoi(s.substr(1).c_str());
  assert(numNodes >= 0);

  // read number of arcs
  size_t pos = s.find(",");
  assert(pos > 0);
  size_t numArcs = atoi(s.substr(pos + 1).c_str());

  // read arcs
  pos = s.find('{');
  assert(pos > 0);
  int node = -1;

  while (pos < s.size()) {
    if (s[pos] == '{') {
      node++;
    } else if (s[pos] == '(') {
      int targetNode = atoi(s.substr(pos + 1).c_str());
      pos = s.find(",", pos);
      assert(pos > 0);
      int cost = atoi(s.substr(pos + 1).c_str());
      _arcList.push_back(SourceTargetCostArc(node, targetNode, cost));
    }
    pos++;
  }
  assert(node == numNodes - 1);
  assert(_arcList.size() == numArcs);

  std::sort(_arcList.begin(), _arcList.end(),
            CompareArcs<SourceTargetCostArc>());
  _offset = compute_offsets(_arcList, numNodes);
  assert(static_cast<size_t>(numNodes) == this->num_nodes());
}
