"""
Fake Hatlab device (16+4 qubit).
"""

import itertools
# from qiskit.test.mock.utils.configurable_backend import ConfigurableFakeBackend
from src.backend_utils.configurable_backend_v2 import ConfigurableFakeBackendV2
from qiskit.providers.models import BackendProperties
from qiskit.providers.models.backendproperties import Nduv, Gate
from qiskit.exceptions import QiskitError
from qiskit.circuit.library.standard_gates import *
from src.utils.riswap_gates.riswap import RiSwapGate


class FakeHatlab(ConfigurableFakeBackendV2):
    """A fake 16+4 qubit backend."""

    def foo(self, start_index, module_size, delete_cross=True):
        """helper functon for building subgraphs of hatlab-large"""
        # router qubits are first bit starting the module it connects to
        # e.g. [0,5,10,15] for start_index=0, module_size=5
        router_qubits = [start_index + module_size * i for i in range(4)]

        # router is all-to-all, except to itself
        coupling_map = [
            el for el in itertools.product(router_qubits, repeat=2) if el[0] != el[1]
        ]

        # delete cross edges if needed
        if module_size == 5 and delete_cross:
            removed_edges = [
                (router_qubits[0], router_qubits[2]),
                (router_qubits[2], router_qubits[0]),
                (router_qubits[1], router_qubits[3]),
                (router_qubits[3], router_qubits[1]),
            ]
            coupling_map = [el for el in coupling_map if el not in removed_edges]

        # build modules extending from each router_qubit
        level_1_round_robin = self.round_robin == 2 or self.round_robin == 3
        shuffled_router_qubits = list(router_qubits)

        for router_qubit in router_qubits:
            if not level_1_round_robin:
                coupling_map += itertools.product(
                    range(router_qubit, router_qubit + module_size), repeat=2
                )
            else:
                # add in connections amoung module not including router
                coupling_map += itertools.product(
                    range(1 + router_qubit, router_qubit + module_size), repeat=2
                )

                # add in connection to shuffled router qubits
                coupling_map += [
                    (i, j)
                    for i, j in zip(
                        shuffled_router_qubits,
                        range(1 + router_qubit, router_qubit + module_size),
                    )
                ]
                # seems to print better without this, again shouldn't matter due to symmetry
                # shuffled_router_qubits.append(shuffled_router_qubits.pop(0))

        return router_qubits, coupling_map

    def __init__(
        self,
        num_qubits,
        router_as_qubits=False,
        twoqubitgate="riswap",
        round_robin=0,
    ):
        # handle round robin options
        # 0 - RR nowhere
        # 1- RR only level_0
        # 2- RR only level_1
        # 3- RR both levels
        self.round_robin = round_robin

        # only allow these options for now, although does not need to be true necessarily
        assert num_qubits == 20 or num_qubits == 68 or num_qubits == 84

        if num_qubits == 20:
            router_qubits, coupling_map = self.foo(
                start_index=0,
                module_size=5,
                delete_cross=False,
            )

        if num_qubits == 68 or num_qubits == 84:
            # set module variable accordingly
            if num_qubits == 68:
                module_size = 4
            else:
                module_size = 5

            # start with level 0 router that foo will build on
            router_qubits = []
            # label level 0 at end of list to keep ordering tidy
            # e.g. # [80,81,82,83]
            level_0_router_qubits = [num_qubits - 4 + i for i in range(4)]
            router_qubits += level_0_router_qubits
            coupling_map = [
                el
                for el in itertools.product(router_qubits, repeat=2)
                if el[0] != el[1]
            ]

            # initialize offset, starts at 0 bc level0 router qubits were placed at the end
            offset = 0

            # call foo to extend off each router qubit
            level_0_round_robin = self.round_robin == 1 or self.round_robin == 3
            shuffled_level_0_router_qubits = list(level_0_router_qubits)

            for router_qubit in level_0_router_qubits:

                temp_router_qubits, temp_coupling_map = self.foo(
                    start_index=offset, module_size=module_size
                )

                # extend global edge lists
                router_qubits += temp_router_qubits
                coupling_map += temp_coupling_map

                # connect new router qubits all to all to source level 0 router_qubit
                if not level_0_round_robin:
                    coupling_map += [
                        (router_qubit, temp_router_qubit)
                        for temp_router_qubit in temp_router_qubits
                    ]
                else:
                    # round robin means level1 router connects to shuffled level0 router qubits
                    coupling_map += [
                        (temp_level0_router, temp_router_qubit)
                        for temp_level0_router, temp_router_qubit in zip(
                            shuffled_level_0_router_qubits, temp_router_qubits
                        )
                    ]
                    # shuffle list using round robin means just change offset by 1
                    # shuffling doesn't actually matter since invariant to order via symmetries
                    # however, may to decide to leave this in because shuffling makes the graphviz plot nicer
                    # shuffled_level_0_router_qubits.append(
                    #     shuffled_level_0_router_qubits.pop(0)
                    # )

                # update offset, router_size*module_size (module_size includes count of the router qubit it is paired with)
                offset += 4 * module_size

        # finally,
        # delete repeats
        coupling_map = list(set(coupling_map))

        # add bidirectional edges
        coupling_map += [[q2, q1] for q1, q2 in coupling_map]

        # check no edges to self
        coupling_map = [[q1, q2] for q1, q2 in coupling_map if q1 != q2]

        # seperate module_qubits
        module_qubits = list(set(range(num_qubits)).difference(set(router_qubits)))

        # ignore
        qubit_coordinates = []

        gate_configuration = {}

        extra_qubits = []
        if router_as_qubits:
            extra_qubits = router_qubits
        gate_configuration[RZGate] = [(i,) for i in module_qubits + extra_qubits]
        gate_configuration[XGate] = [(i,) for i in module_qubits + extra_qubits]
        gate_configuration[YGate] = [(i,) for i in module_qubits + extra_qubits]
        gate_configuration[SXGate] = [(i,) for i in module_qubits + extra_qubits]
        gate_configuration[SXdgGate] = [(i,) for i in module_qubits + extra_qubits]
        gate_configuration[IGate] = [(i,) for i in router_qubits + module_qubits]

        if twoqubitgate == "cr":
            gate_configuration[RZXGate] = [(i, j) for i, j in coupling_map]
        if twoqubitgate == "cx":
            # can do CX on all pairs in coupling map
            gate_configuration[CXGate] = [(i, j) for i, j in coupling_map]
        if twoqubitgate == "riswap":
            gate_configuration[RiSwapGate] = [(i, j) for i, j in coupling_map]
        # gate_configuration[CZGate] = [
        #     (i, j)
        #     for i, j in coupling_map
        #     if not (i in router_qubits and j in router_qubits)
        # ]

        super().__init__(
            name=f"Modular-{twoqubitgate}"
            if not round_robin
            else f"Modular-RR{round_robin}-{twoqubitgate}",
            description="Extended Hatlab 16+4 QC",
            n_qubits=len(router_qubits + module_qubits),
            gate_configuration=gate_configuration,
            parameterized_gates={
                RZGate: ["theta"],
                RiSwapGate: ["alpha"],
            },
            measurable_qubits=module_qubits + router_qubits
            if router_as_qubits
            else module_qubits,
            qubit_coordinates=qubit_coordinates,
            gate_durations={
                IGate: 0,
                RZGate: 0,
                RYGate: 0,
                XGate: 0,
                YGate: 0,
                SXGate: 0,
                SXdgGate: 0,
                CXGate: 2.167,
                RiSwapGate: 1,  # time of iSwap
                U3Gate: 0,
                RZXGate: 1,
            },
            single_qubit_gates=["rz", "x", "y", "sx", "sxdg"],
        )
        self.plot_coupling_map = coupling_map


