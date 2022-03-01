from itertools import product

from qiskit.circuit.quantumcircuit import QuantumCircuit

# TODO:multiply control bits
# TODO: span check incomplete - debug span gates for already in circuit vs adding new
# TODO: convert IR back to qiskit circuit or QASM


class IR:
    """Defines an Intermediate Representation for circuit optimization operations"""

    def __init__(self, circuit):
        """Takes a qiskit circuit and returns a list of bars;
        a bar is a timestep of gates (vertical column), as a list of strings"""

        self.num_qubits = circuit.num_qubits
        self.gate_list = []

        temp_index_list = []
        temp_gate_list = self.num_qubits * [None]
        for gate in circuit.data:

            # exit condition is if qubit already assigned a gate
            # OR if qubit_list contains that span over an already assigned bit
            if any([qubit.index in temp_index_list for qubit in gate[1]]) or any(
                [
                    q1.index < temp and q2.index > temp
                    for q1, q2, temp in product(gate[1], gate[1], temp_index_list)
                ]
            ):  # or any([temp1 < q.index and temp2 > q.index for q, temp1, temp2 in product(gate[1], temp_index_list, temp_index_list)]):
                # fill in missing Is
                temp_gate_list = [
                    "id" if temp_gate is None else temp_gate
                    for temp_gate in temp_gate_list
                ]

                # save and reset temps
                temp_index_list = []
                self.gate_list.append(temp_gate_list)
                temp_gate_list = self.num_qubits * [None]

            # iter through gate register
            for i, qubit in enumerate(gate[1]):
                # add to visited list
                temp_index_list.append(qubit.index)

                # assume all controlled gates start with 'c'
                if gate[0].name.startswith("c"):
                    # control is first bit by convention
                    if i == 0:
                        temp_gate_list[qubit.index] = "c;" + gate[0].name
                    else:
                        temp_gate_list[qubit.index] = "t;" + gate[0].name

                else:
                    temp_gate_list[qubit.index] = gate[0].name

        # on exit, fill Is, reset and save temps last time
        temp_gate_list = [
            "id" if temp_gate is None else temp_gate for temp_gate in temp_gate_list
        ]
        temp_index_list = []
        self.gate_list.append(temp_gate_list)
        temp_gate_list = self.num_qubits * [None]

    def left_justify(self):
        self.gate_list = [
            bar for bar in self.gate_list if any([g != "id" for g in bar])
        ]

    def split(self, window):
        """returns a list of subcircuit hashes divided by window size"""
        if window[1] != len(self.gate_list[0]):
            raise NotImplementedError

        hash_list = []
        for i in range(0, len(self.gate_list) - window[0] + 1):
            hash_list.append(str([x for x in self.gate_list[i : i + window[0]]]))

        return hash_list

    def __str__(self):
        return str([x for x in self.gate_list])

    @staticmethod
    def toCircuit(circuit_ir):
        """given an IR returns a qiskit circuit"""
        # TODO: think of a not ugly way to do this
        # TODO: this won't work for 2qubit gates
        import qiskit.circuit.library.standard_gates as g

        qc = QuantumCircuit(len(circuit_ir.gate_list[0]))
        for bar in circuit_ir.gate_list:
            for index, gate in enumerate(bar):
                if gate == "id":
                    qc.id(index)
                elif gate == "h":
                    qc.h(index)
                elif gate == "z":
                    qc.z(index)
                elif gate == "x":
                    qc.x(index)
                else:
                    raise NotImplementedError

        return qc

    @staticmethod
    def substitute(circuit, sub_circuit, window_iter):
        """static method for circuit window substitutions"""
        circuit_ir = IR(circuit)
        sub_circuit_ir = IR(sub_circuit)
        circuit_ir.gate_list[
            window_iter : len(sub_circuit_ir.gate_list) + 1
        ] = sub_circuit_ir.gate_list

        circuit_ir.left_justify()

        # add back Is so maintains atleast size of window
        while len(circuit_ir.gate_list) < len(sub_circuit_ir.gate_list):
            circuit_ir.gate_list.append(len(sub_circuit_ir.gate_list[0]) * ["id"])

        return IR.toCircuit(circuit_ir)
