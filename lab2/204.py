n = int(input())
numbers = list(map(int, input().split()))

total = 0
for i in range(n):
    if numbers[i]>0:
        total+=1

print(total)
