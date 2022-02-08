# %%
from webbrowser import get
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter, Gate
from qiskit.quantum_info.operators import Operator
from qiskit.circuit.library.standard_gates import *
import numpy as np
from itertools import product
import sympy


# %%
def get_symb_express(base):
    class SymbolicGate(base):
        def __init__(self):
            # steal the matrix definition from the gate
            math = sympy

        def eval(self, symb):
            self.params = [symb]
            math = sympy
            return self.__array__(dtype=None)

        @property
        def params(self):
            """return instruction params."""
            return self._params

        @params.setter
        def params(self, parameters):
            self._params = parameters

    theta = sympy.Symbol("theta")

    return SymbolicGate().eval(theta)


# %%
get_symb_express(RXGate)

# %%
