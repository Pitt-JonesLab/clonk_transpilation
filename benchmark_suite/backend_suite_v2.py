"""Define backends to test"""
import sys

sys.path.append("..")
import json
import os
from pathlib import Path
from backend_utils.mock_backends.fake_allToAll import FakeAllToAll

from backend_utils.mock_backends.fake_hexLattice import FakeHexLattice
from backend_utils import *
from utils.transpiler_passes import level_0_pass_manager


class BackendTranspilerBenchmark:
    def __init__(self, backend, pm, label):
        self.backend = backend
        self.pass_manager = pm
        self.label = label
        self.filename = (
            f"/home/evm9/transpilation_EM/benchmark_suite/data/{self.label}.json"
        )
        self.load_data()

    def load_data(self):
        try:
            with open(self.filename) as fp:
                self.data = json.load(fp)

        except json.JSONDecodeError:
            self.data = {}
        except FileNotFoundError:
            # if doesn't exist create a blank dictionary
            fp = Path(self.filename)
            fp.touch(exist_ok=True)
            self.data = {}

    def save_data(self, parameter, data, circuit_label=None, circuit_parameter=None):
        # parameters in ["diameter", "avg_dist", "degree"]
        if circuit_label is None:
            self.data[parameter] = data
        else:
            # parameters in ["circuit/duration", "circuit/gate_count", "circuit/layout_score"]
            # convert final parameter to string so doesn't cause conflicts from loaded jsons
            self.data[circuit_label][circuit_parameter][str(parameter)] = data

    def save_json(self):
        with open(self.filename, "w") as fp:
            json.dump(self.data, fp, indent=2)


# FIXME wrap in class with some parameters like break early, shuffle, etc
backends = {}

# 2Q gate doesn't matter, we are only going to count swap gates, make them all have CX
_topology = [
    FakeHeavyHex(twoqubitgate="cx"),
    FakeSurfaceCode(twoqubitgate="cx", qubit_size=84, row_length=7),
    FakeHexLattice(twoqubitgate="cx"),
    PenguinVIdeal(twoqubitgate="cx"),
    FakeHatlab(num_qubits=84, router_as_qubits=True, twoqubitgate="cx"),
    FakeHatlab(
        num_qubits=84, router_as_qubits=True, twoqubitgate="cx", round_robin=True
    ),
    FakeHyperCubeV2(n_dimension=7, twoqubitgate="cx"),
]
# FakeAllToAll(twoqubitgate="cx"),]

topology_backends = []
for backend in _topology:
    # don't decompose swaps
    pm = level_0_pass_manager(backend, basis_gate="cx", decompose_swaps=False)
    label = backend.name[:-3]  # remove '-cx' from name
    topology_backends.append(BackendTranspilerBenchmark(backend, pm, label))

decomp_backends = []

dummy_backends = []
backend = FakeHatlab(
    num_qubits=84, router_as_qubits=True, twoqubitgate="cx", round_robin=True
)
pm = level_0_pass_manager(backend, basis_gate="cx", decompose_swaps=False)
label = backend.name[:-3] + "dummy"  # remove '-cx' from name
dummy_backends.append(BackendTranspilerBenchmark(backend, pm, label))

backend = FakeHatlab(
    num_qubits=84, router_as_qubits=True, twoqubitgate="cx", round_robin=False
)
pm = level_0_pass_manager(backend, basis_gate="cx", decompose_swaps=False)
label = backend.name[:-3] + "dummy"  # remove '-cx' from name
dummy_backends.append(BackendTranspilerBenchmark(backend, pm, label))

# _decomposition = [
#     FakeHeavyHex(twoqubitgate="cx"),
#     FakeSurfaceCode(twoqubitgate="cx", qubit_size=84, row_length=7),
#     FakeHatlab(num_qubits=84, router_as_qubits=True, twoqubitgate="cx"),
#     FakeAllToAll(twoqubitgate="cx"),
# ]
# for backend in _decomposition:
#     # don't decompose swaps
#     pm = level_0_pass_manager(backend, basis_gate="cx")
#     label = backend.name + "decomp"
#     decomp_backends.append(BackendTranspilerBenchmark(backend, pm, label))

# _decomposition = [
#     FakeHatlab(num_qubits=84, router_as_qubits=True, twoqubitgate="riswap"),
#     FakeSurfaceCode(twoqubitgate="riswap", qubit_size=84, row_length=7),
#     FakeAllToAll(twoqubitgate="riswap"),
# ]
# for backend in _decomposition:
#     # don't decompose swaps
#     pm = level_0_pass_manager(backend, basis_gate="riswap")
#     label = backend.name + "decomp"
#     decomp_backends.append(BackendTranspilerBenchmark(backend, pm, label))
