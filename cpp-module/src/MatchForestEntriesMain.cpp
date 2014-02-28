// Copyright 2013: Jonas Sternisko

#include <iostream>
#include <string>
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
  string s;
  s = "Maps forest entries and parking lot positions to nodes in the graphs.\n"
      " Usage: ./program <graphR> <graphF> <ForestEntriesXY> <ParkingLotsXY> "
      "<outfile>\n"
      " <graphR> -- \n"
      " <graphF> -- \n"
      " <ForestEntriesXY> -- Locations (x, y) of the forest entries\n"
      " <ParkingLotsXY> -- Locations (x, y) of the parking lots\n"
      " <outfile> -- Path to the output file. \n";
  std::cout << s << std::endl;
}


// This reads in the road graph, forest road graph and the locations of the
// forest entries points. Via a KDTree, the entry points are matched to the
// closest nearby nodes of the road and forest graph. The result is written
// as a new file containing each forest entry point's location and corresponding
// road and forest graph node index.
int main(int argc, char** argv) {
  if (argc != 6) {
    print_usage();
    exit(1);
  }
  RoadGraph graphR, graphF;
  graphR.read_in(argv[1]);
  graphF.read_in(argv[2]);
  vector<vector<float> > fepXY = util::read_column_file<float>(argv[3]);
  assert(fepXY.size() >= 2);
  const vector<float>& xx = fepXY[0];
  const vector<float>& yy = fepXY[1];

  // Map entry points to road graph node indices.
  vector<int> indexR = map_xy_locations_to_closest_node(xx, yy, graphR);
  vector<int> indexF = map_xy_locations_to_closest_node(xx, yy, graphF);

  // Combine and dump.
  vector<XYRF> combined;
  combined.reserve(xx.size());
  assert(indexF.size() == indexR.size() && indexR.size() == xx.size() &&
         xx.size() == yy.size());
  for (size_t i = 0; i < xx.size(); ++i) {
    combined.push_back(XYRF(xx[i], yy[i], indexR[i], indexF[i]));
  }

  // The same for parking lots.
  vector<vector<float> > parkingXY = util::read_column_file<float>(argv[4]);
  assert(parkingXY.size() >= 2);
  const vector<float>& pxx = parkingXY[0];
  const vector<float>& pyy = parkingXY[1];
  indexR = map_xy_locations_to_closest_node(pxx, pyy, graphR);
  indexF = map_xy_locations_to_closest_node(pxx, pyy, graphF);
  assert(indexF.size() == indexR.size() && indexR.size() == pxx.size() &&
         pxx.size() == pyy.size());
  for (size_t i = 0; i < pxx.size(); ++i) {
    combined.push_back(XYRF(pxx[i], pyy[i], indexR[i], indexF[i]));
  }

  // Output.
  string filename = argv[5];  // "forest_entries_xyrf.tmp.txt";
  std::cout << "Writing forest entry locations and graph indices to "
            << filename << std::endl;
  util::dump_vector(combined, filename);

  // Message to external callers which can't fetch the return code.
  std::cout << std::endl << "OK" << std::endl;
  return 0;
}
