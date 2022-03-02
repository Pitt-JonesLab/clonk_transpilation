# passes
from qiskit.transpiler import PassManager

from qiskit.transpiler.passes import (
    ConsolidateBlocks,
    Collect2qBlocks,
    Optimize1qGatesDecomposition,
    UnrollCustomDefinitions,
    ResourceEstimation,
    Layout2qDistance,
)
from utils.qiskit_patch.basis_translator import BasisTranslator
from utils.transpiler_passes.weyl_decompose import RootiSwapWeylDecomposition

# placement pass
from utils.transpiler_passes.nonglobal_trivial_layout import NonGlobalTrivialLayout
from qiskit.transpiler.passes import SabreLayout

# routing passes
from utils.transpiler_passes.nonglobal_swap import NonGlobalSwapPass
from qiskit.transpiler.passes import (
    FullAncillaAllocation,
    EnlargeWithAncilla,
    ApplyLayout,
)

# duration analysis
from utils.transpiler_passes.cost_analysis_pass import DurationCriticalPath

# utils
from utils.riswap_gates.equivalence_library import SessionEquivalenceLibrary as _sel
from utils.riswap_gates.riswap import RiSwapGate
from qiskit.circuit.library import CXGate


def level_0_pass_manager(
    backend,
    basis_gate,
    decompose_swaps=True,
    decompose_1q=True,
    critical_path=False,
    consolidate_blocks_break_early=False,
    shuffle=False,
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

        # outputs a circuit of only 2Q SU(4) unitaries
        # is useful for visualizing minimal DAGs
        if consolidate_blocks_break_early:
            break

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

        # # resource estimation before routing
        # pm0.append(ResourceEstimation())

        # only continue to place swaps after first iteration
        if foo:
            break

        """Stage 2. Routing"""
        # placement
        pm0.append(
            NonGlobalTrivialLayout(backend_target=backend.target, shuffle=shuffle)
        )

        # better layout -- very slow
        # pm0.append(
        #     SabreLayout(
        #         coupling_map=backend.coupling_map,
        #         routing_pass=NonGlobalSwapPass(backend),
        #     )
        # )

        # evaluate how good the layout is
        pm0.append(Layout2qDistance(backend.coupling_map))

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

    # final resource estimation
    pm0.append(ResourceEstimation())

    # timing analysis
    if decompose_swaps and decompose_1q and not consolidate_blocks_break_early:
        pm0.append(DurationCriticalPath(backend, critical_path))

    # critical path estimation
    pm0.append(ResourceEstimation())

    return pm0
