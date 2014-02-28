""" forestentrydetection

    This script performs a set of tasks:
    - classify forest entry points 'WEP'
    - classify arcs which are inside the forest
    - generate population grid points

    Usage:
    python forestentrydetection.py <OSMFile> [<MAXSPEED>]

    Copyright 2013: Institut fuer Informatik
    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
"""

from PIL import Image, ImageDraw
import re
import sys
import os.path
import math
from collections import defaultdict
import pickle
#import numpy as np

from grid import Grid, bounding_box
from graph import Graph, Edge, NodeInfo
import convexhull


speed_table = {"motorway"       : 110, \
               "trunk"          : 110, \
               "primary"        : 70, \
               "secondary"      : 60, \
               "tertiary"       : 50, \
               "motorway_link"  : 50, \
               "trunk_link"     : 50, \
               "primary_link"   : 50, \
               "secondary_link" : 50, \
               "road"           : 40, \
               "unclassified"   : 40, \
               "residential"    : 30, \
               "unsurfaced"     : 30, \
               "cycleway"       : 25, \
               "living_street"  : 10, \
               "bridleway"      : 5, \
               "service"        : 5, \
               "OTHER"          : 0, \
               "track"          : 5, \
               "footway"        : 5, \
               "pedestrian"     : 5, \
               "tertiary_link"  : 5, \
               "path"           : 4, \
               "steps"          : 3}


def type_to_speed(typee):
  if typee in speed_table:
    return speed_table[typee]
  else:
    #print "type '" + typee + "' unknown."
    return 0


def great_circle_distance((lat0, lon0), (lat1, lon1)):
  ''' dist in meters, see http://en.wikipedia.org/wiki/Great-circle_distance '''
  to_rad = math.pi / 180.
  r = 6371000.785
  dLat = (lat1 - lat0) * to_rad
  dLon = (lon1 - lon0) * to_rad
  a = math.sin(dLat / 2.) * math.sin(dLat / 2.)
  a += math.cos(lat0 * to_rad) * math.cos(lat1 * to_rad) * \
      math.sin(dLon / 2) * math.sin(dLon / 2)
  return 2 * r * math.asin(math.sqrt(a))


def read_osmfile(filename, maxspeed):
  """ Parses nodes and arcs from an osm-file.
      Creates two mappings, a graph and a collection of nodes from an osm-file.
      - a mapping {way id -> [list of node ids]}
      - a mapping {way type -> [list of way ids]}
      - a bidirectional graph as a map {node_id -> set([successors])}
      - a dictionary of nodes {node_id -> (lon, lat)}
      - a mapping {osm id -> graph node index}
  """
  def expand_way_to_edges(way_node_list):
    """ For a list of way nodes, this adds arcs between successors.
    """
    edges = []
    size = len(way_node_list)
    for i, j in zip(range(size-1), range(1,size)):
      edges.append((way_node_list[i], way_node_list[j]))
    return edges
  def calculate_edge_cost(a, b, v):
    s = great_circle_distance(a, b)
    t = s / (v * 1000. / 60**2)
    return t
  f = open(filename)
  p_node = re.compile('.*<node id="(\S+)" lat="(\S+)" lon="(\S+)"')
  nodes = {}
  p_waytag = re.compile('\D*k="(\w+)" v="(\w+)"')
  way_nodes = {}
  ways_by_type = {'forest_delim': [], 'highway': []}
  graph = Graph()
  osm_id_map = {}
  state = 'none'
  for line in f:
    stripped = line.strip()
    res = p_node.match(line)
    if res:
      assert state != 'way'
      # switch (lat, lon) to (lon, lat) for (x, y)-coordinates
      nodes[int(res.group(1))] = (float(res.group(3)), float(res.group(2)))
    elif state == 'none':
      if stripped.startswith('<way'):
        state = 'way'
        way_id = int(line.split('id=\"')[1].split('\"')[0])
        node_list = []
    if state == 'way':
      if stripped.startswith('<tag'):
        res = p_waytag.match(stripped)
        if res:
          k, v = res.group(1), res.group(2)
          if k == 'highway':
            way_type = v
            if way_type in speed_table:
              ways_by_type['highway'].append(way_id)
          if (k == 'landuse' and v == 'forest') or  \
             (k == 'natural' and v == 'wood'):
            ways_by_type['forest_delim'].append(way_id)
      elif stripped.startswith('<nd'):
        node_id = int(stripped.split("ref=\"")[1].split("\"")[0])
        node_list.append(node_id)
      elif stripped.startswith('</way'):
        state = 'none'
        if len(ways_by_type['highway']) \
            and ways_by_type['highway'][-1] is way_id:
          edges = expand_way_to_edges(node_list)
          v = type_to_speed(way_type)
          v = v if v <= maxspeed else maxspeed
          if v != 0:
            way_nodes[way_id] = node_list
            for e in edges:
              if e[0] not in osm_id_map:
                osm_id_map[e[0]] = len(graph.nodes)
              x = osm_id_map[e[0]]
              if e[1] not in osm_id_map:
                osm_id_map[e[1]] = len(graph.nodes)
              y = osm_id_map[e[1]]
              if x == y:
                y += 1
                osm_id_map[e[1]] = y
              t = calculate_edge_cost(nodes[e[0]], nodes[e[1]], v)
              graph.add_edge(x, y, t)
              graph.add_edge(y, x, t)
        elif len(ways_by_type['forest_delim']) \
            and ways_by_type['forest_delim'][-1] is way_id:
          way_nodes[way_id] = node_list
  return way_nodes, ways_by_type, graph, nodes, osm_id_map


