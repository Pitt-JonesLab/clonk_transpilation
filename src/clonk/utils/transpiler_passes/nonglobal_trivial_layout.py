from qiskit.transpiler.basepasses import AnalysisPass
from qiskit.transpiler.exceptions import TranspilerError
from qiskit.transpiler.layout import Layout


class NonGlobalTrivialLayout(AnalysisPass):
    """Choose a Layout based on non-global operations for the backend.

    This pass associates a physical qubit (int) to each virtual qubit of the circuit (Qubit).
    For non-global operations in the circuit (trivial does not recursively check decomps),
    as defined by the target, select a qubit that the operation is present on. The rest can be trivial.

    Method:
    The pass should begin with a trivial layout (n_virtual->n_physical), then for each non-global op,
    swap to a remaining trivially mapped qubit.

    TODO Notes:
    Won't be preserving across other passes, so for now just start with this layout and try testing BasisTransform.
    Then, if circuit needs to transform basis first, this mapping doesn't find the nonglobal operation.
    Once you get this working, perhaps adding an internal pass to basischange could work
    (but that internal pass needs to not consider nonglobal ops?)
    Needs to check gates but also measure gates

    This currently is not working, I think because after I do a swap its not presevered.
    A smarter way is to take a qubit's union of all the gates it needs or place it on the one that is closest to it physically so can swap to it.
    ...I need to figure out how the swap routing is supposed to work, and why is it currently not working.
    """

    def __init__(self, backend_target, strategy):
        """NonGlobalTrivialLayout initializer.

        Args:"
            backend_prop (BackendProperties): backend properties object

        Raises:
            TranspilerError: if invalid options
        """

        super().__init__()
        self.backend_target = backend_target
        self.remaining_physical_qubits = backend_target.physical_qubits
        # self.gate_list = []
        self.strategy = strategy

    def run(self, dag):
        """Run the NonGlobalTrivialLayout pass on 'dag'
        Args:
            dag (DAGCircuit): DAG to find layout for

        Raises:
            TranspilerError: if ...
        """
        if not True:
            raise TranspilerError("found something wrong!")

        if self.strategy == "trivial":
            layout = Layout.generate_trivial_layout(
                *(dag.qubits + list(dag.qregs.values()))
            )

        if self.strategy == "shuffle":
            from random import shuffle

            qubits = list(range(len(dag.qubits)))
            qubits = list(range(len(self.backend_target.physical_qubits)))
            shuffle(qubits)
            qubits = qubits[0 : len(dag.qubits)]
            layout = Layout.from_intlist(qubits, *dag.qregs.values())

        if self.strategy == "visual":
            raise NotImplementedError

        # for dag_node in dag.op_nodes():
        #     gate_name = dag_node.op.name
        #     if gate_name == "barrier":
        #         continue
        #     virtual_qubit_list = dag_node.qargs
        #     if len(virtual_qubit_list) == 1:

        #         virtual_qubit = dag_node.qargs[0]

        #         # if already found don't replace, also avoid double swaps
        #         if (layout[virtual_qubit],) in self.backend_target._gate_map[
        #             gate_name
        #         ].keys():
        #             continue

        #         for key, value in self.backend_target._gate_map[gate_name].items():
        #             # key=(1,)
        #             if key[0] in self.remaining_physical_qubits:
        #                 # swap new phyiscal location with virtuals old, this might not work for other than basic cases
        #                 # needs testing
        #                 layout.swap(layout[virtual_qubit], key[0])
        #                 self.remaining_physical_qubits.remove(key[0])
        #                 break
        #     else:
        #         virtual_qubit = [layout[dnq] for dnq in virtual_qubit_list]
        #         if (
        #             tuple(virtual_qubit)
        #             in self.backend_target._gate_map[gate_name].keys()
        #         ):
        #             continue

        # # # layout = Layout()
        # # # for q in dag.qubits:
        # # #     pid = self._qarg_to_id(q)
        # # #     hwid = self.prog2hw[pid]
        # # #     layout[q] = hwid
        # for qreg in dag.qregs.values():
        #     layout.add_register(qreg)
        self.property_set["layout"] = layout
