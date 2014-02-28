// Copyright 2013, Chair of Algorithms and Datastructures.
// Author: Mirko Brodesser <mirko.brodesser@gmail.com>

#ifndef SRC_UTILS_H_
#define SRC_UTILS_H_

#include <sstream>
#include <string>
#include <vector>

namespace utils {
  using std::string;
  using std::ostringstream;

  // Distance in meters, using great-circle distance.
  float distance(float lat1, float lon1, float lat2, float lon2);

  // Joins iterable object to one string.
  template<class I>
  string joinIterable(const I& iterable) {
    ostringstream os;
    for (auto it = iterable.begin(); it < iterable.end(); ++it)
      os << (it != iterable.begin() ? ", " : " ") << *it;
    return os.str();
  }
}  // namespace utils

#endif  // SRC_UTILS_H_
