// Copyright 2013: Jonas Sternisko

#include <iostream>
#include <vector>
#include "./DirectedGraph.h"
#include "./Tree2d.h"
#include "./Util.h"


using std::ostream;
using std::vector;


// Represents X, Y coordinates and index in _R_oad and _F_orest graph.
struct XYRF {
  XYRF(float x, float y, int r, int f) {
    X = x;
    Y = y;
    R = r;
    F = f;
  }
  float X;
  float Y;
  int R;
  int F;
};

ostream& operator<<(std::ostream& os, const XYRF& a) {
  os << a.X << " " << a.Y << " " << a.R << " " << a.F;
  return os;
}


void print_usage() {
  std::cout << "Usage: ./program <graphR> <graphF> <ForestEntriesXY>"
            << std::endl;
}


// This reads in the road graph, forest road graph and the locations of the
// forest entries points. Via a KDTree, the entry points are matched to the
// closest nearby nodes of the road and forest graph. The result is written
// as a new file containing each forest entry point's location and corresponding
// road and forest graph node index.
int main(int argc, char** argv) {
  if (argc != 4) {
    print_usage();
    exit(1);
  }
  RoadGraph graphR, graphF;
  graphR.read_in(argv[1]);
  graphF.read_in(argv[2]);
  vector<vector<float> > fepXY = util::read_column_file<float>(argv[3]);
  const vector<float>& xx = fepXY[0];
  const vector<float>& yy = fepXY[1];

  // Map entry points to road graph node indices.
  vector<int> indexF = map_xy_locations_to_closest_node(xx, yy, graphF);
  vector<int> indexR = map_xy_locations_to_closest_node(xx, yy, graphR);

  // Combine and dump.
  vector<XYRF> combined;
  combined.reserve(xx.size());
  assert(indexF.size() == indexR.size() && indexR.size() == xx.size() &&
         xx.size() == yy.size());
  for (size_t i = 0; i < xx.size(); ++i) {
    combined.push_back(XYRF(xx[i], yy[i], indexR[i], indexF[i]));
  }
  string filename = "forest_entries_xyrf.tmp.txt";
  std::cout << "Writing forest entry locations and r/f graph indices to "
            << filename << std::endl;
  util::dump_vector(combined, filename);

  return 0;
}
