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

struct Hash {
 public:
  size_t operator()(const std::pair<double, double>& x) const throw() {
    std::hash<double> hasher;
    size_t h = hasher(x.first + 2 * x.second);
    return h;
  }
};

typedef unordered_map<pair<double, double>, int, Hash> CoordMap;
//typedef map<pair<double, double>, int> CoordMap;
typedef unordered_map<pair<int, int>, int, Hash> ArcToIdMap;

unordered_map<int, int> ATKISSpeedTable = { {164001, 110},
                                            {164003, 70},
                                            {164005, 110},
                                            {164007, 70},
                                            {164009, 110},
                                            {164010, 70},
                                            {87001, 50},
                                            {87003, 5},
                                            {87004, 25},
                                            {88001, 25},
                                            {89001, 25},
                                            {89002, 10},
                                            {90001, 110},
                                            {90003, 70},
                                            {90005, 110},
                                            {90007, 70},
                                            {90009, 110},
                                            {90010, 70},
                                            {90012, 50},
                                            {90014, 5},
                                            {90015, 25},
                                            {90016, 25},
                                            {90017, 25},
                                            {90018, 10} };


struct CostEdge {
  CostEdge() : cost(-1) { }
  CostEdge(float c, int _) : cost(c) { }
  float cost;
};

std::ostream& operator<<(std::ostream& os, const CostEdge& e) {
  os << e.cost << " ";
  return os;
}

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
  Graph(size_t nodes) : _edges(nodes, vector<pair<int, Edge>>()) { }
  void add_edge(int s, int t, const Edge& e) {
    _nodes.insert(s);
    _nodes.insert(t);
    //_edges[s][t] = e;
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

  //unordered_map<int, unordered_map<int, Edge>> _edges;
  vector<vector<pair<int, Edge> > > _edges;
  unordered_set<int> _nodes;
};

// _____________________________________________________________________________
int determine_speed(int waytype, int maxKmh) {
  auto it = ATKISSpeedTable.find(waytype);
  assert(it != ATKISSpeedTable.end() && "Way type key not contained!");
  int kmh = it->second;
  if (kmh > maxKmh)
    kmh = maxKmh;
  return kmh;
}

// _____________________________________________________________________________
// Returns the Euclidean distance between two points (x0,y0) and (x1,y1).
float euclid(double x0, double y0, double x1, double y1) {
  return sqrt(SQR(x1-x0) + SQR(y1-y0));
}

