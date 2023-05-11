"""Define backends to test."""
import sys

sys.path.append("..")
import json
from pathlib import Path

from src.clonk.backend_utils import *
from src.clonk.backend_utils.mock_backends.Corral_backend_v1 import FakeCorral

from src.clonk.utils.transpiler_passes.pass_manager_v3 import level_1_pass_manager


class BackendTranspilerBenchmark:
    def __init__(self, backend, pm, label):
        self.backend = backend
        self.pass_manager = pm
        self.label = label
        self.filename = f"src/clonk/benchmark_suite/data/{self.label}.json"
        self.load_data()
        if "small" in self.label:
            self.q_range = [4, 6, 8, 10, 12, 14, 16]
        else:
            self.q_range = [8, 16, 24, 32, 40, 48, 56, 64, 72, 80]

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

###

fake_corralv1 = FakeCorral(n=16,k=16, twoqubitgate="riswap")
fake_corralv2 = FakeCorral(n=64,k=64, twoqubitgate="riswap")
fake_corralv3 = FakeCorral(n=128,k=128, twoqubitgate="riswap")
fake_corralv4 = FakeCorral(n=128,k=256, twoqubitgate="riswap")
###

_small_results_part3 = [
    fake_corralv1,
    fake_corralv2,
    fake_corralv3,
    fake_corralv4
]


simple_backends_v3 = []
basis_gates = ["cx", "syc", "riswap", "riswap"]
for backend, basis_gate in zip(_small_results_part3, basis_gates):
    pm = level_1_pass_manager(backend, basis_gate=basis_gate, decompose_swaps=True)
    label = backend.name + "-smallv3"
    simple_backends_v3.append(BackendTranspilerBenchmark(backend, pm, label))
