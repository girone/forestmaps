import threading
import webbrowser
import BaseHTTPServer
import SimpleHTTPServer
import urlparse

FILE = 'index.html'
PORT = 8080


class TestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """ DOCU """

    def do_POST(self):
        """Handle a post request by returning the square of the number."""
        length = int(self.headers.getheader('content-length'))
        data_string = self.rfile.read(length)
        try:
            result = int(data_string) ** 2
        except:
            result = 'error'
        self.wfile.write(result)

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
            "Returns command, parameter."
            splitted = query.split("&")[0].split("=")
            print splitted
            if len(splitted) > 1:
                return splitted[0], splitted[1]
            else:
                return splitted[0], None
        q, args = parse_query(query)
        print "Trying to execute query '" + q + "' with params " + str(args)
        result = None
        try:
            method_call = getattr(self, q)
            try:
                result = method_call(args)
            except TypeError as e:
                print e
            print "Succeeded!"
        except AttributeError as e:
            print e
            print "Failed!"
        return result

    def heatmapRequest(self, leftBottomRightTop):
        """Answers a request for the heatmap in a certain bounding box."""
        if not leftBottomRightTop or leftBottomRightTop == '':
            bbox = heatmap.leftBottomRightTop
        else:
            bbox = [float(s) for s in leftBottomRightTop.split(",")]
        print "self.heatmapRequest called, argument " + str(leftBottomRightTop)
        heatmapExtract = self.generate_heatmap_extract(bbox)
        print "returning heatmap json for ", len(heatmapExtract), " points"
        jsonp = self.format_heatmap_answer(heatmapExtract)
        return jsonp

    def generate_heatmap_extract(self, bbox):
        """Returns an extract of the heatmap in a certain bounding box."""
        return heatmap.extract(bbox)  # global variable

    def format_heatmap_answer(self, heatmapData):
        """Formats a heatmap request answer as JSONP."""
        jsonp  = "heatmap_request_callback({\r\n"
        jsonp += "    datacount: {0},\r\n".format(len(heatmapData))
        jsonp += "    datapoints: \""
        for lat, lon, count in heatmapData:
            jsonp += "{0:.7f},{1:.7f},{2:.1f},".format(lat, lon, count)
        jsonp +=                  "\"\r\n"
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
    server = BaseHTTPServer.HTTPServer(server_address, TestHandler)
    server.serve_forever()


class Heatmap(object):
    def __init__(self, nodes, edges, weights=None):
        """Constructs the heatmap.

        The heatmap will be a set of coordinates and labels, one for each node.

        """
        nodes = [(lat, lon) for (lat, lon, _) in nodes]
        lat, lon = zip(*nodes)
        self.leftBottomRightTop = [min(lon), min(lat), max(lon), max(lat)]
        assert len(edges) == len(weights)
        if weights:
            #edgeToWeigth = {(s,t) : w for (s,t,_),w in zip(edges, weights)}
            edges = [(s, t, w) for (s, t, _), w in zip(edges, weights)]
        else:
            # remove duplicate edges caused by bidirectionality of the graph
            tmp = set([])
            for (s, t, labels) in edges:
                if s < t:
                    tmp.add((s, t, labels[0]))
                else:
                    tmp.add((t, s, labels[0]))
            edges = list(tmp)
        #if weights:
            #relabeledEdges = [(s, t, edgeToWeigth[(s,t)] + edgeToWeigth[(t,s)])
                              #for (s, t, _) in edges]
            #edges = relabeledEdges
        # Map weights to nodes
        heat = [0.] * len(nodes)
        for (s, t, cost) in edges:
            count = float(cost)
            for nodeIndex in [s, t]:
                heat[nodeIndex] += count
        self.maximum = max(heat)
        self.heatmap = sorted(zip(lat, lon, heat))  # sort by latitude

    def extract(self, bbox):
        """Returns the part of the heat map data inside the bounding box."""
        minLon, minLat, maxLon, maxLat = bbox
        if [minLon, minLat, maxLon, maxLat] == self.leftBottomRightTop:
            return self.heatmap
        else:
            filtered = []
            i = 0
            while i < len(self.heatmap) and self.heatmap[i][0] < minLat:
                i += 1
            while i < len(self.heatmap) and self.heatmap[i][0] <= maxLat:
                lat, lon, heat = self.heatmap[i]
                if lon >= minLon and lon <= maxLon:
                    filtered.append((lat, lon, heat))
                i += 1
            return filtered


def read_weights(filename):
    weights = []
    flag = True
    with open(filename) as f:
        for line in f:
            weights.append(float(line.strip()))
            print weights[-1]
    return weights


def main():
    import sys, pickle
    if len(sys.argv) < 3:
        print "Usage: python name.py <nodes.pickle> <edges.pickle> [<weight>]"
        print "       When called without the optional edge weight file,"
        print "       a dummy weight will be computed."
        exit(1)

    nodes, edges = [], []
    with open(sys.argv[1]) as f:
        nodes = pickle.load(f)
    with open(sys.argv[2]) as f:
        edges = pickle.load(f)

    global heatmap

    if len(sys.argv) > 3:
        print "###########LOADING WEIGHTS##############"
        weights = read_weights(sys.argv[3])
        heatmap = Heatmap(nodes, edges, weights)
    else:
        heatmap = Heatmap(nodes, edges)

    open_browser()
    start_server()



if __name__ == "__main__":
    main()
