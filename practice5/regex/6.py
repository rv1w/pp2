import re

pattern = r'[ ,.]'

text = input()

result = re.sub(pattern, ":", text)
print("Result:", result)