// Copyright 2013, Chair of Algorithms and Datastructures.
// Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

#ifndef COMPACTDIRECTEDGRAPHITERATOR_H_
#define COMPACTDIRECTEDGRAPHITERATOR_H_

#include <vector>

// Forward decl.
template<class A> class ArcIterator;
template<class A> class CompactDirectedGraph;

// _____________________________________________________________________________
// This class allows for convenient access to graphs with concatenated arc lists
// by implementing an interface for Iterator creation which enables range-based
// for-loops over the outgoing arcs of a node, while hiding the offset vector to
// the user.
template<class A>
class _AccessMediator {
 public:
  ArcIterator<A> begin() const;
  ArcIterator<A> end() const;

 private:
  // C'tor. Only CompactDirectedGraph should be able to instantiate this class.
  _AccessMediator(const std::vector<A>* const target, const size_t begin,
      const size_t end);
  friend class CompactDirectedGraph<A>;

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

// _____________________________________________________________________________
// ArcIterator

template<class A>
ArcIterator<A>::ArcIterator(const vector<A>* const target, const size_t state)
  : _target(target)
  , _state(state) { }


template<class A>
const A& ArcIterator<A>::operator*() const {
  return _target->operator[](_state);
}


template<class A>
void ArcIterator<A>::operator++() {
  ++_state;
}


template<class A>
bool ArcIterator<A>::operator!=(const ArcIterator& other) const {
  return /*_target != other._target ||*/ _state != other._state;
}

#endif  // COMPACTDIRECTEDGRAPHITERATOR_H_
