a = int(input())
n = list(map(int, input().split()))

maxV=n[0]
minV=n[0]


for i in range(a):
    if n[i]>maxV:
        maxV = n[i]
    if n[i]<minV:
        minV=n[i]

for i in range(a):
    if n[i] == maxV:
        n[i] = minV

print(*n)