// _____________________________________________________________________________
int get_node_index(const pair<double, double>& coordinates, CoordMap* coordmap) {
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
Graph<Edge> read_graph(const vector<vector<double> >& cols,
                       const int maxKmh,
                       CoordMap* coordToNodeMap,
                       ArcToIdMap* arcToId) {
  const vector<double>& fids = cols[0];
  const vector<double>& xx = cols[1];
  const vector<double>& yy = cols[2];
  const vector<double>& wayTypes = cols[3];
  size_t fsize = cols[0].size();
  const vector<double>& weights = (cols.size() > 4) ? cols[4]
                                                    : vector<double>(fsize, 1);

  size_t nodeBound = fsize;  // it's an upper bound for the number of nodes
  Graph<Edge> g(nodeBound);
  int lastIndex = -1;
  float dist = 0;
  int indexA, indexB;

  for (size_t i = 0; i < fsize; ++i) {
    const int index = fids[i];
    if (index == lastIndex) {
      dist += euclid(xx[i], yy[i], xx[i-1], yy[i-1]);
    } else {
      // Finish the current arc
      if (lastIndex != -1) {
        indexB = get_node_index(make_pair(xx[i-1], yy[i-1]), coordToNodeMap);
        float time = dist / (determine_speed(wayTypes[i-1], maxKmh) / 3.6f);
        g.add_edge(indexA, indexB, Edge(time, weights[i-1]));
        g.add_edge(indexB, indexA, Edge(time, weights[i-1]));
        (*arcToId)[make_pair(indexA, indexB)] = lastIndex;
        (*arcToId)[make_pair(indexB, indexA)] = lastIndex;
      }
      // Start a new arc
      indexA = get_node_index(make_pair(xx[i], yy[i]), coordToNodeMap);
      dist = 0;
    }
    lastIndex = index;
  }
  // Finish the last arc
  if (lastIndex != -1) {
    indexB = get_node_index(make_pair(xx.back(), yy.back()), coordToNodeMap);
    float time = dist / (determine_speed(wayTypes.back(), maxKmh) / 3.6f);
    g.add_edge(indexA, indexB, Edge(time, weights.back()));
    g.add_edge(indexB, indexA, Edge(time, weights.back()));
    (*arcToId)[make_pair(indexA, indexB)] = lastIndex;
    (*arcToId)[make_pair(indexB, indexA)] = lastIndex;
  }
  // Restrict the graph to used nodes, i.e. [0...N...nodeBound].
  g._edges.resize(g.num_nodes());
  return g;
}

// _____________________________________________________________________________
unordered_map<int, pair<double, double>> inverse_map(const CoordMap& input) {
  unordered_map<int, pair<double, double>> inverse;
  for (auto it = input.begin(); it != input.end(); ++it) {
    inverse[it->second] = it->first;
  }
  return inverse;
}

// _____________________________________________________________________________
template<class G>
void dump_graph(const string& filename, const G& g, const CoordMap& coordmap) {
  unordered_map<int, pair<double, double>> inverse = inverse_map(coordmap);
  std::ofstream ofs(filename);
  assert(ofs.good());
  ofs << g.num_nodes() << endl;
  ofs << g.num_edges() << endl;
  for (int nodeId: g._nodes) {
    const pair<double, double>& coords = inverse[nodeId];
    ofs << coords.first << " " << coords.second << endl;
  }
  /*for (auto it = g._edges.begin(); it != g._edges.end(); ++it) {
    const int s = it->first;
    const auto& map = it->second;
    for (auto it2 = map.begin(); it2 != map.end(); ++it2) {
      ofs << s << " " << it2->first << " " << it2->second << endl;
    }
  }*/
  size_t nodeId = 0;
  for (auto it = g._edges.begin(); it != g._edges.end(); ++it) {
    for (auto it2 = it->begin(); it2 != it->end(); ++it2) {
      ofs << nodeId << " " << it2->first << " " << it2->second << endl;
    }
    ++nodeId;
  }
}

// _____________________________________________________________________________
void dump_id_map(const string& filename, const ArcToIdMap& map) {
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
  s = "Usage: ./ReadGraphFromFeatureClassDumpMain <InputDump> <maxKmh> "
      "<OutputDump> [<ArcMappingFile>] \n"
      "  InputDump -- \n"
      "  MaxKmh -- \n"
      "  OutputDump -- \n"
      "  ArcMappingFile -- Writes 's t id' of a mapping {(s,t): id} to file.\n";
  cout << s << endl;
}

// _____________________________________________________________________________
int main(const int argc, const char** argv) {
  if (argc < 4 || argc > 5) {
    printUsage();
    exit(1);
  }
  const string infile = argv[1];
  const int maxKmh = util::convert<int>(argv[2]);
  const string outfile = argv[3];

  vector<vector<double> > cols = util::read_column_file<double>(infile);
  assert(cols.size() >= 4);
  assert(cols[0].size() == cols[1].size());
  assert(cols[1].size() == cols[2].size());
  assert(cols[2].size() == cols[3].size());
  assert(cols.size() <= 4 || cols[4].size() == cols[3].size());

  CoordMap coordToNodeMap;
  ArcToIdMap arcToId;
  if (cols.size() == 4) {
    Graph<CostEdge> graph = read_graph<CostEdge>(
        cols, maxKmh, &coordToNodeMap, &arcToId);
    dump_graph(outfile, graph, coordToNodeMap);
  } else if (cols.size() == 5) {
    Graph<CostWeightEdge> graph = read_graph<CostWeightEdge>(
        cols, maxKmh, &coordToNodeMap, &arcToId);
    dump_graph(outfile, graph, coordToNodeMap);
    if (argc > 4) {
      const string mapfile = argv[4];
      dump_id_map(mapfile, arcToId);
    }
  } else {
    assert(false && "Input file has wrong number of columns.");
  }

  cout << endl << "OK" << endl;
  return 0;
}
