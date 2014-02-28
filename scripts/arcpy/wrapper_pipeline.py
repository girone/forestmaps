""" DOCU TODO

"""
import arcpy
import os

# Add library path to the non-arcpy modules.
libpath = os.path.abspath(os.path.split(sys.argv[0])[0] + "\\..\\")
sys.path.append(libpath)
import atkis_graph
from util import msg, Timer


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
    """Creates a graph from ATKIS data stored as FeatureClass in a shapefile."""
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


def main():
    """Parse data from shapefiles and dump graph, population and entries."""
    road_dataset = arcpy.GetParameterAsText(0)
    settlement_dataset = arcpy.GetParameterAsText(1)
    entrypoint_dataset = arcpy.GetParameterAsText(2)
    if not (road_dataset and settlement_dataset and entrypoint_dataset):
        msg("Error with input.")
        exit(1)
    path = os.path.split(road_dataset)[0] + "\\"

    t = Timer()
    t.start_timing("Creating graph from the data...")
    graph, coord_map, _, _ = create_road_graph(road_dataset, max_speed=5)
    node_to_coords = {node : coords for coords, node in coord_map.items()}
    with open("graph.txt", "w") as f:
        f.write("{0}\n".format(graph.size()))
        f.write("{0}\n".format(
                sum([len(edges) for edges in graph.edges.values()])))
        for node in graph.nodes:
            x, y = node_to_coords[node]
            f.write("{0} {1}\n".format(x, y))
        for source, targets in graph.edges.items():
            for target, edge in targets.items():
                f.write("{0} {1} {2}\n".format(source, target, edge.cost))
    t.stop_timing()

    t.start_timing("Creating population points...")
    population_coords = create_population(settlement_dataset,
                                          point_distance=200)
    total_population = 230000
    avg_population = total_population / float(len(population_coords))
    with open("population.txt", "w") as f:
        for coord in population_coords:
            f.write("{0} {1} {2}\n".format(coord[0], coord[1], avg_population))
    t.stop_timing()

    t.start_timing("Parsing forest entries...")
    arr4 = arcpy.da.FeatureClassToNumPyArray(entrypoint_dataset, ["fid", "shape"])
    fep_node_ids = set()
    for east, north in arr4['shape']:
        if (east, north) in coord_map:
            fep_node_ids.add(coord_map[(east, north)])
    with open("entries.txt", "w") as f:
        for entry in fep_node_ids:
            f.write("{0}\n".format(entry))
    t.stop_timing()


if __name__ == '__main__':
    #arcpy.management.Delete("in_memory")
    main()
