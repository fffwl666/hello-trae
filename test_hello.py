import unittest
from itertools import islice

from hello import fibonacci, fibonacci_generator, fib_recursive


class TestFibonacci(unittest.TestCase):
    def test_fibonacci(self):
        cases = [
            (0, []),
            (1, [0]),
            (2, [0, 1]),
            (5, [0, 1, 1, 2, 3]),
            (10, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                self.assertEqual(fibonacci(n), expected)

    def test_generator(self):
        cases = [
            (0, []),
            (1, [0]),
            (2, [0, 1]),
            (5, [0, 1, 1, 2, 3]),
            (10, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                generator = fibonacci_generator()
                self.assertEqual(list(islice(generator, n)), expected)

    def test_generator_continues(self):
        generator = fibonacci_generator()
        self.assertEqual(list(islice(generator, 5)), [0, 1, 1, 2, 3])
        self.assertEqual(next(generator), 5)
        self.assertEqual(next(generator), 8)

    def test_recursive(self):
        cases = [
            (0, 0),
            (1, 1),
            (2, 1),
            (5, 5),
            (10, 55),
        ]
        for k, expected in cases:
            with self.subTest(k=k):
                self.assertEqual(fib_recursive(k), expected)


if __name__ == "__main__":
    unittest.main()
