"""heatmap_server.py -- Entry point to the heatmap server.

Author: Jonas Sternisko.

"""
import threading, webbrowser, BaseHTTPServer, SimpleHTTPServer
import pickle, gc, urlparse, math
import numpy as np
from collections import defaultdict
from heatmap import Heatmap, HeatmapFactory, compute_longitude_stepsize
from timer import Timer


FILE = 'index.html'
PORT = 8080


shortNameToIndex = {"ro" : 0, "ch" : 1, "at" : 2, "de" : 3}

gMinZoomLevel = 5
gMaxZoomLevel = 14


def normalize_zoomlvl(lvl):
    """For a given zoomlevel this returns the index in the layer index."""
    if lvl < gMinZoomLevel:
        return gMinZoomLevel
    elif lvl > gMaxZoomLevel:
        return gMaxZoomLevel
    else:
        return lvl - gMinZoomLevel


def dd():  # module-level definition required for pickle
    return defaultdict(Heatmap)


class HeatmapDatabase(object):
    """Stores the heatmap data."""
    def __init__(self, path=None):
        """Constructor."""
        self.rasterHeatmaps = defaultdict(dd)
        self.initialized = False

    def initialize_all_rasters(self, levelsAndBBoxes, localYResolution=48):
        """Computes the rasters for each dataset."""
        num = len(graphFilenames)
        for i in sorted(shortNameToIndex.values())[:num]:
            self.initialize_dataset_rasters(i, levelsAndBBoxes, localYResolution)
        self.initialized = True
        initials = [k for v,k in
                    sorted([(v,k) for k,v in shortNameToIndex.items()])][:num]
        self.save_heatmap_rasters("+".join(initials) + ".db.pickled")

    def load_heatmap_rasters(self, path):
        print "Loading db from path ", path
        global gLocalBounds
        global gLeftBottomRightTop
        with open(path) as f:
            [self.rasterHeatmaps, gLeftBottomRightTop, gLocalBounds] = pickle.load(f)
        self.initialized = True
        print " --> Done."

    def save_heatmap_rasters(self, filename):
        filename = "data/" + filename
        print "Saving db to ", filename
        with open(filename, 'w') as f:
            pickle.dump([self.rasterHeatmaps, gLeftBottomRightTop, gLocalBounds],
                        f)

    def initialize_dataset_rasters(self, i, levelsAndBBoxes, localYResolution):
        """Computes the raster for each zoomlevel."""
        # parse the original graph data, map edge weights to nodes
        heatmap = heatmap_setup([graphFilenames[i]], [edgeHeatFilenames[i]])[0]
        gc.collect()

        # create the raster for each zoom level
        for index, levelAndBounds in enumerate(reversed(levelsAndBBoxes)):
            if index > 0:
                hm = hmRaster  # recursively build from previous level
            else:
                hm = heatmap
            (level, minLon, minLat, maxLon, maxLat) = levelAndBounds
            print "Creating the raster for level", level
            # compute step size from local scope (js map at zoom level)
            bbox = minLon, minLat, maxLon, maxLat
            latFraction = (maxLat - minLat) / (localYResolution - 1.)
            lonFraction = compute_longitude_stepsize(bbox, latFraction)

            # transform to global scope
            lonStart, latStart, lonEnd, latEnd = heatmap.leftBottomRightTop
            lonStart = lonStart - 0.5 * lonFraction
            latStart = latStart - 0.5 * latFraction
            lonEnd = lonEnd + 0.5 * lonFraction
            latEnd = latEnd + 0.5 * latFraction

            globalYResolution = math.ceil((latEnd - latStart) / latFraction)
            globalXResolution = math.ceil((lonEnd - lonStart) / lonFraction)
            rasterData, latFrac = hm.rasterize(heatmap.leftBottomRightTop,
                                               (globalXResolution,
                                                globalYResolution))
            hmRaster = HeatmapFactory.construct_from_nparray(rasterData)
            hmRaster.latFraction = latFrac
            self.rasterHeatmaps[i][normalize_zoomlvl(level)] = hmRaster

gHeatmapDB = HeatmapDatabase()

class HeatmapRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """A handler that processes requests from the heatmap web UI."""

    #def do_POST(self):
        #"""Handle a post request by returning the square of the number."""
        #length = int(self.headers.getheader('content-length'))
        #data_string = self.rfile.read(length)
        #try:
            #result = int(data_string) ** 2
        #except:
            #result = 'error'
        #self.wfile.write(result)

    def do_GET(self):
        """Handles a GET request."""
        parsed_path = urlparse.urlparse(self.path)
        message = ""
        if parsed_path.query == "":
            # Site lookup, view index.html
            f = self.send_head()
            if f:
                self.copyfile(f, self.wfile)
                f.close()
                return
        else:
            message = self.process_query(parsed_path.query)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message)
        return

    def process_query(self, query):
        """Processes a query, returns False if the query is unknown."""
        def parse_query(query):
            """Returns [(command, parameter)] list."""
            qlist = []
            splitted = query.split("&")
            for entry in splitted:
                cmd, arg = entry.split("=")
                qlist.append((cmd, arg))
            return qlist
        qlist = parse_query(query)
        print "Trying to execute query '" + str(qlist) + "'"
        result = None
        q, args = qlist[0]
        try:
            method_call = getattr(self, q)
            try:
                with Timer() as t:
                    if len(qlist) > 1:
                        print qlist[1:]
                        result = method_call(args, opt=qlist[1:])
                    else:
                        result = method_call(args)
                print " --> This took %s seconds." % t.secs
            except TypeError as e:
                print "ERROR:", e
            print "Success."
        except AttributeError as e:
            print e
            print "Failed!"
        return result

    def datasetBoundsRequest(self, dataset, opt=[]):
        """Requests the bounds of a dataset. Returns JSON."""
        print "datasetBoundsRequest() called with dataset=", dataset
        bounds = gLocalBounds[shortNameToIndex[dataset]]
        (minLon, minLat, maxLon, maxLat) = bounds
        return ('request_dataset_bounds_callback({\n' +
                '   "minLon" : ' + str(minLon) + ',\n' +
                '   "minLat" : ' + str(minLat) + ',\n' +
                '   "maxLon" : ' + str(maxLon) + ',\n' +
                '   "maxLat" : ' + str(maxLat) + ' \n' +
                '});')

    def initializationRequest(self, zoomLevelAndBBoxesString, opt=[]):
        """Requests the raster initialization for the specified dataset.

        This function gets a list of <zoomlevel, bbox>. For each zoomlevel, the
        second argument represents the minimum bounding box of the Javascript
        map widget on the data.

        """
        split = zoomLevelAndBBoxesString.split(",")
        print "SERVER: initializationRequest() called with argument", split
        levelsAndBBoxes = []
        for i in range(len(split) / 5):
            levelsAndBBoxes.append((int(split[5*i]),
                                    float(split[5*i+1]),
                                    float(split[5*i+2]),
                                    float(split[5*i+3]),
                                    float(split[5*i+4])))
        gHeatmapDB.initialize_all_rasters(levelsAndBBoxes)
        return "initialization_callback()"

    def heatmapRequest(self, leftBottomRightTop, opt=[]):
        """Answers a request for the heatmap in a certain bounding box."""
        if not leftBottomRightTop or leftBottomRightTop == '':
            bbox = heatmap.leftBottomRightTop
        else:
            bbox = [float(s) for s in leftBottomRightTop.split(",")]
        print "self.heatmapRequest called, argument " + str(leftBottomRightTop)
        heatmapExtract = self.generate_heatmap_extract(bbox)
        jsonp = self.format_heatmap_answer(heatmapExtract, heatmaps[0].maximum)
        return jsonp

    def format_initialize_request(self):
        minLon, minLat, maxLon, maxLat = gLeftBottomRightTop
        jsonp = ("heatmap_request_callback_initialize_me({{\r\n" +
                 "    minimumLongitude: {0},\r\n" +
                 "    minimumLatitude: {1},\r\n" +
                 "    maximumLongitude: {2},\r\n" +
                 "    maximumLatitude: {3}\r\n" +
                 "}})").format(minLon, minLat, maxLon, maxLat)
        return jsonp

    def heatmapRasterRequest(self, leftBottomRightTop, opt=[]):
        """Answers a request for the heatmap at zoomlevel in a certain range."""
        if not gHeatmapDB.initialized:
            print "Initializing the server: Requesting initialization from user."
            return self.format_initialize_request()
        opt = dict(opt)
        index = 0 if not opt else shortNameToIndex[opt['dataset']]
        zoomlvl = int(opt["zoomlevel"]) if "zoomlevel" in opt else 14
        lvl = normalize_zoomlvl(zoomlvl)
        print "Returning data at zoomindex: ", zoomlevel
        hm = gHeatmapDB.rasterHeatmaps[index][lvl]

        if not leftBottomRightTop or leftBottomRightTop == '':
            bbox = hm.leftBottomRightTop
        else:
            bbox = [float(s) for s in leftBottomRightTop.split(",")]
        heatmapExtract, latStepSize = hm.extract(bbox)
        jsonp = self.format_heatmap_answer(heatmapExtract,
                                           hm.maximum,
                                           radius=latStepSize / 2.)
        return jsonp

    def generate_heatmap_extract(self, bbox):
        """Returns an extract of the heatmap in a certain bounding box."""
        return heatmaps[0].extract(bbox)  # full extact

    def format_heatmap_answer(self, heatmapData, maximum, radius=None):
        """Formats a heatmap request answer as JSONP."""
        jsonp  = "heatmap_request_callback({\r\n"
        jsonp += "    datacount: {0},\r\n".format(len(heatmapData))
        jsonp += "    max : {0},\r\n".format(maximum)
        if radius:
            jsonp += "    radius : {0},\r\n".format(radius)
        jsonp += "    datapoints: ["
        points = []
        for lat, lon, count in heatmapData:
            points.append("{0:.7f},{1:.7f},{2:.1f}".format(lat, lon, count))
        jsonp += ",".join(points)
        jsonp +=                  "]\r\n"
        jsonp += "})"
        return jsonp


