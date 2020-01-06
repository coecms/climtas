#!/usr/bin/env python
# Copyright 2019 Scott Wales
# author: Scott Wales <scott.wales@unimelb.edu.au>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Functions for ranking data, e.g. 'this was the 5th hottest March 2nd'
"""

from .helpers import apply_by_dayofyear, apply_by_monthday

import numpy
import xarray
import scipy.stats


def rank_along_dim(da, dim="time"):
    """
    Apply 'scipy.stats.rankdata' along a specific dimension of the dataset 'da'

    Args:
        da: (:class:`xarray.DataArray`): Data to analyse, must include a 'time'
            dimension

    Returns:
        A new :class:`xarray.DataArray`
    """
    axis = da.get_axis_num("time")
    return numpy.apply_along_axis(scipy.stats.rankdata, axis, da)


def rank_by_dayofyear(da):
    """
    Return the ranking for each grid point at that day of the year

    Leap years will contribute their Dec. 31 values to day 366

    Args:
        da: (:class:`xarray.DataArray`): Data to analyse, must include a 'time'
            dimension

    Returns:
        A new :class:`xarray.DataArray`
    """
    r = apply_by_dayofyear(da, rank_along_dim)
    r.name = f"{r.name}_rank"
    r.attrs["units"] = "1"
    r.attrs["cell_methods"] = "time: rank_by_dayofyear"
    return r


def rank_by_monthday(da):
    """
    Return the ranking for each grid point at that month and day in the
    calendar

    Leap years will contribute their Feb. 29 values to Feb. 29

    Args:
        da: (:class:`xarray.DataArray`): Data to analyse, must include a 'time'
            dimension

    Returns:
        A new :class:`xarray.DataArray`
    """
    r = apply_by_monthday(da, rank_along_dim)
    r.name = f"{r.name}_rank"
    r.attrs["units"] = "1"
    r.attrs["cell_methods"] = "time: rank_by_monthday"
    return r
