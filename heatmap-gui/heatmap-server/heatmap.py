"""heatmap.py

Contains the Heatmap class.

"""
import numpy as np
from math import floor

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
        self.maximum = max(heat)
        # Test: Maybe scaling is better with this:
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
                i += 1
            filtered = np.zeros([len(self.heatmap) - i, 3])
            j = i
            while j < len(self.heatmap) and self.heatmap[j][0] <= maxLat:
                lat, lon, heat = self.heatmap[j]
                if lon >= minLon and lon <= maxLon:
                    filtered[j-i] = self.heatmap[j]
                j += 1
            filtered = np.resize(filtered, [j-i,3])
            return filtered

    def rasterize(self, bbox, (xres,yres)=(180,120)):  #=(640,)
        """Returns a raster discretizing the intensities inside the bbox."""
        minLon, minLat, maxLon, maxLat = bbox
        latFraction = (maxLat - minLat) / (yres - 1.)
        lonFraction = latFraction  # (maxLon - minLon) / (xres - 1.)
        print "latFrac, lonFrac: ", latFraction, lonFraction
        i = 0
        while i < len(self.heatmap) and self.heatmap[i][0] < minLat:
            i += 1

        xres = floor((maxLon - minLon) / lonFraction)
        coords = np.zeros([yres, xres, 2])
        latStart = floor(minLat / latFraction) * latFraction + latFraction
        lonStart = floor(minLon / lonFraction) * lonFraction + lonFraction
        print "minLat, latStart ", minLat, latStart
        print "minLon, lonStart ", minLon, lonStart
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

        raster = np.zeros([yres,xres])
        while i < len(self.heatmap) and self.heatmap[i][0] <= maxLat:
            lat, lon, heat = self.heatmap[i]
            if lon >= minLon and lon <= maxLon:
                ly = (lat - latStart) / latFraction
                lx = (lon - lonStart) / lonFraction
                raster[ly,lx] += heat
            i += 1
        #print np.dstack([coords, raster])[raster[:] > 0]
        return np.dstack([coords, raster])[raster[:] > 0]



