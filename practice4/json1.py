import json

with open("sample-data.json") as file:
    data = json.load(file)

print("Interface status")
print("="*80)
print("DN"," "*40,"Description"," "*5,"speed"," "*2,"MTU")
print("-"*80)

for item in data["imdata"]:
    attributes = item["l1PhysIf"]["attributes"]
    
    dn = attributes.get("dn", "")
    descr = attributes.get("descr", "")
    speed = attributes.get("speed", "")
    mtu = attributes.get("mtu", "")
    
    print(f"{dn:20} {descr:17} {speed:10} {mtu:5}")