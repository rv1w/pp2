import re

pattern = r'^a.*b$'

text = input()

if re.match(pattern, text):
    print("Match found")
else:
    print("No match")