import arcpy
from arcutil import msg

def write_entry_and_parking_population_files(combined_populations_file,
    shpEntries, shpParking, columnName):
    """Writes the population column to the shape files.
    Args:
        combined_populations_file: A file with one column of population values.
        shpEntries: The name of the entry point shapefile.
        shpParking: The name of the parking shapefile.
        columnName: The name of the new column. Will overwrite if exists.
    """
    populations = []
    with open(combined_populations_file) as f:
        for line in f:
            str_value = line.strip()
            if str_value != "":
                populations.append(float(str_value))
            else:
                msg("Warning: Wrong format in the population tempfile: " + line)
        #with open(entry_file) as f:
        #    for line in f:
        #        stripped = line.strip(" \r\n")
        #        if stripped != "":
        #            print "A> ", stripped, populations_file.readline().strip(" \r\n")
        #with open(parking_file) as f:
        #    for line in f:
        #        stripped = line.strip(" \r\n")
        #        if stripped != "":
        #            print "B> ", stripped, populations_file.readline().strip(" \r\n")



    shp = shpEntries
    count1 = add_column_with_values(shp, columnName, populations)
    shp = shpParking
    count2 = add_column_with_values(shp, columnName, populations[count1:])


def add_column_with_values(shp, columnName, values):
    """Adds a column to a shapefile and fills it with values from a list.

    Args:
        shp: The name of the shapefile.
        columnName: The name of the new column. Will overwrite.
        values: The list of values to enter into the column.
    """
    arcpy.management.DeleteField(shp, columnName)
    arcpy.management.AddField(shp, columnName, "FLOAT")
    count = 0
    with arcpy.da.UpdateCursor(shp, [columnName]) as cursor:
        for row in cursor:
            cursor.updateRow([values[count]])
            count += 1
    return count

def test_self():
    write_entry_and_parking_population_files("test-data/1.txt", "test-data/2.txt", "test-data/population.txt")


if __name__ == "__main__":
    test_self()
