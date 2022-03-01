# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""RiSWAP gate."""

from typing import Optional
import numpy as np
from qiskit.circuit.gate import Gate
from qiskit.circuit.quantumregister import QuantumRegister
from qiskit.circuit.parameterexpression import ParameterValueType


class RiSwapGate(Gate):
    r"""RiSWAP gate.

    **Circuit Symbol:**

    .. parsed-literal::

        q_0: ─⨂─
           R(alpha)
        q_1: ─⨂─

    """

    def __init__(self, alpha: ParameterValueType, label: Optional[str] = None):
        """Create new iSwap gate."""
        super().__init__("riswap", 2, [alpha], label=label)

    def __array__(self, dtype=None):
        """Return a numpy.array for the RiSWAP gate."""
        alpha = self.params[0]
        return np.array(
            [
                [1, 0, 0, 0],
                [0, np.cos(np.pi * alpha / 2), 1j * np.sin(np.pi * alpha / 2), 0],
                [0, 1j * np.sin(np.pi * alpha / 2), np.cos(np.pi * alpha / 2), 0],
                [0, 0, 0, 1],
            ],
            dtype=dtype,
        )
