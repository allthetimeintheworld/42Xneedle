import sys
sys.path.insert(0, '../')
from src.math_utils import factorial

def test_factorial_base_case():
    assert factorial(0) == 1

def test_factorial_normal_case():
    assert factorial(5) == 120

def test_factorial_error_case():
    try:
        factorial(-1)
        assert False
    except ValueError as e:
        assert str(e) == 'Factorial not defined for negative numbers'