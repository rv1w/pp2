import re

def snake_to_camel(text):
    return re.sub(r'_([a-z])', lambda m: m.group(1).upper(), text)

text = input()

print("CamelCase:", snake_to_camel(text))