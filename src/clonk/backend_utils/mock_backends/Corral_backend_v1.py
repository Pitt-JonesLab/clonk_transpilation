from src.clonk.backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from qiskit.circuit.library.standard_gates import *
from src.clonk.utils.riswap_gates.riswap import RiSwapGate, fSim
import numpy as np
import time

class FakeCorral(ConfigurableFakeBackendV2):
    def __init__(self, n=16, k=2, twoqubitgate="riswap", jumpSizes=[0,1]):
        qubits = list(range(n))
        coupling_map = []
        for j in jumpSizes:
            if j == 0:
                continue
            coupling_map.extend([[i,i+j] for i in range(n-j)])
            for i in range(j):
                coupling_map.append([i,n-j+i])
        add_connections = self.divideCorralK_math(coupling_map, n, k)
        coupling_map.extend(add_connections)
        qubit_coordinates = [[i, i] for i in range(n-1)]

        gate_configuration = {}
        gate_configuration[IGate] = [(i,) for i in qubits]

        # Can do RXGates on all qubits
        gate_configuration[RXGate] = [(i,) for i in list(set(qubits))]

        # Can do RY on all qubits
        gate_configuration[RYGate] = [(i,) for i in qubits]

        # can do CZ on all pairs in coupling map
        if twoqubitgate == "cr":
            gate_configuration[RZXGate] = [(i, j) for i, j in coupling_map]
        if twoqubitgate == "cx":
            # can do CX on all pairs in coupling map
            gate_configuration[CXGate] = [(i, j) for i, j in coupling_map]
        if twoqubitgate == "riswap":
            gate_configuration[RiSwapGate] = [(i, j) for i, j in coupling_map]
        if twoqubitgate == "syc":
            gate_configuration[fSim] = [(i, j) for i, j in coupling_map]

        # can measure any qubits
        measurable_qubits = qubits

        super().__init__(
            name="Corral_N_"+str(n)+"_"+str(tuple(jumpSizes)).replace(' ', '')+"_K_"+str(k)+"_v_1",
            description="a mock backend in a corral with n nodes and k additional connections across the corral",
            n_qubits=len(qubits),
            gate_configuration=gate_configuration,
            measurable_qubits=measurable_qubits,
            qubit_coordinates=qubit_coordinates,
            gate_durations={
                IGate: 0,
                RXGate: 0,
                RYGate: 0,
                CZGate: 2.167,
            },
            parameterized_gates={
                RXGate: ["theta"],
                RZGate: ["theta"],
                RYGate: ["theta"],
                RiSwapGate: ["alpha"],
                U3Gate: ["theta", "phi", "lambda"],
                RZXGate: ["theta"],
                fSim: ["theta", "phi"],
            },
            single_qubit_gates=["rx", "ry"],
        )
    def snail_to_connectivity(self, snail_edge_list):
        # Convert snail edge list where nodes are snails and edges are qubits
        # To connectivity edge list where nodes are qubits and edges are coupling
        edge_list = []

        # qubits are coupled to a snail edge if they are both adjacent to a snail node
        for qubit, snail_edge in enumerate(snail_edge_list):
            for temp_qubit, temp_snail_edge in enumerate(snail_edge_list):
                if qubit != temp_qubit and (
                    snail_edge[0] in temp_snail_edge or snail_edge[1] in temp_snail_edge
                ):
                    edge_list.append((qubit, temp_qubit))
        return edge_list

    def divideCorralK_math(self, connections, n, k):
        if k < 1:
            return []
        jumpLength = int(n/2)
        newConnections = []
        for i in range(k):
            start = int(i*jumpLength/k)
            newConnections.append([start,start+jumpLength])
        return newConnections


    def divideCorralK_complete(self, connections, n, k):
        """takes in qubit nodes and returns new connections"""
        newConnections = []
        for i in range(k):
            distances = np.array([[n+1 for j in range(n)] for k in range(n)])
            for j in range(n):
                distances[j][j] = 0
            for (j, k) in connections:
                distances[j][k] = 1
                distances[k][j] = 1
            for (j, k) in newConnections:
                distances[j][k] = 1
                distances[k][j] = 1
            changed = True
            while changed:
                changed = False
                for j in range(n):
                    for k in range(n):
                        for l in range(n):
                            newDistance = distances[j][l] + distances[l][k]
                            if newDistance < distances[j][k]:
                                distances[j][k] = newDistance
                                changed = True
            newConnections.append(np.unravel_index(np.argmax(distances), distances.shape))
        
        return newConnections
    

    #FIXME implement to return full node list
    def divideCorralK_complete_snail_nodes(self, connections, n, k):
        newConnections = []
        n = len(connections)
        connections = self.snail_to_connectivity(connections)
        for i in range(k):
            distances = np.array([[n+1 for j in range(n)] for k in range(n)])
            for j in range(n):
                distances[j][j] = 0
            for (j, k) in connections:
                distances[j][k] = 1
                distances[k][j] = 1
            for (j, k) in newConnections:
                distances[j][k] = 1
                distances[k][j] = 1
            changed = True
            while changed:
                changed = False
                for j in range(n):
                    for k in range(n):
                        for l in range(n):
                            newDistance = distances[j][l] + distances[l][k]
                            if newDistance < distances[j][k]:
                                distances[j][k] = newDistance
                                changed = True
            newConnections.append(np.unravel_index(np.argmax(distances), distances.shape))
        
        return newConnections