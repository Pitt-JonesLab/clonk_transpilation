"""Return the longest path in a DAGcircuit as a list of DAGNodes."""

from logging import critical
from qiskit.transpiler.basepasses import AnalysisPass, TransformationPass
from qiskit.transpiler.instruction_durations import InstructionDurations
import retworkx


class TimeCostAnalysis(AnalysisPass):
    """Return the longest path in a DAGcircuit as a list of DAGOpNodes, DAGInNodes, and DAGOutNodes."""

    def __init__(self, backend):
        self.backend = backend
        self.dt = backend.dt
        super().__init__()

    def run(self, dag):
        """Run the TimeCostAnalysis pass on `dag`."""
        instruction_durations = self.backend.instruction_durations

        # define weight as time cost of source node
        def weight_fn(source_node, target_node, weight):
            if dag._multi_graph[source_node].name is None:
                return 0
            # construct dict key
            gate_name = dag._multi_graph[source_node].name
            qubit_tuple = [qubit.index for qubit in dag._multi_graph[source_node].qargs]
            # get time, for iswap^alpha scale duration by alpha
            factor = 1.0
            if gate_name == "riswap" or gate_name == "rzx":
                factor = dag._multi_graph[source_node].op.params[0]
                # XXX hardcode fix bc riswap missnig factor of pi
                if gate_name == "rzx":
                    import numpy as np

                    factor = factor / np.pi
            return int(factor * instruction_durations.get(gate_name, qubit_tuple))

        longest_path = retworkx.dag_longest_path(dag._multi_graph, weight_fn=weight_fn)
        self.property_set["duration_longest_path"] = [
            dag._multi_graph[index] for index in longest_path
        ]
        self.property_set["duration_longest_path_length"] = sum(
            self.dt * weight_fn(index, None, None) for index in longest_path
        )


class DurationCriticalPath(TransformationPass):
    def __init__(self, backend, critical_path_only=True):
        super().__init__()
        self.requires = [TimeCostAnalysis(backend)]
        self.critical_path_only = critical_path_only

    def run(self, dag):
        if self.critical_path_only:
            for node in dag.op_nodes():
                if not node in self.property_set["duration_longest_path"]:
                    dag.remove_op_node(node)

        return dag


class EdgeContentionPass(AnalysisPass):
    """Creates a frequency dict for how many times an edge in coupling map is used"""

    def __init__(self, backend):
        super().__init__()
        self.backend = backend

    def run(self, dag):
        # dict for frequencies
        frequency_dict = {}
        # iteratre over 2Q gates
        for gate in dag.two_qubit_ops():
            # for consistency put gate indexes in sorted order to build a key
            i, j = sorted([gate.qargs[0].index, gate.qargs[1].index])

            key = str((i, j))
            # check if key exists and increment
            if key in frequency_dict.keys():
                frequency_dict[key] += 1
            # otherwise create key
            else:
                frequency_dict[key] = 1

        # save to property set
        self.property_set["edge_frequency"] = frequency_dict
