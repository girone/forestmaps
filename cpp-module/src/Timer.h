// Copyright 2013, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Björn Buchhold <buchholb>
// Adaptions for using <chrono>: Jonas Sternisko <sternis>

#ifndef TIMER_H_
#define TIMER_H_

#include <string>
#include <chrono>

using std::string;

// NOTE(Jonas): chrono::duration::nanoseconds does not work with MinGW for Win7.
// So I decided to stick with milliseconds resolution instead.
class Timer {
 public:
  // Gets a readable timestamp as string.
  // static string getTimeStamp();

  // Resets the timer value to zero and starts the measurement.
  void start();

  // Cont.
  void cont();

  // Stops the measurement
  void stop();

  // Returns the time since start() in usec, continues.
  double intermediate();

  double getUSecs() const {
    return _usecs.count() / 1000.;
  }

  double getMSecs() const {
    return getUSecs();
  }

  double getSecs() const {
    return getUSecs() * (1000);
  }

 private:
  // Timer value.
  std::chrono::milliseconds _usecs;
  // Used by the gettimeofday command.
  std::chrono::high_resolution_clock::time_point _tstart;
  std::chrono::high_resolution_clock::time_point _tend;
};


#endif  // TIMER_H_
