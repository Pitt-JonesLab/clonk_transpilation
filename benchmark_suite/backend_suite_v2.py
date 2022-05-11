"""Define backends to test"""
import sys

sys.path.append("..")
import json
import os
from pathlib import Path
from backend_utils.mock_backends.fake_allToAll import FakeAllToAll

from backend_utils.mock_backends.fake_hexLattice import FakeHexLattice
from backend_utils import *
from utils.transpiler_passes import level_0_pass_manager, pass_manager_v2


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


# # FIXME wrap in class with some parameters like break early, shuffle, etc
# backends = {}

# # 2Q gate doesn't matter, we are only going to count swap gates, make them all have CX
# _topology = [
#     FakeHeavyHex(twoqubitgate="cx"),
#     FakeSurfaceCode(twoqubitgate="cx", qubit_size=84, row_length=7),
#     FakeHexLattice(twoqubitgate="cx"),
#     PenguinVIdeal(twoqubitgate="cx"),
#     FakeHatlab(num_qubits=84, router_as_qubits=True, twoqubitgate="cx"),
#     FakeHatlab(
#         num_qubits=84, router_as_qubits=True, twoqubitgate="cx", round_robin=True
#     ),
#     FakeHyperCubeV2(n_dimension=7, twoqubitgate="cx"),
# ]
# # FakeAllToAll(twoqubitgate="cx"),]

# topology_backends = []
# for backend in _topology:
#     # don't decompose swaps
#     pm = level_0_pass_manager(backend, basis_gate="cx", decompose_swaps=False)
#     label = backend.name[:-3]  # remove '-cx' from name
#     topology_backends.append(BackendTranspilerBenchmark(backend, pm, label))

# ##################

# decomp_backends = []
# basis_gates = ["cx", "cr", "riswap", "cx", "cr", "riswap"]
# labels = ["fSim", "RZX"]
# _decomposition = [
#     FakeAllToAll(twoqubitgate="cx"),
#     FakeAllToAll(twoqubitgate="cr"),
#     # FakeAllToAll(twoqubitgate="riswap"),
#     # FakeSurfaceCode(twoqubitgate="cx", qubit_size=84, row_length=7),
#     # FakeSurfaceCode(twoqubitgate="cr", qubit_size=84, row_length=7),
#     # FakeSurfaceCode(twoqubitgate="riswap", qubit_size=84, row_length=7),
# ]
# for backend, gate, label in zip(_decomposition, basis_gates, labels):
#     pm = level_0_pass_manager(
#         backend,
#         basis_gate=gate,
#         decompose_swaps=True,
#     )
#     label = label
#     decomp_backends.append(BackendTranspilerBenchmark(backend, pm, label))


# ###############
# modular_backends = []
# _hatlab = [
#     FakeHatlab(num_qubits=84, router_as_qubits=True, twoqubitgate="cx", round_robin=0),
#     FakeHatlab(num_qubits=84, router_as_qubits=True, twoqubitgate="cx", round_robin=1),
#     FakeHatlab(num_qubits=84, router_as_qubits=True, twoqubitgate="cx", round_robin=2),
#     FakeHatlab(num_qubits=84, router_as_qubits=True, twoqubitgate="cx", round_robin=3),
#     FakeHyperCubeV2(n_dimension=7, twoqubitgate="cx"),
# ]
# for backend in _hatlab:
#     pm = level_0_pass_manager(backend, basis_gate="cx", decompose_swaps=False)
#     label = backend.name[:-3]
#     modular_backends.append(BackendTranspilerBenchmark(backend, pm, label))

# ##################


