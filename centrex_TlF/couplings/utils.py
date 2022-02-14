from dataclasses import dataclass
from typing import Union

import numpy as np
import scipy.constants as cst
from scipy.sparse import eye, kron
from sympy import Symbol

from centrex_TlF.states import State
from centrex_TlF.transitions.utils import check_transition_coupled_allowed
from centrex_TlF.utils import (
    calculate_power_from_rabi_gaussian_beam,
    calculate_rabi_from_power_gaussian_beam,
)

__all__ = [
    "generate_total_hamiltonian",
    "select_main_states",
    "generate_D",
    "TransitionSelector",
]


def generate_sharp_superoperator(M, identity=None):
    """
    Given an operator M in Hilbert space, generates sharp superoperator M_L in 
    Liouville space (see "Optically pumped atoms" by Happer, Jau and Walker)
    sharp = post-multiplies density matrix: |rho@A) = A_sharp @ |rho) 

    inputs:
    M = matrix representation of operator in Hilbert space

    outputs:
    M_L = representation of M in in Liouville space
    """

    if identity == None:
        identity = eye(M.shape[0], format="coo")

    M_L = kron(M.T, identity, format="csr")

    return M_L


def generate_flat_superoperator(M, identity=None):
    """
    Given an operator M in Hilbert space, generates flat superoperator M_L in 
    Liouville space (see "Optically pumped atoms" by Happer, Jau and Walker)
    flat = pre-multiplies density matrix: |A@rho) = A_flat @ |rho)

    inputs:
    M = matrix representation of operator in Hilbert space

    outputs:
    M_L = representation of M in in Liouville space
    """
    if identity == None:
        identity = eye(M.shape[0], format="coo")

    M_L = kron(identity, M, format="csr")

    return M_L


def generate_superoperator(A, B):
    """
    Function that generates superoperator representing 
    |A@rho@B) = np.kron(B.T @ A) @ |rho)

    inputs:
    A,B = matrix representations of operators in Hilbert space

    outpus:
    M_L = representation of A@rho@B in Liouville space
    """

    M_L = kron(B.T, A, format="csr")

    return M_L


def generate_D(H, QN, ground_main, excited_main, excited_states, Δ=0):
    # find transition frequency
    ig = QN.index(ground_main)
    ie = QN.index(excited_main)
    ω0 = (H[ie, ie] - H[ig, ig]).real

    # calculate the shift Δ = ω - ω₀
    ω = ω0 + Δ

    # shift matrix
    D = np.zeros(H.shape, H.dtype)
    for excited_state in excited_states:
        idx = QN.index(excited_state)
        D[idx, idx] -= ω

    return D


def generate_total_hamiltonian(H_int, QN, couplings):
    """Generate the total rotating frame Hamiltonian

    Args:
        H_int (np.ndarray; complex): internal Hamiltonian
        QN (list, array): array with states
        couplings (dict): dictionary with information about couplings between 
                        states; generated by generate_coupling_field

    Returns:
        np.ndarray; complex: rotating frame Hamiltonian
    """
    H_rot = H_int.copy()
    for coupling in couplings:
        gnd_idx = QN.index(coupling["ground main"])
        H_rot -= np.eye(len(H_rot)) * H_rot[gnd_idx, gnd_idx]
        H_rot += generate_D(
            H_rot,
            QN,
            coupling["ground main"],
            coupling["excited main"],
            coupling["excited states"],
        )
    return H_rot


def check_transitions(transitions):
    ground_states = np.concatenate(
        [transition["ground states approx"] for transition in transitions]
    )
    excited_states = np.concatenate(
        [transition["excited states approx"] for transition in transitions]
    )
    ground_states = np.concatenate([list(zip(*gs.data))[1] for gs in ground_states])
    excited_states = np.concatenate([list(zip(*es.data))[1] for es in excited_states])
    for gs in ground_states:
        assert gs not in excited_states, f"{gs} is both ground state and excited state"


def select_main_states(ground_states, excited_states, polarization):
    """Select main states for calculating the transition strength to normalize 
    the Rabi rate with

    Args:
        ground_states (list, array): list of ground states for the transition
        excited_states (list, array): list of excited states for the transition
        polarization (list, array): polarization vector
    """
    ΔmF = 0 if polarization[2] != 0 else 1

    allowed_transitions = []
    for ide, exc in enumerate(excited_states):
        exc = exc.find_largest_component()
        for idg, gnd in enumerate(ground_states):
            gnd = gnd.find_largest_component()
            if check_transition_coupled_allowed(gnd, exc, ΔmF, return_err=False):
                allowed_transitions.append((idg, ide, exc.mF))

    assert (
        len(allowed_transitions) > 0
    ), "none of the supplied ground and excited states have allowed transitions"

    excited_state = excited_states[allowed_transitions[0][1]]
    ground_state = ground_states[allowed_transitions[0][0]]

    return ground_state, excited_state


@dataclass
class TransitionSelector:
    ground: Union[list, np.ndarray]
    excited: Union[list, np.ndarray]
    polarizations: Union[list, np.ndarray]
    polarization_symbols: Union[list, np.ndarray]
    Ω: Symbol
    δ: Symbol
    description: str = None
    type: str = None
    ground_main: State = None
    excited_main: State = None


# @dataclass
# class Coupling:
#     ground: State
#     excited: State
#     main_coupling: complex
#     ground_states: np.ndarray
#     excited_states: np.ndarray
#     D: np.ndarray
#     fields: list
#     type: str
#     dipole: float

#     def rabi_from_power(self, P, σx, σy):
#        return calculate_rabi_from_power_gaussian_beam(
#             P, self.main_coupling, σx, σy, self.dipole
#         )

#     def power_from_rabi(self, Ω, σx, σy):
#         return calculate_power_from_rabi_gaussian_beam(
#             Ω, self.main_coupling, σx, σy, self.dipole
#         )
