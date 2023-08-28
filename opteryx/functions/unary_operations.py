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
Implement conditions which are essentially unary statements, usually IS statements.

This are executed as functions on arrays rather than functions on elements in arrays.
"""
import numpy


def _is_null(values: numpy.ndarray) -> numpy.ndarray:
    """
    Returns a boolean mask where True indicates that the corresponding element in values is null (NaN).

    Parameters:
        values: numpy.ndarray
            1D array of boolean and/or null values.

    Returns:
        numpy.ndarray: 1D array of booleans serving as a mask.
    """
    return numpy.equal(values, None)


def _is_not_null(values: numpy.ndarray) -> numpy.ndarray:
    """
    Returns a boolean mask where True indicates that the corresponding element in values is not null (NaN).

    Parameters:
        values: numpy.ndarray
            1D array of boolean and/or null values.

    Returns:
        numpy.ndarray: 1D array of booleans serving as a mask.
    """
    return numpy.logical_not(numpy.equal(values, None))


def _is_true(values: numpy.ndarray) -> numpy.ndarray:
    """
    Returns a boolean mask where True indicates that the corresponding element in values is True.

    Parameters:
        values: np.ndarray
            1D array of boolean and/or null values.

    Returns:
        np.ndarray: 1D array of booleans serving as a mask.
    """
    return values == True


def _is_false(values: numpy.ndarray) -> numpy.ndarray:
    """
    Returns a boolean mask where True indicates that the corresponding element in values is False.

    Parameters:
        values: np.ndarray
            1D array of boolean and/or null values.

    Returns:
        np.ndarray: 1D array of booleans serving as a mask.
    """
    return values == False


def _is_not_true(values: numpy.ndarray) -> numpy.ndarray:
    """
    Returns a boolean mask where True indicates that the corresponding element in values is not True.

    Parameters:
        values: np.ndarray
            1D array of boolean and/or null values.

    Returns:
        np.ndarray: 1D array of booleans serving as a mask.
    """
    return values != True


def _is_not_false(values: numpy.ndarray) -> numpy.ndarray:
    """
    Returns a boolean mask where True indicates that the corresponding element in values is not False.

    Parameters:
        values: np.ndarray
            1D array of boolean and/or null values.

    Returns:
        np.ndarray: 1D array of booleans serving as a mask.
    """
    return values != False


UNARY_OPERATIONS = {
    "IsNull": _is_null,
    "IsNotFalse": _is_not_false,
    "IsNotNull": _is_not_null,
    "IsNotTrue": _is_not_true,
    "IsTrue": _is_true,
    "IsFalse": _is_false,
}
