// Copyright 2014: Jonas Sternisko

#include "./GraphSimplificator.h"
#include <algorithm>
#include <set>

// _____________________________________________________________________________
// Return the first arc in the adjacency list of 'from' which points to 'to'.
// Return a copy, otherwise this gets unsave.
// NOTE(Jonas): Returning a reference can be unsafe here: The graph may change.
const Arc& find_arc(const SimplificationGraph& graph, size_t from, size_t to) {
  for (auto it = graph.arcs(from).begin(); it != graph.arcs(from).end(); ++it) {
    if (it->target == static_cast<int>(to)) {
      return *it;
    }
  }
  assert(false && "There is no arc between these two nodes.");
  exit(1);
}

// _____________________________________________________________________________
GraphSimplificator::GraphSimplificator(SimplificationGraph* input)
  : _input(input)
  , _arcCount(input->count_arcs()) {

}

// _____________________________________________________________________________
void GraphSimplificator::initialize_mapping() {
  for (const vector<Arc>& arcs: _input->_arcs) {
    for (const Arc& arc: arcs) {
      int fid = arc.labels[2];
      _representedFids[fid] = {fid};
    }
  }
}

// _____________________________________________________________________________
SimplificationGraph GraphSimplificator::extract_simplified_graph(
    const vector<bool>& contracted) const {
  // Build the simplified graph from the uncontracted nodes and the arcs between
  // them. Shift the indices of the arcs' sources and targets.
  vector<int> indexShift(contracted.begin(), contracted.end());
  std::partial_sum(indexShift.begin(), indexShift.end(), indexShift.begin());
  SimplificationGraph simple;
  for (size_t node = 0; node < _input->num_nodes(); ++node) {
    if (!contracted[node]) {
      simple._nodes.push_back(_input->node(node));
      simple._arcs.push_back(vector<Arc>());
      for (const auto& arc: _input->arcs(node)) {
        if (!contracted[arc.target]) {
          simple._arcs.back().push_back(
              ArcFactory::create(arc.source - indexShift[arc.source],
                                 arc.target - indexShift[arc.target],
                                 arc.labels[0], arc.labels[1], arc.labels[2])
          );
        }
      }
      std::sort(simple._arcs.back().begin(), simple._arcs.back().end(),
                CompareArcs<Arc>());
    }
  }
  return simple;
}

// _____________________________________________________________________________
SimplificationGraph GraphSimplificator::simplify(const set<uint>* doNotContract) {
  initialize_mapping();

  // Iteratively contract nodes with exactly two non-contracted successors.
  vector<bool> contracted(_input->num_nodes(), false);
  for (size_t node = 0; node < _input->num_nodes(); ++node) {
    if (doNotContract && doNotContract->find(node) != doNotContract->end()) {
      continue;
    }
    contracted[node] = contract_node(node, contracted);
  }

  return extract_simplified_graph(contracted);
}

// _____________________________________________________________________________
bool GraphSimplificator::contract_node(size_t node,
                                       const vector<bool>& contracted) {
  vector<int> uncontractedArcIndices;
  for (size_t i = 0; i < _input->arcs(node).size(); ++i) {
    if (!contracted[_input->arcs(node)[i].target]) {
      uncontractedArcIndices.push_back(i);
    }
  }
  if (uncontractedArcIndices.size() != 2) {
    return false;
  }
  // Do not contract nodes with two arcs to the same target.
  vector<int> nghbrs = {_input->arcs(node)[uncontractedArcIndices[0]].target,
                        _input->arcs(node)[uncontractedArcIndices[1]].target};
  if (std::adjacent_find(nghbrs.begin(), nghbrs.end()) == nghbrs.begin()) {
    return false;
  }

  // Contract the node: Add shortcuts between its uncontracted neighbors. These
  // shortcuts represent the FID labels of the now obsolete arcs. The obsolete
  // arcs are not touched.
  int aIndex, bIndex;
  for (size_t i = 0; i < nghbrs.size(); ++i) {
    // For neighbors A and B:        Add a shortcut :
    //    a        b                   a+b
    // A --> node --> B              A --> B
    int A = nghbrs[i];
    int B = nghbrs[(i+1) % nghbrs.size()];
    assert(A != B);
    const Arc& a = find_arc(*_input, A, node);
    aIndex = a.labels[2];
    const Arc& b = find_arc(*_input, node, B);
    bIndex = b.labels[2];
    int combinedCost = a.get_cost() + b.get_cost();
    int maxWeight = std::max(a.labels[1], b.labels[1]);
    int arcIdOfShortcut = _arcCount;
    _input->_arcs[A].push_back(
        ArcFactory::create(A, B, combinedCost, maxWeight, arcIdOfShortcut));
    ++_arcCount;
    _representedFids[arcIdOfShortcut].insert(
        _representedFids[arcIdOfShortcut].end(),
        _representedFids[aIndex].begin(),
        _representedFids[aIndex].end());
    _representedFids[arcIdOfShortcut].insert(
        _representedFids[arcIdOfShortcut].end(),
        _representedFids[bIndex].begin(),
        _representedFids[bIndex].end());
  }
  _representedFids.erase(aIndex);
  _representedFids.erase(bIndex);
  return true;
}

// _____________________________________________________________________________
const unordered_map<int, vector<int>>& GraphSimplificator::edgeIndexToFidsMap()
    const {
  return _representedFids;
}

// _____________________________________________________________________________
Arc ArcFactory::create(int source, int target, int c, int w, int fid) {
  Arc arc;
  arc.source = source;
  arc.target = target;
  arc.labels[0] = c;
  arc.labels[1] = w;
  arc.labels[2] = fid;
  return arc;
}
