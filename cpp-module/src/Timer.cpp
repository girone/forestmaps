// Copyright 2013, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Björn Buchhold <buchholb>
// Adaptions for using <chrono>: Jonas Sternisko <sternis>

#include "./Timer.h"
#include <string>

// _____________________________________________________________________________
/*string Timer::getTimeStamp() {
  struct timeb timebuffer;
  char timeline[26];
  ftime(&timebuffer);
  ctime_r(&timebuffer.time, timeline);
  timeline[19] = '.';
  timeline[20] = 0;

  std::ostringstream os;
  os << timeline;
  os.fill('0');
  os.width(3);
  os << timebuffer.millitm;
  return os.str();
}*/

// _____________________________________________________________________________
void Timer::start() {
  _usecs = milliseconds::zero();
  cont();
}

// _____________________________________________________________________________
void Timer::cont() {
  _tstart = high_resolution_clock::now();
}

// _____________________________________________________________________________
void Timer::stop() {
  _tend = high_resolution_clock::now();
  _usecs = duration_cast<milliseconds>(_tend - _tstart);
}

// _____________________________________________________________________________
double Timer::intermediate() {
  high_resolution_clock::time_point now = high_resolution_clock::now();
  return duration_cast<milliseconds>(now - _tstart).count();
}
