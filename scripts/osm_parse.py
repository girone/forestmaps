""" osm_parse.py -- Code for parsing OpenStreetMap .osm files.

"""
import math
import re
import sys, os
from collections import defaultdict
from graph import Graph, Edge, NodeInfo


OSMWayTypesAndSpeed = [('motorway'       , 130),
                       ('motorway_link'  , 130),
                       ('trunk'          , 120),
                       ('trunk_link'     , 120),
                       ('primary'        , 120),
                       ('primary_link'   , 120),
                       ('secondary'      , 80),
                       ('secondary_link' , 80),
                       ('tertiary'       , 80),
                       ('tertiary_link'  , 70),
                       ('unclassified'   , 50),
                       ('road'           , 50),
                       ('residential'    , 45),
                       ('living_street'  , 30),
                       ('service'        , 30),
                       ('track'          , 30),
                       ('path'           , 5),
                       ('unsurfaced'     , 30),
                       ('cycleway'       , 25),
                       ('bridleway'      , 5),
                       ('OTHER'          , 0),
                       ('footway'        , 5),
                       ('pedestrian'     , 5),
                       ('steps'          , 3)]


OSMSpeedTable = dict(OSMWayTypesAndSpeed)
OSMWayTypeToId = {v[0] : id
                  for id, v in enumerate(OSMWayTypesAndSpeed)}


def type_to_speed(type, speed_table):
    if type in speed_table:
        return speed_table[type]
    else:
        print "type '" + type + "' unknown."
        return 0


def OSMWayTagInterpreter(key, val):
    """Interprets way tags of a standard OSM file.

    Such lines have a format
      <tag k="KEY" v="VAL" />
    We are interested only in ways of KEY=highway and with VAL being one of
    the way types declared in the speed table.

    """
    if key == 'highway' and val in OSMSpeedTable:
        return type_to_speed(val, OSMSpeedTable)
    return False


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


def is_forest_tag(key, val):
    """Returns true on key, value pairs which represent forest OSM tags."""
    return ((key == 'landuse' and val == 'forest') or
            (key == 'natural' and val == 'wood'))


def check_way_order(wayRefs, ref_to_way):
    """Returns true if the referenced ways represent a ring.

    All ways must be defined. A ring has the form [a...b],[b...c],...,[X...a],
    but the referenced part lists may be reversed, For example, the result can
    reference [b...c] OR [c...b].

    """
    firstWay = ref_to_way(wayRefs[0])
    firstNode = firstWay[0]
    lastNode = firstWay[-1]
    for ref in wayRefs[1:]:
        way = ref_to_way(ref)
        if lastNode == way[0]:
            lastNode = way[-1]
        elif lastNode == way[-1]:
            lastNode = way[0]
        else:
            return false
    return lastNode == firstNode


def fix_way_order(wayRefs, ref_to_way):
    """Brings the wayReferences in order such that they form a ring.

    A ring has the form [a...b],[b...c],...,[X...a]. Note that the direction of
    the ways referenced by the elements is not determined. For example, the
    result can reference [b...c] OR [c...b].

    """
    # Quadratic time variant, linear one is too elaborate
    orderedWayRefs = [wayRefs[0]]
    firstWay = ref_to_way(wayRefs[0])
    lastNode = firstWay[-1]
    unusedWayRefs = set(wayRefs[1:])
    while len(unusedWayRefs) > 0:
        for ref in unusedWayRefs:
            way = ref_to_way(ref)
            if way[0] == lastNode:
                lastNode = way[-1]
            elif way[-1] == lastNode:
                lastNode = way[0]
            else:
                continue
            orderedWayRefs.append(ref)
            unusedWayRefs.remove(ref)
            break
    return orderedWayRefs


