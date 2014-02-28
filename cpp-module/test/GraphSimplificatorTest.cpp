// Copyright 2014: Jonas Sternisko

#include <gmock/gmock.h>
#include <set>
#include <string>
#include <vector>
#include "../src/GraphSimplificator.h"

using std::endl;
using ::testing::Contains;
using ::testing::WhenSorted;

typedef SimplificationGraph::Arc_t Arc;


class GraphSimplificatorTest : public ::testing::Test {
 public:
  GraphSimplificatorTest() {
    {
      // Create a graph file. The graph is like this (all edges bidirected):
      /*
       *                             5
       *                             |
       *  0 ------ 1 ------ 3 ------ 2 ---- 4
       *                             |
       *                             6
       */
      // After contraction, it should be
      /*
       *                             3(5)
       *                              |
       *  0 ------------------------ 1(2) ---- 2(4)
       *                              |
       *                             4(6)
       * Note the new indices. Origininal indices are in parenthesis.
       */
      _filename = "complex_graph.tmp.txt";
      std::ofstream ofs(_filename);
      assert(ofs.good());
      ofs << "7" << endl
          << "12" << endl
          << "0 0" << endl
          << "1 1" << endl
          << "2 2" << endl
          << "3 3" << endl
          << "4 4" << endl
          << "5 5" << endl
          << "6 6" << endl
          << "0 1 10.0 1 1" << endl  // Note the last column: additional FID
          << "1 0 10.0 1 1" << endl
          << "1 3 5.0 1 2" << endl
          << "2 3 6.0 1 3" << endl
          << "2 4 9.0 1 4" << endl
          << "2 5 9.0 1 5" << endl
          << "2 6 9.0 1 6" << endl
          << "3 1 5.0 1 2" << endl
          << "3 2 6.0 1 3" << endl
          << "4 2 9.0 1 4" << endl
          << "5 2 9.0 1 5" << endl
          << "6 2 9.0 1 6" << endl;
    }
  }

 protected:
  string _filename;
};


::std::ostream& operator<<(::std::ostream& os, const Arc& arc) {
  return os << arc.to_string();
}


// _____________________________________________________________________________
TEST_F(GraphSimplificatorTest, self_check) {
  // Read the graph
  SimplificationGraph graph;
  graph.read_in(_filename);
  ASSERT_EQ(7, graph.num_nodes());
  ASSERT_EQ(12, graph.count_arcs());
}

// _____________________________________________________________________________
TEST_F(GraphSimplificatorTest, try_to_contract_node) {
  // Read the graph
  SimplificationGraph graph;
  graph.read_in(_filename);
  size_t originalNumberOfArcs = graph.count_arcs();

  // Contract node 1
  GraphSimplificator modul(&graph);
  modul.initialize_mapping();
  vector<bool> contracted(graph.num_nodes(), false);
  bool res = modul.try_to_contract_node(1, contracted);
  EXPECT_TRUE(res);

  // Check the resulting graph: There should be shortcuts 0<-->3 of cost 15.0,
  // everything else remains the same.
  // Has arc id = originalGraph.num_arcs():
  Arc a1 = ArcFactory::create(0, 3, 15.0, 1, 12);
  EXPECT_THAT(graph._arcs[0], Contains(a1));
  // Has arc id = originalGraph.num_arcs() + 1
  Arc a2 = ArcFactory::create(3, 0, 15.0, 1, 13);
  EXPECT_THAT(graph._arcs[3], Contains(a2));

  // It should not be possible to contract node 2 and 4, for instance.
  EXPECT_FALSE(modul.try_to_contract_node(2, contracted));
  EXPECT_FALSE(modul.try_to_contract_node(4, contracted));

  // Check the mapping: The new arcs should represent the old arcs's FIDs.
  auto map = modul.edges_contained_in_shortcut_map();
  EXPECT_THAT(map[originalNumberOfArcs], WhenSorted(vector<int>({1, 2})));
  EXPECT_THAT(map[originalNumberOfArcs+1], WhenSorted(vector<int>({1, 2})));
}

