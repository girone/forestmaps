"""This is an Python/ArcPy wrapper to the C++ module.

Important note: Keep all input data in the same directoy. 
"""
import arcpy
import os
import subprocess
import random
import atkis_graph
from arcutil import msg, Timer

scriptDir = ""

# Some general names
roadGraphFile       = "road_graph.tmp.txt"
forestGraphFile     = "forest_road_graph.tmp.txt"
entryXYFile         = "forest_entries_xy.tmp.txt"
populationFile      = "populations.tmp.txt"
entryXYRFFile       = "forest_entries_xyrf.tmp.txt"
entryPopularityFile = "forest_entries_popularity.tmp.txt"
edgeWeightFile      = "edge_weights.tmp.txt"
ttfFile             = "preferences_TTF.txt"
tifFile             = "preferences_TIF.txt"

columnName = "EdgeWeight"

def set_paths(argv, env):
    """  """
    global scriptDir
    scriptDir = os.path.split(argv[0])[0] + "\\"
    msg("############# scriptDir is " + scriptDir)
    global roadGraphFile, forestGraphFile, entryXYFile, populationFile
    global entryXYRFFile, entryPopularityFile, edgeWeightFile
    global ttfFile, tifFile
    # converted inputs are created at the input data's location
    tmpDir = env.path + "\\"
    roadGraphFile       = tmpDir + roadGraphFile
    forestGraphFile     = tmpDir + forestGraphFile
    entryXYFile         = tmpDir + entryXYFile
    ttfFile             = env.paramTxtTimeToForest
    tifFile             = env.paramTxtTimeInForest

    # intermediate files are created at the script's location
    populationFile      = tmpDir + populationFile
    entryXYRFFile       = tmpDir + entryXYRFFile
    entryPopularityFile = tmpDir + entryPopularityFile
    edgeWeightFile      = tmpDir + edgeWeightFile


def shape_to_polygons(lines, idKeyword):
    """Parses polygons from the points represented by a numpy RecordArray."""
    from itertools import tee, izip
    def pairwise(iterable):
        a,b = tee(iterable)
        next(b, None)
        return izip(a, b)
    polygons = [[tuple(lines[0]['shape'])]]
    for a, b in pairwise(lines):
        if a[idKeyword] != b[idKeyword]:
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

    #msg("Contracting binary nodes...")
    #contraction_list = graph.contract_binary_nodes()
    contraction_list = []
    msg("The graph has %d nodes and %d edges." % (len(graph.nodes),
      sum([len(edge_set) for edge_set in graph.edges.values()])))
    #lcc = graph.lcc()
    #msg("The largest connected component has %d nodes and %d edges." %
    #    (len(lcc.nodes), sum([len(e) for e in lcc.edges.values()])))
    return graph, coord_map, arc_to_fid, contraction_list


def create_population(fc, distance):
    """Creates the population grid."""
    from forestentrydetection import create_population_grid
    fields = [f.name.lower() for f in arcpy.ListFields(fc)]
    idKeyword = "fid" if "fid" in fields else "objectid"
    array = arcpy.da.FeatureClassToNumPyArray(fc, 
                                              [idKeyword, "shape"], 
                                              explode_to_points=True)
    polygons = shape_to_polygons(array, idKeyword)
    populations = create_population_grid(polygons, [], gridPointDistance=distance)
    msg("There are %d populations." % len(populations))
    return populations


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


def parse_and_dump(env):
    """Parses data from shapefiles, dumps it as plain text.

    Returns the mapping from forest graph arcs to shapefile FIDs.
    """
    t = Timer()
    t.start_timing("Creating road graph from the data...")
    speed = 5
    read_graph_and_dump_it(env.paramShpRoads, roadGraphFile, speed)
    t.stop_timing()

    t.start_timing("Creating forest road graph from the data...")
    speed = 5
    forestArcToFID = read_graph_and_dump_it(
            env.paramShpForestRoads, forestGraphFile, speed)
    t.stop_timing()

    t.start_timing("Creating population points...")
    population_coords = create_population(env.paramShpSettlements, 200)
    total_population = 230000
    avg_population = total_population / float(len(population_coords))
    with open(populationFile, "w") as f:
        for coord in population_coords:
            f.write("{0} {1} {2}\n".format(coord[0], coord[1], avg_population))
    t.stop_timing()

    t.start_timing("Parsing forest entry locations...")
    fields = [f.name.lower() for f in arcpy.ListFields(env.paramShpEntrypoints)]
    idKeyword = "fid" if "fid" in fields else "objectid"
    array = arcpy.da.FeatureClassToNumPyArray(env.paramShpEntrypoints, 
                                              [idKeyword, "shape"])
    with open(entryXYFile, "w") as f:
        for east, north in array['shape']:
            f.write("{0} {1}\n".format(east, north))
    t.stop_timing()

    return forestArcToFID


