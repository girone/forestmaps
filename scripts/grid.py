''' 
Copyright 2013: Institut fuer Informatik
Author: Jonas Sternisko <sternis@informatik.uni-freiburg.de>
'''
from PIL import Image, ImageDraw
import numpy as np


def hom(point):
  ''' Returns homogenous representation of a point. '''
  return np.matrix([[point[0]], [point[1]], [1]])

class Grid:
  ''' Represents a grid which maps points in an input space to a fixed grid. '''

  def __init__(self, input_space, grid_size=(10240, 8600), mode="F"):
    ''' Initializes the grid and computes the transformation matrix mapping input
        values to grid cells.
        @mode: Specifies the color-scheme of the grid for values and
               visualization. Example values: 'F', 'RGB'
    '''
    # TODO(Jonas): add some kind of transformation matrix which is initialized
    # during construction and performs the scaling.
    self.grid_size = grid_size
    self.img = Image.new(mode, grid_size, 0)
    self.draw = ImageDraw.Draw(self.img)
    self.grid = np.asarray(self.img)
    self.updated = False
    # compute transformation (linear mapping)
    tx, ty = -input_space[0][0], -input_space[0][1]
    sx = (grid_size[0] + 0.1) / (input_space[1][0] - input_space[0][0])
    sy = (grid_size[1] + 0.1) / (input_space[1][1] - input_space[0][1])
    self.transformation = np.matrix( ((sx, 0, sx*tx), \
                                 (0, sy, sy*ty), \
                                 (0, 0, 1)) );

  def show(self):
    ''' Plots the grid as image. '''
    import matplotlib.pyplot as plt
    plt.figure()
    ax = plt.subplot(111)
    ax.imshow(self.img)
    plt.gca().invert_yaxis()
    plt.show()

  def transform(self, point):
    ''' Transforms a point form the input space to the target space. '''
    res = self.transformation * hom(point)
    return res.item(0), res.item(1)

  def fill_polygon(self, poly, color=255):
    ''' Fills an area of the grid corresponding to a polygon in the input space.
    '''
    transformed = [self.transformation * hom(point) for point in poly]
    self.draw.polygon([(p.item(0), p.item(1)) for p in transformed], fill=color)
    self.updated = True

  def test(self, pos):
    ''' Accesses a field of the grid. Updates the grid if necessary. '''
    if self.updated:
      self.grid = np.asarray(self.img)
      self.updated = False
    assert len(pos) == 2
    transformed = self.transformation * hom(pos)
    row, column = int(transformed[1]), int(transformed[0])
    return self.grid[row][column] > 0

def main():
  print ''' Testing module 'grid'. '''
  g = Grid(((0,0), (1,1)))
  polygon = [(0,0), (0,1), (1,0)]
  g.fill_polygon(polygon)
  print g.test((0.25, 0.25)) == True
  print g.test((0.75, 0.75)) == False
  g.show()

if __name__ == '__main__':
  main()
