n = int(input())
numbers = list(map(int, input().split()))

maxV=-1000000000000000

pos=0

for i in range(n):
    if numbers[i]>maxV:
        maxV = numbers[i]
        pos=i

print(pos+1)