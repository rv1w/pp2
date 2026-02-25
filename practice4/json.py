import json

with open("simple-data.json") as file:
    data = json.load(file)

print("Interface status")
print("="*50)
print("DN"," "*20,"Description"," "*5,"speed"," "*2,"MTU")
print("-"*50)
