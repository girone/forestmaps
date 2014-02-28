import arcpy
import random
import time
import os
import numpy as np


def msg(text):
  arcpy.AddMessage(text)
  print text


env = "C:\\Users\\sternis\\Documents\\ArcGIS\\Data\\"


def main():
  ''' Entry point. '''
  arcpy.management.Delete("in_memory")
  input_table = arcpy.GetParameterAsText(0)
  if not input_table:
    msg("RUNNING AS EXTERNAL SCRIPT")
    arcpy.env.workspace = env
    arcpy.env.scratchWorkspace = env + "scratchoutput.gdb"
    input_table = env + "random.shp"
  else:
    msg("RUNNING AS INTERNAL SCRIPT")
  # msg(input_table)

  path_and_filename = os.path.split(input_table)
  output_table = path_and_filename[0] + "\\output_" + path_and_filename[1]
  arcpy.management.Delete(output_table)

  msg("Copying the table into memory...")
  t0 = time.clock()
  #target_table = arcpy.management.CreateTable("in_memory", "table1")
  #memory_table = "in_memory\\table1"
  #arcpy.management.CopyFeatures(input_table, memory_table)
  ''' For faster performance and reliable field order, it is recommended that
      the list of fields be narrowed to only those that are actually needed.
      NOTE(Jonas): That is indeed much faster (factor 10)!
  '''
  arr= arcpy.da.FeatureClassToNumPyArray(input_table, ("FID", "Id"))
  msg("This took %f seconds." % (time.clock() - t0))

  msg("Adding a new column to the table...")
  t0 = time.clock()
  #arcpy.management.AddField(memory_table, "NewField", "FLOAT")
  # numpy array: pass
  pass
  msg("This took %f seconds." % (time.clock() - t0))

  values = range(100)
  for i in values:
    values[i] = float(random.randint(0, 99))

  #msg("Filling the column with values...")
  #size = int(arcpy.management.GetCount(target_table).getOutput(0))
  #msg("Table has %d rows." % size)
  #pos = 0
  #with arcpy.da.UpdateCursor(target_table, ["NewField"]) as rows:
  #  arcpy.SetProgressor("step", "Inserting values...", 0, size, 1000)
  #  for row in rows:
  #    # row[i] references the ith field specified on creation of the cursor
  #    row[0] = values[pos % len(values)]
  #    #rows.updateRow(row)
  #    pos += 1
  #    if pos % 1000 == 0:
  #      arcpy.SetProgressorPosition()
  #  arcpy.ResetProgressor()

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
    # row[i] references the ith field specified on creation of the cursor
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
  #arcpy.management.CopyFeatures(memory_out_table, output_table)
  # NOTE(Jonas): Here selecting the a subset of fields does not change performance.
  arcpy.da.NumPyArrayToFeatureClass(arr, output_table, ("FID", "Id"))
  msg("This took %f seconds." % (time.clock() - t0))

  arcpy.management.Delete("in_memory")


if __name__ == '__main__':
  main()

