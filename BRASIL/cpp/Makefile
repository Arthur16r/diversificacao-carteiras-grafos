CXX = g++
CXXFLAGS = -std=c++17 -Wall -O2

mst: mst.cpp
	$(CXX) $(CXXFLAGS) -o mst mst.cpp

run: mst
	./mst ../data/processed/distance_matrix_sem_exterior.csv

clean:
	rm -f mst mst_edges.csv

.PHONY: run clean
