import itertools

import numpy as np
from qiskit.circuit.library.standard_gates import *

from src.clonk.backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from src.clonk.utils.riswap_gates.riswap import RiSwapGate, fSim


class FakeModular(ConfigurableFakeBackendV2):
    """A mock backendv2."""

    def __init__(self, twoqubitgate="cx", module_size=4, children=4, total_levels=3):
        assert children <= module_size
        assert (
            children > 1
        )  # I think this would break things with the flattening checks
        # children refers to children per module

        coupling_map = []  # TODO

        def get_unit_module(qubit_counter, reserved_qubits=[]):
            temp_qubits = []
            temp_qubits.extend(reserved_qubits)
            for i in range(module_size - len(temp_qubits)):
                temp_qubits.append(qubit_counter)
                qubit_counter += 1
            temp_edges = [
                el for el in itertools.product(temp_qubits, repeat=2) if el[0] != el[1]
            ]
            return qubit_counter, temp_qubits, temp_edges

        # brainstorming:
        # recursive case, get #children of (target_level-1) module which are joined by +1 (target_level-1) module
        # then create convention that the last child to be the overlapping one and combine qubits at the end
        ##
        def recursive_foo(qubit_counter, current_level, reserved=[]):
            if current_level == 1:
                # convention is that total level is 1 is just a unit
                qubit_counter, r_q, r_e = get_unit_module(qubit_counter, reserved)
                coupling_map.extend(r_e)
                return qubit_counter, r_q
            else:
                reserve_overlapping = []
                temp_module_qubits = []  # list of level-1 modules
                for c_i in range(children):
                    # indexing the recursive list of reserved qubits is where the magic happens :)
                    qubit_counter, c_module = recursive_foo(
                        qubit_counter,
                        current_level=current_level - 1,
                        reserved=reserved[c_i] if len(reserved) > 0 else [],
                    )
                    reserve_overlapping.append([c_module[-1]])
                    temp_module_qubits.append(c_module)
                # now one more module to connect the children, note final module doesn't add any new qubits so don't extend temp
                # this weird packing stuff is a way of flattening a variable number of lists, bc we don't know what level of nested reserve_overlapping has...
                # in the final call to link things together, we use index[0] on the reserved so it uses the opposite node to link together - instead of the one that goes to children
                temp_list = np.array(reserve_overlapping).transpose()
                while len(temp_list) != 1:  # check if not flat yet
                    temp_list = temp_list[0]
                temp_list = temp_list[0]
                qubit_counter, c_module = recursive_foo(
                    qubit_counter, current_level=1, reserved=temp_list
                )
                return qubit_counter, temp_module_qubits

        qubit_counter, _ = recursive_foo(
            qubit_counter=0, current_level=total_levels, reserved=[]
        )
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
            name=f"Modular{module_size}-{children}-{total_levels}-{twoqubitgate}",
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
            gate_durations={  # deprecated
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
