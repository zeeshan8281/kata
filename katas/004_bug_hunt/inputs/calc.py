def median(xs):
    """Middle value of a list of numbers."""
    s = sorted(xs)
    return s[len(s) // 2]  # only correct for odd-length lists
