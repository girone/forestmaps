"""This is an Python/ArcPy wrapper to the C++ module.

"""
import arcpy
import os
import subprocess

# Add library path to the non-arcpy modules.
libpath = os.path.abspath(os.path.split(sys.argv[0])[0] + "\\..\\")
sys.path.append(libpath)
import atkis_graph
from util import msg, Timer


roadGraphFile = "road_graph.txt"
forestGraphFile = "forest_road_graph.txt"
entryXYFile = "forest_entries_xy.txt"
populationFile = "populations.txt"
entryXYRFFile = "forest_entries_xyrf.txt"
entryPopularityFile = "forest_entries_popularity.txt"
edgeWeightFile = "edge_weights.txt"


def shape_to_polygons(lines):
    """Parses polygons from the points represented by a numpy RecordArray

    created by arcpy.FeatureClassToNumPyArray(explode_to_points=True).
    """
    from itertools import tee, izip
    def pairwise(iterable):
        a,b = tee(iterable)
        next(b, None)
        return izip(a, b)
    polygons = [[tuple(lines[0]['shape'])]]
    for a, b in pairwise(lines):
        if a['fid'] != b['fid']:
            polygons.append([])
        polygons[-1].append(tuple(b['shape']))
    return polygons

def create_road_graph(dataset, max_speed):
    """Creates a graph from ATKIS data stored as FeatureClass in a shapefile.

    Returns the graph, a mapping from coordinates to node index, a mapping from
    (s,t) arcs to FIDs of the shapefile, and a list documenting the contraction
    order.

    """
    graph, coord_map, arc_to_fid = \
            atkis_graph.create_from_feature_class(dataset, max_speed)
    msg("The graph has %d nodes and %d edges." % (len(graph.nodes),
      sum([len(edge_set) for edge_set in graph.edges.values()])))

    msg("Contracting binary nodes...")
    #contraction_list = graph.contract_binary_nodes()
    contraction_list = []
    msg("The graph has %d nodes and %d edges." % (len(graph.nodes),
      sum([len(edge_set) for edge_set in graph.edges.values()])))
    #lcc = graph.lcc()
    #msg("The largest connected component has %d nodes and %d edges." %
    #    (len(lcc.nodes), sum([len(e) for e in lcc.edges.values()])))
    return graph, coord_map, arc_to_fid, contraction_list


def create_populations_from_settlement_fc(lines, point_distance):
    """ Creates population points from the 'Ortslage' feature class.

    The point_distance parameter influences the density of the grid.
    """
    polygons = shape_to_polygons(lines)
    from forestentrydetection import create_population_grid
    return create_population_grid(polygons, [], gridPointDistance=point_distance)


def create_population(settlement_dataset,
                      point_distance):
    """Creates the population grid."""
    arr2 = arcpy.da.FeatureClassToNumPyArray(settlement_dataset, ["fid", "shape"],
                                             explode_to_points=True)
    population_coords = create_populations_from_settlement_fc(
        arr2, point_distance)
    msg("There are %d populations." % len(population_coords))
    return population_coords


def read_graph_and_dump_it(shpFile, filename, maxSpeed=5):
    """Creates a graph from polylines and stores it in a simple file format."""
    res = create_road_graph(shpFile, max_speed=maxSpeed)
    graph, coordinateMap, arcToFID, contractionList = res
    nodeToCoords = {node : coords for coords, node in coordinateMap.items()}
    with open(filename, "w") as f:
        f.write("{0}\n".format(graph.size()))
        f.write("{0}\n".format(
                sum([len(edges) for edges in graph.edges.values()])))
        for node in graph.nodes:
            x, y = nodeToCoords[node]
            f.write("{0} {1}\n".format(x, y))
        for source, targets in graph.edges.items():
            for target, edge in targets.items():
                f.write("{0} {1} {2}\n".format(source, target, edge.cost))
    return arcToFID


