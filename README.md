# CLONK-CoupLing tOpology beNchmarKs
## 1. Set up list of coupling maps
### Begin by building a mock backend using the `ConfigurableFakeBackendV2` abstract class.
```python
class FakeExampleV2(ConfigurableFakeBackendV2):
    """A mock backendv2"""

    def __init__(self):
        qubits = list(range(4))
        coupling_map = [[0, 1], [0, 2], [0, 3], [1, 2]]
        qubit_coordinates = [[0, 1], [1, 0], [1, 1], [1, 2]]

        gate_configuration = {}
        gate_configuration[IGate] = [(i,) for i in qubits]

        # only can do RXGates on qubits 0 and 4
        gate_configuration[RXGate] = [
            (i,) for i in list(set(qubits).difference([1, 2]))
        ]
        # can do RY on all qubits
        gate_configuration[RYGate] = [(i,) for i in qubits]

        # can do CZ on all pairs in coupling map
        gate_configuration[CZGate] = [(i, j) for i, j in coupling_map]

        # can only measure qubits 2,3
        measurable_qubits = [2, 3]

        super().__init__(
            name="mock_example",
            description="a mock backend",
            n_qubits=len(qubits),
            gate_configuration=gate_configuration,
            parameterized_gates={RXGate: ["theta"], RYGate: ["theta"]},
            measurable_qubits=measurable_qubits,
            qubit_coordinates=qubit_coordinates,
            gate_durations={
                IGate: 0,
                RXGate: 0,
                RYGate: 0,
                CZGate: 2.167,
            },
            single_qubit_gates=["rx", "ry"],
        )
```
### Create a visual representation of your coupling graph using `topology_visualization.ipynb`
```python
from mock_backends.fake_example import FakeExampleV2
pb = FakeExampleV2()
pretty_print(pb)
```
![image](https://user-images.githubusercontent.com/47376937/161135435-8070aa2a-837b-4d3f-964f-7c6a938cc7b5.png)

### Wrap the mock backend in a 'BackendTranspilerBenchmark' object which handles json loading and saving.
```python
backend_list = []
backend = FakeExampleV2()
pass_manager = level_0_pass_manager(backend, basis_gate="riswap")
backend_list.append(BackendTranspilerBenchmark(backend = backend, pm = pass_manager))
```

## 2. Set up list of circuits to test on
### Take a quantum circuit definition and wrap it in a lambda function so it is parameterized by number of qubits
```python
circuit_list = []
qv_lambda = lambda q: QuantumVolume(num_qubits=q, depth=4)
label = "Quantum_Volume"
circuits[label] = CircuitTranspilerBenchmark(qv_lambda, q_range, label=label)
```

## 3. Pass backend and circuit list to benchmarker
```python
circuit_gen = circuit_list["Quantum_Volume"]
benchmark(backends=backend_list, circuit_generator=circuit_gen, continuously_save=True, overwrite=False)
plot(industry_backends, circuit_gen.label, duration=2)
```
![image](https://user-images.githubusercontent.com/47376937/162125693-8c0017aa-4708-41ff-8ce8-c2520885cd21.png)


### Edge Histogram - WIP
```python
edge_histogram(backend_list, circuit_gen.label)
```
![output](https://user-images.githubusercontent.com/47376937/161140891-175d55a9-6573-4753-a26e-4ea3cca326a8.png)
