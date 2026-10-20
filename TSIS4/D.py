
def quick_sort(dates, low, high):
    if low >= high:
        return

    pivot = dates[(low + high) // 2]
    i = low
    j = high

    while i <= j:
        while dates[i][1] < pivot[1]:
            i += 1
        while dates[j][1] > pivot[1]:
            j -= 1

        if i <= j:
            dates[i], dates[j] = dates[j], dates[i]
            i += 1
            j -= 1

    if low < j:
        quick_sort(dates, low, j)
    if i < high:
        quick_sort(dates, i, high)


n = int(input())
dates = []

for _ in range(n):
    s = input().strip()
    day, month, year = map(int, s.split('-'))

    key = year * 10000 + month * 100 + day
    dates.append((s, key))

quick_sort(dates, 0, n - 1)

for date in dates:
    print(date[0])