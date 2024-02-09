from qiskit.circuit.library.standard_gates import *

from clonk.backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from clonk.utils.riswap_gates.riswap import RiSwapGate


class PenguinV4(ConfigurableFakeBackendV2):
    """A mock backendv2."""

    def __init__(self, twoqubitgate="cx"):
        num_rows = 4  # even
        num_columns = 5  # odd

        qubits = list(range(num_rows * num_columns))

        # need to convert CouplingMap object to an edge list
        from qiskit.transpiler.coupling import CouplingMap

        coupling_map = list(
            CouplingMap.from_grid(
                num_rows=num_rows, num_columns=num_columns
            ).get_edges()
        )

        removed_edges = []
        # delete every other vertical edge
        i = 0
        while i < len(qubits) - num_columns:
            removed_edges.append((i, i + num_columns))
            i += 2

        removed_edges += [(j, i) for i, j in removed_edges]
        coupling_map = [el for el in coupling_map if el not in removed_edges]

        qubit_coordinates = [
            (i, j) for i in range(num_rows) for j in range(num_columns)
        ]

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
            name="penguin_V4",
            description="a mock backend",
            n_qubits=len(qubits),
            gate_configuration=gate_configuration,
            parameterized_gates={
                RZGate: ["theta"],
                RYGate: ["theta"],
                RZXGate: ["theta"],
                U3Gate: ["theta", "phi", "lambda"],
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
            single_qubit_gates=["rz", "x", "y", "sx", "sxdg"],
            qubit_coordinates=qubit_coordinates,
        )

        self.plot_coupling_map = coupling_map
