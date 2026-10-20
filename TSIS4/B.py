
def quick_sort(a, low, high):
    if low >= high:
        return

    pivot = a[(low + high) // 2]
    i = low
    j = high

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
        quick_sort(a, low, j)

    if i < high:
        quick_sort(a, i, high)


n, m = map(int, input().split())

a = list(map(int, input().split())) if n else []
b = list(map(int, input().split())) if m else []

quick_sort(a, 0, n - 1)
quick_sort(b, 0, m - 1)

i = 0
j = 0
result = []

while i < n and j < m:
    if a[i] == b[j]:
        result.append(a[i])
        i += 1
        j += 1
    elif a[i] < b[j]:
        i += 1
    else:
        j += 1

print(*result)