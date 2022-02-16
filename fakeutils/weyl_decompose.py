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

from fakeutils.fakeutils import BasisTranslator
from fakeutils.equivalence_library import SessionEquivalenceLibrary

from fakeutils.weyl import weyl_coordinates
from qiskit.quantum_info.operators import Operator

# from qiskit.circuit.library.standard_gates import *
from fakeutils.riswap import RiSwapGate
from qiskit.circuit import Parameter
from qiskit import QuantumCircuit
import numpy as np


_sel = SessionEquivalenceLibrary


class RootiSwapWeylDecomposition(TransformationPass):
    """Rewrite two-qubit gates using the Weyl decomposition.
    This transpiler pass rewrites two-qubit gates in terms of root iswap gates according
    to the Weyl decomposition. A two-qubit gate will be replaced with at most 3 root i swap gates.
    """

    def __init__(self, decompose_swaps=True):
        """RootiSwapWeylDecomposition pass.
        Args:
            instruction_schedule_map (InstructionScheduleMap): the mapping from circuit
                :class:`~.circuit.Instruction` names and arguments to :class:`.Schedule`\\ s.
        """
        super().__init__()
        self.requires = [BasisTranslator(_sel, ["u3", "cp", "swap", "riswap"])]
        self.decompose_swaps = decompose_swaps

    @staticmethod
    def _improper_orthogonal_decomp(x, y, z):
        alpha = np.arccos(
            np.cos(2 * z) - np.cos(2 * y) + np.sqrt((np.cos(4 * z) + np.cos(4 * y)) / 2)
        )
        beta = np.arccos(
            np.cos(2 * z) - np.cos(2 * y) - np.sqrt((np.cos(4 * z) + np.cos(4 * y)) / 2)
        )
        gamma = 0

        psi = -np.arccos(np.sqrt((1 + np.tan(y - z)) / 2))
        phi = np.arccos(np.sqrt((1 + np.tan(y + z)) / 2))

        def_Lxyz = QuantumCircuit(2)
        # CPhase
        if np.isclose(y, 0) and np.isclose(z, 0):
            def_Lxyz.rz(np.arcsin(np.tan(x)), 1)
            def_Lxyz.rx(-np.pi / 2, 1)
            def_Lxyz.append(RiSwapGate(0.5), [0, 1])
            def_Lxyz.z(1)
            def_Lxyz.ry(2 * np.arcsin(np.sqrt(2) * np.sin(x)), 1)
            def_Lxyz.append(RiSwapGate(0.5), [0, 1])
            def_Lxyz.rx(-np.pi / 2, 1)
            def_Lxyz.rz(np.arcsin(np.tan(x)) - np.pi, 1)

        # Canonicalized SWAP
        elif np.isclose(x, np.pi / 4) and y + np.abs(z) <= np.pi / 4:
            def_Lxyz.rx(phi + psi, 0)
            def_Lxyz.rz(np.pi / 2, 1)
            def_Lxyz.rx(phi - psi, 1)
            def_Lxyz.append(RiSwapGate(0.5), [0, 1])
            def_Lxyz.rx(alpha, 0)
            def_Lxyz.rx(beta, 1)
            def_Lxyz.append(RiSwapGate(0.5), [0, 1])
            def_Lxyz.rx(phi + psi, 0)
            def_Lxyz.rx(phi - psi, 1)
            def_Lxyz.rz(-np.pi / 2, 1)
        else:
            raise NotImplementedError
        return def_Lxyz

    @staticmethod
    def cphase_decomp(unitary):
        # assuming unitary is a CPhase, is true per self.requires pass
        # TODO function structure needs to be reoganized to use canonicalize function
        x, y, z = weyl_coordinates(Operator(unitary).data)
        def_CPhase = RootiSwapWeylDecomposition._improper_orthogonal_decomp(x, y, z)
        return def_CPhase

    # Note this is the way suggested by alibaba paper, but google has a swap->riswap(1/2) decomp rule that uses less 1Q gates
    @staticmethod
    def swap_decomp(unitary):
        def_swap = QuantumCircuit(2)
        def_swap.z(0)
        def_swap.rx(np.pi / 2, 0)
        def_swap.z(0)

        def_swap.rx(-np.pi / 2, 1)

        x, y, z = weyl_coordinates(Operator(unitary).data)
        def_swap += RootiSwapWeylDecomposition._improper_orthogonal_decomp(
            x, y - np.pi / 4, z - np.pi / 4
        )

        def_swap.z(0)
        def_swap.rx(-np.pi / 2, 0)
        def_swap.rz(np.pi / 2, 0)
        def_swap.ry(-np.pi / 2, 0)
        def_swap.z(0)

        def_swap.rx(np.pi / 2, 1)
        def_swap.rz(-np.pi / 2, 1)
        def_swap.ry(np.pi / 2, 1)

        def_swap.append(RiSwapGate(0.5), [0, 1])

        def_swap.z(0)
        def_swap.ry(np.pi / 2, 0)
        def_swap.rz(-np.pi / 2, 0)
        def_swap.z(0)

        def_swap.ry(-np.pi / 2, 1)
        def_swap.rz(np.pi / 2, 1)

        return def_swap

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

        for node in dag.two_qubit_ops():
            # denote 2 different decomp rules, either for swap gates, or for U gates in CPhase basis
            if node.name == "riswap":
                continue
            unitary = Operator(node.op).data
            if node.name == "swap":
                if self.decompose_swaps:
                    dag_weyl = circuit_to_dag(self.swap_decomp(unitary))
                    dag.substitute_node_with_dag(node, dag_weyl)
            else:
                dag_weyl = circuit_to_dag(self.cphase_decomp(unitary))
                dag.substitute_node_with_dag(node, dag_weyl)

        return dag
