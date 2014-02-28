import arcpy
import numpy
import sys

assert len(sys.argv) > 3

print 'Hello World!'

arcpy.AddMessage('Hello Arc-World!')

''' arcpy.da = data access '''
input = 'c:/path/to/data.gdb/SUB/PATH'
arr = arcpy.da.FeatureClassToNumPyArray(input, ('COLUMN_NAME1', 'COLUMN_NAME2'))

arr2 = arcpy.da.TableToNumPyArray(input, (sys.argv[2], sys.argv[3]))


for elem in arr:
  pass


