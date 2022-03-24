import itertools
from qiskit.test.mock.utils.configurable_backend import ConfigurableFakeBackend
from backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Nduv, Gate
from qiskit.exceptions import QiskitError
from qiskit.circuit.library.standard_gates import *
from utils.riswap_gates.riswap import RiSwapGate


class FakeHyperCubeV2(ConfigurableFakeBackendV2):
    """A mock backendv2"""

    def __init__(self, n_dimension, twoqubitgate="cx"):
        qubit_stack = list(range(2 ** n_dimension))

        def foo(n_dimension):
            if n_dimension == 1:
                return [(qubit_stack.pop(0), qubit_stack.pop(0))]

            # call previous dimension twice
            ret1 = foo(n_dimension=n_dimension - 1)
            ret2 = foo(n_dimension=n_dimension - 1)

            # connect associated edges
            coupling_map = ret1 + ret2
            coupling_map.extend([(i[0], j[0]) for i, j in zip(ret1, ret2)])
            coupling_map.extend([(i[1], j[1]) for i, j in zip(ret1, ret2)])

            return coupling_map

        qubits = list(range(2 ** n_dimension))
        coupling_map = list(set(foo(n_dimension)))
        # redundant check to make sure bidirectional
        coupling_map += [(j, i) for i, j in coupling_map]
        coupling_map = list(set(coupling_map))

        qubit_coordinates = None
        # TODO retworkx

        gate_configuration = {}
        gate_configuration[IGate] = [(i,) for i in qubits]

        # global RZ
        gate_configuration[RZGate] = [(i,) for i in qubits]
        # global X, Y, SX, SXdg
        gate_configuration[XGate] = [(i,) for i in qubits]
        gate_configuration[YGate] = [(i,) for i in qubits]
        gate_configuration[SXGate] = [(i,) for i in qubits]
        gate_configuration[SXdgGate] = [(i,) for i in qubits]

        if twoqubitgate == "cx":
            # can do CX on all pairs in coupling map
            gate_configuration[CXGate] = [(i, j) for i, j in coupling_map]
        if twoqubitgate == "riswap":
            gate_configuration[RiSwapGate] = [(i, j) for i, j in coupling_map]

        # global measure
        measurable_qubits = qubits

        super().__init__(
            name=f"Hypercube-{twoqubitgate}",
            description="a mock backend",
            n_qubits=len(qubits),
            gate_configuration=gate_configuration,
            parameterized_gates={
                RZGate: ["theta"],
                RYGate: ["theta"],
                RiSwapGate: ["alpha"],
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
            },
            single_qubit_gates=["rz", "x", "y", "sx", "sxdg"],
        )


# FakeHyperCubeV2(1)