def call_subprocess(prog, args):
    timer = Timer()
    timer.start_timing("Calling " + prog + " with arguments '" + args + "'")
    try:
        #output = subprocess.check_output(prog + " " + args, 
        #                                 stderr=subprocess.STDOUT)  # shell=False
        p = subprocess.Popen(prog + " " + args, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        output = ""
        while True:
            line = p.stdout.readline()
            if not line:
                break
            if line.startswith("Progress: "):
                msg(line.strip())
            else:
                msg("Reading data...")
                output += line
    except subprocess.CalledProcessError as e:
        msg("Error occured.")
        msg(e.output)
        raise
    msg("=====================")
    msg("Subprocess has finished, its output was:")
    msg(output)
    timer.stop_timing()
    msg("=====================")
    return output


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
    fields = [f.name.lower() for f in arcpy.ListFields(shp)]
    idKeyword = "fid" if "fid" in fields else "objectid"
    fields = [idKeyword, columnName]
    count = 0
    with arcpy.da.UpdateCursor(shp, fields) as cursor:
        for row in cursor:
            if row[0] in FIDtoWeight:
                row[1] = FIDtoWeight[row[0]]
                cursor.updateRow(row)
            else:
                msg("{0} not contained".format(row[0]))

class AlgorithmEnvironment(object):
    def __init__(self):
        """Reads the parameters from ArcGIS."""
        self.paramShpRoads = arcpy.GetParameterAsText(0)
        self.paramShpForestRoads = arcpy.GetParameterAsText(1)
        self.paramShpEntrypoints = arcpy.GetParameterAsText(2)
        ## TODO(jonas): Generate population nodes from polygons. ##
        #shpPopulationNodes = arcpy.GetParameterAsText(3)
        self.paramShpSettlements = arcpy.GetParameterAsText(3)

        self.paramShpParking = arcpy.GetParameterAsText(4)
        self.paramTxtTimeToForest = arcpy.GetParameterAsText(5)
        self.paramTxtTimeInForest = arcpy.GetParameterAsText(6)
        self.paramValAlgorithm = arcpy.GetParameterAsText(7)
        self.paramValRasterize = arcpy.GetParameterAsText(8)

        """The path for temporaries and output."""
        self.path = os.path.split(self.paramShpRoads)[0] + "\\"

        if not (self.paramShpRoads and
                self.paramShpForestRoads and
                self.paramShpSettlements and
                self.paramShpEntrypoints and
                self.paramTxtTimeToForest and
                self.paramTxtTimeInForest and
                self.paramValAlgorithm and
                self.paramValRasterize):
            msg("Error with input.")
            exit(1)

        self.paramValAlgorithm = int(self.paramValAlgorithm)
        self.paramValRasterize = self.paramValRasterize == "true"
        msg(str(self.paramValAlgorithm) + " " + str(self.paramValRasterize))


def create_raster(env, columnName, rasterPixelSize=20):
    if not arcpy.GetParameterAsText(0) or env.path.endswith(".gdb\\"):
        # Reason: We are not working in ArcMap, or
        # raster file handling in geodatabases is one hack of inconvenience...
        msg("NOTE: I am not creating any raster from the data. Please do that"+
            " yourself.")
        return
    t = Timer()
    t.start_timing("Rasterizing the forest roads...")
    blub = str(random.randint(0,999))
    raster = env.path + "out_raster_" + blub + ".tif"
    # NOTE(Jonas): If the code below raises any error, you should close ArcMap,
    # delete any file named "raster_*.*" and restart the application.
    if os.path.exists(raster):
        arcpy.management.Delete(raster)
    msg(raster)
    arcpy.conversion.PolylineToRaster(
            env.paramShpForestRoads,
            columnName,
            raster,
            cellsize=rasterPixelSize)
    t.stop_timing()
    layerFile = env.path + "raster_" + blub + ".lyr"
    layer = arcpy.management.MakeRasterLayer(raster, "raster_layer" + blub)
    try:
        arcpy.management.SaveToLayerFile(layer, layerFile)
    except:
        raise
    msg(layerFile)
    layer = arcpy.mapping.Layer(layerFile)
    # layer.transparency = 40
    mxd = arcpy.mapping.MapDocument("CURRENT")
    dataframe = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    arcpy.mapping.AddLayer(dataframe, layer, "TOP")


def main():
    """Prepares data from the ArcGIS/ArcPy side.

    1. Read supplied parameters. Open the shapefiles, dump the content as .txt.
    2. Call the succeeding steps of the C++ module, wait for each to finish.
    3. Load back the resuling arc weights,
    4. If selected, visualize the result in ArcGIS.
    """
    env = AlgorithmEnvironment()
    set_paths(sys.argv, env)
    forestArcToFID = parse_and_dump(env)
    msg("scriptDir = " + scriptDir)
    s = scriptDir
    call_subprocess(scriptDir + "MatchForestEntriesMain.exe",
            roadGraphFile + " " + forestGraphFile + " " + entryXYFile + " " +
            entryXYRFFile)
    call_subprocess(scriptDir + "ForestEntryPopularityMain.exe",
            roadGraphFile + " " + entryXYRFFile + " " + 
            populationFile + " " + ttfFile + " " + entryPopularityFile)
    call_subprocess(scriptDir + "ForestEdgeAttractivenessMain.exe",
            forestGraphFile + " " + entryXYRFFile + " " + 
            entryPopularityFile + " " + tifFile + 
            " " + str(env.paramValAlgorithm) + " " + edgeWeightFile)

    add_column(env.paramShpForestRoads, columnName, forestGraphFile, 
            forestArcToFID, edgeWeightFile)

    if env.paramValRasterize:
        create_raster(env, columnName)

    msg("Finished!")
    return 0


if __name__ == '__main__':
    main()
