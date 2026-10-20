
import sys

def quick_sort(a):
    stack = [(0, len(a) - 1)]

    while stack:
        low, high = stack.pop()

        if low >= high:
            continue

        pivot = a[(low + high) // 2]
        i, j = low, high

        while i <= j:
            while a[i] < pivot:
                i += 1
            while a[j] > pivot:
                j -= 1

            if i <= j:
                a[i], a[j] = a[j], a[i]
                i += 1
                j -= 1

        if low < j:
            stack.append((low, j))
        if i < high:
            stack.append((i, high))


def main():
    input = sys.stdin.buffer.readline

    n = int(input())
    points = list(map(int, input().split()))

    quick_sort(points)

    min_diff = min(points[i + 1] - points[i]
                   for i in range(n - 1))

    result = []
    for i in range(n - 1):
        if points[i + 1] - points[i] == min_diff:
            result.append(str(points[i]))
            result.append(str(points[i + 1]))

    sys.stdout.write(" ".join(result) + "\n")


if __name__ == "__main__":
    main()