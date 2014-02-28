// Copyright 2013-14: Jonas Sternisko

// Util.h/cpp contains general utility functions. Code which is closely related
// to the forest project goes to ForestUtil.h/cpp

#ifndef SRC_UTIL_H_
#define SRC_UTIL_H_

#include <cassert>
#include <algorithm>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <utility>


namespace util {

using std::string;
using std::ostringstream;
using std::vector;

// Like Python's ",".join(iterable) this function joins iterable to a string.
template<class I>
string join(const string& connector, const I& iterable) {
  ostringstream os;
  for (auto it = iterable.begin(); it < iterable.end(); ++it)
    os << (it != iterable.begin() ? connector : "") << *it;
  return os.str();
}

// Adds variable number of arguments to a stream separated by connector.
ostringstream& _append_to_stream(ostringstream& os, const string& connector);
template<class First, class... Rest>
ostringstream& _append_to_stream(ostringstream& os, const string& connector,
                                 const First& first, Rest&... rest) {
  os << connector;
  os << first;
  _append_to_stream(os, connector, rest...);
  return os;
}

// Join again. Variadic template version to support lists of scalars.
// TODO(Jonas): Does not yet work with only one argument, because the iterable
// version is called then. Fix this.
template<class First, class... Types>
string join(const string& connector, const First& first,
    const Types&... input) {
  // const unsigned int size = sizeof...(Types);
  ostringstream os;
  os << first;
  _append_to_stream(os, connector, input...);
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
        // Ignore whitespace-only strings, e.g. spaces at line end.
        string sub = line.substr(last, i - last);
        if (!std::all_of(sub.begin(), sub.end(), isspace)) {
          columns.push_back(vector<T>());
          columns.back().push_back(convert<T>(sub));
        }
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

// Calculates the sum of elements of an iterable range.
template<class T>
T sum(const vector<T>& iterable) {
  T initial = 0;
  return std::accumulate(iterable.cbegin(), iterable.end(), initial);
}

// A hash function for pairs. Warning: The function probably creates a large
// number of hash collisions.
struct PairHash {
 public:
  size_t operator()(const std::pair<double, double>& x) const throw() {
    std::hash<double> hasher;
    size_t h = hasher(x.first + 2 * x.second);
    return h;
  }
};

}  // namespace util


#endif  // SRC_UTIL_H_