# ###############
# small_modular_backends = []
# _hatlab = [
#     # FakeHeavyHex(twoqubitgate="cx"),
#     # FakeHexLattice(twoqubitgate="cx"),
#     FakeSurfaceCode(twoqubitgate="cx", qubit_size=16, row_length=4),
#     # PenguinVIdeal(twoqubitgate="cx"),  #
#     FakeHyperCubeV2(n_dimension=4, twoqubitgate="cx"),
#     #
#     FakeHatlab(
#         num_qubits=20, router_as_qubits=True, twoqubitgate="riswap", round_robin=0
#     ),
#     # FakeHatlab(
#     #     num_qubits=84, router_as_qubits=True, twoqubitgate="riswap", round_robin=1
#     # ),
#     # FakeHatlab(
#     #     num_qubits=84, router_as_qubits=True, twoqubitgate="riswap", round_robin=2
#     # ),
#     FakeHatlab(
#         num_qubits=20, router_as_qubits=True, twoqubitgate="riswap", round_robin=3
#     ),
#     FakeHyperCubeSnail(corral_skip_pattern=(0, 0), twoqubitgate="riswap"),
#     FakeHyperCubeSnail(corral_skip_pattern=(0, 1), twoqubitgate="riswap"),
#     FakeHyperCubeSnail(corral_skip_pattern=(0, 2), twoqubitgate="riswap"),
# ]
# for backend in _hatlab:
#     pm = level_0_pass_manager(backend, basis_gate="cx", decompose_swaps=False)
#     label = "small" + backend.name
#     small_modular_backends.append(BackendTranspilerBenchmark(backend, pm, label))

# ##################
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
_small_motivation = [
    fake_small_heavy_hex,
    fake_small_hex_lattice,
    fake_small_surfaceCode,
    fake_small_penguin,
    fake_small_hypercube,
]
_motivation = [
    fake_heavy_hex,
    fake_hex_lattice,
    fake_surfaceCode,
    fake_penguin,
    fake_hypercube,
]
_results = [fake_heavy_hex, fake_surfaceCode, fake_tree, fake_tree_rr, fake_hypercube]
_small_results = [
    fake_small_surfaceCode,
    fake_small_hypercube,
    fake_small_tree,
    fake_small_tree_rr,
    fake_corralv1,
    fake_corralv2,
    fake_corralv3,
    fake_corralv4,
]
_small_results_part2 = [
    fake_small_heavy_hex,
    fake_small_surfaceCode,
    fake_small_tree,
    fake_small_tree_rr,
    fake_small_hypercube,
    fake_corralv1
]
# results, decompose swaps first, so it doesn't need to generate data twice
# for small, need to adjust labels so differs in save data


results_backends = []
basis_gates = ["cx", "syc", "riswap", "riswap", "riswap"]
for backend, basis_gate in zip(_results, basis_gates):
    pm = level_0_pass_manager(backend, basis_gate=basis_gate, decompose_swaps=True)
    label = backend.name
    results_backends.append(BackendTranspilerBenchmark(backend, pm, label))

motivation_backends = []
basis_gates = ["cx", "cx", "syc", "cx", "riswap"]
for backend, basis_gate in zip(_motivation, basis_gates):
    pm = level_0_pass_manager(backend, basis_gate=basis_gate, decompose_swaps=False)
    label = backend.name
    motivation_backends.append(BackendTranspilerBenchmark(backend, pm, label))

small_motivation_backends = []
basis_gates = ["cx", "cx", "syc", "cx", "riswap"]
for backend, basis_gate in zip(_small_motivation, basis_gates):
    pm = level_0_pass_manager(backend, basis_gate=basis_gate, decompose_swaps=False)
    label = backend.name + "-small"
    small_motivation_backends.append(BackendTranspilerBenchmark(backend, pm, label))

small_results_backends = []
basis_gates = [
    "syc",
    "riswap",
    "riswap",
    "riswap",
    "riswap",
    "riswap"]
#     ,
#     "riswap",
#     "riswap",
# ]
for backend, basis_gate in zip(_small_results, basis_gates):
    pm = level_0_pass_manager(backend, basis_gate=basis_gate, decompose_swaps=False)
    label = backend.name + "-small"
    small_results_backends.append(BackendTranspilerBenchmark(backend, pm, label))

small_results_part2_backends = []
basis_gates = ["cx", "syc", "riswap", "riswap", "riswap", "riswap"]
for backend, basis_gate in zip(_small_results_part2, basis_gates):
    pm = level_0_pass_manager(backend, basis_gate=basis_gate, decompose_swaps=True)
    label = backend.name + "-small"
    small_results_part2_backends.append(BackendTranspilerBenchmark(backend, pm, label))

