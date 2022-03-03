"""Define backends to test"""
import sys
import json
import os
from pathlib import Path

sys.path.append("..")
from backend_utils import *
from utils.transpiler_passes import level_0_pass_manager


class BackendTranspilerBenchmark:
    def __init__(self, backend, pm, label):
        self.backend = backend
        self.pass_manager = pm
        self.label = label
        self.filename = os.getcwd() + f"/data/{self.label}.json"
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
            self.data[circuit_label][circuit_parameter][parameter] = data

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

"""Large Backends"""
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

# Large Hatlab - Breaks early for DAG
backend_hatlab = FakeHatlab(dimension=2, router_as_qubits=True)
pm_hatlab = level_0_pass_manager(
    backend_hatlab,
    basis_gate="riswap",
    shuffle=True,
)
label = "Hatlab-Large-Riswap-Shuffle"
backends[label] = BackendTranspilerBenchmark(backend_hatlab, pm_hatlab, label)

backend_hatlab = FakeHatlab(dimension=2, router_as_qubits=True)
pm_hatlab = level_0_pass_manager(
    backend_hatlab,
    basis_gate="riswap",
    shuffle=False,
)
label = "Hatlab-Large-Riswap-NonShuffle"
backends[label] = BackendTranspilerBenchmark(backend_hatlab, pm_hatlab, label)

large_backends = [backend[1] for backend in backends.items() if "Large" in backend[0]]

shuffle_test = [
    backends["Hatlab-Large-Riswap-NonShuffle"],
    backends["Hatlab-Large-Riswap-Shuffle"],
]
