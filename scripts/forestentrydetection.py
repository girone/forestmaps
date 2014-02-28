""" forestentrydetection.py

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

from arcutil import msg

# find Polygon library on machines without admin rights
libpath = os.path.abspath(
        "/home/sternis/code/forst/external/python2.7/site-packages")
sys.path.append(libpath)

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
    if (len(boundaryPolygons) == 1 or 
        (len(boundaryPolygons) > 1 and len(boundaryPolygons[0]) == 2)):
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
    import convexhull
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


def classify_forest_entries(nodes, edges, nodeFlags):
    """Sets values in @nodeFlags to 2 for forest entries.

    A forest entry is a node which is not inside the forest (flag = 0 so far),
    from which there is an arc to at least one node in the forest (flag = 1).

    """
    for (s, t, _) in edges:
        if nodeFlags[s] == 0 and nodeFlags[t] == 1:
            nodeFlags[s] = 2
    return nodeFlags


def label_nodes_in_polygons_with_value(nodes, polygons, value, labels):
    """Labels nodes with a value if they are inside a polygon.

    Sets the label in @labels of a node to @value, if the node is inside one
    of the polygons.

    """
    from Polygon import Polygon
    # sort nodes and bounding boxes of polygons ascending by latitude
    sortedNodes = sorted([(node, index) for index, node in enumerate(nodes)])
    sortedBoxes = sorted([(bounding_box(poly), index)
                          for index, poly in enumerate(polygons)])
    leftPointer = -1
    lat = -90.
    for box, polygonIndex in sortedBoxes:
        minPolygonLatitude = box[0][0]
        maxPolygonLatitude = box[1][0]
        minPolygonLongitude = box[0][1]
        maxPolygonLongitude = box[1][1]
        while leftPointer < len(sortedNodes) and lat < minPolygonLatitude:
            leftPointer += 1
            lat = sortedNodes[leftPointer][0][0]
        try:
            polygon = Polygon(polygons[polygonIndex])
            nodePointer = leftPointer
            while nodePointer < len(sortedNodes) and lat <= maxPolygonLatitude:
                ((lat, lon, _), index) = sortedNodes[nodePointer]
                if lon >= minPolygonLongitude and lon <= maxPolygonLongitude:
                    if polygon.isInside(lat, lon):
                        labels[index] = value
                nodePointer += 1
            lat = sortedNodes[leftPointer][0][0]
        except:
            e = sys.exc_info()[0]
            print e
            print polygons[polygonIndex]
            print lat, lon



def classify_forest_nodes(nodes, forestPolygons, innerPolygons):
    """Returns a vector of flags distinguishing forest and normal nodes.

    A node is a forest node (flag = 1) if it falls inside a forest polygon.
    A node is a forest node (flag = 3) if it falls inside a glade polygon.

    """
    nodeFlags = [0] * len(nodes)
    # set label 1 for forest nodes, set label 3 for nodes in forest glades
    label_nodes_in_polygons_with_value(nodes, forestPolygons, 1, nodeFlags)
    label_nodes_in_polygons_with_value(nodes, innerPolygons, 3, nodeFlags)
    return nodeFlags


def classify_nodes(nodes, edges, forestPolygons, innerPolygons):
    """Returns a vector of forest flags for the nodes.

    The flag of a node x is
        - 1, if x is inside the forest,
        - 2, if x is an forest entry (it is outside, but has an arc into),
        - 3, if x is in a glade (closed area inside the forest with no forest)
        - 0 otherwise

    """
    nodeFlags = classify_forest_nodes(nodes, forestPolygons, innerPolygons)
    nodeFlags = classify_forest_entries(nodes, edges, nodeFlags)
    return nodeFlags

def restrict_to_forest(poiCategory, flags):
    """Restricts the poiCategory mapping to POIs with non-zero forest flag."""
    return {i:(osm,cat) for i, (osm,cat) in poiCategory.items() if flags[i]}

