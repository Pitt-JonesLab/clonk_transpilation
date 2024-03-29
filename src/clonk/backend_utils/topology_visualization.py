# %%
# %%
from qiskit.transpiler.coupling import CouplingMap

from clonk.backend_utils.mock_backends.ibm import *


def pretty_print(pb):
    # for printing remove bidirectional edges
    temp = list(pb.coupling_map.get_edges())
    temp2 = []
    for i, j in temp:
        if (j, i) not in temp2:
            temp2.append((i, j))
    x = CouplingMap(temp2)

    # black magic errors when I modify the draw function directly in the CouplingMap file so Im just copying the code here to make it work
    import io

    import pydot
    from PIL import Image

    def formatter2(_):
        return dict(dir="none")

    dot_str = x.graph.to_dot(edge_attr=formatter2, graph_attr={"size": "0"})
    dot = pydot.graph_from_dot_data(dot_str)[0]
    png = dot.create_png(prog="sfdp")
    # png = dot.create_png(prog='fdp')
    # pdf = dot.create_pdf(prog="sfdp")
    # png = dot.create_png(prog="neato")
    return Image.open(io.BytesIO(png))


# # %%
# from clonk.backend_utils.mock_backends import FakeHeavyHex
# pb = FakeHeavyHex(twoqubitgate="cx", enforce_max_84=False, small=True)
# print(pb.num_qubits)
# pretty_print(pb)
