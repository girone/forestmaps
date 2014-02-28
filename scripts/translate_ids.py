''' 
For the input OSM file this remembers all node ids and shifts them by a certain
number, translating them to another range.

Usage:
  python SELF.py <OSM_FILE> <INDEX_SHIFT>

'''
import sys
import re


node_id_map = {}
way_id_map = {}


def main():
  def replace_node_id(match_obj):
    new_id = node_id_map[match_obj.group(2)]
    return match_obj.group(1) + str(new_id) + match_obj.group(3)
  def replace_way_id(match_obj):
    new_id = way_id_map[match_obj.group(2)]
    return match_obj.group(1) + str(new_id) + match_obj.group(3)

  if len(sys.argv) < 3:
    print "Error: Wrong arguments."
    exit(1)

  filename = sys.argv[1]
  index_shift = int(sys.argv[2])

  # first sweep: collect node ids
  p_node = re.compile('(.*<node id=")(-*\d+)(".*)')
  p_way = re.compile('(.*<way id=")(-*\d+)(".*)')
  with file(sys.argv[1]) as f:
    for line in f:
      r1 = p_node.match(line)
      r2 = p_way.match(line)
      if r1:
        node_id_map[r1.group(2)] = len(node_id_map) + index_shift
      elif r2:
        way_id_map[r2.group(2)] = len(way_id_map) + index_shift
      elif line.strip().startswith("<relation"):  # ignore relations
        break

  # second sweep: translate node ids and occurrences in other objects (ways...)
  p_noderef = re.compile('(.*<nd ref=")(-*\d+)(".*)')
  with file(sys.argv[1]) as f:
    for line in f:
      line = line.strip()
      line = p_node.sub(replace_node_id, line) 
      line = p_noderef.sub(replace_node_id, line)
      line = p_way.sub(replace_way_id, line)
      if line == '<tag k="Objektname" v="Wald" />':
        print '<tag k="landuse" v="forest" />'
      elif line.startswith("<relation"):  # ignore relations
        break
      else:
        print line
    print "</osm>"


if __name__ == "__main__":
  main()
