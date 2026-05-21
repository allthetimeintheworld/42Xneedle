import pytest
from src.math_utils import factorial

def test_factorial_zero():
    assert factorial(0) == 1

def test_factorial_positive():
    assert factorial(5) == 120

def test_factorial_negative():
    with pytest.raises(ValueError, match="Factorial not defined for negative numbers"):
        factorial(-1)
