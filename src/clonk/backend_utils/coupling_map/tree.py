from itertools import product
from qiskit.transpiler import CouplingMap

class Tree(CouplingMap):
    def __init__(self, module_size=4, children=4, total_levels=3):
        
        qubit_counter = 0
        coupling_map = []

        def _get_module(qubit_counter, starting_qubit=None):
            temp_qubits = []
            if starting_qubit is not None:
                temp_qubits.append(starting_qubit)
            for i in range(module_size - len(temp_qubits)):
                temp_qubits.append(qubit_counter)
                qubit_counter += 1
            temp_edges = [el for el in product(temp_qubits, repeat=2) if el[0] != el[1]]
            # remove before returning so only get the qubits specific to the new module
            if starting_qubit is not None:
                temp_qubits.remove(starting_qubit)
            return qubit_counter, temp_qubits, temp_edges


        qubit_counter, root_q, root_e = _get_module(qubit_counter)
        coupling_map.extend(root_e)


        def _foo_recursive(qubit_counter, root_q, level):
            # convention, root only counts as level=1
            if level == (total_levels - 1):
                return qubit_counter
            offset = 1 if level != 0 else 0
            # this offset says that if we aren't the first level then we need less one child bc it points to the parent
            for node_i in range(children - offset):
                node_q = root_q[node_i]  # +offset]
                # extend a module from this node
                qubit_counter, child_q, child_e = _get_module(
                    qubit_counter, starting_qubit=node_q
                )
                coupling_map.extend(child_e)

                # XXX
                qubit_counter = _foo_recursive(qubit_counter, child_q, level + 1)
            return qubit_counter
        ##
        qubit_counter = _foo_recursive(qubit_counter, root_q, level=0)
        # finally,
        # delete repeats
        coupling_map = list(set(coupling_map))
        # add bidirectional edges
        coupling_map += [[q2, q1] for q1, q2 in coupling_map]
        # check no edges to self
        coupling_map = [[q1, q2] for q1, q2 in coupling_map if q1 != q2]

        super().__init__(coupling_map)