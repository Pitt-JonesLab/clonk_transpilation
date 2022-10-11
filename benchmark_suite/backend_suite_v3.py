"""Define backends to test"""
import sys

sys.path.append("..")
import json
import os
from pathlib import Path
from backend_utils.mock_backends.fake_allToAll import FakeAllToAll

from backend_utils.mock_backends.fake_hexLattice import FakeHexLattice
from backend_utils import *
from utils.transpiler_passes import level_1_pass_manager


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
            # file exists but is empty
            self.data = {}
        except FileNotFoundError:
            self.create_data(n=0)

    def create_data(self, n):
        # if doesn't exist create a blank dictionary'
        fp = Path(self.filename)
        fp.touch(exist_ok=True)
        self.data = {}

    def save_data(self, parameter, data, circuit_label=None, circuit_parameter=None):
        # parameters in ["diameter", "avg_dist", "degree"]
        if circuit_label is None:
            self.data[str(0)][parameter] = data
        else:
            # parameters in ["circuit/duration", "circuit/gate_count", "circuit/layout_score"]
            # convert final parameter to string so doesn't cause conflicts from loaded jsons
            self.data[str(0)][circuit_label][circuit_parameter][str(parameter)] = data

    def save_json(self):
        with open(self.filename, "w") as fp:
            json.dump(self.data, fp, indent=2)


fake_heavy_hex = FakeHeavyHex(twoqubitgate="cx", enforce_max_84=True)
fake_hex_lattice = FakeHexLattice(twoqubitgate="cx", enforce_max_84=True)
fake_surfaceCode = FakeSurfaceCode(twoqubitgate="syc", qubit_size=84, row_length=7)
fake_penguin = PenguinVIdeal(twoqubitgate="cx")
fake_tree = FakeHatlab(
    num_qubits=84, router_as_qubits=True, twoqubitgate="riswap", round_robin=0
)
fake_tree_rr = FakeHatlab(
    num_qubits=84, router_as_qubits=True, twoqubitgate="riswap", round_robin=3
)
fake_hypercube = FakeHyperCubeV2(
    n_dimension=7, twoqubitgate="riswap", enforce_max_84=True
)

###
fake_small_heavy_hex = FakeHeavyHex(twoqubitgate="cx", enforce_max_84=False, small=True)
fake_small_hex_lattice = FakeHexLattice(
    twoqubitgate="cx", enforce_max_84=False, small=True
)
fake_small_surfaceCode = FakeSurfaceCode(
    twoqubitgate="syc", qubit_size=16, row_length=4
)
fake_small_penguin = PenguinVIdeal(twoqubitgate="cx", small=True)
fake_small_tree = FakeHatlab(
    num_qubits=20, router_as_qubits=True, twoqubitgate="riswap", round_robin=0
)
fake_small_tree_rr = FakeHatlab(
    num_qubits=20, router_as_qubits=True, twoqubitgate="riswap", round_robin=3
)
fake_corralv1 = FakeHyperCubeSnail(corral_skip_pattern=(0, 0), twoqubitgate="riswap")
fake_corralv2 = FakeHyperCubeSnail(corral_skip_pattern=(0, 1), twoqubitgate="riswap")
fake_corralv3 = FakeHyperCubeSnail(corral_skip_pattern=(0, 2), twoqubitgate="riswap")
fake_corralv4 = FakeHyperCubeSnail(corral_skip_pattern=(1, 2), twoqubitgate="riswap")
fake_small_hypercube = FakeHyperCubeV2(
    n_dimension=4, twoqubitgate="riswap", enforce_max_84=False
)
###

_small_results_part3 = [
    fake_small_heavy_hex,
    fake_small_surfaceCode,
    fake_small_tree,
    fake_corralv1,
]


simple_backends_v3 = []
basis_gates = ["cx", "syc", "riswap", "riswap"]
for backend, basis_gate in zip(_small_results_part3, basis_gates):
    pm = level_1_pass_manager(backend, basis_gate=basis_gate, decompose_swaps=True)
    label = backend.name + "-smallv3"
    simple_backends_v3.append(BackendTranspilerBenchmark(backend, pm, label))
