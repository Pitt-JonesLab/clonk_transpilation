from qiskit.circuit.library.standard_gates import *

from src.clonk.backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from src.clonk.utils.riswap_gates.riswap import RiSwapGate


class FakeHexLattice(ConfigurableFakeBackendV2):
    """A mock backendv2."""

    def __init__(self, twoqubitgate="cr", enforce_max_84=True, small=False):
        from qiskit.transpiler.coupling import CouplingMap

        assert not (enforce_max_84 and small)
        if small:
            coupling_map = CouplingMap.from_hexagonal_lattice(rows=2, cols=3)
        else:
            coupling_map = CouplingMap.from_hexagonal_lattice(rows=6, cols=5)

        qubits = list(range(len(coupling_map.physical_qubits)))
        # need to convert CouplingMap object to an edge list
        coupling_map = list(coupling_map.get_edges())

        if enforce_max_84:
            # in this case we just need to add 2 qubits to make it 84
            coupling_map += [(54, 82), (82, 83), (83, 40)]
            qubits = list(range(84))

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
            name=f"Hex-Lattice-{twoqubitgate}",
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
                RZXGate: 2,
            },
            single_qubit_gates=["rz", "x", "y", "sx", "sxdg"]
            # qubit_coordinates=qubit_coordinates,
        )
        self.plot_coupling_map = coupling_map