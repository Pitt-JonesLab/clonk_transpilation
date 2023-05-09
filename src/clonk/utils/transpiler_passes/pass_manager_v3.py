# passes
from qiskit.circuit.library import CXGate, RZXGate
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import (
    ApplyLayout,
    Collect2qBlocks,
    ConsolidateBlocks,
    EnlargeWithAncilla,
    FullAncillaAllocation,
    Layout2qDistance,
    Optimize1qGatesDecomposition,
    UnrollCustomDefinitions,
)

from src.clonk.utils.qiskit_patch.basis_translator import BasisTranslator
from src.clonk.utils.qiskit_patch.dense_layout import DenseLayout
from src.clonk.utils.qiskit_patch.resource_estimation import ResourceEstimation

# utils
from src.clonk.utils.riswap_gates.equivalence_library import (
    SessionEquivalenceLibrary as _sel,
)
from src.clonk.utils.riswap_gates.riswap import RiSwapGate, fSim

# routing passes
from src.clonk.utils.transpiler_passes.nonglobal_swap import NonGlobalSwapPass

# placement pass
from src.clonk.utils.transpiler_passes.nonglobal_trivial_layout import (
    NonGlobalTrivialLayout,
)
from src.clonk.utils.transpiler_passes.weyl_decompose import RootiSwapWeylDecomposition

# duration analysis


def level_1_pass_manager(
    backend,
    basis_gate,
    decompose_swaps=True,
    decompose_1q=True,
    critical_path=False,
    consolidate_blocks_break_early=False,
    placement_strategy="dense",
    routing="stochastic",
) -> PassManager:
    if basis_gate == "riswap":
        basis_gate = RiSwapGate(0.5)
    elif basis_gate == "cr":
        import numpy as np

        basis_gate = RZXGate(np.pi / 2)
    elif basis_gate == "syc":
        import numpy as np

        basis_gate = fSim(np.pi / 6, np.pi / 2)
    else:
        basis_gate = CXGate()
    pm0 = PassManager()
    """Stage 1.

    blocking
    """
    additional_basis = []
    if not decompose_1q:
        additional_basis.append("u3")

    # Unroll custom definitions
    pm0.append(
        UnrollCustomDefinitions(_sel, backend.operation_names + additional_basis)
    )

    # analysis pass for converting into SU(4)
    pm0.append(Collect2qBlocks())

    # transformation pass to move to SU(4), use CXGate here because gets overrided later
    pm0.append(ConsolidateBlocks(kak_basis_gate=CXGate(), force_consolidate=True))
    """Stage 2.

    Routing
    """
    # placement
    if placement_strategy == "dense":
        pm0.append(DenseLayout(backend))
    else:
        pm0.append(
            NonGlobalTrivialLayout(
                backend_target=backend.target, strategy=placement_strategy
            )
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
    if routing == "basic":
        pm0.append(NonGlobalSwapPass(backend, decompose_1q=decompose_1q))

    elif routing == "lookahead":
        # better swap? --very slow
        from qiskit.transpiler.passes.routing import LookaheadSwap

        pm0.append(LookaheadSwap(backend.coupling_map))

    elif routing == "stochastic":
        from qiskit.transpiler.passes.routing import StochasticSwap

        pm0.append(StochasticSwap(backend.coupling_map))

    # pre-swap-decompose resource estimation
    # use preswap flag so we can distinguish data in propertyset
    pm0.append(ResourceEstimation(preswap=True))
    """Stage 3.

    Decompose 2Q gates
    """
    # applies two qubit basis decomposition rule
    # TODO: rename, restructure, non-supercontroled
    pm0.append(RootiSwapWeylDecomposition(basis_gate=basis_gate))

    # Write 1Q ops in backend basis
    pm0.append(BasisTranslator(_sel, backend.operation_names + additional_basis))

    # Optimize 1Qs
    pm0.append(
        Optimize1qGatesDecomposition(
            basis=backend.single_qubit_gates + additional_basis
        )
    )

    # final resource estimation
    pm0.append(ResourceEstimation(preswap=False))

    return pm0