def ensure_way_order(listOfNodeIdLists):
    """Sorts the ways such that they are 'transitive'.

    The resulting sequence will be [[a...b],[b...c],[c...d],...,[X...a]].

    Undefined part ways will result in gaps, for example
        [[a...b], None, [c...d], [e...d]]
    will be transformed into
        [[a...b], None, [c...d], [d...e]]

    """
    def have_common_border_element(listA, listB):
        return (listA[0] == listB[0] or listA[0] == listB[-1] or
                listA[-1] == listB[0] or listA[-1] == listB[-1])
    def find_first_defined_element(sequence):
        """Returns the first defined element and its index as (index, elem)."""
        index = element = None
        for i,e in enumerate(sequence):
            if e:
                index = i
                element = e
                break
        return index, element
    def find_matching_second_element(sequence, start, obj):
        """Returns index and element of the first element matching 'obj'.

        A match to 'obj' shares the first or last element. Starts at 'start'.

        """
        index = element = None
        for i,e in enumerate(sequence):
            if e and have_common_border_element(e, obj):
                index = i
                element = e
                break
        return index, element
    def append_first_and_continue(expandedWay, result, remaining):
        # Workaround for polygons splittet at the border: Add the first as
        # separate polygon, proceed with the following.
        result.append(firstDefinedWay)
        result.extend(ensure_way_order(remaining))
        return result

    if len(listOfNodeIdLists) == 0:
        return []
    used = [False] * len(listOfNodeIdLists)
    startIndex, firstDefinedWay = find_first_defined_element(listOfNodeIdLists)
    assert firstDefinedWay
    _, secondDefinedWay = find_matching_second_element(listOfNodeIdLists,
                                                       startIndex + 1,
                                                       firstDefinedWay)
    result = []
    if not secondDefinedWay:
        return append_first_and_recurse(firstDefinedWay, result,
                                        listOfNodeIdLists[startIndex+1:])
    assert len(firstDefinedWay) > 1 and len(secondDefinedWay) > 1
    firstId = firstDefinedWay[0]
    lastId = firstDefinedWay[-1]
    # Add the first way in the correct direction
    if lastId == secondDefinedWay[0] or lastId == secondDefinedWay[-1]:
        pass
    elif firstId == secondDefinedWay[0] or firstId == secondDefinedWay[-1]:
        firstDefinedWay.reverse()
    else:
        return append_first_and_recurse(firstDefinedWay, result,
                                        listOfNodeIdLists[startIndex+1:])
    result.append(firstDefinedWay)
    firstId = result[0][0]
    lastId = result[0][-1]
    # Label all undefined sequences and the current as used.
    for i in range(startIndex + 1):
        used[i] = True
    # Add the remaining way parts
    i = startIndex
    while i < len(listOfNodeIdLists) - 1:
        i += 1
        nodeIdList = listOfNodeIdLists[i]
        if used[i] or not nodeIdList:
            if nodeIdList == None:
                result.append(None)
                used[i] = True
            continue
        if lastId == nodeIdList[0]:
            result.append(nodeIdList)
            used[i] = True
        elif lastId == nodeIdList[-1]:
            nodeIdList.reverse()
            result.append(nodeIdList)
            used[i] = True
        else:
            match = False
            for j in range(i+1, len(listOfNodeIdLists)):
                way = listOfNodeIdLists[j]
                if used[j] or not way:
                    continue
                if way[0] == lastId:
                    result.append(way)
                elif way[-1] == lastId:
                    way.reverse()
                    result.append(way)
                else:
                    continue
                match = True
                used[j] = True
                break
            if match:
                # The way at index j has been matched instead of i, we have to
                # handle i again.
                i -= 1
            else:
                # In case the polygon is without a matching predecessor and
                # without a match among the remaining polygons just add it.
                result.append(nodeIdList)
                used[i] = True
        if result[-1]:  # is not None
            lastId = result[-1][-1]
    if not all(used):
        print zip(used, listOfNodeIdLists)
        print result
        assert all(used)
    return result


