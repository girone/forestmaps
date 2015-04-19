"""This is an Python/ArcPy wrapper to the C++ module.

Important note: Keep all input data in the same directory.
"""
import arcpy
import os
import subprocess
import random
from collections import defaultdict
import atkis_graph
from datetime import datetime
from arcutil import msg, Timer, Progress
import postprocessing as pp

scriptDir = ""
tmpDir = ""

# Some general names
roadFcDump          = "road_feature_class.tmp.txt"
roadGraphFile       = "road_graph.tmp.txt"
forestFcDump        = "forest_road_feature_class.tmp.txt"
forestGraphFile     = "forest_road_graph.tmp.txt"
arcMappingFile      = "arc_to_fid_map.tmp.txt"
entryXYFile         = "forest_entries_xy.tmp.txt"
populationFile      = "populations.tmp.txt"
entryXYRFFile       = "forest_entries_xyrf.tmp.txt"
entryPopularityFile = "forest_entries_popularity.tmp.txt"
entryAndParkingXYRFFile = "forest_entries_plus_parking_xyrf.tmp.txt"
parkingLotsFile     = "parking_lot_positions.tmp.txt"
edgeWeightFile      = "edge_weights.tmp.txt"
ttfFile             = "preferences_TTF.txt"
tifFile             = "preferences_TIF.txt"

kWALKING_SPEED = 4.


def set_paths(argv, env):
    """Sets the paths for temporary files. Deletes the files, if present."""
    global scriptDir
    scriptDir = os.path.split(argv[0])[0] + "\\"
    global roadFcDump, forestFcDump, arcMappingFile
    global roadGraphFile, forestGraphFile, entryXYFile, populationFile
    global entryXYRFFile, entryPopularityFile, edgeWeightFile
    global ttfFile, tifFile, parkingLotsFile, entryAndParkingXYRFFile
    # converted inputs are created at the input data's location
    global tmpDir
    if ".gdb" in env.path:
      tmpDir = env.path
    else:
      tmpDir = env.path + "tmp\\"
    try:
        os.mkdir(tmpDir)
    except OSError:
        assert os.path.exists(tmpDir) and "Could not create the temporary dir."
    roadFcDump          = tmpDir + roadFcDump
    roadGraphFile       = tmpDir + roadGraphFile
    forestFcDump        = tmpDir + forestFcDump
    forestGraphFile     = tmpDir + forestGraphFile
    arcMappingFile      = tmpDir + arcMappingFile
    entryXYFile         = tmpDir + entryXYFile
    ttfFile             = env.paramTxtTimeToForest
    tifFile             = env.paramTxtTimeInForest

    # intermediate files are created at the script's location
    if ".gdb" in env.path:
        populationFile      = tmpDir + "tmp_" + populationFile
        entryXYRFFile       = tmpDir + "tmp_" + entryXYRFFile
        entryPopularityFile = tmpDir + "tmp_" + entryPopularityFile
        edgeWeightFile      = tmpDir + "tmp_" + edgeWeightFile
        parkingLotsFile     = tmpDir + "tmp_" + parkingLotsFile
        entryAndParkingXYRFFile = tmpDir + "tmp_" + entryAndParkingXYRFFile
    else:
        populationFile      = tmpDir + populationFile
        entryXYRFFile       = tmpDir + entryXYRFFile
        entryPopularityFile = tmpDir + entryPopularityFile
        edgeWeightFile      = tmpDir + edgeWeightFile
        parkingLotsFile     = tmpDir + parkingLotsFile
        entryAndParkingXYRFFile = tmpDir + entryAndParkingXYRFFile

    # delete old files
    for path in [roadFcDump, roadGraphFile, forestFcDump, forestGraphFile,
            arcMappingFile, entryXYFile, populationFile, entryXYRFFile,
            entryPopularityFile, edgeWeightFile, parkingLotsFile,
            entryAndParkingXYRFFile]:
        try:
            os.remove(path)
        except:
            pass


