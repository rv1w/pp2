'''1. enumerate()

Loops through a list and gives index + value'''


fruits = ["apple", "banana", "cherry"]

for i, fruit in enumerate(fruits):
    print(i, fruit)


'''zip()

Combines multiple lists into pairs (tuples)

Stops at the shortest list'''

names = ["Alice", "Bob", "Charlie"]
ages = [25, 30, 22]

for name, age in zip(names, ages):
    print(f"{name} is {age} years old")