def parse_and_dump():
    """Parses data from shapefiles, dumps it as plain text.

    Returns the mapping from forest graph arcs to shapefile FIDs.

    """
    shpRoads = arcpy.GetParameterAsText(0)
    shpForestRoads = arcpy.GetParameterAsText(1)
    shpEntryLocations = arcpy.GetParameterAsText(2)
    ## TODO(jonas): Generate population nodes from polygons. ##
    #shpPopulationNodes = arcpy.GetParameterAsText(3)
    shpSettlements = arcpy.GetParameterAsText(3)

    if not (shpRoads and shpForestRoads and shpSettlements and
            shpEntryLocations):
        msg("Error with input.")
        exit(1)
    path = os.path.split(shpRoads)[0] + "\\"

    t = Timer()
    t.start_timing("Creating road graph from the data...")
    read_graph_and_dump_it(shpRoads, roadGraphFile)
    t.stop_timing()

    t.start_timing("Creating forest road graph from the data...")
    forestArcToFID = read_graph_and_dump_it(shpForestRoads, forestGraphFile)
    t.stop_timing()

    t.start_timing("Creating population points...")
    population_coords = create_population(shpSettlements,
                                          point_distance=200)
    total_population = 230000
    avg_population = total_population / float(len(population_coords))
    with open(populationFile, "w") as f:
        for coord in population_coords:
            f.write("{0} {1} {2}\n".format(coord[0], coord[1], avg_population))
    t.stop_timing()

    t.start_timing("Parsing forest entry locations...")
    arr4 = arcpy.da.FeatureClassToNumPyArray(shpEntryLocations, ["fid", "shape"])
    with open(entryXYFile, "w") as f:
        for east, north in arr4['shape']:
            f.write("{0} {1}\n".format(east, north))
    t.stop_timing()

    return forestArcToFID


def call_subprocess(prog, args):
    msg("Calling " + prog + " with arguments '" + args + "'")
    try:
        output = subprocess.check_output(prog + " " + args)  # shell=False
    except CalledProcessError as e:
        msg(e.output)
        raise
    msg("Subprocess has finished, its output was:")
    msg(output)
    return output


def add_column(shp, values):

    assert arcpy.management.GetCount(shp).getOutput(0) == len(values)


def add_column(shp, columnName, forestGraphFile, arcToFID, edgeWeightFile):
    """Adds a column to the dataset in shp and inserts the values.

    Needs graph file as input to map from arcs to FIDs.

    """
    edges = []
    with open(forestGraphFile) as f:
        numNodes = int(f.readline().strip())
        numArcs = int(f.readline().strip())
        for line in f:
            numNodes -= 1
            if numNodes == 0:
                break
        for line in f:
            components = line.strip().split(" ")
            edges.append((float(components[0]), float(components[1])))
    msg(str(numArcs) + " " + str(len(edges)))
    assert numArcs == len(edges)

    weights = []
    with open(edgeWeightFile) as f:
        for line in f:
            weights.append(float(line.strip()))
    assert len(weights) == len(edges)

    FIDtoWeight = {arcToFID[e] : w for e, w in zip(edges, weights)}

    arcpy.management.AddField(shp, columnName, "FLOAT")
    fields = ["fid", columnName]
    count = 0
    with arcpy.da.UpdateCursor(shp, fields) as cursor:
        for row in cursor:
            if row[0] in FIDtoWeight:
                row[1] = FIDtoWeight[row[0]]
                cursor.updateRow(row)
            else:
                msg("{0} not contained".format(row[0]))


def main():
    """Prepares data from the ArcGIS/ArcPy side.

    1. Parse supplied parameters. Open the shapefiles, dump the content as .txt.
    2. Call the succeeding steps of the C++ module, wait for each to finish.
    3. Load back the resuling arc weights, visualize them in ArcGIS.

    """
    forestArcToFID = parse_and_dump()

    call_subprocess("MatchForestEntriesMain.exe",
            roadGraphFile + " " + forestGraphFile + " " + entryXYFile)
    call_subprocess("ForestEntryPopularityMain.exe",
            roadGraphFile + " " + entryXYRFFile + " " + populationFile)
    call_subprocess("ForestEdgeAttractivenessMain.exe",
            forestGraphFile + " " + entryXYRFFile + " " + entryPopularityFile)

    forestShpFile = arcpy.GetParameterAsText(1)
    add_column(forestShpFile, "BlaBlub", forestGraphFile, forestArcToFID,
            edgeWeightFile)

    msg("Finished!")
    return 0


if __name__ == '__main__':
    #arcpy.management.Delete("in_memory")
    main()
