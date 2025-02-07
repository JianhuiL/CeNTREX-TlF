from typing import Sequence, Union

import numpy as np
import numpy.typing as npt
import scipy.constants as cst

from centrex_tlf import states

__all__ = [
    "J_levels",
    "thermal_population",
    "generate_uniform_population_state_indices",
    "generate_uniform_population_states",
]


def J_levels(J: int) -> int:
    """
    Number of hyperfine levels per J rotational level

    Args:
        J (int): rotational level

    Returns:
        int: number of hyperfine levels
    """
    return 4 * (2 * J + 1)


def thermal_population(J: int, T: float, B: float = 6.66733e9, n: int = 100) -> float:
    """
    Thermal population of a given J sublevel

    Args:
        J (int): Rotational level
        T (float): Temperature [Kelvin]
        B (float, optional): Rotational constant. Defaults to 6.66733e9.
        n (int, optional): Number of rotational levels to normalize with. Defaults to
                            100.

    Returns:
        float: relative population in a rational level
    """
    c = 2 * np.pi * cst.hbar * B / (cst.k * T)

    def a(J):
        return -c * J * (J + 1)

    Z = np.sum([J_levels(i) * np.exp(a(i)) for i in range(n)])
    return J_levels(J) * np.exp(a(J)) / Z


def generate_uniform_population_state_indices(
    state_indices: Sequence[int], levels: int
) -> npt.NDArray[np.complex_]:
    """
    spread population uniformly over the given state indices

    Args:
        state_indices (Sequence[int]): indices to put population into
        levels (int): total states involved

    Returns:
        npt.NDArray[np.complex_]: density matrix
    """
    ρ = np.zeros([levels, levels], dtype=complex)
    for ids in state_indices:
        ρ[ids, ids] = 1
    return ρ / np.trace(ρ)


def generate_uniform_population_states(
    selected_states: Union[
        Sequence[states.QuantumSelector],
        states.QuantumSelector,
    ],
    QN: Sequence[states.State],
) -> npt.NDArray[np.complex_]:
    """
    spread population uniformly over the given states

    Args:
        selected_states
            (Union[ Sequence[states.QuantumSelector], states.QuantumSelector, ]):
                state selector(s)
        QN (Sequence[states.State]): all states involved

    Returns:
        npt.NDArray[np.complex_]: density matrix
    """
    levels = len(QN)
    ρ = np.zeros([levels, levels], dtype=complex)

    if isinstance(selected_states, states.QuantumSelector):
        indices = selected_states.get_indices(QN)
    elif isinstance(selected_states, (list, tuple, np.ndarray)):
        indices = np.array([], dtype=np.int_)
        for ss in selected_states:
            indices = np.append(indices, ss.get_indices)
        indices = np.unique(indices)

    for ids in indices:
        ρ[ids, ids] = 1

    return ρ / np.trace(ρ)


def generate_thermal_population_states(
    selected_states: Union[Sequence[states.QuantumSelector], states.QuantumSelector],
    QN: Sequence[states.State],
) -> npt.NDArray[np.complex_]:
    levels = len(QN)
    ρ = np.zeros([levels, levels], dtype=complex)
    return ρ
