'''
    Entry point.

    For every WEP, this enumerates walkways in the forest which fulfill a set of
    conditions.

    Usage:
'''
USAGE = \
    'enumerate_forest_walkways.py <WEPS> <OSM_ID_MAP> <FOREST_NODE_IDS> <GRAPH>'

import pickle
import sys
from enumerate_walkways import WayTree, WayGenerator, enumerate_walkways


def main():
  if len(sys.argv) < 5:
    print USAGE
    exit(1)
  weps = pickle.load(open(sys.argv[1]))
  osm_id_map = pickle.load(open(sys.argv[2]))
  forest_nodes_osm_ids = pickle.load(open(sys.argv[3]))
  g = pickle.load(open(sys.argv[4]))

  ''' concentrate on the inner forests '''
  # outside_nodes = g.nodes - set([osm_id_map[id] for id in forest_nodes_osm_ids])
  # g.remove_partition(outside_nodes)

  ''' generate the walkways from every wep to all weps (within distance) '''
  wep_nodes = [osm_id_map[osm_id] for osm_id in weps]
  wep_nodes_set = set(wep_nodes)
  for node in wep_nodes:
    walkways = enumerate_walkways(g, node, target_nodes=wep_nodes_set, \
        cost_limit=5*60, local_cycle_depth=5)
    print walkways
    s = raw_input("Press ENTER for next cycle.")

if __name__ == '__main__':
  main()

