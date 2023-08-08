from qiskit.transpiler import CouplingMap

class Corral(CouplingMap):
    def __init__(self, num_snails=8, corral_skip_pattern=(0, 0)):

        def _corral(num_snails, skip_pattern):
            num_levels = 2

            assert len(skip_pattern) == num_levels
            snail_edge_list = []
            for snail0, snail1 in zip(range(num_snails), range(1, num_snails + 1)):
                for i in range(num_levels):
                    snail_edge_list.append(
                        (snail0, (skip_pattern[i] + snail1) % num_snails)
                    )
            return snail_edge_list

        def _snail_to_connectivity(snail_edge_list):
            # Convert snail edge list where nodes are snails and edges are qubits
            # To connectivity edge list where nodes are qubits and edges are coupling
            edge_list = []

            # qubits are coupled to a snail edge if they are both adjacent to a snail node
            for qubit, snail_edge in enumerate(snail_edge_list):
                for temp_qubit, temp_snail_edge in enumerate(snail_edge_list):
                    if qubit != temp_qubit and (
                        snail_edge[0] in temp_snail_edge
                        or snail_edge[1] in temp_snail_edge
                    ):
                        edge_list.append((qubit, temp_qubit))
            return edge_list

        snail_edge_list = _corral(num_snails, corral_skip_pattern)
        # if override_split and num_snails >= 32:
        #     snail_edge_list.remove((0, 1))
        #     snail_edge_list.append((0, 16))
        #     snail_edge_list.remove((16, 17))
        #     snail_edge_list.append((0, 16))

        coupling_map = _snail_to_connectivity(snail_edge_list)
        super().__init__(coupling_map)