"""heatmap_server.py -- Entry point to the heatmap server.

Author: Jonas Sternisko.

"""
import threading
import webbrowser
import BaseHTTPServer
import SimpleHTTPServer
import urlparse
from collections import defaultdict
from heatmap import Heatmap
from timer import Timer


FILE = 'index.html'
PORT = 8080


datasetShortNameToIndex = {"ro" : 0, "ch" : 1, "at" : 2, "de" : 3}


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
                        result = method_call(args, opt=qlist[1:])
                    else:
                        result = method_call(args)
                print " --> This took %s seconds." % t.secs
            except TypeError as e:
                print e
            print "Succeeded!"
        except AttributeError as e:
            print e
            print "Failed!"
        return result

    def heatmapRequest(self, leftBottomRightTop, opt=[]):
        """Answers a request for the heatmap in a certain bounding box."""
        if not leftBottomRightTop or leftBottomRightTop == '':
            bbox = heatmap.leftBottomRightTop
        else:
            bbox = [float(s) for s in leftBottomRightTop.split(",")]
        print "self.heatmapRequest called, argument " + str(leftBottomRightTop)
        heatmapExtract = self.generate_heatmap_extract(bbox)
        print "returning heatmap json for ", len(heatmapExtract), " points"
        jsonp = self.format_heatmap_answer(heatmapExtract, heatmaps[0].maximum)
        return jsonp

    def heatmapRasterRequest(self, leftBottomRightTop, opt=[]):
        """Answers a request for the heatmap in a certain bounding box."""
        opt = dict(opt)
        index = 0 if not opt else datasetShortNameToIndex[opt['dataset']]
        if not leftBottomRightTop or leftBottomRightTop == '':
            bbox = heatmaps[index].leftBottomRightTop
        else:
            bbox = [float(s) for s in leftBottomRightTop.split(",")]
        print "self.heatmapRasterRequest called, argument " + str(leftBottomRightTop)

        heatmapExtract, latStepSize = heatmaps[index].rasterize(bbox)
        print "returning heatmap json for ", len(heatmapExtract), " points"
        jsonp = self.format_heatmap_answer(heatmapExtract,
                                           heatmaps[index].maximum,
                                           radius=latStepSize / 2.)
        return jsonp

    def generate_heatmap_extract(self, bbox):
        """Returns an extract of the heatmap in a certain bounding box."""
        return heatmaps[0].extract(bbox)  # full extact
        #return heatmap.rasterize(bbox)  # discretized

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


def heatmap_setup(graphFileNames, edgeHeatsFileNames):
    heatmaps = []
    for graphFile, heatsFile in zip(graphFileNames, edgeHeatsFileNames):
        print "Constructing heatmap from " + graphFile + "..."
        nodes, edges = [], []
        edgeMap = {}
        with open(graphFile) as f1:
            for line in f1:
                parts = line.strip().split(" ")
                if len(parts) == 4:
                    # node line
                    lat, lon, _, flag = parts
                    nodes.append( (float(lat), float(lon), int(flag)) )
                elif len(parts) == 3:
                    # edge line
                    s, t, cost = parts
                    edges.append( (int(s), int(t)) )
        heats = []
        with open(heatsFile) as f2:
            for line in f2:
                heats.append(float(line.strip()))
        assert len(heats) == len(edges) and "Number of heats and edges must equal."
        ss, tt = zip(*edges)
        edges = zip(ss, tt, heats)
        heatmaps.append(Heatmap(nodes, edges))
    return heatmaps


def main():
    import sys
    if len(sys.argv) < 3 or len(sys.argv) % 2 == 0:
        print "Usage: python heatmap_server.py [<GRAPH_FILE> <EDGE_HEAT_FILE>]"
        print "The argument is a list of alternating graph and heat file names."
        exit(1)
    graphFilenames = []
    edgeHeatFilenames = []
    for i in range(1, len(sys.argv), 2):
        graphFilenames.append(sys.argv[i])
        edgeHeatFilenames.append(sys.argv[i+1])
    print graphFilenames
    print edgeHeatFilenames
    global heatmaps
    heatmaps = heatmap_setup(graphFilenames, edgeHeatFilenames)

    #open_browser()
    start_server()



if __name__ == "__main__":
    main()
