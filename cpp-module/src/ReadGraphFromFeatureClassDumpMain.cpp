// Copyright 2014: Jonas Sternisko

#include <iostream>
#include <fstream>
#include <functional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>
#include <map>
#include "./Util.h"

using std::make_pair;
using std::pair;
using std::string;
using std::unordered_map;
using std::unordered_set;
using std::vector;
using std::cout;
using std::endl;

using std::map;

#define SQR(x) ((x)*(x))

typedef unordered_map<pair<float, float>, int, util::PairHash> CoordMap;
// typedef map<pair<float, float>, int> CoordMap;
typedef unordered_map<pair<int, int>, int, util::PairHash> ArcToIdMap;


struct CostEdge {
  CostEdge() : cost(-1) { }
  CostEdge(float c, int _) : cost(c) { }
  float cost;
};

std::ostream& operator<<(std::ostream& os, const CostEdge& e) {
  os << e.cost << " ";
  return os;
}

// An edge which stores a cost and a weight.
struct CostWeightEdge {
  CostWeightEdge() : cost(-1), weight(-1) { }
  CostWeightEdge(float c, int w) : cost(c), weight(w) { }
  float cost;
  uint16_t weight;
};

std::ostream& operator<<(std::ostream& os, const CostWeightEdge& e) {
  os << e.cost << " " << e.weight << " ";
  return os;
}

// A simple graph with easy to use hashmaps as internal storages.
template<class Edge>
class Graph {
 public:
  // Construct with number of nodes known in advance.
  explicit Graph(size_t nodes) : _edges(nodes, vector<pair<int, Edge> >()) { }
  void add_edge(int s, int t, const Edge& e) {
    _nodes.insert(s);
    _nodes.insert(t);
    // _edges[s][t] = e;
    assert(static_cast<size_t>(s) < _edges.size());
    _edges[s].emplace_back(t, e);
  }
  size_t num_nodes() const { return _nodes.size(); }
  /*size_t num_edges() const {
    size_t n = 0;
    for (const pair<int, unordered_map<int, Edge>>& entry: _edges) {
      n += entry.second.size();
    }
    return n;
  }*/
  size_t num_edges() const {
    size_t n = 0;
    for (const auto& list: _edges) {
      n += list.size();
    }
    return n;
  }

  // unordered_map<int, unordered_map<int, Edge>> _edges;
  vector<vector<pair<int, Edge> > > _edges;
  unordered_set<int> _nodes;
};

// _____________________________________________________________________________
int get_node_index(const pair<float, float>& coordinates, CoordMap* coordmap) {
    auto it = coordmap->find(coordinates);
    int index;
    if (it == coordmap->end()) {
      index = coordmap->size();
      (*coordmap)[coordinates] = index;
    } else {
      index = it->second;
    }
    return index;
}

// _____________________________________________________________________________
template<class Edge>
Graph<Edge> read_graph(const vector<vector<float> >& cols,
                       CoordMap* coordToNodeMap,
                       ArcToIdMap* arcToId) {
  cout << "Creating the graph from parsed content..." << endl;
  const vector<float>& fids = cols[0];
  const vector<float>& xx = cols[1];
  const vector<float>& yy = cols[2];
  const vector<float>& costs = cols[3];
  size_t fsize = cols[0].size();
  const vector<float>& weights = (cols.size() > 4) ? cols[4]
                                                    : vector<float>(fsize, 1);

  size_t nodeBound = fsize;  // it's an upper bound for the number of nodes
  Graph<Edge> g(nodeBound);
  int lastFid = -1;
  int indexA, indexB;

  for (size_t i = 0; i < fsize; ++i) {
    const int fid = fids[i];
    if (fid != lastFid) {
      // Finish the current arc
      if (lastFid != -1) {
        indexB = get_node_index(make_pair(xx[i-1], yy[i-1]), coordToNodeMap);
        g.add_edge(indexA, indexB, Edge(costs[i-1], weights[i-1]));
        g.add_edge(indexB, indexA, Edge(costs[i-1], weights[i-1]));
        (*arcToId)[make_pair(indexA, indexB)] = lastFid;
        (*arcToId)[make_pair(indexB, indexA)] = lastFid;
      }
      // Start a new arc
      indexA = get_node_index(make_pair(xx[i], yy[i]), coordToNodeMap);
    }
    lastFid = fid;
  }
  // Finish the last arc
  if (lastFid != -1) {
    indexB = get_node_index(make_pair(xx.back(), yy.back()), coordToNodeMap);
    g.add_edge(indexA, indexB, Edge(costs.back(), weights.back()));
    g.add_edge(indexB, indexA, Edge(costs.back(), weights.back()));
    (*arcToId)[make_pair(indexA, indexB)] = lastFid;
    (*arcToId)[make_pair(indexB, indexA)] = lastFid;
  }
  // Restrict the graph to used nodes, i.e. [0...N...nodeBound].
  g._edges.resize(g.num_nodes());
  cout << "done." << endl;
  return g;
}