def shape_to_polygons(lines, idKeyword):
    """Parses polygons from the points represented by a numpy RecordArray."""
    from itertools import tee, izip
    def pairwise(iterable):
        a,b = tee(iterable)
        next(b, None)
        return izip(a, b)
    polygons = [[tuple(lines[0]['shape'])]]
    inhabitants = [lines[0]['population']]
    for a, b in pairwise(lines):
        if a[idKeyword] != b[idKeyword]:
            polygons.append([])
            inhabitants.append(b['population'])
        polygons[-1].append(tuple(b['shape']))
    assert len(polygons) == len(inhabitants)
    return polygons, inhabitants


def dump_graph_feature_class(dataset, outfile, max_speed):
    """Reads a road feature class, preprocesses and dumps it to a file.

    Preprocesses the feature class such that sequences of way parts are
    represented as one way, maintaining the total distance / speed / cost along
    the way.
    """
    def write_line(f, index, coords, cost, weight):
        """Writes index, coordinates, cost and optional weight to a file."""
        f.write("{0} {1} {2} {3} ".format(index, coords[0], coords[1], cost))
        if weight != -1:
            f.write("{0} ".format(weight))
        f.write("\n")
    def finish_way_segment(f, i, coords1, coordsN, dist, type_, w):
        time = dist / (atkis_graph.determine_speed(type_, max_speed) / 3.6)
        write_line(f, i, coords1, time, w)
        write_line(f, i, coordsN, time, w)
    # In file-geodatabases the id has another name than in plain feature classes
    field_names = [field.name.lower() for field in arcpy.ListFields(dataset)]
    idKeyword = "fid" if "fid" in field_names else "objectid"

    # The forest road graph does not contain a column 'klasse'. In case this is
    # not present, assume the constant speed.
    fields = [idKeyword, "SHAPE@XY"]
    clsKeyword = "klasse"
    if clsKeyword in field_names:
        fields.append(clsKeyword)
    else:
        wayType = 87003  # "Fussgaengerzone" == pedestrian area
    # Read edge weights if present
    weightKeyword = "wert"
    if weightKeyword in field_names:
        fields.append(weightKeyword)
    else:
        weightKeyword = None
    largeRoads = atkis_graph.ATKIS_LARGE_ROAD_CLASSES

    total = int(arcpy.management.GetCount(dataset).getOutput(0))
    count = 0
    p = Progress("Dumping graph from FeatureClass.", total, 100)
    previousIndex = None
    with arcpy.da.SearchCursor(dataset, fields, explode_to_points=True) as rows:
        with open(outfile, "w") as f:
            for row in rows:
                if len(fields) == 3:
                    index, coords, wayType = row
                elif weightKeyword:
                    index, coords, wayType, weight = row
                else:  # len(fields) == 2
                    index, coords = row

                if index == previousIndex:
                    dist += atkis_graph.distance(previousCoords, coords)
                else:  # index != previousIndex
                    # ignore large roads when walking
                    if previousIndex and not (max_speed == kWALKING_SPEED and
                                              previousWayType in largeRoads):
                        finish_way_segment(f, previousIndex,
                                firstCoords, previousCoords, dist, previousWayType,
                                (previousWeight if weightKeyword else -1))
                    dist = 0
                    firstCoords = coords
                    count += 1
                    p.progress(count)
                previousIndex = index
                previousCoords = coords
                previousWayType = wayType
                if weightKeyword:
                    previousWeight = weight
            # finish the last segment
            if previousIndex and not (max_speed == kWALKING_SPEED and
                                      previousWayType in largeRoads):
                if weightKeyword:
                    finish_way_segment(f, previousIndex,
                            firstCoords, previousCoords, dist, previousWayType,
                            (previousWeight if weightKeyword else -1))

    #"""Creates a graph from ATKIS data stored as FeatureClass in a shapefile.

    #Returns the graph, a mapping from coordinates to node index, a mapping from
    #(s,t) arcs to FIDs of the shapefile, and a list documenting the contraction
    #order.
    #"""
    #maxNumNodes = int(arcpy.management.GetCount(dataset).getOutput(0))
    #graph, coord_map, arc_to_fid = \
    #        atkis_graph.create_from_feature_class(dataset, maxNumNodes, max_speed)
    #msg("The graph has %d nodes and %d edges." % (len(graph.edges),
    #        sum([len(edge_set) for edge_set in graph.edges.values()])))

    ##msg("Contracting binary nodes...")
    ##contraction_list = graph.contract_binary_nodes()
    #contraction_list = []
    ##msg("The graph has %d nodes and %d edges." % (len(graph.nodes),
    ##  sum([len(edge_set) for edge_set in graph.edges.values()])))
    ##lcc = graph.lcc()
    ##msg("The largest connected component has %d nodes and %d edges." %
    ##    (len(lcc.nodes), sum([len(e) for e in lcc.edges.values()])))
    #return graph, coord_map, arc_to_fid, contraction_list


