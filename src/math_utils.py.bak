def factorial(n: int) -> int:
    """Calculate the factorial of a non-negative integer n.

    Args:
        n: A non-negative integer.

    Returns:
        The factorial of n.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result