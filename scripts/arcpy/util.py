''' util.py : Contains helper functions. '''
import time
try:
  import arcpy
  HAVE_ARCPY = True
except:
  print "Warning from util.py: Could not find module 'arcpy'!"
  HAVE_ARCPY = False


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