def width_and_height(bbox):
  return (bbox[1][0] - bbox[0][0]), (bbox[1][1] - bbox[0][1])


def classify(highway_nodes, nodes, grid):
  ''' Classifies highway nodes whether they are in the forest or on open
      terrain.
  '''
  forestal_highway_nodes = set()
  open_highway_nodes = set()
  for node_id in highway_nodes:
    lon, lat = nodes[node_id]
    if grid.test((lon, lat)):
      forestal_highway_nodes.add(node_id)
    else:
      open_highway_nodes.add(node_id)
  return forestal_highway_nodes, open_highway_nodes


def select_wep(open_highway_nodes, forestal_highway_nodes, graph, osm_id_map):
  ''' Selects nodes as WEP which are outside the forest and point into it. '''
  weps = set()
  inverse_id_map = {value : key for (key, value) in osm_id_map.items()}
  for osm_id in open_highway_nodes:
    node_id = osm_id_map[osm_id]
    for other_node_id in graph.edges[node_id].keys():
      other_osm_id = inverse_id_map[other_node_id]
      if other_osm_id in forestal_highway_nodes:
        weps.add(osm_id)
        break
  return weps


def create_population_grid(boundary_polygon, forest_polygons, resolution = 100):
  bbox = bounding_box(boundary_polygon)
  grid_points = create_grid_points(bbox, resolution)
  grid_points = filter_point_grid(grid_points, [boundary_polygon], 'intersect')
  grid_points = filter_point_grid(grid_points, forest_polygons, 'difference')
  return grid_points


def create_grid_points(bbox, resolution):
  ''' Creates a point grid for a region with @resolution many points along the
      smaller side of @bbox.
  '''
  w, h = width_and_height(bbox)
  min_side = min(w, h)
  xmin, ymin = bbox[0]
  step = min_side / (resolution + 1)
  grid_points = []
  for i in range(1, int(math.ceil(h / step))):
    for j in range(1, int(math.ceil(w / step))):
      grid_points.append((j*step + xmin, i*step + ymin))  # (lon,lat) ~ (x,y)
  return grid_points


def filter_point_grid(points, regions, operation='intersect'):
  '''
  Filters @points by applying @operation with @regions using a grid.
  Operations:
    'intersect' : returns @points which lie inside @regions
    'difference': returns @points which do not lie inside @regions
  '''
  assert operation in ['intersect', 'difference']
  bbox = bounding_box(points + [p for region in regions for p in region])
  bbox = (bbox[0], (bbox[1][0] * 1.01, bbox[1][1]*1.01))
  grid = Grid(bbox)
  for poly in regions:
    grid.fill_polygon(poly)
  if operation is 'intersect':
    return [p for p in points if grid.test(p) != 0]
  elif operation is 'difference':
    return [p for p in points if grid.test(p) == 0]
  else:
    print "Error: Unsupported operation for 'filter_point_grid'."
    exit(1)


