CXX = g++
CXXFLAGS = -std=c++17 -Wall -O2

mst: mst.cpp
	$(CXX) $(CXXFLAGS) -o mst mst.cpp

run: mst
	./mst ../data/processed/distance_matrix.csv

benchmark_prim: benchmark_prim.cpp mst.cpp
	$(CXX) $(CXXFLAGS) -o benchmark_prim benchmark_prim.cpp

benchmark: benchmark_prim
	./benchmark_prim ../data/processed/benchmark_prim ../data/processed/distance_matrix.csv

clean:
	rm -f mst mst_edges.csv

.PHONY: run clean benchmark
