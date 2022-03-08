from qiskit.transpiler.basepasses import AnalysisPass
import numpy as np


class TopologyAnalysis(AnalysisPass):
    """Evaluate how good a backend is"""

    def __init__(self, backend):
        """TopologyAnalysis initializer.

        Args:
            coupling_map (CouplingMap): Directed graph represented a coupling map.
            property_name (str): The property name to save the score. Default: layout_score
        """
        super().__init__()
        self.backend = backend
        self.coupling_map = backend.coupling_map
        self.coupling_map.compute_distance_matrix()
        self.distance_matrix = self.coupling_map.distance_matrix

    def run(self, dag):
        """
        Run the pass on `dag`.
        Args:
            dag (DAGCircuit): DAG to evaluate.
        """
        # NOTE could instead use coupling_map.get_edges() --I didnt know this method when I first wrote this

        # max distance between any pair of nodes
        self.property_set["Diameter"] = float(np.max(self.distance_matrix))

        # avg length of shortest paths between pairs
        self.property_set["Avg_Distance"] = float(np.average(self.distance_matrix))

        # max number of edges incident on any vertex
        degrees = [sum(row == 1) for row in self.distance_matrix]
        self.property_set["Degree"] = float(np.max(degrees))

        # smallest number of edges whose removal splits network into 2 disconnected equally sized parts
        # self.property_set["Bisection Width"] = "NotImplementedError"
