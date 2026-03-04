import re

pattern = r'^ab*$'

text = input()

if re.match(pattern, text):
    print("Match found")
else:
    print("No match")