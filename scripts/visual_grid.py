""" Visual Grid - visualization of nodes, edges and so on """
import grid

def visualize_nodes(graph, nodeinfo, node_ids=set(), inset=1.0, forest=[]):
  """ Draws a part of @graph denoted by @node_ids to the screen. """
  nodes_to_draw = node_ids if node_ids else range(len(graph.nodes))
  bbox = grid.bounding_box([nodeinfo[id].pos for id in nodes_to_draw])
  w, h = bbox[1][0] - bbox[0][0], bbox[1][1] - bbox[0][1]
  bbox[0][0] -= inset * w
  bbox[1][0] += inset * w
  bbox[0][1] -= inset * h
  bbox[1][1] += inset * h
  g = grid.Grid(bbox, grid_size=(1024,860), mode="RGB")

  for poly in forest:
    g.fill_polygon(poly, fill='#1a7d02')
  for node in nodes_to_draw:
    px, py = nodeinfo[node].pos
    g.draw_circle((px, py), rad=4, outline='#AA0000', fill='#AA0000')
    g.write_text((px, py), str(node))
  for node in nodes_to_draw:
    for other, edge in graph.edges[node].items():
      g.draw_line([nodeinfo[node].pos, nodeinfo[other].pos], fill='#00FFFF', \
          width=2)
  g.show()

