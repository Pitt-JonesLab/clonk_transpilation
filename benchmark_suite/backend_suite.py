"""Define backends to test"""
import sys

sys.path.append("..")
from backend_utils import *
from utils.transpiler_passes import level_0_pass_manager


class BackendTranspilerBenchmark:
    def __init__(self, backend, pm, label):
        self.backend = backend
        self.pass_manager = pm
        self.label = label
        self.times = []


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
    backend_hatlab, basis_gate="riswap", critical_path=True, break_early=True
)
label = "Hatlab-Large-Riswap"
backends[label] = BackendTranspilerBenchmark(backend_hatlab, pm_hatlab, label)

large_backends = [backend[1] for backend in backends.items() if "Large" in backend[0]]
