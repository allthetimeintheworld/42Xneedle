import pytest
from src.math_utils import factorial

def test_factorial_base_case():
    assert factorial(0) == 1

def test_factorial_normal_case():
    assert factorial(5) == 120

def test_factorial_error_case():
    with pytest.raises(ValueError):
        factorial(-1)