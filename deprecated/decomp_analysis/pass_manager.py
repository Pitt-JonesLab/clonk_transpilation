from qiskit.transpiler.passes import CountOpsLongestPath
import sys

sys.path.append("c:\\Users\\19bay\\qiskit_mine\\transpilation_EM")
import fakeutils
from qiskit.transpiler import PassManager
import numpy as np
from fakeutils.equivalence_library import SessionEquivalenceLibrary

_sel = SessionEquivalenceLibrary
from qiskit import transpile
from cost_analysis_pass import DurationCriticalPath
from fakeutils.basis_translator import BasisTranslator
from NuOp.parallel_two_qubit_gate_decomposition import ParallelGateReplacementPass
from itertools import product
from fakeutils.riswap import RiSwapGate
import numpy as np
from mock_backend.fake_surfaceCode import FakeSurfaceCode
from qiskit.transpiler.passes import (
    BasicSwap,
    Optimize1qGates,
    Optimize1qGatesDecomposition,
)
from fakeutils.nonglobal_trivial_layout import NonGlobalTrivialLayout
from fakeutils.weyl_decompose import RootiSwapWeylDecomposition
from fakeutils.nonglobal_swap import NonGlobalSwapPass
from fakeutils.elim_small_ import ElimSmallRZ
from qiskit.circuit.library import CXGate

# Build pass manager
def level_0_pass_manager(
    backend,
    decomp_method="weyl",
    decompose_swaps=False,
    critical_path_only=False,
    decompose_1q=True,
) -> PassManager:
    pm0 = PassManager()

    # FIXME
    # FIXME: Consolidate Blocks does not work for non super controlled gates - fix using alibaba code
    from qiskit.transpiler.passes import ConsolidateBlocks, Collect2qBlocks

    if decomp_method == "weyl":
        pm0.append(Collect2qBlocks())
        pm0.append(
            ConsolidateBlocks(kak_basis_gate=RiSwapGate(0.5), force_consolidate=True)
        )
    else:
        pm0.append(Collect2qBlocks())
        pm0.append(ConsolidateBlocks(kak_basis_gate=CXGate(), force_consolidate=True))

    # TODO: add basic analysis pass to determine initial layout for nonglobal ops
    initial_layout = NonGlobalTrivialLayout(backend_target=backend.target)
    pm0.append(initial_layout)

    # Basic Swaps adds in SWAP gates for 2Q gates that don't exist in coupling graph
    # TODO: insert swaps for nonglobal ops, check 2Q gate specifically instead of generic coupling graph
    # TODO: these ancilla passes should be combined into the nonglobaltrivial layout pass
    from qiskit.transpiler.passes import FullAncillaAllocation
    from qiskit.transpiler.passes import EnlargeWithAncilla
    from qiskit.transpiler.passes import ApplyLayout

    _embed = [
        FullAncillaAllocation(backend.coupling_map),
        EnlargeWithAncilla(),
        ApplyLayout(),
    ]
    # swap_route = BasicSwap(backend.coupling_map)
    # swap_route = NonGlobalSwapPass(backend, decompose_1q=decompose_1q)
    # pm0.append(_embed)
    # pm0.append(swap_route)

    # if decompose_swaps:
    #     swap_route = NonGlobalSwapPass(backend, decompose_1q=decompose_1q)
    #     pm0.append(_embed)
    #     pm0.append(swap_route)

    # Decompose 2Q gates into Riswap basis using either 'weyl' or 'nuop' method, otherwise 'cx'
    if decomp_method == "weyl":
        swap_change = RootiSwapWeylDecomposition(decompose_swaps=False)
        pm0.append(swap_change)
    elif decomp_method == "nuop":
        # TODO: free RiSwapGate parameter
        fid_2q = dict.fromkeys(
            [(i, j) for i, j in product(range(backend.num_qubits), repeat=2) if i != j],
            [1],
        )
        swap_change = ParallelGateReplacementPass(
            [RiSwapGate],
            [[1 / 2]],
            fid_2q,
            [1 for _ in range(54)],
            tol=0.0000001,
            decompose_swaps=False,
        )
        pm0.append(swap_change)
    else:
        # reuse this code now for cx because this is just applying the decomposition rule
        pm0.append(RootiSwapWeylDecomposition(decompose_swaps=False, cx_basis=True))
        # if decompose_swaps:
        #     swap_change = BasisTranslator(_sel, backend.operation_names)
        # else:
        #     swap_change = BasisTranslator(_sel, backend.operation_names + ["swap"])

    # Group together left over 1Q gates into virtual-z basis
    include_basis = []
    # need to include swaps in basis opts, because second weyl will do this
    # include_basis.append("swap")
    if not decompose_1q:
        include_basis.append("u3")

    temp = BasisTranslator(_sel, backend.operation_names + include_basis)
    pm0.append(temp)

    # temp2 = ElimSmallRZ()
    # pm0.append(temp2)

    if not decompose_swaps:
        swap_route = NonGlobalSwapPass(backend, decompose_1q=decompose_1q)
        pm0.append(_embed)
        pm0.append(swap_route)

    oneqopt1 = Optimize1qGates(basis=backend.single_qubit_gates + include_basis)
    pm0.append(oneqopt1)

    oneqopt2 = Optimize1qGatesDecomposition(
        basis=backend.single_qubit_gates + include_basis
    )
    pm0.append(oneqopt2)

    # decompose introduced movement swaps
    if decompose_swaps:
        pass
        # # FIXME
        # if decomp_method == "weyl":
        #     swap_change = RootiSwapWeylDecomposition(decompose_swaps=True)
        #     pm0.append(swap_change)
        # # FIXME rerun all the 1q optimizations, but include basis doesn't have swap now
        # include_basis.remove("swap")
        # temp = BasisTranslator(_sel, backend.operation_names + include_basis)
        # pm0.append([temp, oneqopt1, oneqopt2])

    # timing analysis pass
    if decompose_swaps and decompose_1q:
        cp = DurationCriticalPath(
            backend=backend, critical_path_only=critical_path_only
        )
        pm0.append(cp)
    # else:
    #     pm0.property_set["duration_longest_path_length"] = "Unable to compute as undecomposed SWAP has no duration"

    return pm0
