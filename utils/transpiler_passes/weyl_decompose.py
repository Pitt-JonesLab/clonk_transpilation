# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Weyl decomposition of two-qubit gates in terms of echoed cross-resonance gates."""

from typing import Tuple
from qiskit import QuantumCircuit

from qiskit.circuit import QuantumRegister
from qiskit.circuit.library.standard_gates import RZXGate, HGate, XGate

from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError
from qiskit.transpiler.layout import Layout

from qiskit.dagcircuit import DAGCircuit
from qiskit.converters import circuit_to_dag

from utils.qiskit_patch.two_qubit_decompose import TwoQubitBasisDecomposer
from utils.riswap_gates.equivalence_library import SessionEquivalenceLibrary

from qiskit.quantum_info.synthesis.weyl import weyl_coordinates
from qiskit.quantum_info.operators import Operator

# from qiskit.circuit.library.standard_gates import *
from utils.riswap_gates.riswap import RiSwapGate
from qiskit.circuit import Parameter
from qiskit import QuantumCircuit
import numpy as np


_sel = SessionEquivalenceLibrary


class RootiSwapWeylDecomposition(TransformationPass):
    """Rewrite two-qubit gates using the Weyl decomposition.
    This transpiler pass rewrites two-qubit gates in terms of root iswap gates according
    to the Weyl decomposition. A two-qubit gate will be replaced with at most 3 root i swap gates.
    """

    def __init__(self, basis_gate=False):
        """RootiSwapWeylDecomposition pass.
        Args:
            instruction_schedule_map (InstructionScheduleMap): the mapping from circuit
                :class:`~.circuit.Instruction` names and arguments to :class:`.Schedule`\\ s.
        """
        super().__init__()
        # self.requires = [
        #     BasisTranslator(_sel, ["u3", "cu3", "cp", "swap", "riswap", "id"])
        # ]
        # self.decompose_swaps = decompose_swaps
        self.basis_gate = basis_gate

    # @staticmethod
    # def _improper_orthogonal_decomp(x, y, z):
    #     alpha = np.arccos(
    #         np.cos(2 * z) - np.cos(2 * y) + np.sqrt((np.cos(4 * z) + np.cos(4 * y)) / 2)
    #     )
    #     beta = np.arccos(
    #         np.cos(2 * z) - np.cos(2 * y) - np.sqrt((np.cos(4 * z) + np.cos(4 * y)) / 2)
    #     )
    #     gamma = 0

    #     psi = -np.arccos(np.sqrt((1 + np.tan(y - z)) / 2))
    #     phi = np.arccos(np.sqrt((1 + np.tan(y + z)) / 2))

    #     def_Lxyz = QuantumCircuit(2)
    #     # ISwap
    #     if np.isclose(x, y) and np.isclose(z, 0):
    #         def_Lxyz.append(RiSwapGate(0.5), [0, 1])
    #         def_Lxyz.rz(2 * x, 0)
    #         def_Lxyz.rz(-2 * x + np.pi, 1)
    #         def_Lxyz.append(RiSwapGate(0.5), [0, 1])
    #         def_Lxyz.rz(-np.pi, 1)
    #         return def_Lxyz
    #     # CPhase
    #     if np.isclose(y, 0) and np.isclose(z, 0):
    #         def_Lxyz.rz(np.arcsin(np.tan(x)), 1)
    #         def_Lxyz.rx(-np.pi / 2, 1)
    #         def_Lxyz.append(RiSwapGate(0.5), [0, 1])
    #         def_Lxyz.z(1)
    #         def_Lxyz.ry(2 * np.arcsin(np.sqrt(2) * np.sin(x)), 1)
    #         def_Lxyz.append(RiSwapGate(0.5), [0, 1])
    #         def_Lxyz.rx(-np.pi / 2, 1)
    #         def_Lxyz.rz(np.arcsin(np.tan(x)) - np.pi, 1)
    #         return def_Lxyz
    #     # Canonicalized SWAP
    #     elif np.isclose(x, np.pi / 4) and y + np.abs(z) <= np.pi / 4:
    #         def_Lxyz.rx(phi + psi, 0)
    #         def_Lxyz.rz(np.pi / 2, 1)
    #         def_Lxyz.rx(phi - psi, 1)
    #         def_Lxyz.append(RiSwapGate(0.5), [0, 1])
    #         def_Lxyz.rx(alpha, 0)
    #         def_Lxyz.rx(beta, 1)
    #         def_Lxyz.append(RiSwapGate(0.5), [0, 1])
    #         def_Lxyz.rx(phi + psi, 0)
    #         def_Lxyz.rx(phi - psi, 1)
    #         def_Lxyz.rz(-np.pi / 2, 1)
    #         return def_Lxyz
    #     else:
    #         raise NotImplementedError

    # @staticmethod
    # def cphase_decomp(unitary):
    #     # assuming unitary is a CPhase, is true per self.requires pass
    #     # TODO function structure needs to be reoganized to use canonicalize function
    #     x, y, z = weyl_coordinates(Operator(unitary).data)
    #     def_CPhase = RootiSwapWeylDecomposition._improper_orthogonal_decomp(x, y, z)
    #     return def_CPhase

    # # Note this is the way suggested by alibaba paper, but google has a swap->riswap(1/2) decomp rule that uses less 1Q gates
    # @staticmethod
    # def swap_decomp(unitary):
    #     # FIXME: green, blue, maroon rules
    #     def_swap = QuantumCircuit(2)
    #     def_swap.z(0)
    #     def_swap.rx(np.pi / 2, 0)
    #     def_swap.z(0)

    #     def_swap.rx(-np.pi / 2, 1)

    #     x, y, z = weyl_coordinates(Operator(unitary).data)
    #     def_swap += RootiSwapWeylDecomposition._improper_orthogonal_decomp(
    #         x, y - np.pi / 4, z - np.pi / 4
    #     )

    #     def_swap.z(0)
    #     def_swap.rx(-np.pi / 2, 0)
    #     def_swap.rz(np.pi / 2, 0)
    #     def_swap.ry(-np.pi / 2, 0)
    #     def_swap.z(0)

    #     def_swap.rx(np.pi / 2, 1)
    #     def_swap.rz(-np.pi / 2, 1)
    #     def_swap.ry(np.pi / 2, 1)

    #     def_swap.append(RiSwapGate(0.5), [0, 1])

    #     def_swap.z(0)
    #     def_swap.ry(np.pi / 2, 0)
    #     def_swap.rz(-np.pi / 2, 0)
    #     def_swap.z(0)

    #     def_swap.ry(-np.pi / 2, 1)
    #     def_swap.rz(np.pi / 2, 1)

    #     return def_swap

    # reference: https://arxiv.org/pdf/2105.06074.pdf

    def weyl_decomp(self, unitary):
        return self.decomposer(unitary)

    def interleaving_1q(x, y, z):
        return None

    def canonicalize(x, y, z):
        return None

    def run(self, dag: DAGCircuit):
        """Run the RootiSwapWeylDecomposition pass on `dag`.
        Rewrites two-qubit gates in an arbitrary circuit in terms of echoed cross-resonance
        gates by computing the Weyl decomposition of the corresponding unitary. Modifies the
        input dag.
        Args:
            dag (DAGCircuit): DAG to rewrite.
        Returns:
            DAGCircuit: The modified dag.
        Raises:
            TranspilerError: If the circuit cannot be rewritten.
        """
        # pylint: disable=cyclic-import
        from qiskit.quantum_info import Operator
        from qiskit.quantum_info.synthesis.two_qubit_decompose import (
            TwoQubitControlledUDecomposer,
        )

        if len(dag.qregs) > 1:
            raise TranspilerError(
                "RootiSwapWeylDecomposition expects a single qreg input DAG,"
                f"but input DAG had qregs: {dag.qregs}."
            )

        # trivial_layout = Layout.generate_trivial_layout(*dag.qregs.values())
        from qiskit.circuit.library import CXGate

        self.decomposer = TwoQubitBasisDecomposer(self.basis_gate)
        for node in dag.two_qubit_ops():
            # denote 2 different decomp rules, either for swap gates, or for U gates in CPhase basis
            # if node.name == "riswap":
            #     continue

            # FIXME need to convert unitary to a special unitary first to preserve 1Qs
            unitary = Operator(node.op).data
            # special_unitary = unitary
            dag_sub = circuit_to_dag(self.weyl_decomp(unitary))
            dag.substitute_node_with_dag(node, dag_sub)

            # if node.name == "swap":
            #     if self.decompose_swaps:
            #         dag_weyl = circuit_to_dag(self.swap_decomp(unitary))
            #         dag.substitute_node_with_dag(node, dag_weyl)
            # elif node.name == "cp":
            #     dag_weyl = circuit_to_dag(self.cphase_decomp(unitary))
            #     dag.substitute_node_with_dag(node, dag_weyl)
            # # FIXME
            # # FIXME
            # # FIXME
            # # I need to double check the x,y,z coordinates -> why is CX and CPhase both (np.pi/4 ,0 ,0)
            # # that tells me I need to write CX in CPhase basis first to preverse 1Q gates
            # # but CU is 2 CPhase gates and yet still a (np.pi/4, 0, 0)- how do I preserve 1Q gates?
            # elif node.name == "cu3":
            #     dag_weyl = circuit_to_dag(self.cphase_decomp(unitary))
            #     dag.substitute_node_with_dag(node, dag_weyl)
        return dag