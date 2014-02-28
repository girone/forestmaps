import arcpy
import random
import time
import os
import numpy as np
from matplotlib import mlab


def msg(text):
  arcpy.AddMessage(text)
  print text


path = "C:\\Data\\freiburg_city_clipped\\"
arcpy.env.workspace = path
arcpy.env.scratchWorkspace = path + "scratchoutput.gdb"
mem = "in_memory\\"


def main():
  ''' Entry point. '''
  @np.vectorize
  def selected(ele): return ele in forest_fids
  
  road_dataset = arcpy.GetParameterAsText(0)
  settlement_dataset = arcpy.GetParameterAsText(1)
  forest_dataset = arcpy.GetParameterAsText(2)
  entrypoint_dataset = arcpy.GetParameterAsText(3)

  if not (road_dataset and settlement_dataset and forest_dataset and
      entrypoint_dataset):
    msg("Error with input.")
    exit(1)
    road_dataset = path + "DLM_Wegenetz_fr_city.shp"
    settlement_dataset = path + "DLM_Ortslage_fr_city.shp"
    forest_dataset = path + "DLM_Wald_fr_city.shp"
    entrypoint_dataset = path + "Waldeingang_fr_city.shp"
  else:
    path = os.path.split(road_dataset)[0] + "\\"

  path_and_filename = os.path.split(road_dataset)
  output_dataset = path_and_filename[0] + "\\result_" + path_and_filename[1]
  try:
    arcpy.management.Delete(output_dataset)
  except:
    pass

  msg("Copying the tables into memory...")
  t0 = time.clock()
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
  #forest_fids = set(road_features_array[road_features_array['wanderweg'] == 1]['fid'])
  #forest_roads_array = road_points_array[selected(road_points_array['fid'])]
  arr2 = arcpy.da.FeatureClassToNumPyArray(settlement_dataset, ["fid", "shape"], 
                                           explode_to_points=True)
  arr3 = arcpy.da.FeatureClassToNumPyArray(forest_dataset, ["fid", "shape"], 
                                           explode_to_points=True)
  arr4 = arcpy.da.FeatureClassToNumPyArray(entrypoint_dataset, ["fid", "shape"])
  msg("This took %f seconds." % (time.clock() - t0))

  msg("Dissolve forest, add 1 meter buffer and clipping roads to it...")
  t0 = time.clock()
  forest_roads = path + "roads_clipped.shp"
  tmp1, tmp2 = "dissolved.shp", "buffered.shp"
  if not os.path.exists(forest_roads):
    arcpy.management.Dissolve(forest_dataset, tmp1)
    arcpy.analysis.Buffer(tmp1, tmp2, "1 Meters")
    arcpy.analysis.Clip(road_dataset, tmp2, forest_roads)
    arcpy.management.Delete(tmp1)
    arcpy.management.Delete(tmp2)
    #arcpy.management.Delete(forest_roads)
  msg("This took %f seconds." % (time.clock() - t0))

  msg("Computing distance to nearest forest entry...")
  t0 = time.clock()
  arcpy.analysis.Near(forest_roads, entrypoint_dataset)
  msg("This took %f seconds." % (time.clock() - t0))

  msg("Rasterizing the forest roads...")
  t0 = time.clock()
  raster = path + "out_raster_" + str(random.randint(0,999)) + ".tif"
  if os.path.exists(raster):
    arcpy.management.Delete(raster)
  arcpy.conversion.PolylineToRaster(forest_roads, "NEAR_DIST",
                                    raster, cellsize=20)
  msg("This took %f seconds." % (time.clock() - t0))

  msg("Showing output layer in ArcMap...")
  t0 = time.clock()
  mxd = arcpy.mapping.MapDocument("CURRENT")
  dataframe = arcpy.mapping.ListDataFrames(mxd, "*")[0]
  msg(dataframe)
  # layer = arcpy.management.MakeFeatureLayer(...
  layer = arcpy.management.MakeRasterLayer(raster, "raster_layer")
  try:
    arcpy.management.SaveToLayerFile(layer, path + "raster.lyr")
  except:
    pass
  layer = arcpy.mapping.Layer(path + "raster.lyr")
  # layer.transparency = 40
  arcpy.mapping.AddLayer(dataframe, layer, "TOP")
  msg("This took %f seconds." % (time.clock() - t0))



if __name__ == '__main__':
  arcpy.management.Delete("in_memory")
  main()

