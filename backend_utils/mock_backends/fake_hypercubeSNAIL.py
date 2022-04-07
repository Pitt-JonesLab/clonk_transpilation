import itertools
from qiskit.test.mock.utils.configurable_backend import ConfigurableFakeBackend
from backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Nduv, Gate
from qiskit.exceptions import QiskitError
from qiskit.circuit.library.standard_gates import *
from utils.riswap_gates.riswap import RiSwapGate


class FakeHyperCubeSnail(ConfigurableFakeBackendV2):
    """A mock backendv2"""

    def __init__(self, corral_skip_pattern, twoqubitgate="cx"):
        def corral(skip_pattern):
            num_snails = 8
            num_levels = 2

            assert len(skip_pattern) == num_levels
            snail_edge_list = []
            for snail0, snail1 in zip(range(num_snails), range(1, num_snails + 1)):
                for i in range(num_levels):
                    snail_edge_list.append(
                        (snail0, (skip_pattern[i] + snail1) % num_snails)
                    )
            return snail_edge_list

        def snail_to_connectivity(snail_edge_list):
            # Convert snail edge list where nodes are snails and edges are qubits
            # To connectivity edge list where nodes are qubits and edges are coupling
            edge_list = []

            # qubits are coupled to a snail edge if they are both adjacent to a snail node
            for qubit, snail_edge in enumerate(snail_edge_list):
                for temp_qubit, temp_snail_edge in enumerate(snail_edge_list):
                    if qubit != temp_qubit and (
                        snail_edge[0] in temp_snail_edge
                        or snail_edge[1] in temp_snail_edge
                    ):
                        edge_list.append((qubit, temp_qubit))
            return edge_list

        snail_edge_list = corral(corral_skip_pattern)
        coupling_map = snail_to_connectivity(snail_edge_list)
        qubits = list(range(max([el[0] for el in coupling_map])))

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
            name=f"HypercubeSNAIL-{corral_skip_pattern}-{twoqubitgate}",
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
