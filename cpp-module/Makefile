# Copyright 2012: Jonas Sternisko
#
# This is the Makefile operating upstream to SCons.
#
# To build your code, run 'make [target]'. SCons is expected as up-to-date
# installation inside the project. Alternatively you could set the SCONS
# variable to you system's installation of SCons. See the SConstruct file for
# further documentation and the structure of the source and build directories.

all: compile test checkstyle

SCONS = ./scons/bin/scons
NUM_CORES = $(shell grep -c ^processor /proc/cpuinfo)
MODE = RelWithDebInfo
OMP = 1
BUILD_DIR = build
# allows target 'test' even though there is a directory of that name
.PHONY: test

#update_tags:
#	command -v ctags > /dev/null && ctags *.cpp *.h || true

compile:
	$(SCONS) -j$(NUM_CORES) mode=$(MODE) target_set=main omp=$(OMP) build_dir=$(BUILD_DIR)
	# post action:
	cd $(BUILD_DIR) && ln -sf src/*Main . && cd -

test:
	$(SCONS) -j$(NUM_CORES) mode=$(MODE) target_set=test omp=$(OMP) build_dir=$(BUILD_DIR)
	# post action:
	cd build && ln -sf test/*Test . && cd -
	cd data/tmp && rm -f * && cd -

clean:
	$(SCONS) -c target_set=all
	rm -f build/*Test* build/*Main

checkstyle:
	python cpplint.py src/*.h src/*.hpp src/*impl.h src/*.cpp test/*.cpp