# ####industry comparisons
# industry_backends = []
# basis_gates = ["cx", "syc", "riswap", "riswap", "riswap"]
# labels = [
#     "IBM-CNOT",
#     "Google-SYC",
#     # "Tree-SqiSwap",
#     # "Tree-RR-SqiSwap",
#     # "Hypercube-SqiSwap",
# ]
# _decomposition = [
#     FakeHeavyHex(twoqubitgate="cx"),
#     FakeSurfaceCode(twoqubitgate="syc", qubit_size=84, row_length=7),
#     # FakeHatlab(
#     #     num_qubits=84, router_as_qubits=True, twoqubitgate="riswap", round_robin=0
#     # ),
#     # FakeHatlab(
#     #     num_qubits=84, router_as_qubits=True, twoqubitgate="riswap", round_robin=3
#     # ),
#     # FakeHyperCubeV2(n_dimension=7, twoqubitgate="riswap"),
# ]
# for backend, gate, label in zip(_decomposition, basis_gates, labels):
#     pm = level_0_pass_manager(
#         backend,
#         basis_gate=gate,
#         decompose_swaps=True,
#     )
#     label = label
#     industry_backends.append(BackendTranspilerBenchmark(backend, pm, label))


# # # Routing and Placement Test
# # transp_tests = []
# # backend = FakeHeavyHex(twoqubitgate="cx")
# # pm = level_0_pass_manager(
# #     backend,
# #     basis_gate="cx",
# #     placement_strategy="trivial",
# #     routing="basic",
# #     decompose_swaps=False,
# # )
# # transp_tests.append(BackendTranspilerBenchmark(backend, pm, label))
# # label = "Trivial+Basic"
# # pm = level_0_pass_manager(
# #     backend,
# #     basis_gate="cx",
# #     placement_strategy="trivial",
# #     routing="stochastic",
# #     decompose_swaps=False,
# # )
# # label = "Trivial+Stochastic"
# # transp_tests.append(BackendTranspilerBenchmark(backend, pm, label))
# # pm = level_0_pass_manager(
# #     backend,
# #     basis_gate="cx",
# #     placement_strategy="dense",
# #     routing="basic",
# #     decompose_swaps=False,
# # )
# # label = "Dense+Basic"
# # transp_tests.append(BackendTranspilerBenchmark(backend, pm, label))
# # pm = level_0_pass_manager(
# #     backend,
# #     basis_gate="cx",
# #     placement_strategy="dense",
# #     routing="stochastic",
# #     decompose_swaps=False,
# # )
# # label = "Dense+Stochastic"
# # transp_tests.append(BackendTranspilerBenchmark(backend, pm, label))


# # ###############
# # beta_small_modular_backends = []
# # _beta = [
# #     FakeHatlab(
# #         num_qubits=20, router_as_qubits=True, twoqubitgate="riswap", round_robin=0
# #     ),
# #     # FakeHatlab(
# #     #     num_qubits=84, router_as_qubits=True, twoqubitgate="riswap", round_robin=1
# #     # ),
# #     # FakeHatlab(
# #     #     num_qubits=84, router_as_qubits=True, twoqubitgate="riswap", round_robin=2
# #     # ),
# #     FakeHatlab(
# #         num_qubits=20, router_as_qubits=True, twoqubitgate="riswap", round_robin=3
# #     ),
# #     FakeHyperCubeV2(n_dimension=4, twoqubitgate="riswap"),
# #     FakeHyperCubeSnail(corral_skip_pattern=(0, 0), twoqubitgate="riswap"),
# #     FakeHyperCubeSnail(corral_skip_pattern=(0, 1), twoqubitgate="riswap"),
# #     # FakeHyperCubeSnail(corral_skip_pattern=(0, 2), twoqubitgate="riswap"),
# #     FakeSurfaceCode(twoqubitgate="riswap", qubit_size=16, row_length=4),
# # ]
# # for backend in _beta:
# #     pm = level_0_pass_manager(
# #         backend,
# #         basis_gate="riswap",
# #         decompose_swaps=False,
# #         placement_strategy="shuffle",
# #     )
# #     label = "beta" + backend.name
# #     beta_small_modular_backends.append(BackendTranspilerBenchmark(backend, pm, label))
# # ##################
