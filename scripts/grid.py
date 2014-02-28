""" grid -- This module contains the class grid.

Copyright 2013: Institut fuer Informatik
Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>

"""
from PIL import Image, ImageDraw
import numpy as np
import sys
from itertools import chain


def hom(point):
  """ Returns homogenous representation of a point. """
  return np.matrix([[point[0]], [point[1]], [1]])


def bounding_box(points):
  assert len(points) > 1
  chained = chain(*points) if len(points[0]) != 2 else points
  xmax = ymax = float(-sys.maxint)
  xmin = ymin = float(sys.maxint)
  for point in chained:
    if xmax < point[0]:
      xmax = point[0]
    if xmin > point[0]:
      xmin = point[0]
    if ymax < point[1]:
      ymax = point[1]
    if ymin > point[1]:
      ymin = point[1]
  return [[xmin, ymin], [xmax, ymax]]


class Grid:
  """Represents a grid map, which maps points from an input space to grid cells

  The class provides methods to fill the grid with values, visualize
  it and to test for the value of single grid cells. It abstracts the
  mapping from input space to grid space, such that the external user does
  not have to care about this.

  The mapping from the input space to grid cells is done via a linear
  mapping via a transformation matrix for homogeneous coordinates
  constructed at initialization.

  The grid is constructed using a Image from PIL. The grid is accessed via
  an numpy-array, which is constructed from the Image at the first access
  after a series of changes. The state of the Grid is monitored in the
  variable self.updated.

  """
  def __init__(self, input_space, grid_size=(10240, 8600), mode="F"):
    """ Constructor.

    Initializes the grid and computes the transformation matrix mapping
    input values to grid cells.
    @mode: Specifies the color-scheme of the grid for values and
           visualization. Example values: 'F', 'RGB'

    """
    self.img = Image.new(mode, grid_size, 0)
    self.draw = ImageDraw.Draw(self.img)
    # self.grid = np.ones(1)
    self.grid = np.asarray(self.img)
    self.updated = False
    # set up transformation matrix (linear mapping for homogeneous coordinates)
    tx, ty = -input_space[0][0], -input_space[0][1]
    sx = (grid_size[0] - 1.) / (input_space[1][0] - input_space[0][0])
    sy = (grid_size[1] - 1.) / (input_space[1][1] - input_space[0][1])
    self.transformation = np.matrix( ((sx, 0, sx*tx),
                                      (0, sy, sy*ty),
                                      (0, 0, 1)) );

  def show(self):
    """ Plots the grid as image. """
    import matplotlib.pyplot as plt
    plt.figure()
    ax = plt.subplot(111)
    ax.imshow(self.img)
    #plt.gca().invert_yaxis()
    plt.show()

  def transform(self, point):
    """ Transforms (scale+shift) a point form the input to the grid space. """
    res = self.transformation * hom(point)
    return res.item(0), res.item(1)

  def fill_polygon(self, poly, fill=255):
    """ Fills an area of the grid corresponding to a polygon in the input space.
    """
    transformed = [self.transformation * hom(point) for point in poly]
    self.draw.polygon([(p.item(0), p.item(1)) for p in transformed], fill=fill)
    self.updated = True

  def draw_line(self, line_pts, fill='#FFFFFF', width=1):
    """ Draws a line along a set of points in the input space. """
    transformed = [self.transformation * hom(point) for point in line_pts]
    self.draw.line([(p.item(0), p.item(1)) for p in transformed],
        fill=fill, width=width)
    self.updated = True

  def draw_circle(self, (px, py), rad=1, outline='#00FF00', fill='#000000'):
    """ Draws a circle around @center=(px, py) with radius @rad. """
    transformed = self.transformation * hom((px, py))
    px, py = transformed.item(0), transformed.item(1)
    self.draw.ellipse(((px-rad, py-rad), (px+rad, py+rad)),
        outline=outline, fill=fill)
    self.updated = True

  def write_text(self, (px, py), text, fill='#FFFFFF'):
    """ Adds text to the grid. """
    transformed = self.transformation * hom((px, py))
    px, py = transformed.item(0), transformed.item(1)
    self.draw.text((px, py), text, fill=fill)

  def test(self, pos):
    """ Accesses a field of the grid. Updates the grid if necessary. """
    if self.updated:
      self.grid = np.asarray(self.img)
      self.updated = False
    assert len(pos) == 2
    transformed = self.transformation * hom(pos)
    row, column = int(transformed[1]), int(transformed[0])
    return self.grid[row][column] > 0


def main():
  print """ Testing module 'grid'. """
  g = Grid(((0,0), (1,1)))
  polygon = [(0,0), (0,1), (1,0)]
  g.fill_polygon(polygon)
  print g.test((0.25, 0.25)) == True
  print g.test((0.75, 0.75)) == False
  g.show()

if __name__ == '__main__':
  main()
