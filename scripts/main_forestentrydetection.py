""" Entry point for forest entry detection.

This script performs a set of tasks:
- classify forest entry points "fep"
- classify arcs which are inside the forest
- generate population grid points

Usage:
  python main_forestentrydetection.py <OSMFile> [<MAXSPEED>] ["ATKIS"]

  The optional "ATKIS" flag tells the script that the OSM data was converted
  from ATKIS data.

Copyright 2013: Institut fuer Informatik
Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

"""
from forestentrydetection import *
import osm_parse

def usage_information():
    return "Usage: python script.py <osm_file> [<max_speed>] ['ATKIS']"


def main():
    """Parse an OSM file, classify forest nodes and dump graph and polygons."""
    if len(sys.argv) < 2:
        print usage_information()
        exit(1)
    filebase, ext = os.path.splitext(sys.argv[1])
    path, filename = os.path.split(filebase)
    standardOSM = True
    if "ATKIS" in sys.argv:
        standardOSM = False
        sys.argv.remove("ATKIS")
        print " - Using ATKIS interpreter."

    osmfile = sys.argv[1]
    maxspeed = int(sys.argv[2]) if len(sys.argv) > 2 else 130

    print "Reading nodes, ways and polygons from OSM and creating the graph..."
    parser = osm_parse.OSMParser(maxspeed)
    data = parser.read_osm_file(osmfile)
    (nodes, edges, (forestPolys, innerPolys), adminPolys, pois) = data

    print "Classifying the nodes..."
    forestFlags = classify_nodes(nodes, edges, forestPolys, innerPolys)
    pois = restrict_to_forest(pois, forestFlags)
    print "...done."

    osm_parse.dump_graph(nodes, edges, filename, forestFlags)
    osm_parse.dump_pois(pois, filename)
    with open(filename + ".forest.txt", "w") as polyFile:
        for poly in forestPolys:
            polyFile.write("{0}\n".format(poly))
    with open(filename + ".glade.txt", "w") as polyFile:
        for poly in innerPolys:
            polyFile.write("{0}\n".format(poly))

    #iterpreter = (osm_parse.OSMWayTagInterpreter if standardOSM
    #              else osm_parse.ATKISWayTagInterpreter)
    #tmp = osm_parse.read_file(osmfile, maxspeed, iterpreter)
    #(nodeIds, waysByType, graph, nodes, nodeIndexToOsmId) = tmp

    #print (len(graph.nodes), graph.size(),
           #sum([len(edges) for edges in graph.edges.values()]))

    #filenameBase = os.path.splitext(osmfile)[0]
    #tmp = classify_forest(nodeIds, waysByType, graph, nodes, nodeIndexToOsmId,
                          #filenameBase)
    #(feps, forestHighwayNodes, population, nodeinfo) = tmp

    #print "Writing output..."
    #filename = filenameBase + "." + str(maxspeed) + "kmh"
    #zipped = zip(
    #[feps, forestHighwayNodes, population, graph, nodeIndexToOsmId, nodes, nodeinfo],
    #['Feps', 'ForestIds', 'Population', 'Graph', 'IdMap', 'Nodes', 'Nodeinfo'])
    #for data, extension in zipped:
        #f = open(filename + "." + extension + ".out", 'w')
        #pickle.dump(data, f, protocol=2)
        #f.close()


if __name__ == '__main__':
    main()
