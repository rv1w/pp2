import re

pattern = r'\b[A-Z][a-z]+\b'

text = input()

matches = re.findall(pattern, text)
print("Matches:", matches)