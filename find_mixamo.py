import re

with open('Models/character.fbx', 'rb') as f:
    data = f.read()

pos = 0
found = []
while len(found) < 20:
    p = data.find(b'mixamorig', pos)
    if p == -1: break
    found.append(p)
    pos = p + 9

for p in found[:10]:
    print(data[max(0, p-30):min(len(data), p+50)])
