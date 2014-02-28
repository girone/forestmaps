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


class Heatmap(object):
    def __init__(self, nodes, edges):
        """Constructs the heatmap.

        The heatmap will be a set of coordinates and labels, one for each node.
        The input nodes are a set of 3-tuples (lat, lon, flag) where the flag
        indicates forest nodes (=1) and FEPs (=2).
        The input edges are a set of 3-tuples (s, t, weight).

        """
        nodes = np.array(nodes)
        lats, lons, flags = zip(*nodes)
        self.leftBottomRightTop = [min(lons), min(lats), max(lons), max(lats)]
        # remove duplicate edges caused by bidirectionality of the graph
        tmp = set([])
        for (s, t, w) in edges:
            if s < t:
                tmp.add((s, t, w))
            else:
                tmp.add((t, s, w))
        edges = list(tmp)

        # Map weights to nodes
        heat = [0.] * len(nodes)
        for (s, t, cost) in edges:
            count = float(cost)
            for nodeIndex in [s, t]:
                # Only sum up for forest nodes
                if nodes[nodeIndex][2] == 0:
                    continue
                heat[nodeIndex] += count
        #self.maximum = max(heat)
        # Visualization scales better with this: Choose median of non-zero.
        intensities = np.array(sorted(heat))
        intensities = intensities[intensities[:]>0]
        self.maximum = intensities[len(intensities)/2]
        # Sort by latitude and throw away zero entries.
        nodeHeat = sorted(zip(lats, lons, heat))
        self.heatmap = np.array([node for node in nodeHeat if node[2] != 0.])

    def extract(self, bbox):
        """Returns the part of the heat map data inside the bounding box."""
        minLon, minLat, maxLon, maxLat = bbox
        if [minLon, minLat, maxLon, maxLat] == self.leftBottomRightTop:
            return self.heatmap
        else:
            i = 0
            while i < len(self.heatmap) and self.heatmap[i][0] < minLat:
                i += 1  # could use exponential or binary search here
            filtered = np.zeros([len(self.heatmap) - i, 3])
            j = i
            while j < len(self.heatmap) and self.heatmap[j][0] <= maxLat:
                lat, lon, heat = self.heatmap[j]
                if lon >= minLon and lon <= maxLon:
                    filtered[j-i] = self.heatmap[j]
                j += 1
            filtered = np.resize(filtered, [j-i,3])
            return filtered

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
        coords = np.zeros([yres+2, xres+2, 2])


        lat = latStart
        y = 0
        while y < coords.shape[0]:
            lon = lonStart
            x = 0
            while x < coords.shape[1]:
                coords[y,x] = (lat,lon)
                lon += lonFraction
                x += 1
            lat += latFraction
            y += 1

        raster = np.zeros([yres+2,xres+2])
        i = 0
        while i < len(self.heatmap) and self.heatmap[i][0] < latStart:
            i += 1  # could use exponential or binary search here
        while i < len(self.heatmap) and self.heatmap[i][0] < maxLat + 0.5 * latFraction:
            lat, lon, heat = self.heatmap[i]
            if lon >= lonStart and lon < maxLon + 0.5 * lonFraction:
                ly = (lat + 0.5 * latFraction - latStart) / latFraction
                lx = (lon + 0.5 * lonFraction - lonStart) / lonFraction
                raster[ly,lx] += heat
            i += 1
        #print np.dstack([coords, raster])[raster[:] > 0]
        return np.dstack([coords, raster])[raster[:] > 0], latFraction