# class LegacyFakeHatlab(ConfigurableFakeBackend):
#     """A fake 16+4 qubit backend."""

#     def __init__(self):
#         self.qubit_coordinates = [
#             [2, 3],
#             [1, 2],
#             [0, 2],
#             [0, 4],
#             [1, 4],
#             [3, 4],
#             [2, 5],
#             [2, 6],
#             [4, 6],
#             [4, 5],
#             [4, 3],
#             [5, 4],
#             [6, 4],
#             [6, 2],
#             [5, 2],
#             [3, 2],
#             [4, 1],
#             [4, 0],
#             [2, 0],
#             [2, 1],
#         ]

#         coupling_map = [
#             [0, 5],
#             [0, 10],
#             [0, 15],
#             [5, 0],
#             [5, 10],
#             [5, 15],
#             [10, 0],
#             [10, 5],
#             [10, 15],
#             [15, 0],
#             [15, 5],
#             [15, 10],
#         ]
#         coupling_map += itertools.product(range(0, 5), repeat=2)
#         coupling_map += itertools.product(range(5, 10), repeat=2)
#         coupling_map += itertools.product(range(10, 15), repeat=2)
#         coupling_map += itertools.product(range(15, 20), repeat=2)

#         coupling_map = [[q1, q2] for q1, q2 in coupling_map if q1 != q2]

