""" forestentrydetection

    This script performs a set of tasks:
    - classify forest entry points 'WEP'
    - classify arcs which are inside the forest
    - generate population grid points

    Usage:
    python forestentrydetection.py <OSMFile> [<MAXSPEED>] ["ATKIS"]

    The optional "ATKIS" flag tells the script that the OSM data was converted
    from ATKIS data.

    Copyright 2013: Institut fuer Informatik
    Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
"""

from PIL import Image, ImageDraw
import sys
import os.path
import math
from collections import defaultdict
import pickle

from grid import Grid, bounding_box
from graph import Graph, Edge, NodeInfo
import convexhull
import osm_parse

visualize = True


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


def classify_forest(node_ids, ways_by_type, graph, nodes, osm_id_map,
      filename_base):
  ''' Creates forest polygons and detects forest entries WE in the data. '''
  forest_delim = ways_by_type['forest_delim']
  bbox = bounding_box(nodes.values())

  print 'Computing the convex hull...'
  if visualize:
    visual_grid = Grid(bbox, mode="RGB")
  boundary_filename = filename_base + ".boundary.out"
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
  node_idx, removed = graph.filter_components(node_idx, 500)
  inverse_id_map = {value : key for (key, value) in osm_id_map.items()}
  forestal_highway_nodes = set([inverse_id_map[e] for e in node_idx])
  open_highway_nodes.union(set([inverse_id_map[e] for e in removed]))

  nodeinfo = {osm_id_map[osm_id] : NodeInfo(osm_id, nodes[osm_id]) 
              for osm_id in highway_node_ids}

  # This does not work properly and does not bring the expected benefit.
  #print 'Restrict the graph to largest connected component...'
  #n = graph.size()
  #c = len(graph.nodes)
  #graph = graph.lcc()
  #print "Removed " + str(c - len(graph.nodes))
  ## update indices
  #delete = np.array([0]*n)
  #for i in range(1, n):
  #  if i not in graph.nodes:
  #    delete[i] = 1
  #index_shift = np.cumsum(delete)
  #shifted_graph = Graph()
  #for node in graph.nodes:
  #  if delete[node] == 0:
  #    for to, edge in graph.edges[node].items():
  #      if delete[to] == 0:
  #        shifted_graph.add_edge(node - index_shift[node], 
  #            to - index_shift[to], edge.cost)
  #graph = shifted_graph
  #osm_id_map = \
  #    {k : v - index_shift[v] for k, v in osm_id_map.items() if delete[v] == 0}
  #ind = set([inverse_id_map[n] for n in graph.nodes if delete[node] == 0])
  #forestal_highway_nodes &= ind
  #open_highway_nodes &= ind
  #print 'Removed %d nodes, new size is %d.' % (n - graph.size(), 
  #    graph.size())

  print 'Select WEPs...'
  weps = select_wep(open_highway_nodes, forestal_highway_nodes, graph, 
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

  # restrict to used nodes
  used_osm_ids = forestal_highway_nodes | open_highway_nodes
  nodes = {k:v for k,v in nodes.items() if k in used_osm_ids}
  return weps, forestal_highway_nodes, population, nodeinfo


def main():
  if len(sys.argv) < 2 or os.path.splitext(sys.argv[1])[1] != '.osm':
    print ''' No osm file specified! '''
    exit(1)
  std_osm = True
  if "ATKIS" in sys.argv: 
    std_osm = False
    sys.argv.remove("ATKIS")
    print ' - Using ATKIS interpreter.'

  osmfile = sys.argv[1]
  maxspeed = int(sys.argv[2]) if len(sys.argv) > 2 else 130

  print 'Reading nodes and ways from OSM and creating the graph...'
  node_ids, ways_by_type, graph, nodes, osm_id_map = osm_parse.read_file(
      osmfile, maxspeed, interpret=osm_parse.Std_OSM_way_tag_interpreter 
      if std_osm else osm_parse.ATKIS_to_OSM_way_tag_interpreter)

  print len(graph.nodes), graph.size(), sum([len(edges) for edges in
    graph.edges.values()])

  filename_base = os.path.splitext(osmfile)[0] 
  weps, forestal_highway_nodes, population, nodeinfo = classify_forest(
      node_ids, ways_by_type, graph, nodes, osm_id_map, filename_base)

  print 'Writing output...'
  filename = filename_base + "." + str(maxspeed) + "kmh"
  for data, extension in zip(
      [weps, forestal_highway_nodes, population, graph, osm_id_map, nodes, 
       nodeinfo], 
      ['weps', 'forest_ids', 'population', 'graph', 'id_map', 'nodes', 
       'nodeinfo']
      ):
    f = open(filename + "." + extension + ".out", 'w')
    pickle.dump(data, f, protocol=2)
    f.close()


if __name__ == '__main__':
  ''' Run this module '''
  main()

