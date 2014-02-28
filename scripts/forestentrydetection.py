""" forestentrydetection

    OSM denotes forest polygons as ways with tag either
      <tag k="landuse" v="forest"/>
    or
      <tag k="natural" v="wood"/>

    First sweep: Read all ways, store forest boundary node references.
    Second sweep: Store lat-lon pairs for all boundary nodes in the correct
    order.
""" 

from PIL import Image, ImageDraw
import numpy as np

f = open("saarland-130822.osm")
forest_ways = []

for line in f:
  stripped = line.strip()
  if stripped.startswith('<way'):
    state = 'way'
    way_id = int(line.split('id=\"')[1].split('\"')[0])
  elif stripped.startswith('</way'):
    state = 'none'
  elif state == 'way' and stripped.startswith('<tag'):
    >>> pattern = re.compile("\D*k=\"(\w+)\" v=\"(\w+)\"\D*")
    >>> print pattern.match("<tag k=\"landuse\" v=\"forest\"").group(1)
    landuse
    >>> print pattern.match("<tag k=\"landuse\" v=\"forest\"").group(2)
    forest
    >>> print pattern.match("<tag k=\"landuse\" v=\"forest\"").group()
    <tag k="landuse" v="forest"

