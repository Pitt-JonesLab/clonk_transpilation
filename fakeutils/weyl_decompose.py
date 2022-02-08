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


class RootiSwapWeylDecomposition(TransformationPass):
    """Rewrite two-qubit gates using the Weyl decomposition.
    This transpiler pass rewrites two-qubit gates in terms of echoed cross-resonance gates according
    to the Weyl decomposition. A two-qubit gate will be replaced with at most six non-echoed RZXGates.
    Each pair of RZXGates forms an echoed RZXGate.
    """

    def __init__(self, instruction_schedule_map=None):
        """EchoRZXWeylDecomposition pass.
        Args:
            instruction_schedule_map (InstructionScheduleMap): the mapping from circuit
                :class:`~.circuit.Instruction` names and arguments to :class:`.Schedule`\\ s.
        """
        super().__init__()
        self._inst_map = instruction_schedule_map

    def _is_native(self, qubit_pair: Tuple) -> bool:
        """Return the direction of the qubit pair that is native, i.e. with the shortest schedule."""
        if self._inst_map is None:
            return True
        cx1 = self._inst_map.get("cx", qubit_pair)
        cx2 = self._inst_map.get("cx", qubit_pair[::-1])
        return cx1.duration < cx2.duration

    @staticmethod
    def _echo_rzx_dag(theta):
        rzx_dag = DAGCircuit()
        qr = QuantumRegister(2)
        rzx_dag.add_qreg(qr)
        rzx_dag.apply_operation_back(RZXGate(theta / 2), [qr[0], qr[1]], [])
        rzx_dag.apply_operation_back(XGate(), [qr[0]], [])
        rzx_dag.apply_operation_back(RZXGate(-theta / 2), [qr[0], qr[1]], [])
        rzx_dag.apply_operation_back(XGate(), [qr[0]], [])
        return rzx_dag

    @staticmethod
    def _reverse_echo_rzx_dag(theta):
        reverse_rzx_dag = DAGCircuit()
        qr = QuantumRegister(2)
        reverse_rzx_dag.add_qreg(qr)
        reverse_rzx_dag.apply_operation_back(HGate(), [qr[0]], [])
        reverse_rzx_dag.apply_operation_back(HGate(), [qr[1]], [])
        reverse_rzx_dag.apply_operation_back(RZXGate(theta / 2), [qr[1], qr[0]], [])
        reverse_rzx_dag.apply_operation_back(XGate(), [qr[1]], [])
        reverse_rzx_dag.apply_operation_back(RZXGate(-theta / 2), [qr[1], qr[0]], [])
        reverse_rzx_dag.apply_operation_back(XGate(), [qr[1]], [])
        reverse_rzx_dag.apply_operation_back(HGate(), [qr[0]], [])
        reverse_rzx_dag.apply_operation_back(HGate(), [qr[1]], [])
        return reverse_rzx_dag

    @staticmethod
    def tempalibbadecomp(unitary):
        from fakeutils.weyl import weyl_coordinates
        from qiskit.quantum_info.operators import Operator

        # from qiskit.circuit.library.standard_gates import *
        from fakeutils.equivalence_library import rootiSwap
        from qiskit.circuit import Parameter
        from qiskit import QuantumCircuit
        import numpy as np

        # start with assuming unitary is a CU
        theta = Parameter("theta")
        x, y, z = weyl_coordinates(Operator(unitary).data)
        def_cphase = QuantumCircuit(2)
        def_cphase.rz(np.arcsin(np.tan(x)), 1)
        def_cphase.rx(-np.pi / 2, 1)
        def_cphase.append(rootiSwap, [0, 1])
        def_cphase.z(1)
        def_cphase.ry(2 * np.arcsin(np.sqrt(2) * np.sin(x)), 1)
        def_cphase.append(rootiSwap, [0, 1])
        def_cphase.rx(-np.pi / 2, 1)
        def_cphase.rz(np.arcsin(np.tan(x)) - np.pi, 1)
        return def_cphase

    def run(self, dag: DAGCircuit):
        """Run the EchoRZXWeylDecomposition pass on `dag`.
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
                "EchoRZXWeylDecomposition expects a single qreg input DAG,"
                f"but input DAG had qregs: {dag.qregs}."
            )

        trivial_layout = Layout.generate_trivial_layout(*dag.qregs.values())

        # decomposer = TwoQubitControlledUDecomposer(RZXGate)
        decomposer = self.tempalibbadecomp

        for node in dag.two_qubit_ops():

            unitary = Operator(node.op).data
            dag_weyl = circuit_to_dag(decomposer(unitary))
            dag.substitute_node_with_dag(node, dag_weyl)

        # for node in dag.two_qubit_ops():
        #     if node.name == "rzx":
        #         control = node.qargs[0]
        #         target = node.qargs[1]

        #         physical_q0 = trivial_layout[control]
        #         physical_q1 = trivial_layout[target]

        #         is_native = self._is_native((physical_q0, physical_q1))

        #         theta = node.op.params[0]
        #         if is_native:
        #             dag.substitute_node_with_dag(node, self._echo_rzx_dag(theta))
        #         else:
        #             dag.substitute_node_with_dag(
        #                 node, self._reverse_echo_rzx_dag(theta)
        #             )

        return dag
