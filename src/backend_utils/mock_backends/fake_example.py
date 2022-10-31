import itertools
from src.backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Nduv, Gate
from qiskit.exceptions import QiskitError
from qiskit.circuit.library.standard_gates import *


class FakeExampleV2(ConfigurableFakeBackendV2):
    """A mock backendv2"""

    def __init__(self):
        qubits = list(range(4))
        coupling_map = [[0, 1], [0, 2], [0, 3], [1, 2]]
        qubit_coordinates = [[0, 1], [1, 0], [1, 1], [1, 2]]

        gate_configuration = {}
        gate_configuration[IGate] = [(i,) for i in qubits]

        # only can do RXGates on qubits 0 and 4
        gate_configuration[RXGate] = [
            (i,) for i in list(set(qubits).difference([1, 2]))
        ]
        # can do RY on all qubits
        gate_configuration[RYGate] = [(i,) for i in qubits]

        # can do CZ on all pairs in coupling map
        gate_configuration[CZGate] = [(i, j) for i, j in coupling_map]

        # can only measure qubits 2,3
        measurable_qubits = [2, 3]

        super().__init__(
            name="mock_example",
            description="a mock backend",
            n_qubits=len(qubits),
            gate_configuration=gate_configuration,
            parameterized_gates={RXGate: ["theta"], RYGate: ["theta"]},
            measurable_qubits=measurable_qubits,
            qubit_coordinates=qubit_coordinates,
            gate_durations={
                IGate: 0,
                RXGate: 0,
                RYGate: 0,
                CZGate: 2.167,
            },
            single_qubit_gates=["rx", "ry"],
        )
