from numpy.lib.function_base import kaiser
import qiskit.quantum_info as qi
import qiskit.circuit.library.standard_gates as g
import qiskit.circuit.quantumcircuit as qc
from itertools import product
import numpy as np
from circuit_ir import IR

# TODO: implement recursive window size, right now is hardcoded
window = [3, 2]
# TODO: refactor transpile() return value
# TODO: implement transpile force
# TODO: more advanced cost function (timing)
# TODO: replace IR, use to fix printing
# TODO: refactor messy foo() and product code
# TODO: better practice to check 2 qubit gates in foo (?), see _foobar
# TODO: investigate CNOT edge cases

####
# later todos:
# TODO: QASM convert


class Transpiler:
    def __init__(self, gate_set, str_gate, foobar):
        """Instantiate a transpiler object by specifying a list of gates that circuits may be compiled into"""
        self._foobar = foobar  # TODO: refactor, foobar currently holds custom gate class defintiions
        self.gate_set = gate_set
        # TODO: I can't think of a better way to get this data from gate_set right now
        self.gate_set_str = str_gate
        self.circuit_list = self.generate_all(window)
        self.fingerprint_dict = self.generate_fingerprints()
        self.identity_dict = self.generate_circuitIdentities()
        print(
            f"Created {len(self.identity_dict.keys())} identities from {len(self.circuit_list)} possible circuits"
        )

    def transpile(self, circuit):
        """Given a circuit, find equivalent circuit only using gates from Transpiler instance's gate_set"""
        reduced_circuit = self._force_transpile(circuit)
        # will fail if don't adjust window size
        temp = self._optimizeCircuit(reduced_circuit)
        return temp

    def _force_transpile(self, circuit):
        # from qiskit import transpile as trnsp
        # translator method tells transpiler to use equivalence library
        # TODO: test and debug, does this need a recursive call/gate check
        # TODO: self.gate_set needs to be formatted as strings for basis_gates=
        # transp_qc = trnsp(
        #     circuit,
        #     basis_gates=["id", "cx", "swap"],
        #     optimization_level=0,
        #     translation_method="translator",
        # )
        from qiskit.transpiler.passes.basis import BasisTranslator
        from equivalence_library import SessionEquivalenceLibrary

        translator = BasisTranslator(SessionEquivalenceLibrary, self.gate_set_str)
        from qiskit.converters import circuit_to_dag, dag_to_circuit

        dag = circuit_to_dag(circuit)
        transp_qc = dag_to_circuit(translator.run(dag))

        return transp_qc

    def _optimizeCircuit(self, circuit):
        """Given a circuit, returns a list of equivalent circuits
        optional- specify a gate_set to only include circuits with that gate_set
        ie dont want to decompose a gate into a circuit made up of itself"""

        """First approach at an algorithm, 
        1. Pass through all and find a window subcircuit that has minimum cost,
        reason to only find one is because for each loop don't want to look at intersecting subcircuits
        2. Do replacement, eliminate I bars
        3. Repeat with new circuit until now new subs found"""

        """What about do minimum cost replacement for each window subcircuit and create diverging branches, search using a stack
        obvious problem that could be hard to avoid, recursive identities causes infinite loop
        I'd guess quanto does something like this, 'cost-based search algorithm' is all they say in paper"""

        minimum_cost = -1
        substituted_circuit = circuit
        while 1:
            circuit_key_list = self._circuitToHash(substituted_circuit)
            k = 0
            for circuit_key in circuit_key_list:

                finger_key = self.fingerprint_dict[circuit_key]
                # if gate_set is not None, only return circuits that contain gates from the set
                identities = self.identity_dict[finger_key]
                cost_dict = self.cost_dictionary(identities)

                # use greater than because is counting number of I gates
                if cost_dict[0][1] > minimum_cost:
                    minimum_cost = cost_dict[0][1]
                    min_window_iter = k
                    min_window_sub = cost_dict[0][0]
                k += 1

            # reconstruct using min_window_sub
            substituted_circuit = IR.substitute(
                substituted_circuit, min_window_sub, min_window_iter
            )

            if minimum_cost == -1:
                break
        # this code is redunant, all circuits should be only made of gateset gates anyway
        # restricted_identities = []
        # for circuit in identities:
        #     if all(
        #         [
        #             any(
        #                 [
        #                     isinstance(circuit_gate[0], gate_set_el)
        #                     for gate_set_el in self.gate_set
        #                 ]
        #             )
        #             for circuit_gate in circuit
        #         ]
        #     ):
        #         restricted_identities.append(circuit)
        # return restricted_identities

        return substituted_circuit

    def sort_identities(self, identity_list):
        # start simple, count number of identity gates
        _count_identity = lambda circ: sum(
            [isinstance(gate[0], g.IGate) for gate in circ]
        )
        return sorted(identity_list, key=lambda x: _count_identity(x), reverse=True)

    def cost_dictionary(self, circuit_list):
        _count_identity = lambda circ: sum(
            [isinstance(gate[0], g.IGate) for gate in circ]
        )
        return [(c, _count_identity(c)) for c in self.sort_identities(circuit_list)]

    def generate_circuitIdentities(self):
        """The hash table of substitutions includes the fingerprints as keys
        and an array of matching circuit identities as values."""
        identity_dict = {}
        for circuit in self.circuit_list:
            circuit_key = self._circuitToHash(circuit)[0]
            finger_key = self.fingerprint_dict[circuit_key]
            # if key exists, append it to the list
            if finger_key in identity_dict.keys():
                identity_dict[finger_key].append(circuit)

            # otherwise, create new entry
            else:
                identity_dict[finger_key] = [circuit]

        return identity_dict

    def _circuitToHash(self, circuit):
        # see Fig. 7 of Quanto paper
        # TODO: currently assuming window height always fixed
        # returns a list of hashs, for circuit split by window size
        circuit_ir = IR(circuit)
        circuit_key_list = circuit_ir.split(window)
        return circuit_key_list

    def generate_fingerprints(self):
        """Calculate the unitary matrices and generate their fingerprints"""
        fingerprint_dict = {}
        for circuit in self.circuit_list:
            circuit_key = self._circuitToHash(circuit)[0]
            # rounding unitary matrix so values like .99999999 have same hash as 1.0
            unitary_value = hash(
                np.around(qi.Operator(circuit).data, decimals=8).tobytes()
            )

            fingerprint_dict[circuit_key] = unitary_value
        return fingerprint_dict

    def generate_all(self, window):
        """Generate all the possible circuits of the quantum circuits using the gate set
        window = (width, height)
        """

        circuit_list = []

        def foo(gate_set, height):
            # for multiqubit gates, need to select total of r qubit operands
            # eg CX counts as 2 to total qubit operants
            # this is not exactly accurate, but assume CX is only with 1 control bit
            # TODO: refactor hardcoding

            # perms is a list of possible bars
            gate_perms = []
            # use repeat as height because each gate is atleast 1 height so upperbound
            for gate_comb in product(gate_set, repeat=height):
                operands = 0
                temp_gate_perm = []

                for gate in gate_comb:
                    temp_gate_perm.append(gate)

                    if gate in [g.IGate, g.HGate, g.XGate, g.YGate, g.ZGate]:
                        operands += 1
                    # BAD, this hardcode assumes all custom gates are 2 qubits
                    elif gate in [g.CXGate, g.SwapGate, g.CZGate] + self._foobar:
                        # by adding height, forces 2 qubit gates to only be put in gate_perm if they are at firstt
                        operands += height
                        # TODO: only allow 1 2-qubit gate per bar(?)
                        # operands +=2

                    else:
                        raise NotImplementedError

                    if operands == height:
                        # avoid duplicates
                        if temp_gate_perm not in gate_perms:
                            gate_perms.append(temp_gate_perm)
                        break
                    if operands > height:
                        break

            return gate_perms

        # before taking product need to modify gate_set so includes permutations of control and target qubits
        gate_perms = foo(self.gate_set, window[1])
        gate_perms_2qubitwithtargets = []
        for gate_bar in gate_perms:
            if len(gate_bar) == 1:
                control = 0
                target = 0

                # for swap-family gates dont permuate control and target
                if gate_bar[0] in [g.CXGate]:
                    for control in range(0, window[1]):
                        for target in range(0, window[1]):
                            if control != target:
                                temp_gate_bar = []
                                temp_gate_bar.append((gate_bar[0], [control, target]))

                                # add missing Is - not if in between gate?
                                for qb in range(window[1]):
                                    if qb < min(control, target) or qb > max(
                                        control, target
                                    ):
                                        temp_gate_bar.append((g.IGate, [qb]))
                                gate_perms_2qubitwithtargets.append(temp_gate_bar)

                else:
                    for control in range(0, window[1]):
                        for target in range(control + 1, window[1]):
                            temp_gate_bar = []
                            temp_gate_bar.append((gate_bar[0], [control, target]))

                            # add missing Is - not if in between gate?
                            for qb in range(window[1]):
                                if qb < min(control, target) or qb > max(
                                    control, target
                                ):
                                    temp_gate_bar.append((g.IGate, [qb]))
                            gate_perms_2qubitwithtargets.append(temp_gate_bar)

            else:
                temp_gate_bar = []
                for qubit_index in range(window[1]):
                    temp_gate_bar.append((gate_bar[qubit_index], [qubit_index]))
                gate_perms_2qubitwithtargets.append(temp_gate_bar)

        for gate_perm in product(gate_perms_2qubitwithtargets, repeat=window[0]):
            temp = qc.QuantumCircuit(window[1])
            for gate_bar in gate_perm:

                for gate in gate_bar:
                    temp.append(gate[0](), gate[1])

            circuit_list.append(temp)

        return circuit_list
