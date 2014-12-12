#CXX = g++ -g -Wall -Wno-deprecated -std=c++0x

#CXX = x86_64-w64-mingw32-g++ -g -O3 -Wall -Wno-deprecated -std=c++0x -static-libgcc -static-libstdc++ -static
CXX = i686-pc-mingw32-g++ -g -O3 -Wall -Wno-deprecated -std=c++0x -static-libgcc -static-libstdc++ -static
MAIN_BINARIES = $(addsuffix .exe,$(basename $(wildcard *Main.cpp)))
TEST_BINARIES = $(basename $(wildcard *Test.cpp))
HEADER = $(wildcard *.h)
OBJECTS = $(addsuffix .o,$(basename $(filter-out %Main.cpp %Test.cpp,$(wildcard *.cpp))))
MAIN_LIBS =
TEST_LIBS = -lgtest -lgtest_main -lpthread $(MAIN_LIBS)
OUTDIR = ../build
INCLUDE = -I../lib/googlemock/gtest/include/ -I../lib/googlemock/include/ -I../lib/libkdtree/

.PRECIOUS: %.o

all: compile test checkstyle

compile: $(MAIN_BINARIES)

test: $(TEST_BINARIES)
	for T in $(TEST_BINARIES); do ./$(OUTDIR)/$$T; done

checkstyle:
	python cpplint.py *.h *.cpp

clean:
	rm -f *.o
	rm -f $(MAIN_BINARIES)
	rm -f $(TEST_BINARIES)
	rm -f *.class
	rm -f *Test.TMP.*
	rm -f *TMP*
	rm -f core
	rm -f cc-sizes.txt

%Main.exe: %Main.o $(OBJECTS)
	$(CXX) -o $(OUTDIR)/$@ $^ $(MAIN_LIBS)

%Test: %Test.o $(OBJECTS)
	$(CXX) -o $(OUTDIR)/$@ $^ $(TEST_LIBS)

%.o: %.cpp $(HEADER)
	$(CXX) $(INCLUDE) -c $<
