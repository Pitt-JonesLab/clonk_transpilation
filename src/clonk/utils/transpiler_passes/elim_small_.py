import numpy as np
from qiskit.transpiler.basepasses import TransformationPass


# FIXME
class ElimSmallRZ(TransformationPass):
    def __init__(self):
        super().__init__()

    def run(self, dag):
        for node in dag.gate_nodes():
            if node.name == "rz":
                if np.isclose(float(node.op.params[0]), 0, atol=1e-6):
                    dag.remove_op_node(node)
        return dag
