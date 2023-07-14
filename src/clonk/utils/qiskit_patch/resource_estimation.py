# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Automatically require analysis passes for resource estimation."""

# from qiskit.transpiler.passes.analysis.count_ops import CountOps
# from qiskit.transpiler.passes.analysis.count_ops_longest_path import CountOpsLongestPath
import sys

from qiskit.transpiler.basepasses import AnalysisPass
from qiskit.transpiler.passes.analysis.depth import Depth
from qiskit.transpiler.passes.analysis.size import Size
from qiskit.transpiler.passes.analysis.width import Width

sys.path.append("../")
from qiskit.transpiler.passes.analysis.num_qubits import NumQubits
from qiskit.transpiler.passes.analysis.num_tensor_factors import NumTensorFactors

from src.clonk.utils.qiskit_patch.count_ops import CountOps
from src.clonk.utils.qiskit_patch.count_ops_longest_path import CountOpsLongestPath


class ResourceEstimation(AnalysisPass):
    """Automatically require analysis passes for resource estimation.

    An analysis pass for automatically running:
    * Depth()
    * Width()
    * Size()
    * CountOps()
    * NumTensorFactors()
    """

    def __init__(self, preswap=False):
        super().__init__()
        self.requires += [
            Depth(),
            Width(),
            Size(),
            CountOps(preswap),
            NumTensorFactors(),
            NumQubits(),
            CountOpsLongestPath(preswap),
        ]

    def run(self, _):
        """Run the ResourceEstimation pass on `dag`."""
        pass
