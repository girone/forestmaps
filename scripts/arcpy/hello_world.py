import arcpy
import numpy
import sys
import time

#assert len(sys.argv) > 3

print 'Hello World!'

arcpy.AddMessage('Hello Arc-World!')
arcpy.AddIDMessage('INFORMATIVE', 12, 'Hello World!')


arcpy.SetProgressor("step", "Computing...", 0, 60, 1)
for i in range(60):
  time.sleep(0.2)
  arcpy.SetProgressorPosition()
arcpy.ResetProgressor()

''' arcpy.da = data access '''
input = 'c:/path/to/data.gdb/SUB/PATH'
#arr = arcpy.da.FeatureClassToNumPyArray(input, ('COLUMN_NAME1', 'COLUMN_NAME2'))

#arr2 = arcpy.da.TableToNumPyArray(input, (sys.argv[2], sys.argv[3]))


#for elem in arr:
#  pass


