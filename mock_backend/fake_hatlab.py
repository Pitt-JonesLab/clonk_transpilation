"""
Fake Hatlab device (16+4 qubit).
"""

import itertools
from qiskit.test.mock.utils.configurable_backend import ConfigurableFakeBackend
from qiskit.test.mock.utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Nduv, Gate
from qiskit.exceptions import QiskitError
from qiskit.circuit.library.standard_gates import (
    IGate,
    RXGate,
    RYGate,
    CZGate,
    SwapGate,
)


class FakeHatlab(ConfigurableFakeBackendV2):
    """A fake 16+4 qubit backend."""

    def __init__(self):

        router_qubits = [0, 5, 10, 15]
        module_qubits = list(set(range(20)).difference(set([0, 5, 10, 15])))

        coupling_map = [
            [0, 5],
            [0, 10],
            [0, 15],
            [5, 0],
            [5, 10],
            [5, 15],
            [10, 0],
            [10, 5],
            [10, 15],
            [15, 0],
            [15, 5],
            [15, 10],
        ]
        coupling_map += itertools.product(range(0, 5), repeat=2)
        coupling_map += itertools.product(range(5, 10), repeat=2)
        coupling_map += itertools.product(range(10, 15), repeat=2)
        coupling_map += itertools.product(range(15, 20), repeat=2)

        coupling_map = [[q1, q2] for q1, q2 in coupling_map if q1 != q2]

        qubit_coordinates = [
            [2, 3],
            [1, 2],
            [0, 2],
            [0, 4],
            [1, 4],
            [3, 4],
            [2, 5],
            [2, 6],
            [4, 6],
            [4, 5],
            [4, 3],
            [5, 4],
            [6, 4],
            [6, 2],
            [5, 2],
            [3, 2],
            [4, 1],
            [4, 0],
            [2, 0],
            [2, 1],
        ]
        gate_configuration = {}
        gate_configuration[RXGate] = [(i,) for i in module_qubits]
        gate_configuration[RYGate] = [(i,) for i in module_qubits]
        gate_configuration[IGate] = [(i,) for i in router_qubits + module_qubits]
        gate_configuration[SwapGate] = [(i, j) for i, j in coupling_map]
        gate_configuration[CZGate] = [
            (i, j)
            for i, j in coupling_map
            if not (i in router_qubits and j in router_qubits)
        ]

        super().__init__(
            "fake_hatlab",
            "hatlab 16+4 QC",
            20,
            gate_configuration,
            parameterized_gates={RXGate: "theta", RYGate: "theta"},
            measurable_qubits=module_qubits,
            qubit_coordinates=qubit_coordinates,
        )


class LegacyFakeHatlab(ConfigurableFakeBackend):
    """A fake 16+4 qubit backend."""

    def __init__(self):
        self.qubit_coordinates = [
            [2, 3],
            [1, 2],
            [0, 2],
            [0, 4],
            [1, 4],
            [3, 4],
            [2, 5],
            [2, 6],
            [4, 6],
            [4, 5],
            [4, 3],
            [5, 4],
            [6, 4],
            [6, 2],
            [5, 2],
            [3, 2],
            [4, 1],
            [4, 0],
            [2, 0],
            [2, 1],
        ]

        coupling_map = [
            [0, 5],
            [0, 10],
            [0, 15],
            [5, 0],
            [5, 10],
            [5, 15],
            [10, 0],
            [10, 5],
            [10, 15],
            [15, 0],
            [15, 5],
            [15, 10],
        ]
        coupling_map += itertools.product(range(0, 5), repeat=2)
        coupling_map += itertools.product(range(5, 10), repeat=2)
        coupling_map += itertools.product(range(10, 15), repeat=2)
        coupling_map += itertools.product(range(15, 20), repeat=2)

        coupling_map = [[q1, q2] for q1, q2 in coupling_map if q1 != q2]

        super().__init__(
            name="fake_hatlab",
            n_qubits=20,
            coupling_map=coupling_map,
            basis_gates=["id", "rx", "ry", "cz", "swap"],
            single_qubit_gates=["id", "rx", "ry"],
        )

    def _build_props(self) -> BackendProperties:
        """Build properties for backend."""
        qubits = []
        gates = []

        for (qubit_t1, qubit_t2, freq, read_err) in zip(
            self.qubit_t1, self.qubit_t2, self.qubit_frequency, self.qubit_readout_error
        ):
            qubits.append(
                [
                    Nduv(date=self.now, name="T1", unit="µs", value=qubit_t1),
                    Nduv(date=self.now, name="T2", unit="µs", value=qubit_t2),
                    Nduv(date=self.now, name="frequency", unit="GHz", value=freq),
                    Nduv(date=self.now, name="readout_error", unit="", value=read_err),
                ]
            )

        for gate in self.basis_gates:
            parameters = [
                Nduv(date=self.now, name="gate_error", unit="", value=0.01),
                Nduv(date=self.now, name="gate_length", unit="ns", value=4 * self.dt),
            ]

            if gate in self.single_qubit_gates:
                for i in range(self.n_qubits):
                    # add a restriction that router qubits cannot do 1Q Operations
                    if i in [0, 5, 10, 15]:
                        continue
                    gates.append(
                        Gate(
                            gate=gate,
                            name=f"{gate}_{i}",
                            qubits=[i],
                            parameters=parameters,
                        )
                    )
            elif gate == "swap" or gate == "cz":
                # for (qubit1, qubit2) in list(
                #     itertools.combinations(range(self.n_qubits), 2)
                # ):
                for (qubit1, qubit2) in self.coupling_map:

                    # add a restriction that router qubits can only do swap
                    if (
                        qubit1 in [0, 5, 10, 15]
                        or qubit2 in [0, 5, 10, 15]
                        and gate != "swap"
                    ):
                        continue

                    gates.append(
                        Gate(
                            gate=gate,
                            name=f"{gate}{qubit1}_{qubit2}",
                            qubits=[qubit1, qubit2],
                            parameters=parameters,
                        )
                    )
            else:
                raise QiskitError(
                    "{gate} is not supported by fake backend builder."
                    "".format(gate=gate)
                )

        return BackendProperties(
            backend_name=self.name,
            backend_version=self.version,
            last_update_date=self.now,
            qubits=qubits,
            gates=gates,
            general=[],
        )