class OSMRelation(object):
    """Right now, this represents a multipolygon.

    See http://wiki.openstreetmap.org/wiki/Relation:multipolygon

    """
    def __init__(self, id_):
        self.outerOsmWays = []
        self.innerOsmWays = []
        self.tags = {"id": id_}

    def add_member(self, type_, ref, role):
        if type_ == "way":
            if role == "outer":
                self.outerOsmWays.append(ref)
            elif role == "inner":
                self.innerOsmWays.append(ref)
            else:
                print "Error: Unexpected role for relation member way: ", role

    def is_forest_polygon(self):
        # Condition removed. Reason: Data errors.
        #return self.tags["type"] == "multipolygon" and self.tags["forest"]
        return ("forest" in self.tags and self.tags["forest"])

    def is_boundary_polygon(self):
        return ("type" in self.tags and self.tags["type"] == "boundary")

    def expand_to_polygons(self, ref_to_way, ref_to_node):
        """Expands the osm ways described by this relation to polygons.

        Takes two functions mapping from way ids to ways (lists of node
        references) and from node ids to nodes (pairs of lat, lon).
        Expands the multipolygon relation such that all ways in self.outer
        and self.inner form polygons.

        """
        outer = self.expand_ways_to_polygons(self.outerOsmWays, ref_to_way,
                                             ref_to_node)
        inner = self.expand_ways_to_polygons(self.innerOsmWays, ref_to_way,
                                             ref_to_node)
        return outer, inner

    def add_tag(self, key, value):
        """Adds a tag to tags of this relation."""
        self.tags[key] = value

    def get_value(self, key):
        """Returns the value of a tag with key."""
        return (self.tags[key] if key in self.tags else None)

    def expand_ways_to_polygons(self, listOfWayIds, ref_to_way, ref_to_node):
        """Expands a set of ways (lists of way references) to a polygon.

        In a first step, the way references are translated into osm node ids.
        If one or more osm way ids are not defined, these are considered as
        gaps. For fully defined ways we ensure that the node ids form a ring
        by reordering them if neccessary (by reversing part ways).

        In the second step, gaps are handled as follows:
        1) If there is a gap between the last node of a way and the first node
        of the next way, a new polygon is started.
        2) If there is a gap because the previous way(-part) is missing in the
        dataset, the two ways enclosing the gap are connected by a direct line
        instead.

        TODO(Jonas): Put this method outside of OSMRelation?
        """
        def extract_latlon(node):
            return (node[0], node[1])

        if len(listOfWayIds) == 0:
            return []

        # Translate ids to nodeIdLists and reorder if neccessary.
        ways = map(ref_to_way, listOfWayIds)
        ways = [w if w else (None, None, None) for w in ways]
        osmWayIds, wayTypes, listOfNodeIdLists = zip(*ways)
        if not any(listOfNodeIdLists):
            return []
        listOfNodeIdLists = ensure_way_order(listOfNodeIdLists)

        # Convert node ids to polygons.
        resultPolygons = []
        polygon = []
        lastNodeIdOfLastWay = -1
        preceedingGapBecauseOfMissingWay = False
        for i, listOfNodeIds in enumerate(listOfNodeIdLists):
            if not listOfNodeIds:
                # ... because the way is missing in the OSM data
                preceedingGapBecauseOfMissingWay = True
            else:
                firstNodeId = listOfNodeIds[0]
                # Gap condition 1+2): Finish the current and start a new polygon.
                if (firstNodeId != lastNodeIdOfLastWay or
                    preceedingGapBecauseOfMissingWay):
                    # TODO(Jonas): In case of condition 2, it's maybe better to
                    # connect the polygons (do not start a new one).
                    if len(polygon) > 2:
                        resultPolygons.append(polygon)
                    polygon = []
                    preceedingGapBecauseOfMissingWay = False
                for nodeId in listOfNodeIds:
                    polygon.append(extract_latlon(ref_to_node(nodeId)))
                lastNodeIdOfLastWay = listOfNodeIds[-1]
        if len(polygon) > 2:  # add last polygon
            resultPolygons.append(polygon)
        return resultPolygons


relevantRelationTags = set([("type", "multipolygon"),
                            ("type", "boundary"),
                            ("boundary", "administrative")])


def outer(listA, listB):  # TODO(Jonas): Find a better name.
    """Returns the outer product, relational join or wtf ever."""
    return [(a, b) for a in listA for b in listB]


