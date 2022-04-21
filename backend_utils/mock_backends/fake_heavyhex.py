import itertools
from os import kill
from cirq import XPowGate
from backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Nduv, Gate
from qiskit.exceptions import QiskitError
from qiskit.circuit.library.standard_gates import *
from utils.riswap_gates.riswap import RiSwapGate


class FakeHeavyHex(ConfigurableFakeBackendV2):
    """A mock backendv2"""

    def __init__(self, twoqubitgate="cr", enforce_max_84=True):

        from qiskit.transpiler.coupling import CouplingMap

        coupling_map = CouplingMap.from_heavy_hex(distance=7)
        qubits = list(range(len(coupling_map.physical_qubits)))
        # need to convert CouplingMap object to an edge list
        coupling_map = list(coupling_map.get_edges())

        if enforce_max_84:
            # define list of nodes to remove
            kill_list = [
                68,
                108,
                40,
                41,
                72,
                48,
                114,
                47,
                113,
                71,
                107,
                39,
                106,
                38,
                105,
                70,
                111,
                45,
                112,
                46,
                37,
                104,
                36,
                103,
                35,
                69,
                109,
                42,
                43,
                110,
                44,
            ]

            # we also need to rename all the qubits as we place them back in!!!1
            rename = {}
            k = 0
            for i in range(len(coupling_map)):
                if i in kill_list:
                    rename[i] = -1
                else:
                    rename[i] = k
                    k += 1
            # shoot, the coupling map is not well ordered I think I need to choose which to delete by hand
            temp_coupling_map = []
            for i, j in coupling_map:
                if i not in kill_list and j not in kill_list:
                    temp_coupling_map.append((rename[i], rename[j]))
            coupling_map = temp_coupling_map
            qubits = list(range(84))

        # choose 6 so roughly matches order of other large backends
        # num_qubits = 83.5
        # but have to round up to nearest odd integer so choose 7
        # qubits = list(range(115))

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

        # global measure
        measurable_qubits = qubits

        super().__init__(
            name=f"Heavy-Hex-{twoqubitgate}",
            description="a mock backend",
            n_qubits=len(qubits),
            gate_configuration=gate_configuration,
            parameterized_gates={
                RZGate: ["theta"],
                RYGate: ["theta"],
                RiSwapGate: ["alpha"],
                U3Gate: ["theta", "phi", "lambda"],
                RZXGate: ["theta"],
            },
            measurable_qubits=measurable_qubits,
            gate_durations={
                IGate: 0,
                RZGate: 0,
                RYGate: 0,
                XGate: 0,
                YGate: 0,
                SXGate: 0,
                SXdgGate: 0,
                CXGate: 2,
                RiSwapGate: 2,  # time of iSwap
                U3Gate: 0,
                RZXGate: 2.478,
            },
            single_qubit_gates=["rz", "x", "y", "sx", "sxdg"]
            # qubit_coordinates=qubit_coordinates,
        )
        self.plot_coupling_map = coupling_map
