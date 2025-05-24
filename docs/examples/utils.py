"""Module for computing runoff using the NRCS-PDM model with snowmelt."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, overload

import numpy as np
import xarray as xr
from numba import config as nbconfig
from numba import njit, prange

if TYPE_CHECKING:
    from numpy.typing import NDArray

    FloatArray = NDArray[np.floating[Any]]
    UIntArray = NDArray[np.uint32]

nbconfig.THREADING_LAYER = "workqueue"

__all__ = ["compute_kge", "separate_snow", "to_numpy"]

SMALL = 1e-6


@njit("f8(f8[::1], f8[::1])", nogil=True)
def compute_kge(sim: FloatArray, obs: FloatArray) -> float:
    """Compute the original Kling-Gupta Efficiency (2009)."""
    cc = np.corrcoef(obs, sim)[0, 1]
    alpha = np.std(sim) / np.std(obs)
    beta = np.sum(sim) / np.sum(obs)
    kge = 1 - np.sqrt(np.square(cc - 1) + np.square(alpha - 1) + np.square(beta - 1))
    return kge


@overload
def to_numpy(data: Any, dtype: Literal["f8"] = "f8") -> FloatArray: ...


@overload
def to_numpy(data: Any, dtype: Literal["uint32"]) -> UIntArray: ...


def to_numpy(data: Any, dtype: Literal["f8", "uint32"] = "f8") -> FloatArray | UIntArray:
    """Convert data to a contiguous numpy array with specified dtype."""
    return np.asarray(data, dtype=dtype, order="C")


@njit("f8[::1](f8[::1], f8[::1], f8, f8)", parallel=True, nogil=True)
def _separate_snow(
    prcp: FloatArray,
    tmin: FloatArray,
    t_rain: np.float64,
    t_snow: np.float64,
) -> FloatArray:
    """Separate snow in precipitation."""
    t_rng = t_rain - t_snow
    snow = np.zeros_like(prcp)

    for t in prange(prcp.shape[0]):
        if tmin[t] > t_rain:
            snow[t] = 0.0
        elif tmin[t] < t_snow:
            snow[t] = prcp[t]
        else:
            snow[t] = prcp[t] * (t_rain - tmin[t]) / t_rng
    return snow


def separate_snow(clm: xr.Dataset, t_rain: float, t_snow: float) -> xr.Dataset:
    r"""Separate snow from precipitation.

    Notes
    -----
    The snow separation is based on the Martinez and Gupta (2010) method.
    For more details please refer to Equation 3 in the following publication:
    https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2009WR008294

    Also, for the parameters of this model, please refer to the following publication:
    https://link.springer.com/article/10.1007/s00376-012-2192-7

    The equation is as follows:

    .. math::

        \text{Snow}(t) =
        \begin{cases}
        0, & T^{\text{rain}} < T^{\min}(t) \\
        P(t) \times \dfrac{T^{\text{rain}} - T^{\min}(t)}{T^{\text{rain}} - T^{\text{snow}}}, & T^{\text{snow}} < T^{\min}(t) < T^{\text{rain}} \\
        P(t), & T^{\min}(t) < T^{\text{snow}}
        \end{cases}

    Parameters
    ----------
    clm : xarray.Dataset
        Dataset containing the following variables:

        - ``prcp``: precipitation (mm/day) with time, x, and y dims
        - ``tmin``: minimum temperature (°C) with time, x, and y dims

    t_rain : float
        Rain temperature threshold (°C).
    t_snow : float
        Snow temperature threshold (°C).

    Returns
    -------
    xarray.Dataset
        Dataset containing the following additional variable:

        - ``snow``: daily snowfall (mm)
    """

    def snow_func(
        prcp: FloatArray,
        tmin: FloatArray,
        t_rain: float,
        t_snow: float,
    ) -> FloatArray:
        """Separate snow based on Martinez and Gupta (2010)."""
        return _separate_snow(
            to_numpy(prcp),
            to_numpy(tmin),
            np.float64(t_rain),
            np.float64(t_snow),
        )

    clm["snow"] = xr.apply_ufunc(
        snow_func,
        clm["prcp"],
        clm["tmin"],
        kwargs={"t_rain": t_rain, "t_snow": t_snow},
        input_core_dims=[["time"], ["time"]],
        output_core_dims=[["time"]],
        vectorize=True,
        output_dtypes=[clm["prcp"].dtype],
    ).transpose("time", "y", "x")
    clm["snow"].attrs["units"] = "mm"
    clm["snow"].attrs["long_name"] = "Daily Snowfall"
    return clm
