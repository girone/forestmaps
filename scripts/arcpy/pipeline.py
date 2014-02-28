import arcpy
import random
import os
import numpy as np
from matplotlib import mlab
from util import msg, Timer


def main():
  @np.vectorize
  def selected(ele): return ele in forest_fids
  
  t = Timer()

  path = "C:\\Data\\freiburg_city_clipped\\"
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

  t.start_timing("Copying the tables into memory...")
  ''' For faster performance and reliable field order, it is recommended that
      the list of fields be narrowed to only those that are actually needed.
      NOTE(Jonas): That is indeed much faster (factor 10)!
  '''
  sr = arcpy.Describe(road_dataset).spatialReference
  ''' Convention: Field names are lowercase. '''
  road_points_array = arcpy.da.FeatureClassToNumPyArray(
      road_dataset, ["fid", "shape", "klasse", "wanderweg", "shape_leng"],
      spatial_reference=sr, explode_to_points=True)
  _, index = np.unique(road_points_array['fid'], return_index=True)
  road_features_array = road_points_array[index]
  arr2 = arcpy.da.FeatureClassToNumPyArray(settlement_dataset, ["fid", "shape"], 
                                           explode_to_points=True)
  arr4 = arcpy.da.FeatureClassToNumPyArray(entrypoint_dataset, ["fid", "shape"])
  t.stop_timing()

  t.start_timing("Computing distance to nearest forest entry...")
  arcpy.analysis.Near(forest_roads, entrypoint_dataset)
  t.stop_timing()

  t.start_timing("Rasterizing the forest roads...")
  raster = path + "out_raster_" + str(random.randint(0,999)) + ".tif"
  if os.path.exists(raster):
    arcpy.management.Delete(raster)
  arcpy.conversion.PolylineToRaster(forest_roads, "NEAR_DIST",
                                    raster, cellsize=20)
  t.stop_timing()

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

