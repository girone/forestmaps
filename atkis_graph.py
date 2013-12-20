"""atkis_graph.py : Builds a graph from ATKIS data.

The data comes as numpy.array generated by arcpy.da.FeatureClassToNumPyArray()
with explode_to_points=True.

"""
from math import sqrt
from collections import defaultdict
from itertools import tee, izip
import numpy as np
from graph import Graph
from arcutil import msg, Progress


ATKIS_HIGHWAY_VALUE_RANGE = set(range(164001, 164012) + range(87001, 87005) +
                                range(89001, 89003) + range(90001, 90019))


ATKISSpeedTable = {164001 : 110,
                   164003 : 70,
                   164005 : 110,
                   164007 : 70,
                   164009 : 110,
                   164010 : 70,
                    87001 : 50,
                    87003 : 5,
                    87004 : 25,
                    88001 : 25,
                    89001 : 25,
                    89002 : 10,
                    90001 : 110,
                    90003 : 70,
                    90005 : 110,
                    90007 : 70,
                    90009 : 110,
                    90010 : 70,
                    90012 : 50,
                    90014 : 5,
                    90015 : 25,
                    90016 : 25,
                    90017 : 25,
                    90018 : 10}


def ATKISWayTagInterpreter(key, val):
    """Interprets way tags of OSM files created by ogr2osm.py from ATKIS data.

    This data comes with a lot if tag lines of this format:
      <tag k="KEY" v="VAL" />
    We are only interested in ways which are streets, footpaths and so on.
    These have a tag with KEY="KLASSE" and VAL being an interger in a range
    according to the ATKIS documentation.
    Moreover, the speed on these streets is explicitly given by two tags with
    KEY="Speed_Tobl" and KEY="Speed_To_1" (forward and backward speed). We take
    the average of these two.
    HACK: We just take one value, whichever comes last.
    HACKHACK: We don't care--and take a handish speed table.

    """
    if key == 'KLASSE':
        if int(val) in ATKISSpeedTable:
            return type_to_speed(int(val), ATKISSpeedTable)
        else:
            print "Unknown combination: ", key, val
    return False


def pairwise(iterable):
  """ Example: [w, x, y, z]  --> [(w, x), (x, y), (y, z)]. """
  a, b = tee(iterable)
  next(b, None)
  return izip(a, b)


def distance(p1, p2):
  """ Euclid. """
  return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def determine_speed(way_type, max_speed):
  """ Get the speed in km/h on a specific way type. """
  speed = ATKISSpeedTable[way_type]
  return max_speed if speed > max_speed else speed


def create_mappings_from_polylines(arr):
  """ Creates two mappings (defined below) from lines in a numpy.recarray. """
  def add_node(position):
    """ Returns node index of the node at the position. """
    if position not in coord_to_node:
      coord_to_node[position] = len(coord_to_node)
    return coord_to_node[position]
  def add_two_arcs(x, y, arc_id, cost):
    """ Bidirectional. """
    arcs[x].add((y, arc_id, cost))
    arcs[y].add((x, arc_id, cost))

  coord_to_node = {}  # {(easting, northing) : node_index}
  arcs = defaultdict(set)  # {base_node --> set([(head_node, fid, type, cost)])
  for a, b in pairwise(arr):
    if a['fid'] == b['fid']:
      index_a = add_node(tuple(a['shape']))
      index_b = add_node(tuple(b['shape']))
      dist = distance(a['shape'], b['shape'])
      add_two_arcs(index_a, index_b, a['fid'], a['klasse'], dist)
  return coord_to_node, arcs


def create_graph_from_arc_map(preliminary_arcs, max_speed):
  """ Assumes the input contains two arcs for bidirectional edges. """
  g = Graph()
  for s, out_set in preliminary_arcs.items():
    for (t, fid, way_type, dist) in out_set:
      cost = dist / (determine_speed(way_type, max_speed) / 3.6)
      g.add_edge(s, t, cost)
  return g


def create_graph_via_numpy_array(dataset, max_speed=5):
  """ For faster performance and reliable field order, it is recommended that
      the list of fields be narrowed to only those that are actually needed.
      NOTE(Jonas): That is indeed much faster (factor 10)!
  """
  sr = arcpy.Describe(road_dataset).spatialReference
  # Convention: Field names are lowercase.
  arr = arcpy.da.FeatureClassToNumPyArray(
      road_dataset, ["fid", "shape", "klasse", "wanderweg", "shape_leng"],
      spatial_reference=sr, explode_to_points=True)
  #_, index = np.unique(road_points_array['fid'], return_index=True)
  #road_features_array = road_points_array[index]
  """ Uses a numpy structured array in to produce the graph. """
  coord_to_node_map, arc_map = create_mappings_from_polylines(arr, max_speed)
  return create_graph_from_arc_map(arc_map), coord_to_node_map


def create_from_feature_class(fc, max_speed=5):
  """ Reads a feature class from disk, creates a graph from its Polylines. """
  def add_node(coordinate):
    """ Adds a node for a coordinate (if none exists yet). Returns its id. """
    if coordinate not in coord_to_node:
      coord_to_node[coordinate] = len(coord_to_node)
    return coord_to_node[coordinate]
  graph = Graph()
  coord_to_node = {}
  arc_to_fid = {}
  field_names = ["fid", "SHAPE@XY", "klasse", "wanderweg"]
  last_fid = None
  import arcpy
  total = int(arcpy.management.GetCount(fc).getOutput(0))
  count = 0
  p = Progress("Building graph from FeatureClass.", total, 100)
  with arcpy.da.SearchCursor(fc, field_names, explode_to_points=True) as rows:
    for row in rows:
      #msg("{0} {1} {2} {3}".format(row[0], row[1], row[2], row[3]))
      fid, coordinates, way_type, path_flag = row
      if fid == last_fid:
        index_a = add_node(last_coordinates)
        index_b = add_node(coordinates)
        dist = distance(last_coordinates, coordinates)
        cost = dist / (determine_speed(way_type, max_speed) / 3.6)
        graph.add_edge(index_a, index_b, cost)
        graph.add_edge(index_b, index_a, cost)
        arc_to_fid[(index_a, index_b)] = fid
        arc_to_fid[(index_b, index_a)] = fid
      else:
        count += 1
        p.progress(count)
      last_fid = fid
      last_coordinates = coordinates
  return graph, coord_to_node, arc_to_fid


import unittest

class AtkisGraphTest(unittest.TestCase):
  def test_create_mappings(self):
    arr = np.array([(15, [1.0, 3.0]), (15, [2.0, 0.0]), (16, [5.0, 0.0]),
                    (16, [2.0, 0.0]), (21, [6.0, 2.0]), (21, [5.0, 0.0]),
                    (22, [5.0, 0.0]), (22, [3.0, -1.0])],
                   dtype=[('fid', '<i4'), ('shape', '<f4', (2,))])
    coord_to_node, arcs = create_mappings_from_polylines(arr)
    #print coord_to_node
    #print arcs

  def test_create_graph(self):
    arr = np.array([(15, [1.0, 3.0]), (15, [2.0, 0.0]), (16, [5.0, 0.0]),
                    (16, [2.0, 0.0]), (21, [6.0, 2.0]), (21, [5.0, 0.0]),
                    (22, [5.0, 0.0]), (22, [3.0, -1.0])],
                   dtype=[('fid', '<i4'), ('shape', '<f4', (2,))])
    map1, map2 = create_mappings_from_polylines(arr)
    graph = create_graph_from_arc_map(map2)
    print graph


if __name__ == '__main__':
  unittest.main()

