"""example_script.py -- An example for basic arcpy functionality.

Courtesy of:
    http://pythongisandstuff.wordpress.com/2011/07/12/tutorial-arcpy-basics/

"""
import arcpy

# get input feature class
inputFeatureClass = arcpy.GetParameterAsText(0)

# get buf size
buf = "5 Meters"

# get output feature class
outputFeatureClass = arcpy.GetParameterAsText(1)

assert inputFeatureClass != outputFeatureClass

# inform user of selected feature class path
arcpy.AddMessage("  Buffering input Feature Class, " + inputFeatureClass +
                 " by " + buf + " Meters and writing to: "
                 + outputFeatureClass)

arcpy.Buffer_analysis(inputFeatureClass,  outputFeatureClass, buf)
