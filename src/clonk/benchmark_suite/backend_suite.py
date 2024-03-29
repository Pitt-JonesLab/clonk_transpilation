"""Define backends to test."""
import json
import sys
from pathlib import Path

sys.path.append("..")
from clonk.backend_utils import *
from clonk.utils.transpiler_passes import level_0_pass_manager


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

backend_hatlab = FakeHatlab(router_as_qubits=True)
pm_hatlab = level_0_pass_manager(backend_hatlab, basis_gate="riswap")
label = "Hatlab-Riswap"
backends[label] = BackendTranspilerBenchmark(backend_hatlab, pm_hatlab, label)

backend_lattice = FakeSurfaceCode(twoqubitgate="riswap")
pm_lattice = level_0_pass_manager(backend_lattice, basis_gate="riswap")
label = "Lattice-Riswap"
backends[label] = BackendTranspilerBenchmark(backend_lattice, pm_lattice, label)

backend_lattice = FakeSurfaceCode(twoqubitgate="cx")
pm_lattice = level_0_pass_manager(backend_lattice, basis_gate="cx")
label = "Lattice-CX"
backends[label] = BackendTranspilerBenchmark(backend_lattice, pm_lattice, label)
"""Large Backends."""
# Large Lattice
backend_lattice = FakeSurfaceCode(twoqubitgate="cx", qubit_size=81, row_length=9)
pm_lattice = level_0_pass_manager(backend_lattice, basis_gate="cx")
label = "Lattice-Large-CX"
backends[label] = BackendTranspilerBenchmark(backend_lattice, pm_lattice, label)

backend_lattice = FakeSurfaceCode(twoqubitgate="riswap", qubit_size=81, row_length=9)
pm_lattice = level_0_pass_manager(backend_lattice, basis_gate="riswap")
label = "Lattice-Large-Riswap"
backends[label] = BackendTranspilerBenchmark(backend_lattice, pm_lattice, label)

# Large Hypercubes
backend_hypercube = FakeHyperCubeV2(7, twoqubitgate="cx")
pm_hypercube = level_0_pass_manager(backend_hypercube, basis_gate="cx")
label = "Hypercube-Large-CX"
backends[label] = BackendTranspilerBenchmark(backend_hypercube, pm_hypercube, label)

backend_hypercube = FakeHyperCubeV2(7, twoqubitgate="riswap")
pm_hypercube = level_0_pass_manager(backend_hypercube, basis_gate="riswap")
label = "Hypercube-Large-Riswap"
backends[label] = BackendTranspilerBenchmark(backend_hypercube, pm_hypercube, label)

# Large Hatlab
backend_hatlab = FakeHatlab(dimension=2, router_as_qubits=True)
pm_hatlab = level_0_pass_manager(
    backend_hatlab,
    basis_gate="riswap",
    placement_strategy="shuffle",
    consolidate_blocks_break_early=True,
)
label = "Hatlab-Large-Riswap-Shuffle"
backends[label] = BackendTranspilerBenchmark(backend_hatlab, pm_hatlab, label)

# Large Hatlab Nonshuffle
backend_hatlab = FakeHatlab(dimension=2, router_as_qubits=True)
pm_hatlab = level_0_pass_manager(
    backend_hatlab, basis_gate="riswap", placement_strategy="trivial", routing="basic"
)
label = "Hatlab-Large-Riswap-Basic"
backends[label] = BackendTranspilerBenchmark(backend_hatlab, pm_hatlab, label)

# Large Hatlab Visualizer
backend_hatlab = FakeHatlab(dimension=2, router_as_qubits=True)
pm_hatlab = level_0_pass_manager(backend_hatlab, basis_gate="riswap")
label = "Hatlab-Large-Riswap-Upgrade"
backends[label] = BackendTranspilerBenchmark(backend_hatlab, pm_hatlab, label)


# build some groups
large_backends = [backend[1] for backend in backends.items() if "Large" in backend[0]]

# shuffle_test = [
#     backends["Hatlab-Large-Riswap-NonShuffle"],
#     backends["Hatlab-Large-Riswap-Shuffle"],
#     backends["Hatlab-Large-Riswap-Dense"],
# ]
backend_hypercube = FakeHyperCubeV2(7, twoqubitgate="riswap")
pm_hypercube = level_0_pass_manager(
    backend_hypercube, basis_gate="riswap", routing="basic"
)
label = "Hypercube-Large-Riswap-Basic"
backends[label] = BackendTranspilerBenchmark(backend_hypercube, pm_hypercube, label)

backend_hypercube = FakeHyperCubeV2(7, twoqubitgate="riswap")
pm_hypercube = level_0_pass_manager(
    backend_hypercube, basis_gate="riswap", routing="stochastic"
)
label = "Hypercube-Large-Riswap-Stochastic"
backends[label] = BackendTranspilerBenchmark(backend_hypercube, pm_hypercube, label)

# routing_test = [
#     backends["Hatlab-Large-Riswap-Basic"],
#     backends["Hatlab-Large-Riswap-Stochastic"],
#     backends["Hypercube-Large-Riswap-Basic"],
#     backends["Hypercube-Large-Riswap-Stochastic"],
# ]


# Large Hatlab
backend_hatlab = FakeHatlab(dimension=2, router_as_qubits=True)
pm_hatlab = level_0_pass_manager(
    backend_hatlab, basis_gate="riswap", placement_strategy="trivial", routing="basic"
)
label = "Hatlab-Large-Riswap-Trivial"
backends[label] = BackendTranspilerBenchmark(backend_hatlab, pm_hatlab, label)

# Large Hatlab
backend_hatlab = FakeHatlab(dimension=2, router_as_qubits=True)
pm_hatlab = level_0_pass_manager(backend_hatlab, basis_gate="riswap")
label = "Hatlab-Large-Riswap-Dense"
backends[label] = BackendTranspilerBenchmark(backend_hatlab, pm_hatlab, label)

# placement_test = [
#     backends["Hatlab-Large-Riswap-Trivial"],
#     backends["Hatlab-Large-Riswap-Dense"],
# ]

# basic_test = [
#     backends["Hatlab-Large-Riswap-Basic"],
#     backends["Hatlab-Large-Riswap-Upgrade"],
# ]

# Heavy Hex
backend_heavy_hex = FakeHeavyHex()
pm_hh = level_0_pass_manager(backend_heavy_hex, basis_gate="cx")
label = "Heavy-Hex"
backends[label] = BackendTranspilerBenchmark(backend_heavy_hex, pm_hh, label)

new_test = [backends["Hatlab-Large-Riswap-Upgrade"], backends["Heavy-Hex"]]

ibm_backends = []
ibm_backend_list = [
    PenguinV1(),
    PenguinV2(),
    PenguinV3(),
    PenguinV4(),
    FakeHeavyHex(twoqubitgate="cr"),
]  # FalconR4()]
for backend in ibm_backend_list:
    pm = level_0_pass_manager(backend, basis_gate="CR", decompose_swaps=False)
    label = backend.name
    ibm_backends.append(BackendTranspilerBenchmark(backend, pm, label))

ibm_gate_backends = []
ibm_gate_backends.append(ibm_backends[-1])
backend = FakeHeavyHex(twoqubitgate="riswap")
pm = level_0_pass_manager(backend, basis_gate="riswap", decompose_swaps=False)
label = backend.name
ibm_gate_backends.append(BackendTranspilerBenchmark(backend, pm, label))
