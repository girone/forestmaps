""" DOCU TODO

"""
import arcpy
import random
import os
import sys
import numpy as np
from matplotlib import mlab
from util import msg, Timer
from collections import defaultdict
''' Add library path for the non-arcpy modules. '''
libpath = os.path.abspath(os.path.split(sys.argv[0])[0] + "\\..\\")
sys.path.append(libpath)
import atkis_graph
from graph import Graph
from fep_weight_computation import connect_population_to_graph, reachability_analysis
import edge_weight_computation


newFieldName = "EdgeWeight"
path = "C:\\Data\\toy_data_rosskopf\\"
COST_LIMIT_TO_FOREST_ENTRY = 10*60
COST_LIMIT_IN_FOREST = 60*60

def create_road_graph(dataset, max_speed):
  ''' Creates a graph from ATKIS data stored as FeatureClass in a shapefile. '''
  lines_threshold = 1e6
  msg(str(arcpy.management.GetCount(dataset).getOutput(0)) + " <?> " + str(lines_threshold))
  if False and arcpy.management.GetCount(dataset).getOutput(0) < lines_threshold:
    graph, coord_map = atkis_graph.create_graph_via_numpy_array(dataset,
                                                                max_speed)
  else:
    graph, coord_map, arc_to_fid = \
        atkis_graph.create_from_feature_class(dataset, max_speed)
  msg("The graph has %d nodes and %d edges." % (len(graph.nodes),
      sum([len(edge_set) for edge_set in graph.edges.values()])))

  msg("Contracting binary nodes...")
  contraction_list = graph.contract_binary_nodes()
  msg("The graph has %d nodes and %d edges." % (len(graph.nodes),
      sum([len(edge_set) for edge_set in graph.edges.values()])))
  #lcc = graph.lcc()
  #msg("The largest connected component has %d nodes and %d edges." %
  #    (len(lcc.nodes), sum([len(e) for e in lcc.edges.values()])))
  return graph, coord_map, arc_to_fid, contraction_list


