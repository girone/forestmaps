// Copyright 2013, Chair of Algorithms and Datastructures.
// Author: Mirko Brodesser <mirko.brodesser@gmail.com>

#include <cmath>

#include "./utils.h"

namespace utils {
  float distance(float lat1, float lon1, float lat2, float lon2) {
    // http://en.wikipedia.org/wiki/Great-circle_distance
    const double degToRad = M_PI / 180.;
    const double R = 6371000.785;
    const double dLat = (lat2 - lat1) * degToRad;
    const double dLon = (lon2 - lon1) * degToRad;
    double a = sin(dLat / 2) * sin(dLat / 2);
    a += cos(lat1 * degToRad) * cos(lat2 * degToRad) * sin(dLon / 2) *
        sin(dLon / 2);
    return 2 * R * asin(sqrt(a));
  }
}  // namespace utils
