// Copyright 2013, Chair of Algorithms and Datastructures.
// Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

#ifndef SRC_COMPACTDIRECTEDGRAPHITERATOR_H_
#define SRC_COMPACTDIRECTEDGRAPHITERATOR_H_

#include <string>
#include <vector>
#include <sstream>

// Forward decl.
template<class A> class ArcIterator;
template<class A> class OffsetListGraph;


// This class allows for convenient access to graphs with concatenated arc lists
// by implementing an interface for Iterator creation which enables range-based
// for-loops over the outgoing arcs of a node, while hiding the offset vector to
// the user.
template<class A>
class _AccessMediator {
 public:
  ArcIterator<A> begin() const;
  ArcIterator<A> end() const;
  size_t size() const;
  const std::string string() const;

 private:
  // C'tor. Only CompactDirectedGraph should be able to instantiate this class.
  _AccessMediator(const std::vector<A>* const target, const size_t begin,
      const size_t end);
  friend class OffsetListGraph<A>;

  const std::vector<A>* const _target;
  size_t _begin;
  size_t _end;
};


// _____________________________________________________________________________
// Implements a STL-like Iterator for the outgoing arcs of a node in the compact
// graph representation.
template<class A>
class ArcIterator {
 public:
  const A& operator*() const;
  const A* operator->() const;
  void operator++();
  bool operator!=(const ArcIterator& other) const;

 private:
  ArcIterator(const std::vector<A>* const target, const size_t state);
  const std::vector<A>* const _target;
  size_t _state;

  friend class _AccessMediator<A>;
};

// _____________________________________________________________________________
// TEMPLATE DEFINITIONS GO BELOW //

// _AccessMediator

template<class A>
_AccessMediator<A>::_AccessMediator(const std::vector<A>* const target,
    const size_t begin, const size_t end)
  : _target(target)
  , _begin(begin)
  , _end(end) { }


template<class A>
ArcIterator<A> _AccessMediator<A>::begin() const {
  return ArcIterator<A>(_target, _begin);
}


template<class A>
ArcIterator<A> _AccessMediator<A>::end() const {
  return ArcIterator<A>(_target, _end);
}


template<class A>
size_t _AccessMediator<A>::size() const {
  return _end - _begin;
}


template<class A>
const std::string _AccessMediator<A>::string() const {
  std::ostringstream os;
  for (size_t i = _begin; i < _end; ++i) {
    os << ((i != _begin) ? ", " : "") << _target->at(i).string();
  }
  return os.str();
}


// _____________________________________________________________________________
// ArcIterator

template<class A>
ArcIterator<A>::ArcIterator(const std::vector<A>* const target,
  const size_t state)
  : _target(target)
  , _state(state) { }


template<class A>
const A& ArcIterator<A>::operator*() const {
  return _target->operator[](_state);
}


template<class A>
const A* ArcIterator<A>::operator->() const {
  return &_target->operator[](_state);
}


template<class A>
void ArcIterator<A>::operator++() {
  ++_state;
}


template<class A>
bool ArcIterator<A>::operator!=(const ArcIterator& other) const {
  return /*_target != other._target ||*/ _state != other._state;
}

#endif  // SRC_COMPACTDIRECTEDGRAPHITERATOR_H_
