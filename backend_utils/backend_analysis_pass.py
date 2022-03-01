# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

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

        # max distance between any pair of nodes
        self.property_set["Diameter"] = np.max(self.distance_matrix)

        # avg length of shortest paths between pairs
        self.property_set["Avg_Distance"] = np.average(self.distance_matrix)

        # max number of edges incident on any vertex
        degrees = [sum(row == 1) for row in self.distance_matrix]
        self.property_set["Degree"] = np.max(degrees)

        # smallest number of edges whose removal splits network into 2 disconnected equally sized parts
        self.property_set["Bisection Width"] = "NotImplementedError"
