import sys

sys.path.append("..")

# passes
from qiskit.transpiler import PassManager

from qiskit.transpiler.passes import (
    ConsolidateBlocks,
    Collect2qBlocks,
    Optimize1qGatesDecomposition,
    UnrollCustomDefinitions,
)
from fakeutils.basis_translator import BasisTranslator
from fakeutils.weyl_decompose import RootiSwapWeylDecomposition

# placement pass
from fakeutils.nonglobal_trivial_layout import NonGlobalTrivialLayout
from qiskit.transpiler.passes import SabreLayout

# routing passes
from fakeutils.nonglobal_swap import NonGlobalSwapPass
from qiskit.transpiler.passes import (
    FullAncillaAllocation,
    EnlargeWithAncilla,
    ApplyLayout,
)

# duration analysis
from decomp_analysis.cost_analysis_pass import DurationCriticalPath

# utils
from fakeutils.equivalence_library import StandardEquivalenceLibrary as _sel
from fakeutils.riswap import RiSwapGate
from qiskit.circuit.library import CXGate


def level_0_pass_manager(
    backend,
    basis_gate,
    decompose_swaps=True,
    decompose_1q=True,
) -> PassManager:

    if basis_gate == "riswap":
        basis_gate = RiSwapGate(0.5)
    else:
        basis_gate = CXGate()
    pm0 = PassManager()

    foo = False
    while 1:
        """Stage 1. Decomposition"""
        additional_basis = []
        if not decompose_1q:
            additional_basis.append("u3")

        # Unroll custom definitions
        pm0.append(
            UnrollCustomDefinitions(_sel, backend.operation_names + additional_basis)
        )

        # analysis pass for converting into SU(4)
        pm0.append(Collect2qBlocks())

        # transformation pass to move to SU(4)
        pm0.append(ConsolidateBlocks(kak_basis_gate=basis_gate, force_consolidate=True))

        # applies two qubit basis decomposition rule
        # TODO: rename, restructure, non-supercontroled
        pm0.append(RootiSwapWeylDecomposition(basis_gate=basis_gate))

        # TODO: insert nuop option

        # Write 1Q ops in backend basis
        pm0.append(BasisTranslator(_sel, backend.operation_names + additional_basis))

        # Optimize 1Qs
        pm0.append(
            Optimize1qGatesDecomposition(
                basis=backend.single_qubit_gates + additional_basis
            )
        )

        if foo:
            break

        """Stage 2. Routing"""
        # placement
        pm0.append(NonGlobalTrivialLayout(backend_target=backend.target))

        # better layout -- very slow
        # pm0.append(
        #     SabreLayout(
        #         coupling_map=backend.coupling_map,
        #         routing_pass=NonGlobalSwapPass(backend),
        #     )
        # )

        # analysis prep
        _embed = [
            FullAncillaAllocation(backend.coupling_map),
            EnlargeWithAncilla(),
            ApplyLayout(),
        ]
        pm0.append(_embed)

        # insert swaps
        pm0.append(NonGlobalSwapPass(backend, decompose_1q=decompose_1q))

        # better swap --very slow
        # from qiskit.transpiler.passes.routing import LookaheadSwap
        # pm0.append(LookaheadSwap(backend.coupling_map))

        """Stage 3. Decompose Movement Swaps"""
        # TODO: empty target movement?

        foo = True
        if not decompose_swaps:
            break

    # timing analysis
    if decompose_swaps and decompose_1q:
        pm0.append(DurationCriticalPath(backend, False))

    return pm0
