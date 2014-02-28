'''example_script.py

Example script from http://pythongisandstuff.wordpress.com/2011/07/12/tutorial-arcpy-basics/

'''
import arcpy
 
# get input feature class
inputFeatureClass = arcpy.GetParameterAsText(0)
 
# get buffer size
buffer = "5 Meters"
 
# get output feature class
outputFeatureClass = arcpy.GetParameterAsText(1)

assert inputFeatureClass != outputFeatureClass
 
# inform user of selected feature class path
arcpy.AddMessage('  Buffering input Feature Class, '+inputFeatureClass+' by '+buffer+' Meters and writing to: '+outputFeatureClass)
 
buffer_corrected = buffer # + ' Meters'
 
arcpy.Buffer_analysis(inputFeatureClass,  outputFeatureClass, buffer_corrected)