def shape_to_polygons(lines):
  """ Parses polygons from the points represented by lines in a numpy
  RecordArray created by arcpy.FeatureClassToNumPyArray(explode_to_points=True).
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


def create_populations_from_settlement_fc(lines, point_distance):
  ''' Creates population points from the 'Ortslage' feature class. The
  point_distance parameter influences the density of the grid.
  '''
  polygons = shape_to_polygons(lines)
  from forestentrydetection import create_population_grid
  return create_population_grid(polygons, [], gridPointDistance=point_distance)


def create_population(settlement_dataset,
                      coordinate_to_graph_node,
                      graph,
                      point_distance):
  ''' Creates the population representatives and connects them to the graph. '''
  arr2 = arcpy.da.FeatureClassToNumPyArray(settlement_dataset, ["fid", "shape"],
                                           explode_to_points=True)
  population_coords = create_populations_from_settlement_fc(
      arr2, point_distance)
  coord_map_inv = {v:k for k,v in coordinate_to_graph_node.items()}
  population_nodes = connect_population_to_graph(
      population_coords, graph, [coord_map_inv[node] for node in graph.nodes],
      lambda x: x)
  if arcpy.GetParameterAsText(0):
    '''Showing output layer in ArcMap...'''
    population_array = np.array(
        [zip(range(len(population_coords)), population_coords)],
        np.dtype([('idfield', np.int32), ('XY', '<f8', 2)]))
    population_fc = path + "population.shp"
    arcpy.management.Delete(population_fc)
    arcpy.da.NumPyArrayToFeatureClass(
        population_array, population_fc, ['XY'],
        arcpy.Describe(settlement_dataset).spatialReference)

    mxd = arcpy.mapping.MapDocument("CURRENT")
    dataframe = arcpy.mapping.ListDataFrames(mxd, "*")[0]

    layer = arcpy.management.MakeFeatureLayer(population_fc,
                                                'population_layer1')
    #except:
    #  pass
    #try:
    arcpy.management.SaveToLayerFile(layer, path + "pp_layer.lyr")
    #except:
    #  pass
    layer = arcpy.mapping.Layer(path + "pp_layer.lyr")
    arcpy.mapping.AddLayer(dataframe, layer, "TOP")
  msg("There are %d populations." % len(population_nodes))
  return population_nodes


def distribute_population_to_feps(population_nodes, reachable_feps):
    """Distributes the population to reachable forest entry points.

    Assumes equal population distribution over the population points.
    Assumes a fixed total population.
    Distribution does not consider distance yet. # TODO(jonas)

    """
    fep_population = defaultdict(float)
    avg_population = 280000. / len(population_nodes)
    for pop in population_nodes:
      if len(reachable_feps[pop]):
        population_share = avg_population / len(reachable_feps[pop])
        for entry, dist in reachable_feps[pop]:
          fep_population[entry] += population_share
    msg("Forest entry population share:")
    for v, k in sorted([(v, k) for k, v in fep_population.items()]):
      msg(str(k) + " " + str(v))
    return fep_population


def map_fid_to_arc_weight(edges, edgeToFID):
    """Returns a map from FID to the corresponding weight."""
    fidToWeight = {}
    for s, targets in edges.items():
      for t, edge in targets.items():
        weight = edge.cost
        fidToWeight[edgeToFID[(s,t)]] = weight
    return fidToWeight


def add_weight_column(dataset, fidToWeight):
    """Adds a column to the dataset and inserts the weights for each arc."""
    arcpy.management.AddField(dataset, newFieldName, "FLOAT")
    fields = ["fid", newFieldName]
    count = 0
    with arcpy.da.UpdateCursor(dataset, fields) as cursor:
      for row in cursor:
        if row[0] in fidToWeight:
          row[1] = fidToWeight[row[0]]
          msg(fidToWeight[row[0]])
          cursor.updateRow(row)
        else:
          count += 1
    msg("Could not match {0} edges".format(count))



def main():
  global path

  t = Timer()

  arcpy.env.workspace = path
  arcpy.env.scratchWorkspace = path + "scratchoutput.gdb"
  mem = "in_memory\\"

  road_dataset = arcpy.GetParameterAsText(0)
  forest_roads = arcpy.GetParameterAsText(1)
  settlement_dataset = arcpy.GetParameterAsText(2)
  entrypoint_dataset = arcpy.GetParameterAsText(3)

  if not (road_dataset and settlement_dataset and forest_roads and
      entrypoint_dataset):
    msg("Error with input.")
    #exit(1)
    road_dataset = path + "DLM_Wegenetz_rosskopf.shp"
    forest_roads = path + "forest_roads.shp"
    settlement_dataset = path + "DLM_Ortslage_rosskopf.shp"
    entrypoint_dataset = path + "Waldeingang_rosskopf.shp"
  else:
    path = os.path.split(road_dataset)[0] + "\\"

  path_and_filename = os.path.split(road_dataset)
  output_dataset = path_and_filename[0] + "\\result_" + path_and_filename[1]
  try:
    arcpy.management.Delete(output_dataset)
  except:
    pass

  t.start_timing("Creating graph from the data...")
  graph, coord_map, _, _ = create_road_graph(road_dataset, max_speed=5)
  t.stop_timing()

  t.start_timing("Creating graph from the data...")
  forest_graph, forest_coord_map, forest_arc_to_fid, contraction_list = \
      create_road_graph(forest_roads, max_speed=5)
  t.stop_timing()

  t.start_timing("Creating population points...")
  population_nodes = create_population(settlement_dataset, coord_map, graph,
                                       point_distance=200)
  t.stop_timing()

  arr4 = arcpy.da.FeatureClassToNumPyArray(entrypoint_dataset, ["fid", "shape"])
  #fep_node_ids = [coord_map[tuple(coord)] for coord in arr4["shape"]]
  fep_node_ids = set()
  for east, north in arr4['shape']:
    if (east, north) in coord_map:
      fep_node_ids.add(coord_map[(east, north)])
  msg("There are {0} FEPs, {1} could not be found.".format(
      len(fep_node_ids), len(arr4['shape']) - len(fep_node_ids)))

  t.start_timing("Reachability analysis...")
  reachable_feps = reachability_analysis(graph, fep_node_ids, population_nodes,
                                         cost_limit=COST_LIMIT_TO_FOREST_ENTRY)
  # population point -> (fep, dist)
  # TODO(jonas): Categorization.
  t.stop_timing()

  """Compute the edge weight model."""
  t.start_timing("Distributing population to forest entries...")
  fep_population = distribute_population_to_feps(
      population_nodes, reachable_feps)
  t.stop_timing()
  t.start_timing("Computing edge weights...")
  edge_weights = edge_weight_computation.compute_edge_weight(
      forest_graph, fep_node_ids, fep_population,
      cost_limit=COST_LIMIT_IN_FOREST)
  t.stop_timing()
  msg(sorted([(v, k) for k, v in edge_weights.items()]))
  msg("##########")

  """Map arc weight to underlying contracted arcs."""
  t.start_timing("Mapping edge weights back to FIDs...")
  weightedGraph = Graph()
  weightedGraph.nodes = forest_graph.nodes.copy()
  for s, targets in forest_graph.edges.items():
    for tt in targets.keys():
      weightedGraph.add_edge(s, tt, edge_weights[(s,tt)])
  weightedGraph.undo_contraction(contraction_list)
  fid_to_edge_weight = map_fid_to_arc_weight(weightedGraph.edges,
                                             forest_arc_to_fid)
  add_weight_column(forest_roads, fid_to_edge_weight)
  t.stop_timing()


  #t.start_timing("Computing distance to nearest forest entry...")
  #arcpy.analysis.Near(forest_roads, entrypoint_dataset)
  #t.stop_timing()

  t.start_timing("Rasterizing the forest roads...")
  blub = str(random.randint(0,999))
  raster = path + "out_raster_" + blub + ".tif"
  if os.path.exists(raster):
    arcpy.management.Delete(raster)
  #arcpy.conversion.PolylineToRaster(forest_roads, "NEAR_DIST", raster, cellsize=20)
  arcpy.conversion.PolylineToRaster(forest_roads, newFieldName, raster, cellsize=5)
  t.stop_timing()

  if arcpy.GetParameterAsText(0):
    '''Showing output layer in ArcMap...'''
    mxd = arcpy.mapping.MapDocument("CURRENT")
    dataframe = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    msg(dataframe)
    # layer = arcpy.management.MakeFeatureLayer(...
    layer = arcpy.management.MakeRasterLayer(raster, "raster_layer")
    try:
      arcpy.management.SaveToLayerFile(layer, "raster_" + blub + ".lyr")
    except:
      pass
    layer = arcpy.mapping.Layer(path + "raster_" + blub + ".lyr")
    # layer.transparency = 40
    arcpy.mapping.AddLayer(dataframe, layer, "TOP")



if __name__ == '__main__':
  arcpy.management.Delete("in_memory")
  main()