def open_browser():
    """Start a browser after waiting for half a second."""
    def _open_browser():
        webbrowser.open('http://localhost:%s/%s' % (PORT, FILE))
        pass
    thread = threading.Timer(0.5, _open_browser)
    thread.start()


def start_server():
    """Start the server."""
    server_address = ("", PORT)
    server = BaseHTTPServer.HTTPServer(server_address, HeatmapRequestHandler)
    print "Server starts running now..."
    server.serve_forever()


def read_weights(filename):
    weights = []
    flag = True
    with open(filename) as f:
        for line in f:
            weights.append(float(line.strip()))
    return weights


def read_graph_file(filename):
    """Reads a graph file and returns nodes and edges."""
    nodes, edges = [], []
    with open(filename) as f1:
        numNodes = int(f1.readline())
        numEdges = int(f1.readline())
        nodes = np.zeros([numNodes,3], dtype="float32")
        edges = np.zeros([numEdges,2], dtype="int32")
        nodeCount = 0
        edgeCount = 0
        for line in f1:
            parts = line.split(" ")
            if len(parts) == 4:
                # node line
                nodes[nodeCount] = (float(parts[0]), float(parts[1]), int(parts[3])) 
                nodeCount += 1
            elif len(parts) == 3:
                # edge line
                edges[edgeCount] = (int(parts[0]), int(parts[1])) 
                edgeCount += 1
    return nodes, edges


def heatmap_setup(graphFileNames, edgeHeatsFileNames):
    heatmaps = []
    for graphFile, heatsFile in zip(graphFileNames, edgeHeatsFileNames):
        print "Reading graph from " + graphFile + "..."
        nodes, edges = read_graph_file(graphFile)
        heats = []
        print "Reading heats from " + heatsFile + "..."
        with open(heatsFile) as f2:
            heats = np.zeros([edges.shape[0], 1], dtype="float32")
            heatCount = 0
            for line in f2:
                heats[heatCount] = float(line)
                heatCount += 1
        print "Constructing heatmap from data..."
        heatmaps.append(HeatmapFactory.construct_from_graph(nodes, edges, heats))
    return heatmaps


def determine_bounds(graphFileNames):
    """Determines left, bottom, right and top bounds of all datasets.

    Returns the global bounds and a list of the bounds for each dataset.

    """
    print "Determining data set bounds..."
    gminLon = 180
    gminLat = 90
    gmaxLon = -180
    gmaxLat = -90
    localBounds = []
    for f in graphFileNames:
        print f, "..."
        minLon = 180
        minLat = 90
        maxLon = -180
        maxLat = -90
        with open(f) as f1:
            for line in f1:
                parts = line.strip().split(" ")
                if len(parts) == 4:  # node line
                    slat, slon, _, _ = parts
                    lat = float(slat)
                    lon = float(slon)
                    minLat = min(minLat, lat)
                    minLon = min(minLon, lon)
                    maxLat = max(maxLat, lat)
                    maxLon = max(maxLon, lon)
                elif len(parts) == 3:  # first edge line
                    break
            print " --> Bounds are ", minLon, minLat, maxLon, maxLat
            gminLat = min(gminLat, minLat)
            gminLon = min(gminLon, minLon)
            gmaxLat = max(gmaxLat, maxLat)
            gmaxLon = max(gmaxLon, maxLon)
            localBounds.append((minLon, minLat, maxLon, maxLat))
    print "Global dataset bounds are ", gminLon, gminLat, gmaxLon, gmaxLat
    return (gminLon, gminLat, gmaxLon, gmaxLat), localBounds


def main():
    import sys
    if ((len(sys.argv) < 3 or len(sys.argv) % 2 == 0)
        and not len(sys.argv) == 2 and sys.argv[1].contains("db.pickled")):
        print "Usage: python heatmap_server.py [<GRAPH_FILE> <EDGE_HEAT_FILE>] || [<HEATMAP PICKLED>]"
        print "The argument is a list of alternating graph and heat file names."
        print "  -- OR -- "
        print "The argument is a path to a pickled heatmap db."
        exit(1)
    global graphFilenames
    global edgeHeatFilenames
    global gLeftBottomRightTop
    global gLocalBounds
    global gHeatmapDB
    if len(sys.argv) > 2:
        graphFilenames = []
        edgeHeatFilenames = []
        for i in range(1, len(sys.argv), 2):
            graphFilenames.append(sys.argv[i])
            edgeHeatFilenames.append(sys.argv[i+1])
        gLeftBottomRightTop, gLocalBounds = determine_bounds(graphFilenames)
    else:
        path = sys.argv[1]
        gHeatmapDB.load_heatmap_rasters(path)



    #open_browser()
    start_server()



if __name__ == "__main__":
    main()
