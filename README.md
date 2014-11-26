=== Overview ===

This SVN repository contains the code for the ForestMaps project (the part that 
affected the cooperation with the FVA, not the code for the paper). This file 
gives an overview over the code. For a more detailed documentation, see the 
official documentation shipped to FVA.

=== Content ===

The project has three main components:
 1) scripts/ -- This contains the ArcPy scripts used by the ArcGIS toolboxes,
  the wrapper script (i.e. the main entry point) as well as some other Python 
  scripts from the early development stages.
 2) cpp-module/ -- This contains C++ code and unit tests. This code comes with
  a separate build system (SCons) and conducts the computation intense parts
  of the modelling process.
 3) heatmap-gui/ -- This contains the heatmap server and the forest maps GUI as
  used in the presentation site forestmaps.informatik.uni-freiburg.de. It comes
  with separate documentation.
  
Furthermore, the root directory of the project contains:
 4) makefile -- Used to build and collect the code ready for shipping 'make
  deploy'
 5) deploy/ -- Contains the deployed code.
 6) doc/ -- Contains some documentation. For a more thorough documentation of
  the projects progress, see the google-docs.



