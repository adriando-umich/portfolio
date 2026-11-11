"""Room protection: Monte Carlo simulation of one night at a 10-cabin lodge."""
import numpy as np

CABINS, GUESTS, LOW = 10, 100, 100


def simulate(protect, high, nights=20000, seed=7):
    """Mean revenue per night. Guests arrive one at a time. The low rate applies until only `protect` cabins are left."""
    rng = np.random.default_rng(seed)
    business = rng.random((nights, GUESTS)) < 0.05
    wtp = np.where(business, rng.normal(300, 45, (nights, GUESTS)), rng.normal(100, 25, (nights, GUESTS)))
    left = np.full(nights, CABINS); revenue = np.zeros(nights)
    for g in range(GUESTS):
        rate = np.where(left <= protect, high, LOW)
        book = (wtp[:, g] >= rate) & (left > 0)
        revenue += rate * book; left = left - book
    return revenue.mean(), revenue.std(), left.mean()


if __name__ == "__main__":
    for protect in range(0, 11):
        print(protect, [round(simulate(protect, high)[0]) for high in range(160, 361, 20)])
