""" forestentrydetection

    OSM denotes forest polygons as ways with tag either
      <tag k="landuse" v="forest"/>
    or
      <tag k="natural" v="wood"/>

    First sweep: Read all ways, store forest boundary node references.
    Second sweep: Store lat-lon pairs for all boundary nodes in the correct
    order.
""" 

from PIL import Image, ImageDraw
import numpy as np
import re
import sys
import os.path
import math
from collections import defaultdict
import scipy
from scipy.spatial import qhull
from grid import Grid


def map_way_ids_to_nodes(osmfile):
  """ Creates two mappings and a graph from an osm-file.
      - a mapping {way id -> [list of node ids]} 
      - a mapping {way type -> [list of way ids]}
      - a bidirectional graph as a map {node_id -> set([successors])}
  """
  def expand_way_to_edges(way_node_list):
    """ For a list of way nodes, this adds bidirectional arcs between successors.
    """
    edges = []
    size = len(way_node_list)
    for i, j in zip(range(size-1), range(1,size)):
      edges.append((way_node_list[i], way_node_list[j]))
    return edges
  f = open(osmfile)
  p = re.compile('\D*k="(\w+)" v="(\w+)"')
  way_nodes = {}
  way_types = {'forest_delim': [], 'highway': []}
  graph = defaultdict(set)
  state = 'none'
  for line in f:
    stripped = line.strip()
    if state == 'none':
      if stripped.startswith('<way'):
        state = 'way'
        way_id = int(line.split('id=\"')[1].split('\"')[0])
        node_list = []
    if state == 'way':
      if stripped.startswith('<tag'):
        res = p.match(stripped)
        if res:
          if res.group(1) == 'highway':
            way_types['highway'].append(way_id)
          if (res.group(1) == 'landuse' and res.group(2) == 'forest') or  \
             (res.group(1) == 'natural' and res.group(2) == 'wood'):
            way_types['forest_delim'].append(way_id)
      elif stripped.startswith('<nd'):
        node_id = int(stripped.split("ref=\"")[1].split("\"")[0])
        node_list.append(node_id)
      elif stripped.startswith('</way'):
        state = 'none'
        way_nodes[way_id] = node_list
        if way_types['highway'][-1] is way_id:
          edges = expand_way_to_edges(node_list)
          for e in edges:
            graph[e[0]].add(e[1])
            graph[e[1]].add(e[0])
  return way_nodes, way_types, graph


def read_nodes(osmfile):
  """ Parses OSM nodes from a file. """
  f = open(osmfile)
  p = re.compile('.*<node id="(\S+)" lat="(\S+)" lon="(\S+)"')
  nodes = {}
  for line in f:
    res = p.match(line)
    if res:
      # switch (lat, lon) to (lon, lat) as (x, y)-coordinates
      nodes[int(res.group(1))] = (float(res.group(3)), float(res.group(2))) 
  return nodes


def bounding_box(points):
  xmax = ymax = float(-sys.maxint)
  xmin = ymin = float(sys.maxint)
  for point in points:
    if xmax < point[0]:
      xmax = point[0]
    if xmin > point[0]:
      xmin = point[0]
    if ymax < point[1]:
      ymax = point[1]
    if ymin > point[1]:
      ymin = point[1]
  return ((xmin, ymin), (xmax, ymax))


def width_and_height(bbox):
  return (bbox[1][0] - bbox[0][0]), (bbox[1][1] - bbox[0][1])


def compute_forest_grid(forest_polygons, bbox, (resx, resy) = (10240, 8600)):
  ''' Computes a grid (array) distinguishing forest and open ground. '''
  # compute scale
  width, height = width_and_height(bbox)
  resx, resy = 10240, 8600
  scale = min(float(resx/width), float(resy/height))
  scaled_polygons = []
  ((xmin, ymin), (xmax, ymax)) = bbox
  for poly in forest_polygons:
    # Point tuples contain (lon, lat). Use (minlon, maxlat) as reference point
    # (0,0) of the coordinate system.
    scaled_polygons.append(scale_and_shift(poly, scale, xmin, ymax))
  # fill the forest_grid
  img = Image.new("F", (resx, resy), 0)
  draw = ImageDraw.Draw(img)
  for poly in scaled_polygons:
    draw.polygon(poly, fill=255)
  return np.asarray(img), (scale, bbox), scaled_polygons


def scale_and_shift(polygon, scale, xmin, ymin):
  scaled = []
  for point in polygon:
    xdiff = abs(point[0] - xmin)
    ydiff = abs(point[1] - ymin)
    scaled.append((xdiff * scale, ydiff * scale))
  return scaled


def classify(highway_nodes, nodes, grid):
  ''' Classifies highway nodes whether they are in the forest or on open 
      terrain.
  '''
  def to_idx((x, y)):
    ''' image: (x,y) vs. array: (row,col) with x = col, y = row '''
    return (y, x)
  # classify using the grid
  forestal_highway_nodes = set()
  open_highway_nodes = set()
  for node_id in highway_nodes:
    lon, lat = nodes[node_id]
    if grid.test((lon, lat)):
      forestal_highway_nodes.add(node_id)
    else:
      open_highway_nodes.add(node_id)
  return forestal_highway_nodes, open_highway_nodes


