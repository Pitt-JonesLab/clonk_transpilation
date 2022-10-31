import itertools
from src.backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Nduv, Gate
from qiskit.exceptions import QiskitError
from qiskit.circuit.library.standard_gates import *
from src.utils.riswap_gates.riswap import RiSwapGate, fSim


class FakeSurfaceCode(ConfigurableFakeBackendV2):
    """A mock backendv2"""

    def __init__(self, twoqubitgate="cx", qubit_size=20, row_length=5):
        qubits = list(range(qubit_size))
        # assume 4 rows, 5 cols
        row_length = row_length
        coupling_map = []
        for u in qubits:
            down = u + row_length
            if down < len(qubits):
                coupling_map.append([u, down])
            up = u - row_length
            if up >= 0:
                coupling_map.append([u, up])
            left = u - 1
            if u % row_length != 0:
                coupling_map.append([u, left])
            right = u + 1
            if (u + 1) % row_length != 0:
                coupling_map.append([u, right])

        # qubit_coordinates = [[0, 1], [1, 0], [1, 1], [1, 2]]

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
            name=f"Square-Lattice-{twoqubitgate}",
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
            gate_durations={
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
