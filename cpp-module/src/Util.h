// Copyright 2013: Jonas Sternisko

#ifndef SRC_UTIL_H_
#define SRC_UTIL_H_

#include <cassert>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>


namespace util {
  using std::string;
  using std::ostringstream;
  using std::vector;

  // Distance in meters, using great-circle distance.
  float distance(float lat1, float lon1, float lat2, float lon2);

  // Like Python's ",".join(iterable) this function joins iterable to a string.
  template<class I>
  string join(const string& connector, const I& iterable) {
    ostringstream os;
    for (auto it = iterable.begin(); it < iterable.end(); ++it)
      os << (it != iterable.begin() ? connector : "") << *it;
    return os.str();
  }

  // Converts the input type to the output type.
  template<class B, class A>
  B convert(const A& input) {
    std::stringstream ss;
    B output;
    ss << input;
    ss >> output;
    return output;
  }

  // Reads a space separated file containing a table with N rows and M columns.
  // Returns M vectors, each contains N elements.
  template<class T>
  vector<vector<T> > read_column_file(const string& filename) {
    std::ifstream ifs(filename);
    if (!ifs.good()) {
      printf("File not found: %s\n", filename.c_str());
    }
    assert(ifs.good());
    // determine the number of columns from the first line
    vector<vector<T> > columns;
    string line;
    getline(ifs, line);
    int last = 0;
    for (size_t i = 0; i <= line.size(); ++i) {
      if ((i < line.size() && line[i] == ' ') || i == line.size()) {
        if (i - last > 0) {
          columns.push_back(vector<T>());
          columns.back().push_back(convert<T>(line.substr(last, i - last)));
        }
        last = i + 1;
      }
    }
    // get all other content
    int count = columns.size();
    while (ifs.good()) {
      string entry;
      ifs >> entry;
      if (entry != "") {
        columns[count % columns.size()].push_back(convert<T>(entry));
        count++;
      }
    }
    return columns;
  }


  // Writes a vector row-wise to a file.
  template<class T>
  void dump_vector(const vector<T>& vec, const string& filename) {
    std::ofstream ofs(filename);
    assert(ofs.good());
    for (const T& element: vec)
      ofs << element << std::endl;
  }

}  // namespace util


#endif  // SRC_UTIL_H_
