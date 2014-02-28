import arcpy
import random
import os
import sys
import numpy as np
from matplotlib import mlab
from util import msg, Timer
''' Add library path for the non-arcpy modules. '''
libpath = os.path.abspath(os.path.split(sys.argv[0])[0] + "\\..\\")
sys.path.append(libpath)
import atkis_graph
from fep_weight_computation import connect_population_to_graph, reachability_analysis


def create_road_graph(road_dataset, max_speed):
  ''' Creates a graph from ATKIS data stored as FeatureClass in a shapefile. '''
  lines_threshold = 1e6
  msg(str(arcpy.management.GetCount(road_dataset)) + " <?> " + str(lines_threshold))
  if arcpy.management.GetCount(road_dataset) < lines_threshold:
    graph, coord_map = atkis_graph.create_graph_via_numpy_array(road_dataset,
                                                                max_speed)
  else:
    graph, coord_map = atkis_graph.create_from_feature_class(road_dataset,
                                                             max_speed)
  msg("The graph has %d nodes and %d edges." % (len(graph.nodes),
      sum([len(edge_set) for edge_set in graph.edges.values()])))

  msg("Contracting binary nodes...")
  graph.contract_binary_nodes()
  msg("The graph has %d nodes and %d edges." % (len(graph.nodes),
      sum([len(edge_set) for edge_set in graph.edges.values()])))
  lcc = graph.lcc()
  msg("The largest connected component has %d nodes and %d edges." %
      (len(lcc.nodes), sum([len(e) for e in lcc.edges.values()])))
  return graph, coord_map


def shape_to_polygons(lines):
  ''' Parses polygons from the points represented by lines in a numpy 
  RecordArray created by arcpy.FeatureClassToNumPyArray(explode_to_points=True).
  '''
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
  return create_population_grid(polygons, [], grid_point_distance=point_distance)


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
    layer = arcpy.management.MakeFeatureLayer(population_fc, 'population_layer1')
    try:
      arcpy.management.SaveToLayerFile(layer, "pp_layer.lyr")
    except:
      pass
    layer = arcpy.mapping.Layer(path + "pp_layer.lyr")
    arcpy.mapping.AddLayer(dataframe, layer, "TOP")
  msg("There are %d populations." % len(population_nodes))
  return population_nodes


path = "C:\\Data\\freiburg_city_clipped\\"

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
    road_dataset = path + "DLM_Wegenetz_fr_city.shp"
    forest_roads = path + "forest_roads.shp"
    settlement_dataset = path + "DLM_Ortslage_fr_city.shp"
    entrypoint_dataset = path + "Waldeingang_fr_city.shp"
  else:
    path = os.path.split(road_dataset)[0] + "\\"

  path_and_filename = os.path.split(road_dataset)
  output_dataset = path_and_filename[0] + "\\result_" + path_and_filename[1]
  try:
    arcpy.management.Delete(output_dataset)
  except:
    pass

  t.start_timing("Creating graph from the data...") 
  graph, coord_map = create_road_graph(road_dataset, max_speed=5)
  t.stop_timing()

  t.start_timing("Creating population points...")
  population_nodes = create_population(settlement_dataset, coord_map, graph, 
                                       point_distance=200)
  t.stop_timing()

  arr4 = arcpy.da.FeatureClassToNumPyArray(entrypoint_dataset, ["fid", "shape"])
  #fep_node_ids = [coord_map[tuple(coord)] for coord in arr4["shape"]]
  fep_node_ids = []
  for east, north in arr4['shape']:
    if (east, north) in coord_map:
      fep_node_ids.append(coord_map[(east, north)])
  msg("There are {0} FEPs, {1} could not be found.".format(
      len(fep_node_ids), len(arr4['shape']) - len(fep_node_ids)))

  t.start_timing("Reachability analysis...")
  reachable_feps = reachability_analysis(graph, fep_node_ids, population_nodes)
  t.stop_timing()

#  t.start_timing("Computing distance to nearest forest entry...")
#  arcpy.analysis.Near(forest_roads, entrypoint_dataset)
#  t.stop_timing()

#  t.start_timing("Rasterizing the forest roads...")
#  raster = path + "out_raster_" + str(random.randint(0,999)) + ".tif"
#  if os.path.exists(raster):
#    arcpy.management.Delete(raster)
#  arcpy.conversion.PolylineToRaster(forest_roads, "NEAR_DIST",
#                                    raster, cellsize=20)
#  t.stop_timing()

  if arcpy.GetParameterAsText(0):
    '''Showing output layer in ArcMap...'''
    mxd = arcpy.mapping.MapDocument("CURRENT")
    dataframe = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    msg(dataframe)
    # layer = arcpy.management.MakeFeatureLayer(...
    layer = arcpy.management.MakeRasterLayer(raster, "raster_layer")
    try:
      arcpy.management.SaveToLayerFile(layer, "raster.lyr")
    except:
      pass
    layer = arcpy.mapping.Layer(path + "raster.lyr")
    # layer.transparency = 40
    arcpy.mapping.AddLayer(dataframe, layer, "TOP")



if __name__ == '__main__':
  arcpy.management.Delete("in_memory")
  main()