def create_population(fc, distance):
    """Creates the population grid."""
    from forestentrydetection import create_population_grid
    fields = [f.name.lower() for f in arcpy.ListFields(fc)]
    idKeyword = "fid" if "fid" in fields else "objectid"
    # workaround for data still not conforming to specification
    populationKey = "first_bevo" if "first_bevo" in fields else None
    if not populationKey:
        populationKey = ("first_bevoelkerung_touris_2011__touris"
                         if "first_bevoelkerung_touris_2011__touris" in fields
                         else None)
    assert populationKey and \
            ("Population field missing in data or it has a wrong name.")

    array = arcpy.da.FeatureClassToNumPyArray(
            fc, [idKeyword, "shape", populationKey], explode_to_points=True)
    if len(array.dtype.names) == 3:
        array.dtype.names = (idKeyword, 'shape', 'population')
    else:
        array.dtype.names = (idKeyword, 'shape')
    polygons, inhabitants = shape_to_polygons(array, idKeyword)
    populations = [create_population_grid(p, [], gridPointDistance=distance)
                   for p in polygons]
    msg("There are %d populations groups." % len(populations))
    return populations, inhabitants


def read_and_dump_parking(parkingShp):
    """Parses and dumps the parking lot locations."""
    fields = [f.name.lower() for f in arcpy.ListFields(parkingShp)]
    idKeyword = "fid" if "fid" in fields else "objectid"
    fieldnames = [idKeyword, "shape", "RANK", "EW"]
    array = arcpy.da.FeatureClassToNumPyArray(
            parkingShp, fieldnames, explode_to_points=True)
    with open(parkingLotsFile, "w") as f:
        for _, coords, rank, pop in array:
            f.write("{0} {1} {2} {3}\n".format(coords[0], coords[1], rank, pop))


def parse_and_dump(env):
    """Parses data from shapefiles, dumps it as plain text.

    Reads the feature class data and dumps the important information of it.
    Returns the mapping from forest graph arcs to shapefile FIDs.
    """
    t = Timer()
    t.start_timing("Dumping road data...")
    dump_graph_feature_class(env.paramShpRoads, roadFcDump, kWALKING_SPEED)
    t.stop_timing()
    msg("Creating graph...")
    call_subprocess(scriptDir + "ReadGraphFromFeatureClassDumpMain.exe",
            roadFcDump + " " + roadGraphFile)

    t.start_timing("Dumping forest road data...")
    dump_graph_feature_class(env.paramShpForestRoads, forestFcDump, kWALKING_SPEED)
    t.stop_timing()
    msg("Creating graph...")
    call_subprocess(scriptDir + "ReadGraphFromFeatureClassDumpMain.exe",
            forestFcDump + " " + forestGraphFile + " " + arcMappingFile)
    with open(arcMappingFile) as f:
        forestArcToFID = {}
        for line in f:
            a, b, fid = line.strip().split(" ")
            forestArcToFID[(int(a), int(b))] = int(fid)

    t.start_timing("Creating population points...")
    population_groups, inhabitants = create_population(env.paramShpSettlements,
                                                       200)
    global tmpDir
    shp = "populations_computed_" + datetime.today().strftime("%Y_%m_%d_%H_%M_%S")
    if ".gdb" not in tmpDir:
        # The suffix ".shp" does not work with geodatabases.
        shp = shp + ".shp"
    shp = arcpy.ValidateTableName(shp, tmpDir)
    msg("Writing populations to '{}' and '{}'.".format(populationFile, tmpDir + shp))
    ptGeoms = []
    populations = []
    sr = arcpy.Describe(env.paramShpRoads).spatialReference
    arcpy.management.CreateFeatureclass(tmpDir, shp, "POINT", spatial_reference=sr)
    with arcpy.da.InsertCursor(tmpDir + shp, ["SHAPE@"]) as cursor:
        with open(populationFile, "w") as f:
            #pt = arcpy.Point()
            for coordinates, inhabs in zip(population_groups, inhabitants):
                avg_population = inhabs / float(len(coordinates))
                for c in coordinates:
                    f.write("{0} {1} {2}\n".format(c[0], c[1], avg_population))
                    # arcpy shape file generation
                    #pt.x, pt.y = c
                    #ptGeoms.append(arcpy.PointGeometry(pt))
                    pt = arcpy.Point(c[0], c[1])
                    cursor.insertRow([pt])
                    populations.append(avg_population)
        #arcpy.management.Append(ptGeoms, tmpDir + shp, "NO_TEST")
    pp.add_column_with_values(tmpDir + shp, "population", populations)
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

    t.start_timing("Parsing parking lot locations...")

    read_and_dump_parking(env.paramShpParking)
    t.stop_timing()

    return forestArcToFID


