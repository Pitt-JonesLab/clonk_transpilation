import numpy as np
import retworkx
import pydot
import os
import tempfile
from PIL import Image
from qiskit.circuit.library.standard_gates import *

from src.clonk.backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from src.clonk.utils.riswap_gates.riswap import RiSwapGate, fSim


class FakeCorral(ConfigurableFakeBackendV2):
    def __init__(self, n=16, k=2, twoqubitgate="riswap", jumpSizes=[0, 1]):
        
        #FIXME delete all?
        qubits = list(range(n))
        coupling_map = []
        #call corral()
        coupling_map = self.corral(n,2) #n number of snail, 2 is number of levels
        #call add_new_edges
        coupling_map = self.add_new_edges(coupling_map, k)
        # for j in jumpSizes:
        #     if j == 0:
        #         continue
        #     coupling_map.extend([[i, i + j] for i in range(n - j)])
        #     for i in range(j):
        #         coupling_map.append([i, n - j + i])
        # add_connections = self.divideCorralK_math(coupling_map, n, k)
        # coupling_map.extend(add_connections)
        qubit_coordinates = [[i, i] for i in range(n - 1)]
        #end delete?

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
            name="Corral_N_"
            + str(n)
            + "_"
            + str(tuple(jumpSizes)).replace(" ", "")
            + "_K_"
            + str(k)
            + "_v_1",
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
                RZGate: 0,
                XGate: 0,
                YGate: 0,
                SXGate: 0,
                SXdgGate: 0,
                CXGate: 2,
                RiSwapGate: 2,  # time of iSwap
                U3Gate: 0,
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
        """n determines jump length, k is how many connections to be added."""
        if k < 1:
            return []
        jumpLength = int(n / 2)
        newConnections = []
        for i in range(k):
            start = int(i * jumpLength / k)
            newConnections.append([start, start + jumpLength])
        return newConnections

    # define corral, use for init? TODO
    def corral(self, num_snails=32, num_levels=2):
        """returns edge list of a corral of size specified
        snails are nodes, edges are qubits"""

        snail_edge_list = []
        for snail0, snail1 in zip(range(num_snails), range(1, num_snails + 1)):
            for i in range(num_levels):
                snail_edge_list.append((snail0, snail1 % num_snails))
        return snail_edge_list

    def add_new_edges(self, corral_list, num_new_edges=1): 
        """Finds the best edges to add based on max distance
        corral is list of snail map (nodes=snails, edges=qubits)
        k is how many edges to add"""

        graph = retworkx.PyGraph() #convert corral to graph to use retworkx libraries
        graph.add_nodes_from(list(range( max(max(corral_list))+1 )))
        for edge in corral_list:
            graph.add_edge(edge[0],edge[1], 1)
        # self.display_graph(graph)

        #find edge with greatest weight
        max_pos = self.get_max_distance_nodes_list(graph)
        for k in range(num_new_edges):
            new_edge = (max_pos[0][0], max_pos[0][1])

            #find what edges to remove so there arent' 5 connections on a snail
            # need to remove 2 edges (1 from each snail), so can add another edge to the snails that were previously connected to the new edge's nodes
            remove_edge_1, remove_edge_2, additionalEdge =  self.get_edges_remove_add(graph, new_edge)

            #add and remove edges
            graph.add_edge(new_edge[0],new_edge[1],1) #add first edge, calc by greatest weight
            graph.remove_edge(remove_edge_1[0], remove_edge_1[1]) #remove edge generated by prev edge connections
            graph.remove_edge(remove_edge_2[0], remove_edge_2[1]) 
            graph.add_edge(additionalEdge[0], additionalEdge[1], 1) #add new edge connected nodes that lost an edge


            #alt implementation, save some computing but doesn't update max distance as freq
            # max_pos = np.delete(max_pos, 0, 0)
            # if len(max_pos) < 1 and k <num_new_edges-1:
            #     max_pos = self.get_max_distance_nodes_list(graph)

            max_pos = self.get_max_distance_nodes_list(graph)

        return graph.edge_list() #return in same format of list of edges

    def display_graph(self, graph):
        """takes in and displays pyplot graph"""
        dot_str = graph.to_dot(
            lambda node: dict(
                color='black', fillcolor='lightblue', style='filled'))
        dot = pydot.graph_from_dot_data(dot_str)[0]

        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_path = os.path.join(tmpdirname, 'graph.png')
            dot.write_png(tmp_path)
            image = Image.open(tmp_path)
            os.remove(tmp_path)
        display(image) #uncomment to display graph

    def get_max_distance_nodes_list(self, graph):
        """returns numpy list of tuples, tuple is two nodes with a max distance between them"""
        temp_dist_matrix = retworkx.graph_distance_matrix(graph) #get distance matrix
        max_pos = np.where(temp_dist_matrix == temp_dist_matrix.max())  #find max distances
        return list(zip(max_pos[0], max_pos[1]))  

    def get_edges_remove_add(self, graph, new_edge):
        """takes new edge and returns 2 edges to remove and 1 to add to keep balance (4 qubits/snail)"""
        g_edges = graph.edge_list()
        #FIXME find way to make sure no node get's disconnected on removal
        remove_edge_1 = None
        remove_edge_2 = None
        for e in g_edges:
            if e[0] == new_edge[0]:
                remove_edge_1 = e
                newNode_1 = e[1]
            elif e[1] == new_edge[0]:
                remove_edge_1 = e
                newNode_1 = e[0]
            elif e[0] == new_edge[1]:
                remove_edge_2 = e
                newNode_2 = e[1]
            elif e[1] == new_edge[1]:
                remove_edge_2 = e
                newNode_2 = e[0]
            if remove_edge_1 is not None and remove_edge_2 is not None:
                break
        return remove_edge_1, remove_edge_2, (newNode_1, newNode_2)
    
    def divideCorralK_complete(self, connections, n, k):
        """Takes in qubit nodes and returns new connections."""
        newConnections = []
        for i in range(k):
            distances = np.array([[n + 1 for j in range(n)] for k in range(n)])
            for j in range(n):
                distances[j][j] = 0
            for j, k in connections:
                distances[j][k] = 1
                distances[k][j] = 1
            for j, k in newConnections:
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
            newConnections.append(
                np.unravel_index(np.argmax(distances), distances.shape)
            )

        return newConnections
    
    

    # FIXME implement to return full node list
    def divideCorralK_complete_snail_nodes(self, connections, n, k):
        newConnections = []
        n = len(connections)
        connections = self.snail_to_connectivity(connections)
        for i in range(k):
            distances = np.array([[n + 1 for j in range(n)] for k in range(n)])
            for j in range(n):
                distances[j][j] = 0
            for j, k in connections:
                distances[j][k] = 1
                distances[k][j] = 1
            for j, k in newConnections:
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
            newConnections.append(
                np.unravel_index(np.argmax(distances), distances.shape)
            )

        return newConnections