#         super().__init__(
#             name="fake_hatlab",
#             n_qubits=20,
#             coupling_map=coupling_map,
#             basis_gates=["id", "rx", "ry", "cz", "swap"],
#             single_qubit_gates=["id", "rx", "ry"],
#         )

#     def _build_props(self) -> BackendProperties:
#         """Build properties for backend."""
#         qubits = []
#         gates = []

#         for (qubit_t1, qubit_t2, freq, read_err) in zip(
#             self.qubit_t1, self.qubit_t2, self.qubit_frequency, self.qubit_readout_error
#         ):
#             qubits.append(
#                 [
#                     Nduv(date=self.now, name="T1", unit="µs", value=qubit_t1),
#                     Nduv(date=self.now, name="T2", unit="µs", value=qubit_t2),
#                     Nduv(date=self.now, name="frequency", unit="GHz", value=freq),
#                     Nduv(date=self.now, name="readout_error", unit="", value=read_err),
#                 ]
#             )

#         for gate in self.basis_gates:
#             parameters = [
#                 Nduv(date=self.now, name="gate_error", unit="", value=0.01),
#                 Nduv(date=self.now, name="gate_length", unit="ns", value=4 * self.dt),
#             ]

#             if gate in self.single_qubit_gates:
#                 for i in range(self.n_qubits):
#                     # add a restriction that router qubits cannot do 1Q Operations
#                     if i in [0, 5, 10, 15]:
#                         continue
#                     gates.append(
#                         Gate(
#                             gate=gate,
#                             name=f"{gate}_{i}",
#                             qubits=[i],
#                             parameters=parameters,
#                         )
#                     )
#             elif gate == "swap" or gate == "cz":
#                 # for (qubit1, qubit2) in list(
#                 #     itertools.combinations(range(self.n_qubits), 2)
#                 # ):
#                 for (qubit1, qubit2) in self.coupling_map:

#                     # add a restriction that router qubits can only do swap
#                     if (
#                         qubit1 in [0, 5, 10, 15]
#                         or qubit2 in [0, 5, 10, 15]
#                         and gate != "swap"
#                     ):
#                         continue

#                     gates.append(
#                         Gate(
#                             gate=gate,
#                             name=f"{gate}{qubit1}_{qubit2}",
#                             qubits=[qubit1, qubit2],
#                             parameters=parameters,
#                         )
#                     )
#             else:
#                 raise QiskitError(
#                     "{gate} is not supported by fake backend builder."
#                     "".format(gate=gate)
#                 )

#         return BackendProperties(
#             backend_name=self.name,
#             backend_version=self.version,
#             last_update_date=self.now,
#             qubits=qubits,
#             gates=gates,
#             general=[],
#         )
#