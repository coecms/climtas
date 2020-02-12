#!/usr/bin/env python
# Copyright 2020 Scott Wales
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

from climtas.blocked import *
import xarray
import pandas
import dask.array
from climtas.helpers import *
import pytest


def test_groupby_dayofyear():
    time = pandas.date_range("20020101", "20050101", freq="D", closed="left")
    daily = xarray.DataArray(numpy.random.random(time.size), coords=[("time", time)])

    blocked_doy = blocked_groupby(daily, time="dayofyear")
    xarray_doy = daily.groupby("time.dayofyear")

    for op in "min", "max", "mean", "sum":
        xarray.testing.assert_equal(
            getattr(blocked_doy, op)(), getattr(xarray_doy, op)()
        )

    time = pandas.date_range("20020101", "20030101", freq="D", closed="left")
    daily = xarray.DataArray(numpy.random.random(time.size), coords=[("time", time)])

    blocked_doy = blocked_groupby(daily, time="dayofyear")
    xarray_doy = daily.groupby("time.dayofyear")

    for op in "min", "max", "mean", "sum":
        xarray.testing.assert_equal(
            getattr(blocked_doy, op)()[0:365], getattr(xarray_doy, op)()
        )


def test_groupby_dayofyear_dask():
    time = pandas.date_range("20020101", "20050101", freq="D", closed="left")
    daily = xarray.DataArray(
        dask.array.zeros(time.size, chunks=50), coords=[("time", time)]
    )

    blocked_doy_max = blocked_groupby(daily, time="dayofyear").max()
    xarray_doy_max = daily.groupby("time.dayofyear").max()

    # We should be making less chunks than xarray's default
    assert chunk_count(blocked_doy_max) <= 0.1 * chunk_count(xarray_doy_max)

    # We should be have a less complex graph than xarray's default
    assert graph_size(blocked_doy_max) <= 0.2 * graph_size(xarray_doy_max)


def test_groupby_monthday():
    time = pandas.date_range("20020101", "20050101", freq="D", closed="left")
    daily = xarray.DataArray(numpy.random.random(time.size), coords=[("time", time)])

    blocked_doy = blocked_groupby(daily, time="monthday")

    daily.coords["monthday"] = daily.time.dt.month * 100 + daily.time.dt.day
    xarray_doy = daily.groupby("monthday")

    for op in "min", "max", "mean", "sum":
        numpy.testing.assert_array_equal(
            getattr(blocked_doy, op)(), getattr(xarray_doy, op)()
        )


def test_groupby_monthday_dask():
    time = pandas.date_range("20020101", "20050101", freq="D", closed="left")
    daily = xarray.DataArray(
        dask.array.zeros(time.size, chunks=50), coords=[("time", time)]
    )

    blocked_doy_max = blocked_groupby(daily, time="monthday").max()

    daily.coords["monthday"] = daily.time.dt.month * 100 + daily.time.dt.day
    xarray_doy_max = daily.groupby("monthday").max()

    # We should be making less chunks than xarray's default
    assert chunk_count(blocked_doy_max) <= 0.1 * chunk_count(xarray_doy_max)

    # We should be have a less complex graph than xarray's default
    assert graph_size(blocked_doy_max) <= 0.2 * graph_size(xarray_doy_max)


def test_groupby_climatology():
    time = pandas.date_range("20020101", "20050101", freq="D", closed="left")
    daily = xarray.DataArray(
        dask.array.random.random(time.size, chunks=50), coords=[("time", time)]
    )

    climatology = blocked_groupby(daily, time="dayofyear").mean()
    delta = blocked_groupby(daily, time="dayofyear") - climatology

    climatology_xr = daily.groupby("time.dayofyear").mean()
    delta_xr = daily.groupby("time.dayofyear") - climatology_xr

    numpy.testing.assert_array_equal(delta_xr, delta)


def test_groupby_percentile():
    time = pandas.date_range("20020101", "20050101", freq="D", closed="left")
    daily = xarray.DataArray(
        dask.array.random.random(time.size, chunks=50), coords=[("time", time)]
    )

    climatology = blocked_groupby(daily, time="dayofyear").percentile(90)

    climatology_xr = (
        daily.load().groupby("time.dayofyear").reduce(numpy.percentile, q=90)
    )

    numpy.testing.assert_array_equal(climatology_xr[:-1], climatology[:-1])


def test_groupby_apply():
    import scipy.stats

    time = pandas.date_range("20020101", "20050101", freq="D", closed="left")
    daily = xarray.DataArray(
        dask.array.random.random(time.size, chunks=50), coords=[("time", time)]
    )

    blocked_double = blocked_groupby(daily, time="dayofyear").apply(lambda x: x * 2)
    xarray.testing.assert_equal(daily * 2, blocked_double)

    blocked_rank = blocked_groupby(daily, time="dayofyear").rank()


def test_resample_safety():
    time = pandas.date_range("20020101", "20050101", freq="D", closed="left")
    daily = xarray.DataArray(
        dask.array.random.random(time.size, chunks=50), coords=[("time", time)]
    )

    # Not a coordinate
    with pytest.raises(Exception):
        blocked_resample(sliced, x=24)

    # Samples doesn't evenly divide length
    sliced = daily[0:15]
    with pytest.raises(Exception):
        blocked_resample(sliced, time=24)

    # Irregular
    sliced = xarray.concat([daily[0:15], daily[17:26]], dim="time")
    assert sliced.size == 24
    with pytest.raises(Exception):
        blocked_resample(sliced, time=24)


def test_groupby_safety():
    time = pandas.date_range("20020101", "20050101", freq="D", closed="left")
    daily = xarray.DataArray(
        dask.array.random.random(time.size, chunks=50), coords=[("time", time)]
    )

    # Not a coordinate
    with pytest.raises(Exception):
        blocked_groupby(sliced, x="dayofyear")

    # Samples don't cover a full year
    sliced = daily[1:365]
    with pytest.raises(Exception):
        blocked_groupby(sliced, time="dayofyear")

    sliced = daily[0:364]
    with pytest.raises(Exception):
        blocked_groupby(sliced, time="dayofyear")

    sliced = xarray.concat([daily[0:15], daily[17:365]], dim="time")
    with pytest.raises(Exception):
        blocked_groupby(sliced, time="dayofyear")
