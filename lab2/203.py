n = int(input())
numbers = list(map(int, input().split()))

total = 0
for i in range(n):
    total += numbers[i]

print(total)
