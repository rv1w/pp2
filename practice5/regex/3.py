import re

pattern = r'\b[a-z]+_[a-z]+\b'

text = input()

matches = re.findall(pattern, text)
print("Matches:", matches)