import qiskit.circuit.quantumcircuit as qc
from qiskit.circuit.equivalence_library import SessionEquivalenceLibrary
import qiskit.extensions as qe
import numpy as np
from qiskit.circuit.equivalence import EquivalenceLibrary
from qiskit.circuit.library.standard_gates.equivalence_library import (
    StandardEquivalenceLibrary,
)
import qiskit.circuit.library.standard_gates as g

SessionEquivalenceLibrary = EquivalenceLibrary(base=StandardEquivalenceLibrary)

# https://github.com/Qiskit/qiskit-terra/blob/main/qiskit/circuit/library/standard_gates/equivalence_library.py


class rootSwap(qe.UnitaryGate):
    def __init__(self):
        super().__init__(
            data=np.array(
                [
                    [1, 0, 0, 0],
                    [0, 0.5 * (1 + 1j), 0.5 * (1 - 1j), 0],
                    [0, 0.5 * (1 - 1j), 0.5 * (1 + 1j), 0],
                    [0, 0, 0, 1],
                ]
            ),
            label=r"$\sqrt{SWAP}$",
        )


_rootSwapEquiv = qc.QuantumCircuit(2)
_rootSwapEquiv.append(rootSwap(), [0, 1])
_rootSwapEquiv.append(rootSwap(), [0, 1])
# TODO: what happens if I add a second equivalence in the transpiler call?
SessionEquivalenceLibrary.add_equivalence(g.SwapGate(), _rootSwapEquiv)
