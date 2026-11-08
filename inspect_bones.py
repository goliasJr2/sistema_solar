import re
import struct
import numpy as np

with open('Models/character.fbx', 'rb') as f:
    data = f.read()

# Find all Clusters
clusters = re.findall(rb'Deformer::Cluster\s+mixamorig:([a-zA-Z0-9_\-]+)\x00\x01SubDeformer', data)
unique_bones = []
for b in clusters:
    bname = b.decode('ascii', errors='ignore')
    if bname not in unique_bones:
        unique_bones.append(bname)

print(f"Total de ossos unicos nos Clusters ({len(unique_bones)}):")
for i, b in enumerate(unique_bones):
    print(f"  {i}: {b}")
