""" create_json.py

Reads a graph file and creates JSON output for edge weights.

"""
from osm_parse import OSMSpeedTable

def main():
    import sys
    if len(sys.argv) < 2:
        print "Usage: python script.py <graph_file>"
        exit(1)
    limit = None
    if len(sys.argv) > 2:
        limit = int(sys.argv[2])

    count = 0
    with open("saarland-130822.graph.txt") as f:
        numNodes = int(f.readline())
        numEdges = int(f.readline())
        nodes = []
        for i in range(numNodes):
            line = f.readline()
            sLat, sLon, sOsmId, sFlag = line.split(" ")
            nodes.append((sLat, sLon))
        dumpedNodes = set([])

        strings = []
        for i in range(numEdges):
            line = f.readline()
            sFrom, sTo, sDist, sTime, sType = line.strip().split(" ")
            from_ = int(sFrom)
            to = int(sTo)
            if to not in dumpedNodes:
                dumpedNodes.add(to)
                val = len(OSMSpeedTable) - int(sType)
                strings.append('{' +
                               ' "lat": ' + nodes[to][0] +
                               ', "lon": ' + nodes[to][1] +
                               ', "count": ' + str(val) +
                               '}')
                if limit:
                    count += 1
                    if count == limit:
                        break
        print "[", ", ".join(strings) + "]"


if __name__ == '__main__':
    main()

