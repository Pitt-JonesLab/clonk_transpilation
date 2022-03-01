"""Map (with minimum effort) a DAGCircuit onto a `coupling_map` adding swap gates."""

from asyncio import InvalidStateError
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.layout import Layout
from qiskit.circuit.library.standard_gates import SwapGate


class NonGlobalSwapPass(TransformationPass):
    """Map (with minimum effort) a DAGCircuit onto a backend adding swap gates.

    The basic mapper is a minimum effort to insert swap gates to map the DAG onto
    a coupling map. When a gate is not in the backend qubit's possibilities, it inserts
    one or more swaps in front to make it compatible.
    """

    def __init__(self, backend, decompose_1q=True, fake_run=False):
        """BasicSwap initializer.

        Args:
            coupling_map (CouplingMap): Directed graph represented a coupling map.
            fake_run (bool): if true, it only pretend to do routing, i.e., no
                swap is effectively added.
        """
        super().__init__()
        self.backend = backend
        self.coupling_map = backend.coupling_map
        self.fake_run = fake_run
        self.decompose_1q = decompose_1q

    def run(self, dag):
        """Run the BasicSwap pass on `dag`.

        Args:
            dag (DAGCircuit): DAG to map.

        Returns:
            DAGCircuit: A mapped DAG.

        Raises:
            TranspilerError: if the coupling map or the layout are not
            compatible with the DAG.
        """
        # if self.fake_run:
        #     raise NotImplementedError
        #     return self.fake_run(dag)

        new_dag = dag._copy_circuit_metadata()

        if len(dag.qregs) != 1 or dag.qregs.get("q", None) is None:
            raise TranspilerError("Basic swap runs on physical circuits only")

        if len(dag.qubits) > len(self.coupling_map.physical_qubits):
            raise TranspilerError(
                "The layout does not match the amount of qubits in the DAG"
            )

        canonical_register = dag.qregs["q"]
        trivial_layout = Layout.generate_trivial_layout(canonical_register)
        current_layout = trivial_layout.copy()

        for layer in dag.serial_layers():
            subdag = layer["graph"]

            for gate in subdag.op_nodes():
                physical_q_list = [current_layout[qarg] for qarg in gate.qargs]
                if len(physical_q_list) > 2:
                    raise NotImplementedError
                if len(physical_q_list) == 2:
                    single = 0
                    physical_q0 = physical_q_list[0]
                    physical_q1 = physical_q_list[1]
                    need_swap = (
                        self.coupling_map.distance(physical_q0, physical_q1) != 1
                    )
                if len(physical_q_list) == 1:
                    single = 1
                    physical_q0 = physical_q_list[0]
                    # assert needs swap if gate not present on current physical qubit
                    need_swap = True
                    candidate_qubits = []
                    for instruction in self.backend.instructions:
                        # find match in instrction config, or if not decompose, find any 1Q gate in position
                        if (
                            instruction[0].name == gate.name
                            or (
                                gate.name == "u3"
                                and not instruction[0].name in ["id", "reset"]
                                and not self.decompose_1q
                            )
                        ) and instruction[1] == (physical_q0,):
                            need_swap = False
                            # break
                        elif instruction[0].name == gate.name or (
                            gate.name == "u3"
                            and not instruction[0].name in ["id", "reset"]
                            and not self.decompose_1q
                        ):
                            if instruction[1][0] != physical_q0:
                                candidate_qubits.append(instruction[1][0])

                    # FIXME can be improved with more context awareness
                    # if need_swap then assign physical_q1 to be the closest qubit that contains the gate we need
                    if need_swap:
                        if len(candidate_qubits) == 1:
                            raise InvalidStateError
                        physical_q1 = candidate_qubits[0]
                        min_path = len(
                            self.coupling_map.shortest_undirected_path(
                                physical_q0, physical_q1
                            )
                        )
                        # minimize length of path to qubit that contains the instruction we need
                        for phys_qubit in candidate_qubits[1:]:
                            temp = self.coupling_map.shortest_undirected_path(
                                physical_q0, phys_qubit
                            )
                            if min_path > len(temp):
                                min_path = len(temp)
                                physical_q1 = phys_qubit

                if need_swap:
                    # Insert a new layer with the SWAP(s).
                    swap_layer = DAGCircuit()
                    swap_layer.add_qreg(canonical_register)

                    path = self.coupling_map.shortest_undirected_path(
                        physical_q0, physical_q1
                    )
                    # offset by single, if doing a 1Q gate need to SWAP all the way, not just to where they touch on coupling map
                    for swap in range(len(path) - 2 + single):
                        connected_wire_1 = path[swap]
                        connected_wire_2 = path[swap + 1]

                        qubit_1 = current_layout[connected_wire_1]
                        qubit_2 = current_layout[connected_wire_2]

                        # create the swap operation
                        swap_layer.apply_operation_back(
                            SwapGate(), qargs=[qubit_1, qubit_2], cargs=[]
                        )

                    # layer insertion
                    order = current_layout.reorder_bits(new_dag.qubits)
                    new_dag.compose(swap_layer, qubits=order)

                    # update current_layout
                    for swap in range(len(path) - 2 + single):
                        current_layout.swap(path[swap], path[swap + 1])

            order = current_layout.reorder_bits(new_dag.qubits)
            new_dag.compose(subdag, qubits=order)

        if self.fake_run:
            self.property_set["final_layout"] = current_layout
            return dag
        else:
            return new_dag

    def _fake_run(self, dag):
        """Do a fake run the BasicSwap pass on `dag`.

        Args:
            dag (DAGCircuit): DAG to improve initial layout.

        Returns:
            DAGCircuit: The same DAG.

        Raises:
            TranspilerError: if the coupling map or the layout are not
            compatible with the DAG.
        """
        if len(dag.qregs) != 1 or dag.qregs.get("q", None) is None:
            raise TranspilerError("Basic swap runs on physical circuits only")

        if len(dag.qubits) > len(self.coupling_map.physical_qubits):
            raise TranspilerError(
                "The layout does not match the amount of qubits in the DAG"
            )

        canonical_register = dag.qregs["q"]
        trivial_layout = Layout.generate_trivial_layout(canonical_register)
        current_layout = trivial_layout.copy()

        for layer in dag.serial_layers():
            subdag = layer["graph"]
            for gate in subdag.two_qubit_ops():
                physical_q0 = current_layout[gate.qargs[0]]
                physical_q1 = current_layout[gate.qargs[1]]
                if self.coupling_map.distance(physical_q0, physical_q1) != 1:
                    path = self.coupling_map.shortest_undirected_path(
                        physical_q0, physical_q1
                    )
                    # update current_layout
                    for swap in range(len(path) - 2):
                        current_layout.swap(path[swap], path[swap + 1])

        self.property_set["final_layout"] = current_layout
        return dag
