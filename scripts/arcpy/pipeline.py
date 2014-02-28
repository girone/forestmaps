import arcpy
import random
import time


target_table = arcpy.GetParameterAsText(0)

arcpy.AddMessage("Adding a new column to the table...")
t0 = time.clock()
arcpy.AddField_management(target_table, "NewField", "FLOAT")
arcpy.AddMessage("This took %f seconds." % (time.clock() - t0))

values = range(100)
for i in values:
  values[i] = float(random.randint(0, 99))

#arcpy.AddMessage("Filling the column with values...")
#size = int(arcpy.GetCount_management(target_table).getOutput(0))
#arcpy.AddMessage("Table has %d rows." % size)
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

t0 = time.clock()
arcpy.AddMessage("Converting table to numpy array...")
tab = arcpy.da.TableToNumPyArray(target_table, "*")
arcpy.AddMessage("This took %f seconds." % (time.clock() - t0))

arcpy.AddMessage("Filling the column with values...")
size = tab.shape[0]
arcpy.AddMessage("Table has %d rows." % size)
pos = 0
arcpy.SetProgressor("step", "Inserting values...", 0, size, 1000)
t0 = time.clock()
for row in tab:
  # row[i] references the ith field specified on creation of the cursor
  row[0] = values[pos % len(values)]
  pos += 1
  if pos % 1000 == 0:
    arcpy.SetProgressorPosition()
arcpy.AddMessage("This took %f seconds." % (time.clock() - t0))
arcpy.ResetProgressor()

arcpy.AddMessage("Converting numpy array back to table...")
t0 = time.clock()
arcpy.da.NumPyArrayToTable(tab, target_table)
arcpy.AddMessage("This took %f seconds." % (time.clock() - t0))

