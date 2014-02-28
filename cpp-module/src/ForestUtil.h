// Copyright 2014: Jonas Sternisko
//

// ForestUtil.h/cpp contains utility functions which are not as general as the
// stuff in Util.h/cpp.

#ifndef SRC_FORESTUTIL_H_
#define SRC_FORESTUTIL_H_

#include <vector>

namespace forest {

using std::vector;

// Distance between coordinates in meters, using great-circle distance.
float distance(float lat1, float lon1, float lat2, float lon2);

// Checks the user preferences read from a text file for correct values.
bool check_preferences(const vector<vector<float> >& preferences);

}


#endif  // SRC_FORESTUTIL_H_
