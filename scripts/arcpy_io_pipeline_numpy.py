"""arcpy_io_pipeline_numpy.py -- Demo for file input/output with arcpy + numpy.

"""
import arcpy
import random
import time
import os
import numpy as np


def msg(text):
  arcpy.AddMessage(text)
  print text


env = "C:\\Users\\sternis\\Documents\\ArcGIS\\Data\\"
arcpy.env.workspace = env
arcpy.env.scratchWorkspace = env + "scratchoutput.gdb"


def main():
  """ Entry point. """
  arcpy.management.Delete("in_memory")
  input_table = arcpy.GetParameterAsText(0)
  if not input_table:
    msg("RUNNING AS EXTERNAL SCRIPT")
    input_table = env + "random.shp"
  else:
    msg("RUNNING AS INTERNAL SCRIPT")
  # msg(input_table)

  path_and_filename = os.path.split(input_table)
  output_table = path_and_filename[0] + "\\output_" + path_and_filename[1]
  arcpy.management.Delete(output_table)

  msg("Copying the table into memory...")
  t0 = time.clock()
  """ For faster performance and reliable field order, it is recommended that
      the list of fields be narrowed to only those that are actually needed.
      NOTE(Jonas): That is indeed much faster (factor 10)!
  """
  arr= arcpy.da.TableToNumPyArray(input_table, ("FID", "Id"))
  msg("This took %f seconds." % (time.clock() - t0))

  msg("Adding a new column to the table...")
  t0 = time.clock()
  # numpy array: pass
  pass
  msg("This took %f seconds." % (time.clock() - t0))

  values = range(100)
  for i in values:
    values[i] = float(random.randint(0, 99))

  #t0 = time.clock()
  #msg("Converting table to numpy array...")
  #arr = arcpy.da.FeatureClassToNumPyArray(memory_table, "*")
  #msg("This took %f seconds." % (time.clock() - t0))

  msg("Filling the column with values...")
  size = arr.shape[0]
  #msg("Table has %d rows." % size)
  pos = 0
  t0 = time.clock()
  for row in arr:
    row[1] = values[pos % len(values)]
    pos += 1
  msg("This took %f seconds." % (time.clock() - t0))

  #msg("Converting numpy array back to table...")
  #t0 = time.clock()
  #memory_out_table = "in_memory\\" + "table2"
  #arcpy.da.NumPyArrayToFeatureClass(arr, memory_out_table, ("FID", "Shape", "Id", "NewField"))
  #msg("This took %f seconds." % (time.clock() - t0))

  msg("Writing output table to '" + output_table + "'")
  t0 = time.clock()
  # NOTE(Jonas): Here selecting the a subset of fields does not change performance.
  arcpy.da.NumPyArrayToTable(arr, output_table, ("FID", "Id"))
  msg("This took %f seconds." % (time.clock() - t0))

  arcpy.management.Delete("in_memory")


if __name__ == '__main__':
  main()

