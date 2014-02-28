"""heatmap.py

Contains the Heatmap class.

"""
import numpy as np
import math

def great_circle_distance((lat0, lon0), (lat1, lon1)):
    """In meters, after http://en.wikipedia.org/wiki/Great-circle_distance."""
    to_rad = math.pi / 180.
    r = 6371000.785
    dLat = (lat1 - lat0) * to_rad
    dLon = (lon1 - lon0) * to_rad
    a = math.sin(dLat / 2.) * math.sin(dLat / 2.)
    a += (math.cos(lat0 * to_rad) * math.cos(lat1 * to_rad) *
          math.sin(dLon / 2) * math.sin(dLon / 2))
    return 2 * r * math.asin(math.sqrt(a))

def gcd(a, b):
    """Shorthand for great_circle_distance(a,b)."""
    return great_circle_distance(a, b)


def compute_longitude_stepsize(bbox, latitudeStepSize):
    """

    For a given coordinate bounding box and latitude step size, this computes
    the according longitude step size such that the raster defined by the two
    step sizes is approximately equidistant.

    """
    minLon, minLat, maxLon, maxLat = bbox
    latStepDistance = gcd((maxLat, minLon), (maxLat - latitudeStepSize, minLon))
    distancePerLonDegreeAtMaxLat = gcd((maxLat, minLon), (maxLat, minLon + 1.0))
    longitudeStepSize = latStepDistance / distancePerLonDegreeAtMaxLat
    return longitudeStepSize


class HeatmapFactory(object):
    @staticmethod
    def construct_from_graph(nodes, edges, heats):
        """Constructs the heatmap.

        The heatmap will be a list of coordinates and labels, one for each node.
        The input nodes are a list of 3-tuples (lat, lon, flag) where the flag
        indicates forest nodes (=1) and FEPs (=2).
        The input edges are a list of tuples (s, t).
        The input heats are a list of floats.

        """
        hm = Heatmap()
        hm.leftBottomRightTop = [min(nodes[:,1]), min(nodes[:,0]), max(nodes[:,1]), max(nodes[:,0])]

        # Map weights to nodes
        print "mapping/summing weights..."
        heat = np.zeros([len(nodes),1], dtype="float32")
        for i, (s, t) in enumerate(edges):
            # remove duplicate edges caused by bidirectionality of the graph
            if s < t:
                count = heats[i]
                # Only sum up for forest nodes
                if nodes[s][2] != 0:
                    heat[s] += count
                if nodes[t][2] != 0:
                    heat[t] += count
        # Visualization scales better with this: Choose median of non-zero.
        print "final steps..."
        intensities = np.array(sorted(heat))
        intensities = intensities[intensities[:]>0]
        hm.maximum = intensities[len(intensities)/2]
        # Sort by latitude and throw away zero entries.
        nodeHeat = np.hstack([nodes[:,:2], heat])
        nodeHeat = nodeHeat[nodeHeat[:,2] > 0.]
        hm.heatmap = nodeHeat[nodeHeat[:,0].argsort()]
        return hm

    @staticmethod
    def construct_from_nparray(nodeHeat):
        """Constructs a heatmap from numpy data array."""
        assert nodeHeat.shape[1] == 3
        hm = Heatmap()
        hm.heatmap = nodeHeat
        # self.leftBottomRightTop = [min(lons), min(lats), max(lons), max(lats)]
        lonsAscending = sorted(nodeHeat[:,1])
        hm.leftBottomRightTop = [lonsAscending[0], nodeHeat[0,0],
                                 lonsAscending[-1], nodeHeat[-1,0]]
        # Visualization scales better with this: Choose median of non-zero.
        intensities = nodeHeat[:,2]
        hm.maximum = intensities[len(intensities)/2]
        # This value has to be set outside
        hm.latFraction = 0
        return hm


class Heatmap(object):
    def __init__(self):
        """Constructor."""

    def extract(self, bbox):
        """Returns the part of the heat map data inside the bounding box."""
        minLon, minLat, maxLon, maxLat = bbox
        if [minLon, minLat, maxLon, maxLat] == self.leftBottomRightTop:
            return self.heatmap, self.latFraction
        else:
            i = 0
            while i < len(self.heatmap) and self.heatmap[i][0] < minLat:
                i += 1  # could use exponential or binary search here
            filtered = []
            j = i
            while j < len(self.heatmap) and self.heatmap[j][0] <= maxLat:
                lat, lon, heat = self.heatmap[j]
                if lon >= minLon and lon <= maxLon:
                    filtered.append(self.heatmap[j])
                j += 1
            return np.asarray(filtered), self.latFraction

    def rasterize(self, bbox, (xres,yres)=(18,48)):  #=(640,)
        """Returns a raster discretizing the intensities inside the bbox.

        The yres is important, xres is computed from it.

        """
        minLon, minLat, maxLon, maxLat = bbox
        latFraction = (maxLat - minLat) / (yres - 1.)
        lonFraction = compute_longitude_stepsize(bbox, latFraction)

        latStart = (math.floor(minLat / latFraction) - 0.5) * latFraction
        lonStart = (math.floor(minLon / lonFraction) - 0.5) * lonFraction
        xres = math.ceil((maxLon + 0.5 * lonFraction - lonStart) / lonFraction)
        latEnd = maxLat + 0.5 * latFraction
        lonEnd = maxLon + 0.5 * lonFraction

        # initialize coordinates of the raster points
        lats = np.arange(latStart, latEnd, latFraction)
        lons = np.linspace(lonStart, lonEnd, num=xres+1, endpoint=True)
        lons, lats = np.meshgrid(lons, lats)
        raster = np.dstack([lats, lons, np.zeros([yres+1,xres+1])])
        lats, lons = [], []

        # initialize raster values: collect points which fall into each bin
        print "initialize..."
        heatBins = raster[:,:,2]
        a = 0
        print "summing up..."
        num = len(self.heatmap)
        while a < num and self.heatmap[a][0] < latStart:
            a += 1  # could use exponential or binary search here
        latOffset = 0.5 * latFraction - latStart
        lonOffset = 0.5 * lonFraction - lonStart
        for i in range(a, num):
            lat, lon, heat = self.heatmap[i]
            if lat > latEnd:
                break
            if lon >= lonStart and lon < lonEnd:
                ly = (lat + latOffset) / latFraction
                lx = (lon + lonOffset) / lonFraction
                heatBins[ly,lx] += heat
        print "filtering..."
        return raster[heatBins[:] > 0], latFraction