// _____________________________________________________________________________
unordered_map<int, pair<float, float>> inverse_map(const CoordMap& input) {
  unordered_map<int, pair<float, float>> inverse;
  for (auto it = input.begin(); it != input.end(); ++it) {
    inverse[it->second] = it->first;
  }
  return inverse;
}

// _____________________________________________________________________________
template<class G>
void dump_graph(const string& filename, const G& g, const CoordMap& coordmap) {
  cout << "Creating inverse map..." << endl;
  unordered_map<int, pair<float, float>> inverse = inverse_map(coordmap);
  cout << "Writing output..." << endl;
  std::ofstream ofs(filename);
  assert(ofs.good());
  ofs << g.num_nodes() << endl;
  ofs << g.num_edges() << endl;
  for (int nodeId: g._nodes) {
    const pair<float, float>& coords = inverse[nodeId];
    ofs << coords.first << " " << coords.second << endl;
  }
  size_t nodeId = 0;
  size_t arcId = 0;
  for (auto it = g._edges.begin(); it != g._edges.end(); ++it) {
    for (auto it2 = it->begin(); it2 != it->end(); ++it2) {
      ofs << nodeId << " " << it2->first << " " << it2->second << " "
          << arcId++ << endl;
    }
    ++nodeId;
  }
  cout << "done." << endl;
}

// _____________________________________________________________________________
void dump_id_map(const string& filename, const ArcToIdMap& map) {
  cout << "Writing id map ..." << endl;
  std::ofstream ofs(filename);
  assert(ofs.good());
  for (const auto& entry: map) {
    ofs << entry.first.first << " " << entry.first.second << " " << entry.second
        << endl;
  }
}

// _____________________________________________________________________________
void printUsage() {
  string s;
  s = "Usage: ./ReadGraphFromFeatureClassDumpMain <InputDump> <OutputDump> "
      "[<ArcMappingFile>] \n"
      "  InputDump -- \n"
      "  OutputDump -- \n"
      "  ArcMappingFile -- Writes 's t id' of a mapping {(s,t): id} to file.\n";
  cout << s << endl;
}

// _____________________________________________________________________________
int main(const int argc, const char** argv) {
  if (argc < 3 || argc > 4) {
    printUsage();
    exit(1);
  }
  const string infile = argv[1];
  const string outfile = argv[2];

  cout << "Reading input ..." << endl;
  vector<vector<float> > cols = util::read_column_file<float>(infile);
  assert(cols.size() >= 4);
  assert(cols[0].size() == cols[1].size());
  assert(cols[1].size() == cols[2].size());
  assert(cols[2].size() == cols[3].size());
  assert(cols.size() <= 4 || cols[4].size() == cols[3].size());
  cout << "done." << endl;

  CoordMap coordToNodeMap;
  ArcToIdMap arcToId;
  if (cols.size() == 4) {
    Graph<CostEdge> graph = read_graph<CostEdge>(
        cols, &coordToNodeMap, &arcToId);
    dump_graph(outfile, graph, coordToNodeMap);
  } else if (cols.size() == 5) {
    Graph<CostWeightEdge> graph = read_graph<CostWeightEdge>(
        cols, &coordToNodeMap, &arcToId);
    dump_graph(outfile, graph, coordToNodeMap);
    if (argc > 3) {
      const string mapfile = argv[3];
      dump_id_map(mapfile, arcToId);
    }
  } else {
    assert(false && "Input file has wrong number of columns.");
  }

  cout << endl << "OK" << endl;
  return 0;
}

