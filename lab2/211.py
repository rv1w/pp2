n,l,r=list(map(int,input().split()))
a=list(map(int,input().split()))

while l < r:
    a[l-1], a[r-1] = a[r-1], a[l-1]
    l += 1
    r -= 1

print(*a)

