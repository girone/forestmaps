''' convexhull.py

    Computes the convex hull of an osm dataset and stores its nodes in a
    textfile.

    Copyright 2013:
    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
'''
import pickle
import scipy
from scipy.spatial import qhull
import numpy as np
import sys


def sort_hull(hull, points):
  ''' Sorts the indices of a convex hull by their node's angle to the center
      point.
  '''
  ps = set()
  for x, y in hull:
    ps.add(x)
    ps.add(y)
  ps = np.array(list(ps))
  center = points[ps].mean(axis=0)
  A = points[ps] - center
  return points[ps[np.argsort(np.arctan2(A[:,1], A[:,0]))]]


def compute(points):
  ''' Computes the convex hull of a point set. '''
  hull = scipy.spatial.qhull.Delaunay(points).convex_hull
  return sort_hull(hull, np.array(points))


def load(filename):
  try:
    f = open(filename)
  except IOError:
    print 'Could not open ' + filename
    exit(1)
  hull = pickle.load(f)
#  for line in f:
#    (lat, lon) = \
#        tuple((float(lat), float(lon)) for lat, lon in line.strip().split(" "))
#    hull.append((lat, lon))
  return hull


def save(hull, filename):
  try:
    f = open(filename, 'w')
  except IOError:
    print 'Could not write to ' + filename
    exit(1)
#  for point in hull:
#    f.write(str(point[0]) + " " + str(point[1]) + "\n")
  pickle.dump(hull, f)