// _____________________________________________________________________________
TEST_F(GraphSimplificatorTest, simplify) {
  // Read the graph
  SimplificationGraph graph;
  graph.read_in(_filename);

  // Simplify it
  GraphSimplificator modul(&graph);
  SimplificationGraph result = modul.simplify();

  // Check the result. It should look like described in the header.
  /*
       *                             3(5)
       *                              |
       *  0 ------------------------ 1(2) ---- 2(4)
       *                              |
       *                             4(6)
       */
  EXPECT_EQ(5, result.num_nodes());
  EXPECT_EQ(8, result.count_arcs());
  EXPECT_EQ("[5,8,{(0,1,[21,1,15])},"
            "{(1,0,[21,1,14])(1,2,[9,1,4])(1,3,[9,1,5])(1,4,[9,1,6])},"
            "{(2,1,[9,1,4])},{(3,1,[9,1,5])},{(4,1,[9,1,6])}]",
            result.to_string());

  // Check the mapping: The new arcs should represent the old arcs's FIDs.
  auto map = modul.edges_contained_in_shortcut_map();
  EXPECT_THAT(map[14], WhenSorted(vector<int>({1, 2, 3})));
  EXPECT_THAT(map[15], WhenSorted(vector<int>({1, 2, 3})));
}

// _____________________________________________________________________________
TEST_F(GraphSimplificatorTest, simplify_do_not_contract) {
  // Read the graph
  SimplificationGraph graph;
  graph.read_in(_filename);

  // Simplify it
  GraphSimplificator modul(&graph);
  set<uint> doNotContract = {4, 3, 6};
  SimplificationGraph result = modul.simplify(&doNotContract);

  // Check the result. The specified node (3) should not be contracted.
  /*
   *                             4(5)
   *                              |
   *  0 --------2(3) ----------- 1(2) ---- 3(4)
   *                              |
   *                             5(6)
   */
  EXPECT_EQ(6, result.num_nodes());
  EXPECT_EQ(10, result.count_arcs());
  EXPECT_EQ("[6,10,{(0,2,[15,1,12])},"
            "{(1,2,[6,1,3])(1,3,[9,1,4])(1,4,[9,1,5])(1,5,[9,1,6])},"
            "{(2,0,[15,1,13])(2,1,[6,1,3])},{(3,1,[9,1,4])},{(4,1,[9,1,5])},"
            "{(5,1,[9,1,6])}]",
            result.to_string());

  // Check the mapping: The new arcs should represent the old arcs's FIDs.
  auto map = modul.edges_contained_in_shortcut_map();
  EXPECT_THAT(map[12], WhenSorted(vector<int>({1, 2})));
  EXPECT_THAT(map[13], WhenSorted(vector<int>({1, 2})));
}


// _____________________________________________________________________________
// This tests a special case:
/*
 *  0 -- 2 -- 3                             1(2) -- 2(3)
 *  |  / |               contraction        /|
 *  | /  |               ---------->       / |         with double arcs 0 <-> 1
 *  1    4                              0(1) 3(4)
 */
// After contracting a first node, anotherone has two arcs to the same neighbor.
// It should not be contracted in this case.
TEST_F(GraphSimplificatorTest, special_case) {
  string filename = "complex_graph_special_case.tmp.txt";
  {
    // Create a graph file. The graph looks like described above.
    std::ofstream ofs(filename);
    assert(ofs.good());
    ofs << "5" << endl
        << "10" << endl
        << "0 0" << endl
        << "1 1" << endl
        << "2 2" << endl
        << "3 3" << endl
        << "4 4" << endl
        << "0 1 5.0 1 1" << endl
        << "0 2 5.0 1 2" << endl
        << "1 0 5.0 1 1" << endl
        << "1 2 15.0 1 3" << endl
        << "2 0 5.0 1 2" << endl
        << "2 1 15.0 1 3" << endl
        << "2 3 70.0 1 4" << endl
        << "2 4 70.0 1 5" << endl
        << "3 2 70.0 1 4" << endl
        << "4 2 70.0 1 5" << endl;
  }

  {
    // Simplify the graph. Node 1 should remain uncontracted.
    SimplificationGraph input;
    input.read_in(filename);

    // Simplify
    GraphSimplificator modul(&input);
    SimplificationGraph result = modul.simplify();
    // Check the result
    EXPECT_EQ(4, result.num_nodes());
    EXPECT_EQ(8, result.count_arcs());
    EXPECT_EQ("[4,8,{(0,1,[15,1,3])(0,1,[10,1,10])},"
              "{(1,0,[15,1,3])(1,0,[10,1,11])(1,2,[70,1,4])(1,3,[70,1,5])},"
              "{(2,1,[70,1,4])},{(3,1,[70,1,5])}]",
              result.to_string());

    // Check the mapping: The new arcs should represent the old arcs's FIDs.
    auto map = modul.edges_contained_in_shortcut_map();
    EXPECT_THAT(map[10], WhenSorted(vector<int>({1, 2})));
    EXPECT_THAT(map[11], WhenSorted(vector<int>({1, 2})));
  }
}


