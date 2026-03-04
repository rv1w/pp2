import re

text = input()

result = re.findall(r'[A-Z][a-z]*', text)

print("Split result:", result)