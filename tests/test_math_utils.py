import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from math_utils import factorial
import pytest


def test_factorial_base_case():
    assert factorial(0) == 1


def test_factorial_normal_case():
    assert factorial(5) == 120


def test_factorial_negative_case():
    with pytest.raises(ValueError) as excinfo:
        factorial(-1)
    assert str(excinfo.value) == "Factorial not defined for negative numbers"