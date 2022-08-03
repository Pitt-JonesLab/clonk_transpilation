"""Define circuits to test"""
from supermarq.benchmarks import *
from supermarq.features import cirq_to_qiskit


class CircuitTranspilerBenchmark:
    # TODO: circuit_lambda could take multiple params if desired
    def __init__(self, circuit_lambda, q_range, label):
        self.circuit_lambda = circuit_lambda
        self.q_range = q_range
        self.label = label


# FIXME should this be a class, q_range is a parameter, instead of dict use get methods
circuits = {}
q_range = [8, 16, 24, 32, 40, 48, 56, 64, 72, 80]
# q_range = [
#     4,
#     6,
#     8,
#     10,
#     12,
#     14,
#     16,
# ]  # XXX danger bad coding practice, if I run these on these on wrong set of benchmarks
depth = 10

# Random
# from qiskit.circuit.random import random_circuit

# random_lambda = lambda q: random_circuit(q, depth, measure=False, max_operands=2)
# label = "Randomized_QC"
# circuits[label] = CircuitTranspilerBenchmark(random_lambda, q_range, label=label)

# # Quantum Volume
from qiskit.circuit.library import QuantumVolume

qv_lambda = lambda q: QuantumVolume(num_qubits=q, depth=q)
label = "Quantum_Volume"
circuits[label] = CircuitTranspilerBenchmark(qv_lambda, q_range, label=label)

# QFT
from qiskit.circuit.library.basis_change import QFT

qft_lambda = lambda q: QFT(q)
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
qaoa_vanilla_lambda = lambda q: cirq_to_qiskit(QAOAVanillaProxy(q).circuit())
label = "QAOA_Vanilla"
circuits[label] = CircuitTranspilerBenchmark(qaoa_vanilla_lambda, q_range, label=label)

# VQE - very slow to generate
# vqe_lambda = lambda q: cirq_to_qiskit(VQEProxy(q, 4).circuit()[0])
# label = "VQE"
# circuits[label] = CircuitTranspilerBenchmark(vqe_lambda, q_range, label=label)

# Simulation
hamiltonian_lambda = lambda q: cirq_to_qiskit(
    HamiltonianSimulation(q, 1 / depth, 0.5).circuit()
)
label = "TIM_Hamiltonian"
circuits[label] = CircuitTranspilerBenchmark(hamiltonian_lambda, q_range, label=label)


# weighted adder or ripple carry adder
from qiskit.circuit.library.arithmetic.adders.cdkm_ripple_carry_adder import (
    CDKMRippleCarryAdder,
)
from qiskit import QuantumCircuit

# using trick of composing into an empty circuit so that it builds everything into a single quantumregister
adder_lambda = (
    lambda q: QuantumCircuit(q)
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
ghz_lambda = lambda q: cirq_to_qiskit(GHZ(q).circuit())
label = "GHZ"
circuits[label] = CircuitTranspilerBenchmark(ghz_lambda, q_range, label=label)
