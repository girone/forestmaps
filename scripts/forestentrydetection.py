""" forestentrydetection.py

This script performs a set of tasks:
- classify forest entry points "fep"
- classify arcs which are inside the forest
- generate population grid points

Usage:
python forestentrydetection.py <OSMFile> [<MAXSPEED>] ["ATKIS"]

The optional "ATKIS" flag tells the script that the OSM data was converted from
ATKIS data.

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


def classify(highwayNodes, nodes, grid):
    """Classifies nodes whether they are in the forest or on open terrain."""
    forestHighwayNodes = set()
    openHighwayNodes = set()
    for nodeId in highwayNodes:
        lon, lat = nodes[nodeId]
        if grid.test((lon, lat)):
            forestHighwayNodes.add(nodeId)
        else:
            openHighwayNodes.add(nodeId)
    return forestHighwayNodes, openHighwayNodes


def select_fep(openHighwayNodes, forestHighwayNodes, graph, nodeIndexToOsmId):
    """Selects nodes as FEP which are outside the forest and point into."""
    feps = set()
    inverseIdMap = {value : key for (key, value) in nodeIndexToOsmId.items()}
    for osmId in openHighwayNodes:
        nodeId = nodeIndexToOsmId[osmId]
        for otherNodeId in graph.edges[nodeId].keys():
            otherOsmId = inverseIdMap[otherNodeId]
            if otherOsmId in forestHighwayNodes:
                feps.add(osmId)
                break
    return feps


def create_population_grid(boundaryPolygons, forestPolygons, resolution=None,
                           gridPointDistance=None):
    """Creates the population grid points.

    Points are distributed in a rectangular grid inside the area of the
    boundaryPolygons minus the forestPolygons. The resolution can be specified
    either by the number of points along the smaller side of the bounding box
    of all polygons, or by the distance between every two points.

    """
    bbox = bounding_box(boundaryPolygons)
    gridPoints = create_grid_points(bbox, resolution, gridPointDistance)
    if len(boundaryPolygons) == 1:
        polys = [boundaryPolygons]
    else:
        polys = boundaryPolygons
    gridPoints = filter_point_grid(gridPoints, polys, 'intersect')
    gridPoints = filter_point_grid(gridPoints, forestPolygons, 'difference')
    return gridPoints


def create_grid_points(bbox, resolution, gridPointDistance):
    """Creates a point grid.

    Creates a point grid for a region with @resolution many points along the
    smaller side of @bbox or @gridPointDistance meters between every pair of
    neighboring points.

    """
    assert bool(resolution) != bool(gridPointDistance)  # Specify exactly one!
    w, h = width_and_height(bbox)
    minSideLength = min(w, h)
    xmin, ymin = bbox[0]
    if resolution:
        step = minSideLength / (resolution + 1)
    else:
        if w < 180:
            # we are working on (lat, lon) coordinates, determine step size
            p0, p1 = bbox
            p1p = [p1[0], p0[1]]  # project p1 to same latitude as p0
            step = (gridPointDistance / great_circle_distance(p0, p1p)) * w
            print "step = {0}".format(step)
        else:
            # Gauss-Kruger (east, north) coordinates in meters
            step = gridPointDistance
    gridPoints = []
    for i in range(1, int(math.ceil(h / step))):
        for j in range(1, int(math.ceil(w / step))):
            # (lon,lat) ~ (x,y)
            gridPoints.append((j*step + xmin, i*step + ymin))
    return gridPoints


def filter_point_grid(points, regions, operation='intersect'):
    """Filters @points by applying @operation with @regions using a grid.

    Operations:
      'intersect' : returns @points which lie inside @regions
      'difference': returns @points which do not lie inside @regions

    """
    assert operation in ['intersect', 'difference']
    bbox = bounding_box(points + [p for region in regions for p in region])
    bbox = (bbox[0], [bbox[1][0] * 1.01, bbox[1][1]*1.01])
    grid = Grid(bbox, grid_size=(1024, 860))
    for poly in regions:
        grid.fill_polygon(poly)
    if operation is 'intersect':
        return [p for p in points if grid.test(p) != 0]
    elif operation is 'difference':
        return [p for p in points if grid.test(p) == 0]
    else:
        print "Error: Unsupported operation for 'filter_point_grid'."
        exit(1)


def classify_forest(nodeIds, waysByType, graph, nodes, nodeIndexToOsmId, filenameBase):
    """Creates forest polygons and detects forest entries WE in the data."""
    forestDelim = waysByType['forest_delim']
    bbox = bounding_box(nodes.values())
    print bbox

    print "Computing the convex hull..."
    if visualize:
        visualGrid = Grid(bbox, mode="RGB")
    boundaryFilename = filenameBase + ".boundary.out"
    if os.path.exists(boundaryFilename):
        hull = convexhull.load(boundaryFilename)
    else:
        points = [list(p) for p in nodes.values()]
        hull = convexhull.compute(points)
        convexhull.save(hull, boundaryFilename)
    if visualize:
        visualGrid.fill_polygon(hull, fill="#fadbaa")

    print "Creating forest grid from polygons..."
    forestPolygons = [[nodes[id] for id in nodeIds[wayId]]
                      for wayId in forestDelim]
    forestGrid = Grid(bbox)
    for poly in forestPolygons:
        forestGrid.fill_polygon(poly)

    print "Classifying highway nodes..."
    highwayNodeIds = set([id for wayId in waysByType['highway']
                             for id in nodeIds[wayId]])
    forestHighwayNodes, openHighwayNodes = classify(highwayNodeIds, nodes,
                                                    forestGrid)

    print "Restrict forests to large connected components..."
    # turn this off, when fast results are needed
    nodeIdx = [nodeIndexToOsmId[e] for e in forestHighwayNodes]
    nodeIdx, removed = graph.filter_components(nodeIdx, 500)
    inverseIdMap = {value : key for (key, value) in nodeIndexToOsmId.items()}
    forestHighwayNodes = set([inverseIdMap[e] for e in nodeIdx])
    openHighwayNodes.union(set([inverseIdMap[e] for e in removed]))

    nodeinfo = {nodeIndexToOsmId[osmId] : NodeInfo(osmId, nodes[osmId])
                for osmId in highwayNodeIds}

    print "Select feps..."
    feps = select_fep(openHighwayNodes, forestHighwayNodes, graph, nodeIndexToOsmId)
    print str(len(feps)) + ' feps'

    print "Creating the population grid..."
    xmin, ymin = bbox[0]
    xmax, ymax = bbox[1]
    dummy = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
    boundaryPolygon = hull
    population = create_population_grid(boundaryPolygon, forestPolygons, 10)

    if visualize:
        print "Visualizing the result..."
        for poly in forestPolygons:
            visualGrid.fill_polygon(poly, fill="#00DD00")
        for nodeId in feps:
            (x,y) = visualGrid.transform(nodes[nodeId])
            r = 10
            visualGrid.draw.ellipse((x-r,y-r,x+r,y+r), fill="#BB1111")
        for (x,y) in population:
            (x,y) = visualGrid.transform((x,y))
            r = 30
            visualGrid.draw.ellipse((x-r, y-r, x+r, y+r), fill="#0000FF")
        visualGrid.show()

    # restrict to used nodes
    usedOsmIds = forestHighwayNodes | openHighwayNodes
    nodes = {k:v for k,v in nodes.items() if k in usedOsmIds}
    return feps, forestHighwayNodes, population, nodeinfo


def usage_information():
    return "Usage: python script.py <osm_file> <max_speed>"


def main():
    if len(sys.argv) < 2 or os.path.splitext(sys.argv[1])[1] != '.osm':
        print "No osm file specified!"
        print usage_information()
        exit(1)
    standardOSM = True
    if "ATKIS" in sys.argv:
        standardOSM = False
        sys.argv.remove("ATKIS")
        print " - Using ATKIS interpreter."

    osmfile = sys.argv[1]
    maxspeed = int(sys.argv[2]) if len(sys.argv) > 2 else 130

    print "Reading nodes and ways from OSM and creating the graph..."
    iterpreter = (osm_parse.OSMWayTagInterpreter if standardOSM
                  else osm_parse.ATKISWayTagInterpreter)
    tmp = osm_parse.read_file(osmfile, maxspeed, iterpreter)
    (nodeIds, waysByType, graph, nodes, nodeIndexToOsmId) = tmp

    print (len(graph.nodes), graph.size(),
           sum([len(edges) for edges in graph.edges.values()]))

    filenameBase = os.path.splitext(osmfile)[0]
    tmp = classify_forest(nodeIds, waysByType, graph, nodes, nodeIndexToOsmId,
                          filenameBase)
    (feps, forestHighwayNodes, population, nodeinfo) = tmp

    print "Writing output..."
    filename = filenameBase + "." + str(maxspeed) + "kmh"
    zipped = zip(
    [feps, forestHighwayNodes, population, graph, nodeIndexToOsmId, nodes, nodeinfo],
    ['Feps', 'ForestIds', 'Population', 'Graph', 'IdMap', 'Nodes', 'Nodeinfo'])
    for data, extension in zipped:
        f = open(filename + "." + extension + ".out", 'w')
        pickle.dump(data, f, protocol=2)
        f.close()


if __name__ == '__main__':
    main()

