"""heatmap.py

Contains the Heatmap class.

"""

class Heatmap(object):
    def __init__(self, nodes, edges, weights=None, nodeFlags=None):
        """Constructs the heatmap.

        The heatmap will be a set of coordinates and labels, one for each node.

        """
        nodes = [(lat, lon) for (lat, lon, _) in nodes]
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
        # Sort by latitude and throw away zero entries.
        self.heatmap = sorted(zip(lat, lon, heat))
        self.heatmap = [(lat, lon, heat) for (lat, lon, heat) in self.heatmap
                        if heat != 0.]

    def extract(self, bbox):
        """Returns the part of the heat map data inside the bounding box."""
        minLon, minLat, maxLon, maxLat = bbox
        if [minLon, minLat, maxLon, maxLat] == self.leftBottomRightTop:
            return self.heatmap
        else:
            filtered = []
            i = 0
            while i < len(self.heatmap) and self.heatmap[i][0] < minLat:
                i += 1
            while i < len(self.heatmap) and self.heatmap[i][0] <= maxLat:
                lat, lon, heat = self.heatmap[i]
                if lon >= minLon and lon <= maxLon:
                    filtered.append((lat, lon, heat))
                i += 1
            return filtered
