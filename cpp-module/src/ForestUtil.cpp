// Copyright 2014: Jonas Sternisko

#include "./ForestUtil.h"
#include <cassert>
#include <cmath>
#include <algorithm>
#include <iostream>

using std::accumulate;

const float kMY_PI = atan(1) * 4;  // workaround for missing M_PI in Windows

namespace forest {

// _____________________________________________________________________________
float distance(float lat1, float lon1, float lat2, float lon2) {
  // http://en.wikipedia.org/wiki/Great-circle_distance
  const double degToRad = kMY_PI / 180.;
  const double R = 6371000.785;
  const double dLat = (lat2 - lat1) * degToRad;
  const double dLon = (lon2 - lon1) * degToRad;
  double a = sin(dLat / 2) * sin(dLat / 2);
  a += cos(lat1 * degToRad) * cos(lat2 * degToRad) * sin(dLon / 2) *
      sin(dLon / 2);
  return 2 * R * asin(sqrt(a));
}


// _____________________________________________________________________________
bool check_preferences(const vector<vector<float> >& preferences) {
  using std::cout;
  using std::endl;
  for (size_t i = 1; i < preferences[0].size(); ++i) {
    if (preferences[0][i] <= preferences[0][i-1]) {
      cout << "Wrong prefence intervals: upper bound " << preferences[0][i]
           << " is less than or equal its predecessor." << endl;
      exit(1);
    }
  }

  for (float share: preferences[1]) {
    if (share < 0 || share > 1) {
      cout << "Wrong preference values: share " << share
           << " is not in [0,1]." << endl;
      exit(1);
    }
  }

  float sum = accumulate(preferences[1].begin(), preferences[1].end(), 0.f);
  if (sum >= 1.0000001f) {
    cout << "Sum of preference category shares is greater than 1:" << endl;
    cout << sum << endl;
    exit(1);
  }

  return true;
}

}  // namespace forst
