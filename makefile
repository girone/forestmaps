# This makefile automates the deployment of the forest code.

PYCODE=arcpy_c++_pipeline_wrapper.py \
       atkis_graph.py \
       graph.py \
       arcutil.py \
       forestentrydetection.py \
       grid.py \
       convexhull.py


.PHONY : deploy
deploy:
	@echo Deploying...
	cd cpp-module/src && make clean && make compile && cd -
	cp -v cpp-module/build/*Main.exe deploy
	@for i in $(PYCODE); do cp -v scripts/$$i deploy; done;

ship:
	echo Implement this
