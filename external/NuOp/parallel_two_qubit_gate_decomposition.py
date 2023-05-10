import multiprocessing as mp
import time

import numpy as np
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.passes.optimization.optimize_1q_gates import Optimize1qGates
from scipy.optimize import minimize

optimise1qgates = Optimize1qGates()


from external.NuOp.gates_numpy import get_gate_unitary_qiskit


class GateTemplate:
    """Creates a unitary matrix using a specified two-qubit gate, number of
    layers and single-qubit rotation parameters."""

    def __init__(self, two_qubit_gate, two_qubit_gate_params):
        """
        two_qubit_gate: a function that returns the numpy matrix for the desired gate
        two_qubit_gate_params: inputs to the function e.g., for fsim gates, params has fixed theta, phi values
        """
        self.two_qubit_gate = two_qubit_gate
        self.two_qubit_gate_params = two_qubit_gate_params

    def u3_gate(self, theta, phi, lam):
        return np.matrix(
            [
                [np.cos(theta / 2), -np.exp(1j * lam) * np.sin(theta / 2)],
                [
                    np.exp(1j * phi) * np.sin(theta / 2),
                    np.exp(1j * (phi + lam)) * np.cos(theta / 2),
                ],
            ]
        )

    def multiply_all(self, matrices):
        product = np.eye(4)
        for i in range(len(matrices)):
            product = np.matmul(matrices[i], product)
        return product

    def u3_layer(self, x):
        u3_1 = self.u3_gate(*x[0:3])
        u3_2 = self.u3_gate(*x[3:6])
        t1 = np.kron(u3_1, u3_2)
        return t1

    def n_layer_unitary(self, n_layers, params):
        """
        n_layers: number of layers desired in the template
        params: list of 1Q gate rotation parameters, specified by the optimizer
        """
        gate_list = []
        idx = 0
        gate_list.append(self.u3_layer(params[idx : idx + 6]))
        idx += 6
        for i in range(n_layers):
            if len(self.two_qubit_gate_params):
                gate_list.append(self.two_qubit_gate(*self.two_qubit_gate_params))
            else:
                gate_list.append(self.two_qubit_gate())
            gate_list.append(self.u3_layer(params[idx : idx + 6]))
            idx += 6
        return self.multiply_all(gate_list)

    def get_num_params(self, n_layers):
        return 6 * (n_layers + 1)


class TwoQubitGateSynthesizer:
    """Synthesises a gate implementation for a target unitary, using a
    specified gate template."""

    def __init__(self, target_unitary, gate_template_obj):
        self.target_unitary = target_unitary
        self.gate_template_obj = gate_template_obj

    def unitary_distance_function(self, A, B):
        # return (1 - np.abs(np.sum(np.multiply(B,np.conj(np.transpose(A))))) / 4)
        # return (1 - (np.abs(np.sum(np.multiply(B,np.conj(A)))))**2+4 / 20) # quantum volume paper
        return 1 - np.abs(np.sum(np.multiply(B, np.conj(A)))) / 4

    def make_cost_function(self, n_layers):
        target_unitary = self.target_unitary

        def cost_function(x):
            A = self.gate_template_obj.n_layer_unitary(n_layers, x)
            B = target_unitary
            return self.unitary_distance_function(A, B)

        return cost_function

    def get_num_params(self, n_layers):
        return self.gate_template_obj.get_num_params(n_layers)

    def rand_initialize(self, n_layers):
        params = self.get_num_params(n_layers)
        return [np.pi * 2 * np.random.random() for i in range(params)]

    def gen_constraints(self, n_layers):
        params = self.get_num_params(n_layers)
        cons = []
        for i in range(params):
            cons.append({"type": "ineq", "fun": lambda x: -x[i] + 2 * np.pi})
        return cons

    def solve_instance(self, n_layers, trials):
        self.cost_function = self.make_cost_function(n_layers)
        constraints = self.gen_constraints(n_layers)
        results = []
        best_idx = 0
        best_val = float("inf")
        for i in range(trials):
            init = self.rand_initialize(n_layers)
            res = minimize(
                self.cost_function,
                init,
                # method="BFGS",
                constraints=constraints,
                options={"maxiter": 1000 * 30},
            )
            results.append(res)
            if best_val > res.fun:
                best_val = res.fun
                best_idx = i
        return results[best_idx]

    def optimal_decomposition(
        self,
        tol=1e-3,
        fidelity_2q_gate=1.0,
        fidelity_1q_gate=[1.0, 1.0],
        max_num_layers=8,
        force_gate_count=None,
    ):
        cutoff_with_tol = True
        results = []
        best_idx = 0
        best_fidelity = 0

        if force_gate_count is not None:
            gate_range = range(force_gate_count - 1, force_gate_count)
        else:
            gate_range = range(max_num_layers)

        for i in gate_range:
            if cutoff_with_tol and best_fidelity > 1.0 - tol:
                break

            # Solve an instance with i+1 layers, doing 1 random trial
            res = self.solve_instance(n_layers=i + 1, trials=3)
            results.append(res)

            # Evaluate the fidelity after adding one layer
            hw_fidelity = ((fidelity_1q_gate[0] * fidelity_1q_gate[1]) ** (2 + i)) * (
                fidelity_2q_gate ** (i + 1)
            )
            unitary_fidelity = 1.0 - res.fun
            current_fidelity = hw_fidelity * unitary_fidelity

            # print(self.gate_template_obj.two_qubit_gate, "passed 2q fid:", fidelity_2q_gate, "est hw fid:", hw_fidelity, unitary_fidelity, current_fidelity)

            # Update if the best_fidelity so far has been 0 (initial case)
            if best_fidelity == 0:
                best_idx = i
                best_fidelity = current_fidelity

            # Update if the current value is much smaller than the previous minimum
            if current_fidelity - best_fidelity > tol * 0.1:
                best_idx = i
                best_fidelity = current_fidelity

        if force_gate_count:
            return best_idx + 1, results[0], best_fidelity
        else:
            return best_idx + 1, results[best_idx], best_fidelity


