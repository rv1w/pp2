import re

def camel_to_snake(text):
    return re.sub(r'(?<!^)([A-Z])', r'_\1', text).lower()

text = input()

print("Snake_case:", camel_to_snake(text))