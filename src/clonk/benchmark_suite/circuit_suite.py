"""Define circuits to test."""
from supermarq.benchmarks.ghz import GHZ
from supermarq.benchmarks.hamiltonian_simulation import HamiltonianSimulation
from supermarq.benchmarks.qaoa_vanilla_proxy import QAOAVanillaProxy
from supermarq.converters import cirq_to_qiskit


class CircuitTranspilerBenchmark:
    # TODO: circuit_lambda could take multiple params if desired
    def __init__(self, circuit_lambda, q_range, label):
        self.circuit_lambda = circuit_lambda
        # self.q_range = q_range
        self.label = label


# FIXME should this be a class, q_range is a parameter, instead of dict use get methods
circuits = {}
depth = 10
q_range = None  # deprecated, move to backendbenchmark object

# Random
# from qiskit.circuit.random import random_circuit

# random_lambda = lambda q: random_circuit(q, depth, measure=False, max_operands=2)
# label = "Randomized_QC"
# circuits[label] = CircuitTranspilerBenchmark(random_lambda, q_range, label=label)

# # Quantum Volume
from qiskit.circuit.library import QuantumVolume


def qv_lambda(q):
    return QuantumVolume(num_qubits=q, depth=q)


label = "Quantum_Volume"
circuits[label] = CircuitTranspilerBenchmark(qv_lambda, q_range, label=label)

# QFT
from qiskit.circuit.library.basis_change import QFT


def qft_lambda(q):
    return QFT(q)


label = "QFT"
circuits[label] = CircuitTranspilerBenchmark(qft_lambda, q_range, label=label)

# # Inverse QFT
# inverse_qft_lambda = lambda q: QFT(q, inverse=True)
# label = "IQFT"
# circuits[label] = CircuitTranspilerBenchmark(inverse_qft_lambda, q_range, label=label)

# QAOA, takes a long time to generate - consider capping max size before 20
# qaoa_lambda = lambda q: cirq_to_qiskit(QAOAFermionicSwapProxy(q).circuit())
# label = "QAOA_Fermionic_Swap"
# circuits[label] = CircuitTranspilerBenchmark(qaoa_lambda, q_range, label=label)


# # QAOA vanilla
def qaoa_vanilla_lambda(q):
    return cirq_to_qiskit(QAOAVanillaProxy(q).circuit())


label = "QAOA_Vanilla"
circuits[label] = CircuitTranspilerBenchmark(qaoa_vanilla_lambda, q_range, label=label)

# VQE - very slow to generate
# vqe_lambda = lambda q: cirq_to_qiskit(VQEProxy(q, 4).circuit()[0])
# label = "VQE"
# circuits[label] = CircuitTranspilerBenchmark(vqe_lambda, q_range, label=label)


# Simulation
def hamiltonian_lambda(q):
    return cirq_to_qiskit(HamiltonianSimulation(q, 1 / depth, 0.5).circuit())


label = "TIM_Hamiltonian"
circuits[label] = CircuitTranspilerBenchmark(hamiltonian_lambda, q_range, label=label)


from qiskit import QuantumCircuit

# weighted adder or ripple carry adder
from qiskit.circuit.library.arithmetic.adders.cdkm_ripple_carry_adder import (
    CDKMRippleCarryAdder,
)


# using trick of composing into an empty circuit so that it builds everything into a single quantumregister
def adder_lambda(q):
    return (
        QuantumCircuit(q)
        .compose(CDKMRippleCarryAdder(num_state_qubits=int((q - 1) / 2)), inplace=False)
        .decompose()
        .decompose()
        .decompose()
    )


label = "Adder"
circuits[label] = CircuitTranspilerBenchmark(adder_lambda, q_range, label=label)

# multiplier
# from qiskit.circuit.library.arithmetic.multipliers import RGQFTMultiplier

# multiplier_lambda = (
#     lambda q: QuantumCircuit(q)
#     .compose(RGQFTMultiplier(num_state_qubits=int(q / 4)), inplace=False)
#     .decompose()
#     .decompose()
#     .decompose()
# )
# label = "Multiplier"
# circuits[label] = CircuitTranspilerBenchmark(multiplier_lambda, q_range, label=label)


# # GHZ
def ghz_lambda(q):
    return cirq_to_qiskit(GHZ(q).circuit())


label = "GHZ"
circuits[label] = CircuitTranspilerBenchmark(ghz_lambda, q_range, label=label)
