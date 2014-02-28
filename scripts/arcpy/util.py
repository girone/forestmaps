''' util.py : Contains helper functions. '''
import time
import sys

try:
  import arcpy
  HAVE_ARCPY = True
except:
  print "Warning from util.py: Could not find module 'arcpy'!"
  HAVE_ARCPY = False
if HAVE_ARCPY:
  try:
    mxd = arcpy.mapping.MapDocument("CURRENT")
    HAVE_ARCPY_UI = bool(mxd)
  except:
    HAVE_ARCPY_UI = False


def msg(text):
  if HAVE_ARCPY:
    arcpy.AddMessage(text)
  print text


class Timer(object):
  def __init__(self):
    self.timestamp = 0

  def start_timing(self, text):
    msg(text)
    self.timestamp = time.clock()

  def stop_timing(self):
    msg("This took %.1f seconds." % (time.clock() - self.timestamp))


class Progress(object):
  ''' A progress measuring tool, which abstracts from ArcUI and console. '''
  def __init__(self, task_description, total_steps, resolution=100):
    self.total_steps = int(total_steps)
    self.resolution = resolution
    self.completed = 0
    if HAVE_ARCPY_UI:
      arcpy.SetProgressor("step", task_description, 0, total_steps,
                          int(total_steps / float(resolution)))
  def __del__(self):
    if HAVE_ARCPY_UI:
      arcpy.ResetProgressor()

  def progress(self, steps_completed=-1):
    ''' Sets the progress to a new state. '''
    if steps_completed < 0:
      self.completed += 1
      steps_completed = self.completed
    if steps_completed % (self.total_steps / self.resolution) == 0:
      self.progress_visualization(steps_completed)
    if steps_completed == self.total_steps:
      self.finish()

  def progress_visualization(self, steps_completed):
    ''' Visualizes the progress. '''
    if HAVE_ARCPY_UI:
      arcpy.SetProgressorPosition()
    else:
      sys.stdout.write("\r%.1f%%" % (steps_completed * 100. / self.total_steps))

  def finish(self):
    if HAVE_ARCPY_UI:
      arcpy.ResetProgressor()
    else:
      print 'Done.'


