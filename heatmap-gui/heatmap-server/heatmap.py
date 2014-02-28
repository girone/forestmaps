"""heatmap.py

Contains the Heatmap class.

"""
import numpy as np

class Heatmap(object):
    def __init__(self, nodes, edges, weights=None, nodeFlags=None):
        """Constructs the heatmap.

        The heatmap will be a set of coordinates and labels, one for each node.

        """
        nodes = np.array([(lat, lon) for (lat, lon, _) in nodes])
        lat, lon = zip(*nodes)
        self.leftBottomRightTop = [min(lon), min(lat), max(lon), max(lat)]
        assert len(edges) == len(weights)
        if weights:
            # WORKAROUND: Fix missing edges with empty weight
            for index, (edge, weight) in enumerate(zip(edges, weights)):
                if edge == []:
                    edges[index] = (0, 0, [])
                    weights[index] = 0
            edges = [(s, t, w) for (s, t, _), w in zip(edges, weights)]
        else:
            # remove duplicate edges caused by bidirectionality of the graph
            tmp = set([])
            for (s, t, labels) in edges:
                if s < t:
                    tmp.add((s, t, labels[0]))
                else:
                    tmp.add((t, s, labels[0]))
            edges = list(tmp)

        # Map weights to nodes
        heat = [0.] * len(nodes)
        for (s, t, cost) in edges:
            count = float(cost)
            for nodeIndex in [s, t]:
                # WORKAROUND: Only sum up for forest nodes
                assert nodeFlags
                if nodeFlags[nodeIndex] == 0:
                    continue
                # ENDOF WORKAROUND
                heat[nodeIndex] += count
        self.maximum = max(heat)
        # Test: Maybe scaling is better with this:
        intensities = np.array(sorted(heat))
        intensities = intensities[intensities[:]>0]
        self.maximum = intensities[len(intensities)/2]
        # Sort by latitude and throw away zero entries.
        nodeHeat = sorted(zip(lat, lon, heat))
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

    def rasterize(self, bbox, (xres,yres)=(180,120)):  #=(640,480)
        """Returns a raster discretizing the intensities inside the bbox."""
        minLon, minLat, maxLon, maxLat = bbox
        latFraction = (maxLat - minLat) / (yres - 1.)
        lonFraction = (maxLon - minLon) / (xres - 1.)
        i = 0
        while i < len(self.heatmap) and self.heatmap[i][0] < minLat:
            i += 1

        coords = np.zeros([yres,xres,2])
        lat = minLat
        y = 0
        while lat <= maxLat:
            lon = minLon
            x = 0
            while lon <= maxLon:
                coords[y,x] = (lat,lon)
                lon += lonFraction
                x += 1
            lat += latFraction
            y += 1

        raster = np.zeros([yres,xres])
        while i < len(self.heatmap) and self.heatmap[i][0] <= maxLat:
            lat, lon, heat = self.heatmap[i]
            if lon >= minLon and lon <= maxLon:
                ly = (lat - minLat) / latFraction
                lx = (lon - minLon) / lonFraction
                raster[ly,lx] += heat
            i += 1
        #print np.dstack([coords, raster])[raster[:] > 0]
        return np.dstack([coords, raster])[raster[:] > 0]