def call_subprocess(prog, args):
    """Calls an external program and waits for it it finish.

    The return code and output cannot be fetched at the same time. So we
    require a successfull program to have a newline with "OK" at the end
    of its output.
    """
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
                #msg(line.strip())
                pass
            else:
                output += line
            msg(line.strip())
    except subprocess.CalledProcessError as e:
        msg("Error occured.")
        msg(e.output)
        raise
    if "OK" in [s.strip() for s in output.split("\n")[-2:]]:
        returnCode = 0
    else:
        returnCode = 1
    msg("=====================")
    msg("Subprocess has finished {0}.".format(
        "successfully" if returnCode == 0 else "with an error"))
    msg(output)
    timer.stop_timing()
    msg("=====================")
    if returnCode != 0:
        assert False and "Error: Subprocess did not succeed."
        exit(1)
    return output


def add_edgeweight_column(shp, columnName, forestGraphFile, arcToFID,
                          edgeWeightFile):
    """Adds a column to the dataset (shp-file or geoDB) and inserts the values.

    Needs graph file as input to map from arcs to FIDs.
    Args:
        shp: The shapefile containing the forest graph edges.
        columnName: The name for the new column.
        forestGraphFile: The tempfile containing the forest graph.
        arcToFID: The file containing the mapping from arc to forest id.
        edgeWeightFile: The file containing the edge weights.
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
            assert len(components) >= 2
            edges.append((int(components[0]), int(components[1])))
    msg(str(numArcs) + " " + str(len(edges)))
    assert numArcs == len(edges)

    weights = []
    with open(edgeWeightFile) as f:
        for line in f:
            weights.append(float(line.strip()))
    assert len(weights) == len(edges)

    # The undirected edges of the road network are represented by two directed
    # arcs in the graphs. So we get two edge weights wa and wb, meaning "wa
    # people are taking this way in one direction and wb people in the
    # opposite". The sum of both weights is the weight of the undirected edge.
    FIDtoWeight = defaultdict(float)
    for e, w in zip(edges, weights):
        FIDtoWeight[arcToFID[e]] += w

    arcpy.management.DeleteField(shp, columnName)
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
                #msg("{0} not contained".format(row[0]))
                count += 1
    msg(("Warning: {0} of {1} FIDs could not be matched. Probably their road " +
         "type has been ignored.").format(
         count, arcpy.management.GetCount(shp).getOutput(0)))


class AlgorithmEnvironment(object):
    def __init__(self):
        """Reads the parameters from ArcGIS."""
        self.paramShpRoads         = arcpy.GetParameterAsText(1)
        self.paramShpForestRoads   = arcpy.GetParameterAsText(2)
        self.paramShpSettlements   = arcpy.GetParameterAsText(3)
        self.paramShpEntrypoints   = arcpy.GetParameterAsText(4)
        self.paramShpParking       = arcpy.GetParameterAsText(5)

        self.paramTxtTimeToForest  = arcpy.GetParameterAsText(7)
        self.paramPopulationShares = [
            float(arcpy.GetParameterAsText(i).replace(",", "."))
            for i in [8, 9, 10]
        ]
        self.paramOutputName1      = arcpy.GetParameterAsText(11)

        self.paramTxtTimeInForest  = arcpy.GetParameterAsText(13)
        self.paramValAlgorithm     = arcpy.GetParameterAsText(14)
        self.paramOutputName2      = arcpy.GetParameterAsText(15)

        """The path for temporaries and output."""
        self.path = os.path.split(self.paramShpRoads)[0] + "\\"

        if not (self.paramShpRoads and
                self.paramShpForestRoads and
                self.paramShpSettlements and
                self.paramShpEntrypoints and
                self.paramShpParking and
                self.paramTxtTimeToForest and
                self.paramTxtTimeInForest and
                self.paramValAlgorithm and
                self.paramPopulationShares and
                self.paramOutputName1 and
                self.paramOutputName2):
            msg("Error with input.")
            exit(1)

        self.paramValAlgorithm = int(self.paramValAlgorithm)
        assert (sum(self.paramPopulationShares) > 0 and
                sum(self.paramPopulationShares) <= 1)

        msg("Parameters are: \n" +
            ",\n".join([str(e) for e in [self.paramShpRoads,
                        self.paramShpForestRoads,
                        self.paramShpSettlements,
                        self.paramShpEntrypoints,
                        self.paramShpParking,
                        self.paramTxtTimeToForest,
                        self.paramTxtTimeInForest,
                        self.paramValAlgorithm,
                        self.paramPopulationShares,
                        self.paramOutputName1,
                        self.paramOutputName2]]))


def main():
    """Wrapper to the C++ modules. Prepares data from the ArcGIS/ArcPy side.

    1. Read supplied parameters. Open the shape files, dump the content as .txt.
    2. Call the succeeding steps of the C++ module, wait for each to finish.
    3. Load back the resulting arc weights,
    4. If selected, visualize the result in ArcGIS.
    """
    env = AlgorithmEnvironment()
    set_paths(sys.argv, env)
    forestArcToFID = parse_and_dump(env)
    msg("scriptDir = " + scriptDir)
    s = scriptDir

    call_subprocess(scriptDir + "MatchForestEntriesMain.exe",
            roadGraphFile + " " + forestGraphFile + " " + entryXYFile + " " +
            parkingLotsFile + " " + entryAndParkingXYRFFile)

    call_subprocess(scriptDir + "ForestEntryPopularityMain.exe",
            roadGraphFile + " " + entryAndParkingXYRFFile + " " +
            populationFile + " " + ttfFile + " " + parkingLotsFile + " " +
            entryPopularityFile + " " +
            " ".join(str(e) for e in env.paramPopulationShares))

    pp.write_entry_and_parking_population_files(
            entryPopularityFile, env.paramShpEntrypoints, env.paramShpParking,
            env.paramOutputName1)

    # TODO(Jonas): Use gflags for all the binaries to pass parameters more readable.
    tifFileWalk = tifFileBike = tifFileCar = tifFile # TODO(Jonas): Remove this with separate values.
    call_subprocess(scriptDir + "ForestEdgeAttractivenessMain.exe",
            forestGraphFile + " " + entryAndParkingXYRFFile + " " +
            entryPopularityFile + " " +
            tifFileWalk + " " +
            #tifFileBike + " " +
            #tifFileCar + " " +
            str(env.paramValAlgorithm) + " " + edgeWeightFile)

    add_edgeweight_column(env.paramShpForestRoads, env.paramOutputName2,
        forestGraphFile, forestArcToFID, edgeWeightFile)

    msg("Finished!")
    return 0


if __name__ == '__main__':
    main()


