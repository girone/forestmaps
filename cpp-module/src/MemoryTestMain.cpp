// Copyright 2014: Jonas Sternisko

#include <iostream>
#include <string>
#include <vector>
#include "./Util.h"


void print_usage() {
  std::cout << "Tries to allocate a number of GB. "
            << "Usage: ./MemoryTestMain <GB>" << std::endl;
}

int64_t power(int base, int exponent) {
  int64_t result = base;
  while (--exponent > 0) {
    result *= base;
  }
  return result;
}

int main(const int argc, const char** argv) {
  if (argc != 2) {
    print_usage();
    return 1;
  }

  int count = util::convert<int>(argv[1]);
  int64_t number = power(2, 30) * count;

  std::cout << "allocated " << number << " many bytes." << std::endl;
  std::vector<char> dummy(number, 0);
  std::cout << "done" << std::endl;
  dummy.assign(number, 1);
  std::cout << "assigned some value" << std::endl;
  std::cout << "done!" << std::endl;


  std::string blub;
  std::cin >> blub;



  return 0;
}
