'''
    Entry point.

    For every WEP, this enumerates walkways in the forest which fulfill a set of
    conditions.

    Usage:
'''
USAGE = \
    'enumerate_forest_walkways.py <WEPS> <OSM_ID_MAP> <FOREST_NODE_IDS> ' \
    '<GRAPH> <NODEINFO>'

import pickle
import sys
import os.path
from enumerate_walkways import WayTree, WayGenerator, enumerate_walkways
import visual_grid
import edgedistance


def main():
  if len(sys.argv) < 6:
    print USAGE
    exit(1)
  weps = pickle.load(open(sys.argv[1]))
  osm_id_map = pickle.load(open(sys.argv[2]))
  forest_nodes_osm_ids = pickle.load(open(sys.argv[3]))
  g = pickle.load(open(sys.argv[4]))
  nodeinfo = pickle.load(open(sys.argv[5]))

  forest_polygons = pickle.load(open("data/saarland-130822.forest_polygons.out"))

  ''' Set parameters '''
  limit = 20*60

  wep_nodes = [osm_id_map[osm_id] for osm_id in weps]
  wep_nodes_set = set(wep_nodes)

  ''' Concentrate way generation on forests '''
  n = len(g.nodes)
  outside_nodes = g.nodes - set([osm_id_map[id] for id in forest_nodes_osm_ids])
  outside_nodes -= wep_nodes_set
  g.remove_partition(outside_nodes)
  print n, len(g.nodes)

  ''' Contract binary nodes except WEPs. '''
  n = len(g.nodes)
  g.contract_binary_nodes(exclude=wep_nodes)
  print n, len(g.nodes)


  ''' Compute the distance to the edge of the woods (or load it) '''
  print 'Computing edge distance...'
  name = "data/saarland-130822.edge_distance.out"
  if os.path.exists(name):
    d_edge = pickle.load(open(name))
  else:
    d_edge = edgedistance.compute_edge_distance(g, wep_nodes, limit/2)
    pickle.dump(d_edge, open(name, 'w'))
  print 'Done!'


  ''' Generate the walkways from every wep to all weps (within distance) '''
  count = 0
  for node in wep_nodes:
    count += 1
    walkways = enumerate_walkways(g, node, target_nodes=wep_nodes_set, \
        cost_limit=limit, local_cycle_depth=5, edge_distance=d_edge)
    print "%d of %d ways generated" % (count, len(wep_nodes))
    #print walkways
    #print " %d  ways found with cost limit %.1f min." % (len(walkways), limit/60.)
    #s = raw_input("Press ENTER for next cycle.")


if __name__ == '__main__':
  main()

