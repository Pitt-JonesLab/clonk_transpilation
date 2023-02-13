#from cirq import cphase
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


from qiskit.quantum_info.operators import Operator

circuit = qc.QuantumCircuit(2, name="rootswap")
cx = Operator(
    [
        [1, 0, 0, 0],
        [0, 0.5 * (1 + 1j), 0.5 * (1 - 1j), 0],
        [0, 0.5 * (1 - 1j), 0.5 * (1 + 1j), 0],
        [0, 0, 0, 1],
    ]
)

circuit.unitary(cx, [0, 1])
rootSwap = circuit.to_gate()

# define rootiswap
circuit = qc.QuantumCircuit(2, name="rootiswap")
cx = Operator(
    [
        [1, 0, 0, 0],
        [0, 1 / np.sqrt(2), 1j / np.sqrt(2), 0],
        [0, 1j / np.sqrt(2), 1 / np.sqrt(2), 0],
        [0, 0, 0, 1],
    ]
)
circuit.unitary(cx, [0, 1])
rootiSwap = circuit.to_gate()


def iswap(alpha):
    return np.matrix(
        [
            [1, 0, 0, 0],
            [0, np.cos(np.pi * alpha / 2), 1j * np.sin(np.pi * alpha / 2), 0],
            [0, 1j * np.sin(np.pi * alpha / 2), np.cos(np.pi * alpha / 2), 0],
            [0, 0, 0, 1],
        ]
    )


# class rootiswap_gate(qe.UnitaryGate):
#     def __init__(self):
#         super().__init__(
#             data=np.array(
#                 [
#                     [1, 0, 0, 0],
#                     [0, 1 / np.sqrt(2), 1j / np.sqrt(2), 0],
#                     [0, 1j / np.sqrt(2), 1 / np.sqrt(2), 0],
#                     [0, 0, 0, 1],
#                 ]
#             ),
#             label=r"rootiswap",
#         )


# SWAP out of rootSWAP
_rootSwapEquiv = qc.QuantumCircuit(2)
_rootSwapEquiv.append(rootSwap, [0, 1])
_rootSwapEquiv.append(rootSwap, [0, 1])
SessionEquivalenceLibrary.add_equivalence(g.SwapGate(), _rootSwapEquiv)

# CX out of rootSWAP
_cxEquiv = qc.QuantumCircuit(2)
_cxEquiv.ry(np.pi / 2, 1)
_cxEquiv.append(rootSwap, [0, 1])
_cxEquiv.z(0)
_cxEquiv.append(rootSwap, [0, 1])
_cxEquiv.rz(-np.pi / 2, 0)
_cxEquiv.rz(-np.pi / 2, 1)
_cxEquiv.ry(-np.pi / 2, 1)
SessionEquivalenceLibrary.add_equivalence(g.CXGate(), _cxEquiv)

# rootSWAP out of CX
_rootSwapEquiv = qc.QuantumCircuit(2)
_rootSwapEquiv.cx(0, 1)
_rootSwapEquiv.h(0)
_rootSwapEquiv.rz(np.pi / 4, 0)
_rootSwapEquiv.rz(-np.pi / 4, 1)
_rootSwapEquiv.h(0)
_rootSwapEquiv.h(1)
_rootSwapEquiv.cx(0, 1)
_rootSwapEquiv.h(0)
_rootSwapEquiv.h(1)
_rootSwapEquiv.rz(-np.pi / 4, 0)
_rootSwapEquiv.h(0)
_rootSwapEquiv.cx(0, 1)
_rootSwapEquiv.rz(-np.pi / 2, 0)
_rootSwapEquiv.rz(np.pi / 2, 1)
SessionEquivalenceLibrary.add_equivalence(rootSwap, _rootSwapEquiv)

# add decomp rule for CZ out of Cphase
_czEquiv = qc.QuantumCircuit(2)
_czEquiv.append(g.CPhaseGate(np.pi), [0, 1])
SessionEquivalenceLibrary.add_equivalence(g.CZGate(), _czEquiv)
