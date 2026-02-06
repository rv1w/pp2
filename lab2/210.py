a = int(input())
n = list(map(int, input().split()))

n.sort()
n.reverse()

print(*n)