''' clip_forest_roads.py : Clips a road network to its forest parts.

Input: 
  road network, forest polygons, [include special walkways=False], 
  [buffer size='2 Meters']
Procedure:
  - DISSOLVE the separate forest polygons to a single set of polygons
  - add a BUFFER to the forest, such that internal boundaries will be filled
  - CLIP the road network to the forest polygons
  - [APPEND additional special roads ('Wanderwege') which are outside the
    forest]
'''
import os
import arcpy
from util import Timer


def main():
  path = "C:\\Data\\freiburg_city_clipped\\"
  arcpy.env.workspace = path
  arcpy.env.scratchWorkspace = path + "scratchoutput.gdb"
  mem = "in_memory\\"
  t = Timer()

  road_dataset = arcpy.GetParameterAsText(0)
  forest_dataset = arcpy.GetParameterAsText(1)
  if not (forest_dataset and road_dataset):
    ''' Set up parameter for testing. '''
    forest_dataset = path + "DLM_Wald_fr_city.shp"
    road_dataset = path + "DLM_Wegenetz_fr_city.shp"
  else:
    path = os.path.split(road_dataset)[0] + "\\"

  buffer_size = arcpy.GetParameterAsText(2)
  if not buffer_size:
    buffer_size = 2
  buffer_size = str(buffer_size) + " Meters"

  include_special_roads = arcpy.GetParameterAsText(3)
  if not include_special_roads:
    include_special_roads = False 
  # TODO(Jonas): implement this
  #forest_fids = set(road_features_array[road_features_array['wanderweg'] == 1]['fid'])

  tmp1, tmp2 = mem + "dissolved", mem + "buffered"

  t.start_timing("Dissolve forest polygons for faster clipping...")
  arcpy.management.Dissolve(forest_dataset, tmp1)
  t.stop_timing()

  t.start_timing("Add " + str(buffer_size) + " buffer to the forest...")
  arcpy.analysis.Buffer(tmp1, tmp2, str(buffer_size))
  t.stop_timing()

  t.start_timing("Clipping roads to the buffered forest...")
  forest_roads = path + "forest_roads.shp"
  if os.path.exists(forest_roads):
    arcpy.management.Delete(forest_roads)
  arcpy.analysis.Clip(road_dataset, tmp2, forest_roads)
  t.stop_timing()
  arcpy.management.Delete(tmp1)
  arcpy.management.Delete(tmp2)

  ''' If ArcMap is active, show the new data. '''
  if arcpy.GetParameterAsText(0):
    mxd = arcpy.mapping.MapDocument("CURRENT")
    dataframe = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    # layer = arcpy.management.MakeFeatureLayer(...
    layer = arcpy.management.MakeFeatureLayer(forest_roads, "forest_roads_layer")
    try:
      arcpy.management.SaveToLayerFile(layer, path + "forest_roads.lyr")
    except:
      pass
    layer = arcpy.mapping.Layer(path + "forest_roads.lyr")
    arcpy.mapping.AddLayer(dataframe, layer, "TOP")


if __name__ == '__main__':
  arcpy.management.Delete("in_memory")
  main()