relevantPOITags = set(
    outer(["tourism"], ["viewpoint", "attraction", "artwork", "picnic_site"]) +
    outer(["natural"], ["peak", "spring"]) +
    outer(["amenity"], ["place_of_worship", "restaurant", "bar", "shelter",
                        "bench", "drinking_water", "bbq", "biergarten", "cafe",
                        "fountain", "pub", ]) +
    outer(["leisure"], ["playground", "miniature_golf", "nature_reserve",
                        "swimming_pool", "water_park", "park", "garden"]) +
    [("fireplace", "yes")] +
    [("beer_garden", "yes")] +
    outer(["man_made"], ["tower", "bridge"]) +
    outer(["historic"], ["memorial", "castle"]) +
    outer(["waterway"], ["stream", "river", "riverbank"]) +
    outer(["water"], ["river", "lake"]))


def tag_to_poi_category(key, value):
    category = 1
    if key == "amenity" or value == "viewpoint":
        category = 2
    elif value == "castle" or value == "tower":
        category = 3
    return category


class OSMParser(object):
    def __init__(self, maxSpeed):
        self.maxSpeed = maxSpeed
        self.regexPatternNode = re.compile(
                '<node id="(\S+)".* lat="(\S+)" lon="(\S+)"')
        self.regexPatternWayStart = re.compile(
                '<way.* id="(\S+)".*')
        self.regexPatternRelationMember = re.compile(
                '<member type="way" ref="(\S+)" role="(\S+)"/>')
        self.regexPatternTag = re.compile(
                '<tag k="(.+)" v="(.+)"/>')
        self.osmNodes = []
        self.osmHighwayEdges = []
        self.osmNodeIdPolygons = []
        self.osmIdToNodeIndex = None
        self.osmIdToArcIndex = None
        self.osmRelations = []
        self.lineNumber = 0
        self.currentWayId = -1
        self.currentWayType = 'undefined'
        # Stores tags for nodes and ways (relations are separate)
        self.osmTags = defaultdict(dict)

    def osm_id_to_node(self, osmId):
        return self.osmNodes[self.osm_id_to_node_index(osmId)]

    def osm_id_to_node_index(self, osmId):
        if not self.osmIdToNodeIndex:
            self.osmIdToNodeIndex = {osm : i
                                 for i, (_,_,osm) in enumerate(self.osmNodes)}
        return self.osmIdToNodeIndex[osmId]

    def osm_id_to_arc(self, osmId):
        index = self.osm_id_to_arc_index(osmId)
        return (self.osmNodeIdPolygons[index] if index else None)

    def osm_id_to_arc_index(self, osmId):
        if not self.osmIdToArcIndex:
            dic = {osmId_ : i
                   for i, (osmId_,_,_) in enumerate(self.osmNodeIdPolygons)}
            self.osmIdToArcIndex = dic
        if osmId not in self.osmIdToArcIndex:
            # Some ways are referenced in relations but outside of the dataset.
            return None
        return self.osmIdToArcIndex[osmId]

    def parse_node_properties(self, match):
        """Extracts latitude, longitude and osmID from a regex match object."""
        return (float(match.group(2)), float(match.group(3)),
                int(match.group(1)))

    def compute_dist_between_ids(self, osmIdA, osmIdB, wayClass):
        (latA, lonA, _) = self.osmNodes[self.osm_id_to_node_index(osmIdA)]
        (latB, lonB, _) = self.osmNodes[self.osm_id_to_node_index(osmIdB)]
        return great_circle_distance((latA, lonA), (latB, lonB))

    def compute_cost_between_ids(self, osmIdA, osmIdB, wayClass):
        s = self.compute_dist_between_ids(osmIdA, osmIdB, wayClass)
        v = type_to_speed(wayClass, OSMSpeedTable)
        v = v if v <= self.maxSpeed else self.maxSpeed
        t = s / (v / 3.6)
        return t

    def expand_current_way_to_edges(self, bidirectional=True):
        """Expands a list of way node ids to a sequence of edges."""
        wayNodeIdList = self.currentWay
        edges = []
        size = len(wayNodeIdList)
        for i, j in zip(range(size-1), range(1,size)):
            osmIdA = wayNodeIdList[i]
            osmIdB = wayNodeIdList[j]
            wayClass = self.currentHighwayCategory
            labels = [self.compute_dist_between_ids(osmIdA, osmIdB, wayClass),
                      self.compute_cost_between_ids(osmIdA, osmIdB, wayClass),
                      OSMWayTypeToId[wayClass]]
            edges.append((wayNodeIdList[i], wayNodeIdList[j], labels))
            if bidirectional:
                edges.append((wayNodeIdList[j], wayNodeIdList[i], labels))
        return edges

    def read_node_line(self, line, state):
        """Processes a line which denotes a node and returns a new state."""
        if state != 'read_nodes' and line.startswith('<node'):
            state = 'read_nodes'
        if state == 'read_nodes':
            res = self.regexPatternNode.match(line)
            if res:
                self.osmNodes.append(self.parse_node_properties(res))
                if not line.endswith('/>'):
                    state = 'node_content'
            else:
                if line.startswith("<way"):
                    state = 'read_ways'
                else:
                    print "Error: Got unexpected line in state 'read_nodes':"
                    print self.lineNumber, line
                    exit(1)
        elif state == 'node_content':
            res = self.regexPatternTag.match(line)
            if res:
                #print "matched ", line
                key, value = res.group(1), res.group(2)
                osmID = self.osmNodes[-1][2]
                if (key, value) in relevantPOITags:
                    self.osmTags[osmID][key] = value
            elif line.startswith("</node>"):
                state = 'read_nodes'
        return state

    def read_way_line(self, line, state):
        """Processes a line which describes a way and returns a new state."""
        if line.startswith("<way"):
            res = self.regexPatternWayStart.match(line)
            assert res
            self.currentWay = []
            self.currentWayType = 'undefined'
            self.currentHighwayCategory = None
            self.currentWayId = int(res.group(1))
        elif line.startswith("<nd"):
            osmId = int(line.split("ref=\"")[1].split("\"")[0])
            self.currentWay.append(osmId)
        elif line.startswith("<tag"):
            self.process_way_tag_line(line)
        elif line.startswith("</way"):
            self.finalize_way()
        elif line.startswith("<relation"):
            state = 'read_relations'
        else:
            pass
        return state

    def process_way_tag_line(self, line):
        """Processes an OSM way tag line."""
        res = self.regexPatternTag.match(line)
        if res:
            key, val = res.group(1), res.group(2)
            if key == 'highway' and val in OSMSpeedTable:
                self.currentWayType = 'highway'
                self.currentHighwayCategory = val
            elif is_forest_tag(key, val):
                self.currentWayType = 'forest_delimiter'
            elif (key, val) in relevantPOITags:
                self.osmTags[self.currentWayId][key] = val

    def finalize_way(self):
        """Finishes the current way."""
        waytype = self.currentWayType
        # Store all ways, as they may serve as boundary in a relation.
        polyline = self.currentWay
        osmId = self.currentWayId
        self.osmNodeIdPolygons.append((osmId, waytype, polyline))
        if waytype == 'highway':
            self.osmHighwayEdges.extend(self.expand_current_way_to_edges())

    def read_relation_line(self, line, state):
        """Processes a line associated with a relation."""
        if line.startswith("<relation"):
            id_ = int(line.split('"')[1])
            self.currentRelation = OSMRelation(id_)
        elif line.startswith("</relation"):
            self.finalize_relation(self.currentRelation)
            self.currentRelation = None
        elif line.startswith("</osm>"):
            state = 'other'
        else:
            self.process_multipolygon_relation_content_line(line)
        return state

    def process_multipolygon_relation_content_line(self, line):
        def is_relevant_tag(key, value):
            return (key == "name" or key == "wikipedia" or key == "admin_level"
                    or (key, value) in relevantRelationTags)
        assert self.currentRelation
        res = self.regexPatternRelationMember.match(line)
        if res:
            ref = int(res.group(1))
            role = res.group(2)
            if role == "outer" or role == "inner":
                self.currentRelation.add_member("way", ref, role)
        else:
            res = self.regexPatternTag.match(line)
            if res:
                key, val = res.group(1), res.group(2)
                if is_forest_tag(key, val):
                    self.currentRelation.add_tag("forest", True)
                elif is_relevant_tag(key, val):
                    self.currentRelation.add_tag(key, val)

    def is_relevant_relation(self, r):
        return (r.is_forest_polygon() or
                #(r.get_value("type") == "multipolygon" and len(r.tags) > 1) or
                r.get_value("type") == "boundary" and "name" in r.tags and "admin_level" in r.tags)

    def finalize_relation(self, relation):
        assert relation
        if self.is_relevant_relation(relation):
            self.osmRelations.append(relation)

    def expand_relations(self):
        """Expands relations. Should be called after all relations are read."""
        self.outerForestPolygons = []
        self.innerForestPolygons = []
        self.administrativeBoundaries = []
        self.osmIdToArcIndex = None
        for relation in self.osmRelations:
            if relation.is_forest_polygon():
                outer, inner = relation.expand_to_polygons(self.osm_id_to_arc,
                                                           self.osm_id_to_node)
                self.outerForestPolygons.extend(outer)
                self.innerForestPolygons.extend(inner)
            else:
                #print "Processing boundary of " + str(relation.get_value("name"))
                outer, _ = relation.expand_to_polygons(self.osm_id_to_arc,
                                                       self.osm_id_to_node)
                self.administrativeBoundaries.append((relation.tags, outer))

    def read_line(self, line, state):
        """Reads and interprets a line."""
        if state == 'read_nodes' or state == 'init' or state == 'node_content':
            state = self.read_node_line(line, state)
        if state == 'read_ways':
            state = self.read_way_line(line, state)
        if state == 'read_relations':
            state = self.read_relation_line(line, state)
        return state

    def read_osm_file(self, filename):
        """Reads an Open Street Map file.

        Returns nodes, edges, forest polygons:
          - Nodes are tuples (lat, lon, osmID).
          - Edges are between two nodes, referred to by indices [0...#nodes-1].
          - Forest polygons, each is a list of tuples (lat, lon, osmID).
          - Inner forest polygons (glades), as above.

        Assumes that the OSM file is ordered such that it lists nodes before
        ways and ways before anything else.
        Assumes that ways list node references first and tags afterwards.

        """
        def get_filesize(f):
            old_file_position = f.tell()
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(old_file_position, os.SEEK_SET)
            return size
        state = 'init'
        print "Reading osm file..."
        with open(filename) as f:
            fsize = get_filesize(f)
            avgLinesize = 0.
            for line in f:
                self.lineNumber += 1
                avgLinesize = (1. / self.lineNumber * len(line) +
                      (self.lineNumber - 1.) / self.lineNumber * avgLinesize)
                state = self.read_line(line.strip(), state)
                if state == 'other':
                    break
                if self.lineNumber % 1000000 == 0:
                    sys.stdout.write("\rRead {0:.2f}%".format(
                            100. * self.lineNumber * avgLinesize / fsize))
                    sys.stdout.flush()
        print "...finished."

        print "Filtering and expanding parsed osm content..."
        poiCategory = self.label_points_of_interest(self.osmTags)

        nodes = self.highway_part(self.osmNodes, self.osmHighwayEdges)
        edges = self.translate_osm_edges(nodes, self.osmHighwayEdges)
        nodes, poiCategory = self.add_missing_poi_nodes(nodes, poiCategory)

        self.expand_relations()  # translates relations into node polygons
        enum = enumerate(self.osmNodeIdPolygons)
        nodeIdPolygons = [poly for i, (osmId, wayType, poly) in enum
                          if wayType == 'forest_delimiter']
        # TODO(jonas): Avoid double usage of forest borders in from relations.
        simplePolygons = self.translate_osm_to_node_polygons(nodeIdPolygons)
        outerForestPolygons = self.outerForestPolygons + simplePolygons
        innerForestPolygons = self.innerForestPolygons
        print "...done!"
        return (nodes,
                edges,
                (outerForestPolygons, innerForestPolygons),
                self.administrativeBoundaries,
                poiCategory)

    def add_missing_poi_nodes(self, nodes, poiCategory):
        """Adds nodes referenced by poiCategory to nodes if they are missing.

        Returns poiCategory extended by the index of each referenced node.

        """
        mapping = {osmId : index for index, (_,_,osmId) in enumerate(nodes)}
        for osmId, category in poiCategory.items():
            if osmId not in mapping:
                mapping[osmId] = len(nodes)
                nodes.append(self.osm_id_to_node(osmId))
        return nodes, {mapping[osmId] : (osmId, category)
                       for osmId, category in poiCategory.items()}

    def label_points_of_interest(self, osmTags):
        """Assigns POI categories to points and ways with POI tags."""
        def set_max(indexToCategory, osmId, category):
            if not osmId in indexToCategory:
                indexToCategory[osmId] = category
            else:
                indexToCategory[osmId] = max(indexToCategory[osmId], category)
        def process_poi_tags_for_node(osmId, tags, poiCategory):
            """Assigns the highest POI category of its labels to a node."""
            for key, value in tags.items():
                set_max(poiCategory, osmId, tag_to_poi_category(key, value))
        def dummy():
            try:
                self.osm_id_to_arc_index(0)
            except:
                pass
            try:
                self.osm_id_to_node_index(0)
            except:
                pass
        dummy()  # Dummy, creates the maps needed below.
        assert self.osmIdToNodeIndex
        assert self.osmIdToArcIndex
        poiCategory = defaultdict(int)
        for osmId, tags in osmTags.items():
            if osmId in self.osmIdToNodeIndex:
                process_poi_tags_for_node(osmId, tags, poiCategory)
            elif osmId in self.osmIdToArcIndex:
                arc = self.osm_id_to_arc(osmId)
                assert arc
                _, _, points = arc
                # expand the way to nodes
                for osmId in points:
                    process_poi_tags_for_node(osmId, tags, poiCategory)
            else:
                print osmId, " not in self.osmIdToArcIndex or self.osmIdToNodeIndex"
                assert False and "OSM id is missing."
        return poiCategory

    def highway_part(self, osmNodes, osmHighwayEdges):
        """Returns the nodes which are part of a highway in the OSM data."""
        isHighwayNode = [False] * len(osmNodes)
        for (s, t, _) in osmHighwayEdges:
            isHighwayNode[self.osm_id_to_node_index(s)] = True
            isHighwayNode[self.osm_id_to_node_index(t)] = True
        return [node for i, node in enumerate(osmNodes) if isHighwayNode[i]]

    def translate_osm_edges(self, highwayNodes, osmHighwayEdges):
        """Replaces osm node ids in edges with corresponding node indices."""
        mapping = {osm : index for index, (_,_,osm) in enumerate(highwayNodes)}
        return [(mapping[s], mapping[t], label)
                for (s, t, label) in osmHighwayEdges]

    def translate_osm_to_node_polygons(self, osmNodeIdPolygons):
        """Replaces osm node ids with coordinates."""
        tmp = [map(self.osm_id_to_node, poly) for poly in osmNodeIdPolygons]
        return [[(lat,lon) for lat,lon,_ in poly] for poly in tmp]


