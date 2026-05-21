def factorial(n):
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    elif n == 0:
        return 1
    else:
        return n * factorial(n-1)
