import itertools
from backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Nduv, Gate
from qiskit.exceptions import QiskitError
from qiskit.circuit.library.standard_gates import *
from utils.riswap_gates.riswap import RiSwapGate, fSim


class FakeTree(ConfigurableFakeBackendV2):
    """A mock backendv2"""

    def __init__(self, twoqubitgate="cx", module_size=4, children=4, total_levels=3):
        assert children <= module_size
        #children refers to children per module

    
        
        qubit_counter = 0 #increment everytime request a new one
        coupling_map = [] #TODO

        def get_module(qubit_counter, starting_qubit=None):
            temp_qubits = []
            if starting_qubit is not None:
                temp_qubits.append(starting_qubit)
            for i in range(module_size - len(temp_qubits)):
                temp_qubits.append(qubit_counter)
                qubit_counter+=1
            temp_edges = [
                el
                for el in itertools.product(temp_qubits, repeat=2)
                if el[0] != el[1]
            ]
            #remove before returning so only get the qubits specific to the new module
            if starting_qubit is not None:
                temp_qubits.remove(starting_qubit)
            return qubit_counter, temp_qubits, temp_edges
        
        qubit_counter, root_q, root_e = get_module(qubit_counter)
        coupling_map.extend(root_e)
        
        def foo_recursive(qubit_counter, root_q, level):
            #convention, root only counts as level=1
            if level == (total_levels-1):
                return qubit_counter
            offset = 1 if level != 0 else  0
            #this offset says that if we aren't the first level then we need less one child bc it points to the parent
            for node_i in range(children-offset):

                node_q = root_q[node_i]#+offset]
                #extend a module from this node
                qubit_counter, child_q, child_e = get_module(qubit_counter, starting_qubit=node_q)
                coupling_map.extend(child_e)

                #XXX
                qubit_counter= foo_recursive(qubit_counter, child_q, level+1)
            return qubit_counter

        ##
        qubit_counter = foo_recursive(qubit_counter, root_q, level=0)
        qubits = list(range(qubit_counter))

        # finally,
        # delete repeats
        coupling_map = list(set(coupling_map))
        # add bidirectional edges
        coupling_map += [[q2, q1] for q1, q2 in coupling_map]
        # check no edges to self
        coupling_map = [[q1, q2] for q1, q2 in coupling_map if q1 != q2]

        gate_configuration = {}
        gate_configuration[IGate] = [(i,) for i in qubits]

        # global RZ
        gate_configuration[RZGate] = [(i,) for i in qubits]
        # global X, Y, SX, SXdg
        gate_configuration[XGate] = [(i,) for i in qubits]
        gate_configuration[YGate] = [(i,) for i in qubits]
        gate_configuration[SXGate] = [(i,) for i in qubits]
        gate_configuration[SXdgGate] = [(i,) for i in qubits]

        if twoqubitgate == "cr":
            gate_configuration[RZXGate] = [(i, j) for i, j in coupling_map]
        if twoqubitgate == "cx":
            # can do CX on all pairs in coupling map
            gate_configuration[CXGate] = [(i, j) for i, j in coupling_map]
        if twoqubitgate == "riswap":
            gate_configuration[RiSwapGate] = [(i, j) for i, j in coupling_map]
        if twoqubitgate == "syc":
            gate_configuration[fSim] = [(i, j) for i, j in coupling_map]

        # global measure
        measurable_qubits = qubits

        super().__init__(
            name=f"Tree{module_size}-{children}-{total_levels}-{twoqubitgate}",
            description="a mock backend",
            n_qubits=len(qubits),
            gate_configuration=gate_configuration,
            parameterized_gates={
                RZGate: ["theta"],
                RYGate: ["theta"],
                RiSwapGate: ["alpha"],
                U3Gate: ["theta", "phi", "lambda"],
                RZXGate: ["theta"],
                fSim: ["theta", "phi"],
            },
            measurable_qubits=measurable_qubits,
            gate_durations={ #deprecated
                IGate: 0,
                RZGate: 0,
                RYGate: 0,
                XGate: 0,
                YGate: 0,
                SXGate: 0,
                SXdgGate: 0,
                CXGate: 1,
                RiSwapGate: 1,  # time of iSwap
                U3Gate: 0,
                RZXGate: 1,
                fSim: 0.748,
            },
            single_qubit_gates=["rz", "x", "y", "sx", "sxdg"]
            # qubit_coordinates=qubit_coordinates,
        )
        self.plot_coupling_map = coupling_map
