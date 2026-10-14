"""斐波那契数列：迭代、生成器、记忆化递归三种实现。"""

import sys
from functools import lru_cache


def fibonacci(n):
    """迭代法：返回斐波那契数列的前 n 项列表。"""
    seq = []
    a, b = 0, 1
    for _ in range(n):
        seq.append(a)
        a, b = b, a + b
    return seq


def fibonacci_generator():
    """生成器：无限按序产出斐波那契数。"""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


@lru_cache(maxsize=None)
def fib_recursive(k):
    """记忆化递归：返回第 k 项（从第 0 项开始计数）。"""
    if k < 2:
        return k
    return fib_recursive(k - 1) + fib_recursive(k - 2)


def main():
    # 支持命令行传入项数，默认 10
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    if n < 0:
        print("项数不能为负数")
        return

    seq = fibonacci(n)
    print(f"前 {n} 项：{seq}")
    for i, value in enumerate(seq):
        print(f"F({i}) = {value}")

    # 用生成器取前 n 项，与迭代法结果比对
    gen = fibonacci_generator()
    gen_seq = [next(gen) for _ in range(n)]
    assert gen_seq == seq, "生成器与迭代法结果不一致"

    # 用记忆化递归求末项，验证三种实现结果一致
    if n > 0:
        assert fib_recursive(n - 1) == seq[-1], "递归法与迭代法结果不一致"

    print("三种实现结果一致。")


if __name__ == "__main__":
    main()