def dump_graph(nodes, edges, filename=None, nodeFlags=None):
    """Writes graph to some output target, stdout by default."""
    from itertools import izip
    if filename:
        with open(filename + ".graph.txt", "w") as f:
            f.write(str(len(nodes)) + "\n")
            f.write(str(len(edges)) + "\n")
            if not nodeFlags:
                for node in nodes:
                    (lat, lon, osm_id) = node
                    f.write("{0} {1} {2}\n".format(lat, lon, osm_id))
            else:
                for node, flag in izip(nodes, nodeFlags):
                    (lat, lon, osm_id) = node
                    f.write("{0} {1} {2} {3}\n".format(lat, lon, osm_id, flag))
            for edge in edges:
                s, t, labels = edge
                labelsAsString = " ".join([str(l) for l in labels])
                f.write("{0} {1} {2}\n".format(s, t, labelsAsString))
    else:
        print len(nodes)
        print len(edges)
        for node in nodes:
            (lat, lon, osm_id) = node
            print lat, lon#, osm_id
        for edge in edges:
            s, t, labels = edge
            labelsAsString = " ".join([str(l) for l in labels])
            print "{0} {1} {2}\n".format(s, t, labelsAsString)


def dump_pois(pois, fileprefix=None):
    """Dumps POIs, a mapping from index to osmId and category."""
    if not fileprefix:
        fileprefix = "output"
    with open(fileprefix + ".pois.txt", "w") as f:
        for index, (osmId, category) in sorted(list(pois.items())):
            f.write("{0} {1} {2}\n".format(index, osmId, category))