def _driver_func(
    target_unitary,
    gate_def,
    gate_param,
    fidelity_2q_gate,
    fidelity_1q_gate,
    tol,
    force_gate_count,
):
    attempts = 1
    for i in range(attempts):  # Max 3 attempts. Typically 1st attempt always succeeds
        gt = GateTemplate(gate_def, gate_param)
        gs = TwoQubitGateSynthesizer(target_unitary, gt)
        x = int(1 / gate_param[0] + 3)
        layer_count, result_obj, fidelity = gs.optimal_decomposition(
            tol,
            fidelity_2q_gate,
            fidelity_1q_gate,
            max_num_layers=x,
            force_gate_count=force_gate_count,
        )
        if result_obj.success is True:
            return [layer_count, result_obj, fidelity]
        else:
            if i == attempts - 1:
                return [layer_count, result_obj, 0.0]

    # print("Couldn't find decomposition")
    # print(target_unitary)
    # print(gate_def)
    # print(gate_param)
    # print(fidelity_2q_gate)
    # print(tol)
    # assert(0)


from qiskit.transpiler.basepasses import TransformationPass


class ParallelGateReplacementPass(TransformationPass):
    """
    Takes a hardware mapped/routed Qiskit circuit and performs gate replacement
    Parallelizes over two-qubit gates and different hardware gates (jobs = n_algorithm_gates * n_hardware_gates)
    """

    def __init__(
        self,
        gate_defs,
        gate_params,
        fidelity_dict_2q_gate,
        fidelity_list_1q_gate,
        tol=1e-3,
        decompose_swaps=True,
        force_gate_count=None,
        trotterization=False,
    ):
        self.gate_defs = gate_defs
        self.gate_params = gate_params
        self.fidelity_dict_2q_gate = fidelity_dict_2q_gate
        self.fidelity_list_1q_gate = fidelity_list_1q_gate
        self.tol = tol
        self.num_target_gates = len(self.gate_defs)

        self.decompose_swaps = decompose_swaps
        self.force_gate_count = force_gate_count
        assert self.num_target_gates == len(self.gate_params)
        super().__init__()

    def run(self, circ, num_threads=1, exact_decom=False):
        job_list = []
        node_list = {}
        # dag = circuit_to_dag(circ)
        dag = circ
        #
        job_id = 0
        for gate in dag.topological_op_nodes():
            if not len(gate.qargs) == 2:
                continue
            target_unitary = get_gate_unitary_qiskit(gate.op)
            # Hardware qubits which are being operated on
            idx = (gate.qargs[0].index, gate.qargs[1].index)
            """Print(idx) print(gate) print(gate.qargs) print(gate.cargs)"""
            gate_tuple = (min(idx), max(idx))
            for i in range(self.num_target_gates):
                if exact_decom:
                    fidelity_2q_gate = 1.0
                    fidelity_1q_gate = [1.0, 1.0]
                    self.tol = 1e-6
                else:
                    fidelity_2q_gate = self.fidelity_dict_2q_gate[gate_tuple][i]
                    fidelity_1q_gate = [
                        self.fidelity_list_1q_gate[gate_tuple[0]],
                        self.fidelity_list_1q_gate[gate_tuple[1]],
                    ]
                job_list.append(
                    (
                        target_unitary,
                        self.gate_defs[i],
                        self.gate_params[i],
                        fidelity_2q_gate,
                        fidelity_1q_gate,
                        self.tol,
                        self.force_gate_count,
                    )
                )
                node_list[(gate, i)] = job_id
                job_id += 1
        # print(job_list)

        # TODO: removed for now
        # pool seems to be breaking in qiskit pass manager
        if True or len(job_list) == 1:
            # results = [_driver_func(*job_list[0])]
            results = []
            for i in range(len(job_list)):
                results.append([_driver_func(*job_list[i])])
        else:
            time.time()
            # print("Jobs:", len(job_list))
            # print("Threads:", num_threads)
            pool = mp.Pool(num_threads)
            # starmap guarentees ordering of results
            results = pool.starmap(_driver_func, job_list)
            pool.close()
            time.time()
            # print("Compile time:", end - start)

        # Stitch outputs
        new_dag = DAGCircuit()
        for qreg in dag.qregs.values():
            new_dag.add_qreg(qreg)
        for creg in dag.cregs.values():
            new_dag.add_creg(creg)
        # qr = new_dag.qregs['q']
        new_circ = dag_to_circuit(new_dag)

        for gate in dag.topological_op_nodes():
            if not len(gate.qargs) == 2:
                new_circ.compose(gate.op, gate.qargs, gate.cargs, inplace=True)
                continue
            if gate.name == "swap" and not self.decompose_swaps:
                new_circ.compose(gate.op, gate.qargs, gate.cargs, inplace=True)
                continue

            # Pick out the best implementation for this gate
            best_fidelity = 0
            best_res_obj = None
            best_layer_count = 0
            best_idx = 0
            for i in range(self.num_target_gates):
                tmp = results[node_list[(gate, i)]]
                if tmp == []:
                    continue
                else:
                    # my_layer_count, my_result_obj, my_fidelity = results[
                    #     node_list[(gate, i)]
                    # ]
                    # not sure why but somewhere this got nested in an extra list
                    my_layer_count, my_result_obj, my_fidelity = results[
                        node_list[(gate, i)]
                    ][0]
                if my_fidelity >= best_fidelity:
                    best_fidelity = my_fidelity
                    best_res_obj = my_result_obj
                    best_layer_count = my_layer_count
                    best_idx = i

            idx = best_idx
            gate_func = self.gate_defs[idx]
            param = self.gate_params[idx]
            layers = best_layer_count
            angles = best_res_obj.x
            new_circ.u3(angles[0], angles[1], angles[2], [gate.qargs[1]])
            new_circ.u3(angles[3], angles[4], angles[5], [gate.qargs[0]])
            param_idx = 6
            for i in range(layers):
                # new_circ.unitary(
                #     Operator(gate_func(*param)),
                #     [gate.qargs[1].index, gate.qargs[0].index],
                #     label=self.gate_labels[idx],
                # )
                new_circ.append(
                    gate_func(*param), [gate.qargs[1].index, gate.qargs[0].index]
                )
                new_circ.u3(
                    angles[param_idx],
                    angles[param_idx + 1],
                    angles[param_idx + 2],
                    [gate.qargs[1].index],
                )
                new_circ.u3(
                    angles[param_idx + 3],
                    angles[param_idx + 4],
                    angles[param_idx + 5],
                    [gate.qargs[0].index],
                )
                param_idx += 6
        optimized_dag = optimise1qgates.run(circuit_to_dag(new_circ))
        self.property_set["best_fid"] = best_fidelity
        return optimized_dag
        # new_circ = dag_to_circuit(optimized_dag)
        # return new_circ
