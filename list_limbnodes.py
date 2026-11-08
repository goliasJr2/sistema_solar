import re

with open('Models/character.fbx', 'rb') as f:
    data = f.read()

pattern = re.compile(rb'mixamorig:([a-zA-Z0-9_\-]+)\x00\x01ModelS\x08\x00\x00\x00LimbNode')
bones = [m.group(1).decode('ascii') for m in pattern.finditer(data)]
print(f"Total de ossos do esqueleto ({len(bones)}):")
for i, b in enumerate(bones):
    print(f"  {i+1:2d}. {b}")
