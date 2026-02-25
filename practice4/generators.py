#1
# def square_generator(n):
#     for i in range(n + 1):
#         yield i * i

# a=int(input())

# for num in square_generator(a):
#     print(num)

#2
# def even(n):
#     for i in range(n + 1):
#         if i % 2 == 0:
#             yield i


# n = int(input())

# print(",".join(str(num) for num in even(n)))

#3
# def div_by3and4(n):
#     for i in range(n + 1):
#         if i%3==0 and i%4==0:
#             yield i


# n = int(input())

# for num in div_by3and4(n):
#     print(num)

#4
# def squares(a, b):
#     for i in range(a, b + 1):
#         yield i * i

# for x in squares(3, 7):
#     print(x)

#5
# def count(n):
#     while n >= 0:
#         yield n
#         n -= 1

# for num in count(5):
#     print(num)