def classify_forest(osmfile, maxspeed=130):
  print 'Reading nodes and ways from OSM and creating the graph...'
  node_ids, ways_by_type, digraph, nodes, osm_id_map = read_osmfile(osmfile, \
      maxspeed)
  forest_delim = ways_by_type['forest_delim']
  bbox = bounding_box(nodes.values())
  print 'Computing the convex hull...'
  if visualize:
    visual_grid = Grid(bbox, mode="RGB")
  boundary_filename = os.path.splitext(osmfile)[0] + ".boundary.out"
  if os.path.exists(boundary_filename):
    hull = convexhull.load(boundary_filename)
  else:
    points = [list(p) for p in nodes.values()]
    hull = convexhull.compute(points)
    convexhull.save(hull, boundary_filename)
  if visualize:
    visual_grid.fill_polygon(hull, fill="#fadbaa")

  print 'Creating forest grid from polygons...'
  forest_polygons = \
      [[nodes[id] for id in node_ids[way_id]] for way_id in forest_delim]
  forest_grid = Grid(bbox)
  for poly in forest_polygons:
    forest_grid.fill_polygon(poly)

  print 'Classifying highway nodes...'
  highway_node_ids = \
      set([id for way_id in ways_by_type['highway'] for id in node_ids[way_id]])
  forestal_highway_nodes, open_highway_nodes = \
      classify(highway_node_ids, nodes, forest_grid)

  print 'Restrict forests to large connected components...'
  # turn this off, when fast results are needed
  node_idx = [osm_id_map[e] for e in forestal_highway_nodes]
  node_idx, removed = digraph.filter_components(node_idx, 500)
  inverse_id_map = {value : key for (key, value) in osm_id_map.items()}
  forestal_highway_nodes = set([inverse_id_map[e] for e in node_idx])
  open_highway_nodes.union(set([inverse_id_map[e] for e in removed]))

  nodeinfo = {osm_id_map[osm_id] : NodeInfo(osm_id, nodes[osm_id]) \
              for osm_id in highway_node_ids}

  # This does not work properly and does not bring the expected benefit.
  #print 'Restrict the graph to largest connected component...'
  #n = digraph.size()
  #c = len(digraph.nodes)
  #digraph = digraph.lcc()
  #print "Removed " + str(c - len(digraph.nodes))
  ## update indices
  #delete = np.array([0]*n)
  #for i in range(1, n):
  #  if i not in digraph.nodes:
  #    delete[i] = 1
  #index_shift = np.cumsum(delete)
  #shifted_graph = Graph()
  #for node in digraph.nodes:
  #  if delete[node] == 0:
  #    for to, edge in digraph.edges[node].items():
  #      if delete[to] == 0:
  #        shifted_graph.add_edge(node - index_shift[node], \
  #            to - index_shift[to], edge.cost)
  #digraph = shifted_graph
  #osm_id_map = \
  #    {k : v - index_shift[v] for k, v in osm_id_map.items() if delete[v] == 0}
  #ind = set([inverse_id_map[n] for n in digraph.nodes if delete[node] == 0])
  #forestal_highway_nodes &= ind
  #open_highway_nodes &= ind
  #print 'Removed %d nodes, new size is %d.' % (n - digraph.size(), \
  #    digraph.size())

  print 'Select WEPs...'
  weps = select_wep(open_highway_nodes, forestal_highway_nodes, digraph, \
      osm_id_map)
  print str(len(weps)) + ' WEPs'

  print 'Creating the population grid...'
  xmin, ymin = bbox[0]
  xmax, ymax = bbox[1]
  dummy = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
  boundary_polygon = hull
  population = create_population_grid(boundary_polygon, forest_polygons, 10)

  if visualize:
    print 'Visualizing the result...'
    for poly in forest_polygons:
      visual_grid.fill_polygon(poly, fill="#00DD00")
    for node_id in weps:
      x, y = visual_grid.transform(nodes[node_id])
      r = 10
      visual_grid.draw.ellipse((x-r,y-r,x+r,y+r), fill="#BB1111")
    for (x,y) in population:
      (x, y) = visual_grid.transform((x,y))
      r = 30
      visual_grid.draw.ellipse((x-r, y-r, x+r, y+r), fill="#0000FF")
    visual_grid.show()

  pickle.dump(forest_polygons, \
      open(os.path.splitext(osmfile)[0] + ".forest_polygons.out", "w"), \
      protocol=2)

  # restrict to used nodes
  used_osm_ids = forestal_highway_nodes | open_highway_nodes
  nodes = {k:v for k,v in nodes.items() if k in used_osm_ids}
  return weps, forestal_highway_nodes, population, digraph, osm_id_map, nodes, \
      nodeinfo

visualize = False

def main():
  if len(sys.argv) < 2 or os.path.splitext(sys.argv[1])[1] != '.osm':
    print ''' No osm file specified! '''
    exit(1)
  osmfile = sys.argv[1]
  maxspeed = int(sys.argv[2]) if len(sys.argv) > 2 else 130

  weps, forestal_highway_nodes, population, graph, osm_id_map, nodes, nodeinfo \
      = classify_forest(osmfile, maxspeed)

  print 'Writing output...'
  # f = open(os.path.splitext(osmfile)[0] + '.WEPs.out', 'w')
  # for p in weps:
  #   f.write(str(p) + '\n')
  # f.close()
  # f = open(os.path.splitext(osmfile)[0] + '.forest_nodes.out', 'w')
  # for n in forestal_highway_nodes:
  #   f.write(str(n) + '\n')
  # f.close()
  # ''' Output the population locations. The cpp-module will create nodes from
  #     these. '''
  # f = open(os.path.splitext(osmfile)[0] + '.population_grid_points.out', 'w')
  # for (x,y) in population:
  #   f.write(str(y) + ' ' + str(x) + '\n')  # (x,y) = (lon,lat)
  # f.close()
  filename = os.path.splitext(osmfile)[0] + "." + str(maxspeed) + "kmh"
  for data, extension in \
      zip([weps, forestal_highway_nodes, population, graph, osm_id_map, nodes, \
          nodeinfo], \
          ['weps', 'forest_ids', 'population', 'graph', 'id_map', 'nodes', \
          'nodeinfo']):
    f = open(filename + "." + extension + ".out", 'w')
    pickle.dump(data, f, protocol=2)
    f.close()


if __name__ == '__main__':
  ''' Run this module '''
  main()

