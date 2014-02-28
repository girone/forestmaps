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
from collections import defaultdict


def expand_way_to_edges(way_node_list):
  """ For a list of way nodes, this adds bidirectional arcs between successors.
  """
  edges = []
  size = len(way_node_list)
  for i, j in zip(range(size-1), range(1,size)):
    edges.append((way_node_list[i], way_node_list[j]))
    edges.append((way_node_list[j], way_node_list[i]))
  return edges


def map_way_ids_to_nodes(osmfile):
  """ Creates two mappings and a graph from an osm-file.
      - a mapping {way id -> [list of node ids]} 
      - a mapping {way type -> [list of way ids]}
      - a bidirectional graph as a map {node_id -> set([successors])}
  """
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


def visualize(data):
  ''' Views an image '''
  import matplotlib.pyplot as plt
  plt.figure()
  ax = plt.subplot(111)
  ax.imshow(data)
  plt.show()


def compute_forest_grid(forest_delim, way_nodes, nodes, \
    (resx, resy) = (10240, 8600)):
  ''' Computes a grid (array) distinguishing forest and open ground. '''
  def dimensions(polygons):
    xmax = ymax = float(-sys.maxint)
    xmin = ymin = float(sys.maxint)
    for poly in polygons:
      for point in poly:
        if xmax < point[0]:
          xmax = point[0]
        if xmin > point[0]:
          xmin = point[0]
        if ymax < point[1]:
          ymax = point[1]
        if ymin > point[1]:
          ymin = point[1]
    return [xmin, xmax, ymin, ymax]
  def width_and_height(dimensions):
    assert len(dimensions) == 4
    return (dimensions[1] - dimensions[0]), (dimensions[3] - dimensions[2])
  # compute scale
  [xmin, xmax, ymin, ymax] = dimensions([nodes.values()])
  width, height = width_and_height([xmin, xmax, ymin, ymax])
  resx, resy = 10240, 8600
  scale = min(float(resx/width), float(resy/height))
  # collect polygons
  forest_polygons = []
  for way_id in forest_delim:
    poly = []
    for node_id in way_nodes[way_id]:
      poly.append(nodes[node_id])
    forest_polygons.append(poly)
  scaled_polygons = []
  for poly in forest_polygons:
    # Point tuples contain (lon, lat). Use (minlon, maxlat) as reference point
    # (0,0) of the coordinate system.
    scaled_polygons.append(scale_and_shift(poly, scale, xmin, ymax))
  # fill the grid
  img = Image.new("F", (resx, resy), 0)
  draw = ImageDraw.Draw(img)
  for poly in scaled_polygons:
    draw.polygon(poly, fill=255)
  return np.asarray(img), (scale, xmin, xmax, ymin, ymax), scaled_polygons


def scale_and_shift(polygon, scale, xmin, ymin):
  scaled = []
  for point in polygon:
    xdiff = abs(point[0] - xmin)
    ydiff = abs(point[1] - ymin)
    scaled.append((xdiff * scale, ydiff * scale))
  return scaled


def classify(way_types, way_nodes, nodes, grid, \
    (scale, xmin, xmax, ymin, ymax)):
  ''' TODO(jonas): Document this! '''
  def to_idx((x, y)):
    ''' image: (x,y) vs. array: (row,col) with x = col, y = row '''
    return (y, x)
  # detect highway nodes which are inside the forest
  highway_nodes = set()
  for way_id in way_types['highway']:
    for node_id in way_nodes[way_id]:
      highway_nodes.add(node_id)
  # classify using the grid
  forestal_highway_nodes = set()
  open_highway_nodes = set()
  for node_id in highway_nodes:
    lon, lat = nodes[node_id]
    [(x, y)] = scale_and_shift([(lon, lat)], scale, xmin, ymax)
    if grid[to_idx((x,y))] > 0:
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


def main():
  if len(sys.argv) != 2 or os.path.splitext(sys.argv[1])[1] != '.osm':
    print ''' No osm file specified! '''
    exit(1)
  osmfile = sys.argv[1]
  resx, resy = 10240, 8600

  print 'Reading ways from OSM and creating the graph...'
  way_nodes, way_types, digraph = map_way_ids_to_nodes(osmfile)
  forest_delim = way_types['forest_delim']

  print 'Reading nodes from OSM...'
  nodes = read_nodes(osmfile)
  
  print 'Creating forest grid from polygons...'
  grid, aspect, scaled_polygons = \
      compute_forest_grid(forest_delim, way_nodes, nodes, (resx, resy))
  
  print 'Classifying highway nodes...'
  forestal_highway_nodes, open_highway_nodes = \
      classify(way_types, way_nodes, nodes, grid, aspect)
  # filter forest nodes such that only large connected components form a forest
  print 'Restrict forests to large connected components...'
  forestal_highway_nodes, removed = lcc(forestal_highway_nodes, digraph, 100)
  open_highway_nodes.union(removed)

  print 'Select WEPs...'
  weps = select_wep(open_highway_nodes, forestal_highway_nodes, digraph)
  print str(len(forestal_highway_nodes)) + ' nodes inside the forest'
  print str(len(open_highway_nodes)) + ' nodes on open ground'
  print str(len(weps)) + ' WEPs'

  print 'Visualizing the result...'
  (scale, xmin, xmax, ymin, ymax) = aspect
  img = Image.new("RGB", (resx, resy), 1)
  draw = ImageDraw.Draw(img)
  for poly in scaled_polygons:
    draw.polygon(poly, fill="#00DD00")
  for node_id in weps:
    [(x, y)] = scale_and_shift([nodes[node_id]], scale, xmin, ymax)
    r = 10
    draw.ellipse((x-r,y-r,x+r,y+r), fill="#BB1111")
  visualize(img)

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