def lcc(nodes, graph, threshold):
  ''' 
  Filters the @nodes such that only those which form a connected component in
  the @graph of size larger than @threshold remain.
  '''
  def get_component(node, nodes, graph):
    ''' Determines the component (set of connected nodes) of @node. '''
    component = set()
    queue = [node]
    while len(queue):
      top = queue.pop()
      component.add(top)
      for adjacent_node in graph[top]:
        if adjacent_node in nodes and adjacent_node not in component:
          queue.append(adjacent_node)
    assert len(component) == len(set(component))
    return component
  node_set = set(nodes)
  remaining = []
  removed = []
  while len(node_set):
    node = node_set.pop()
    component = get_component(node, node_set, graph)
    node_set -= component
    if len(component) >= threshold:
      remaining.extend(component)
    else:
      removed.extend(component)
  assert len(remaining) == len(set(remaining))
  return set(remaining), removed


def select_wep(open_highway_nodes, forestal_highway_nodes, graph):
  ''' Selects nodes as WEP which are outside the forest and point into it. '''
  weps = set()
  for node_id in open_highway_nodes:
    for other_node_id in graph[node_id]:
      if other_node_id in forestal_highway_nodes:
        weps.add(node_id)
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
  else:
    return [p for p in points if grid.test(p) == 0]

def sort_hull(hull, vecs):
  ''' Sorts the points of a convex hull by their angle to the center point. '''
  ps = set()
  for x, y in hull:
    ps.add(x)
    ps.add(y)
  ps = np.array(list(ps))
  center = vecs[ps].mean(axis=0)
  A = vecs[ps] - center
  return vecs[ps[np.argsort(np.arctan2(A[:,1], A[:,0]))]]


def main():
  if len(sys.argv) != 2 or os.path.splitext(sys.argv[1])[1] != '.osm':
    print ''' No osm file specified! '''
    exit(1)
  osmfile = sys.argv[1]
  resx, resy = 10240, 8600

  print 'Reading ways from OSM and creating the graph...'
  node_ids, way_types, digraph = map_way_ids_to_nodes(osmfile)
  forest_delim = way_types['forest_delim']

  print 'Reading nodes from OSM...'
  nodes = read_nodes(osmfile)
  bbox = bounding_box(nodes.values())
  print 'Computing the convex hull...'
  visual_grid = Grid(bbox, mode="RGB")
  points = [list(p) for p in nodes.values()]
  hull = scipy.spatial.qhull.Delaunay(points).convex_hull
  hull = sort_hull(hull, np.array(points))
  visual_grid.fill_polygon(hull, color="#EEEEEE")
  
  print 'Creating forest grid from polygons...'
  # TODO(Jonas): Rework the modularization of the next two methods.
  forest_polygons = \
      [[nodes[id] for id in node_ids[way_id]] for way_id in forest_delim]
  #forest_grid, aspect = compute_forest_grid(forest_polygons, bbox, (resx, resy))
  forest_grid = Grid(bbox)
  for poly in forest_polygons:
    forest_grid.fill_polygon(poly)
  
  print 'Classifying highway nodes...'
  highway_node_ids = \
      set([id for way_id in way_types['highway'] for id in node_ids[way_id]])
  forestal_highway_nodes, open_highway_nodes = \
      classify(highway_node_ids, nodes, forest_grid)

  print 'Restrict forests to large connected components...'
  # turn this off, when fast results are needed
  forestal_highway_nodes, removed = lcc(forestal_highway_nodes, digraph, 100)
  open_highway_nodes.union(removed)

  print 'Select WEPs...'
  weps = select_wep(open_highway_nodes, forestal_highway_nodes, digraph)
  print str(len(weps)) + ' WEPs'

  print '''Creating the population grid...'''
  xmin, ymin = bbox[0]
  xmax, ymax = bbox[1]
  dummy = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
  boundary_polygon = hull
  grid = create_population_grid(boundary_polygon, forest_polygons, 10)

  print 'Visualizing the result...'
  for poly in forest_polygons:
    visual_grid.fill_polygon(poly, color="#00DD00")
  for node_id in weps:
    x, y = visual_grid.transform(nodes[node_id])
    r = 10
    visual_grid.draw.ellipse((x-r,y-r,x+r,y+r), fill="#BB1111")
  for (x,y) in grid:
    (x, y) = visual_grid.transform((x,y))
    r = 30
    visual_grid.draw.ellipse((x-r, y-r, x+r, y+r), fill="#0000FF")
  visual_grid.show()

  print 'Writing output...'
  f = open(os.path.splitext(osmfile)[0] + '.WEPs.out', 'w')
  for p in weps:
    f.write(str(p) + '\n')
  f.close()
  f = open(os.path.splitext(osmfile)[0] + '.forest_nodes.out', 'w')
  for n in forestal_highway_nodes:
    f.write(str(n) + '\n')
  f.close()

if __name__ == '__main__':
  ''' Run this module '''
  main()

