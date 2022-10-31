import itertools
from src.backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Nduv, Gate
from qiskit.exceptions import QiskitError
from qiskit.circuit.library.standard_gates import *
from src.utils.riswap_gates.riswap import RiSwapGate


class PenguinV3(ConfigurableFakeBackendV2):
    """A mock backendv2"""

    def __init__(self):

        num_rows = 12  # even
        num_columns = 11  # odd

        qubits = list(range(num_rows * num_columns))

        # need to convert CouplingMap object to an edge list
        from qiskit.transpiler.coupling import CouplingMap

        coupling_map = list(
            CouplingMap.from_grid(
                num_rows=num_rows, num_columns=num_columns
            ).get_edges()
        )
        # removed_edges = [
        #     (1, 6),
        #     (2, 7),
        #     (3, 8),
        #     (6, 11),
        #     (8, 13),
        #     (11, 16),
        #     (12, 17),
        #     (13, 18),
        # ]

        removed_edges = []
        i = 1
        j = 0
        while j < num_rows:
            while 4 * i < num_columns:
                # (1,6)
                removed_edges.append(
                    (
                        (num_columns * j) + (4 * i - 3),
                        (num_columns * (j + 1)) + (4 * i - 3),
                    )
                )
                # (2,7)
                removed_edges.append(
                    (
                        (num_columns * j) + (4 * i - 2),
                        (num_columns * (j + 1)) + (4 * i - 2),
                    )
                )
                # (3,8)
                removed_edges.append(
                    (
                        (num_columns * j) + (4 * i - 1),
                        (num_columns * (j + 1)) + (4 * i - 1),
                    )
                )
                # (6,11)
                removed_edges.append(
                    (
                        (num_columns * (j + 1)) + (4 * i - 3),
                        (num_columns * (j + 2)) + (4 * i - 3),
                    )
                )
                # (8,13)
                removed_edges.append(
                    (
                        (num_columns * (j + 1)) + (4 * i - 1),
                        (num_columns * (j + 2)) + (4 * i - 1),
                    )
                )
                # (11,16)
                removed_edges.append(
                    (
                        (num_columns * (j + 2)) + (4 * i - 3),
                        (num_columns * (j + 3)) + (4 * i - 3),
                    )
                )
                # (12,17)
                removed_edges.append(
                    (
                        (num_columns * (j + 2)) + (4 * i - 2),
                        (num_columns * (j + 3)) + (4 * i - 2),
                    )
                )
                # (13,18)
                removed_edges.append(
                    (
                        (num_columns * (j + 2)) + (4 * i - 1),
                        (num_columns * (j + 3)) + (4 * i - 1),
                    )
                )
                i += 1
            j += 4
            i = 1

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

        gate_configuration[RZXGate] = [(i, j) for i, j in coupling_map]

        # global measure
        measurable_qubits = qubits

        super().__init__(
            name="penguin_V3",
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
