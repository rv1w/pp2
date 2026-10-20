
def quick_sort(a, low, high):
    if low >= high:
        return

    pivot = a[(low + high) // 2]
    i = low
    j = high

    while i <= j:
        while a[i] > pivot:
            i += 1
        while a[j] < pivot:
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

matrix = []
for _ in range(n):
    matrix.append(list(map(int, input().split())))

for j in range(m):
    column = []

    for i in range(n):
        column.append(matrix[i][j])

    quick_sort(column, 0, n - 1)

    for i in range(n):
        matrix[i][j] = column[i]

for row in matrix:
    print(*row)