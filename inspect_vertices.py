import struct
import os

with open('Models/character.fbx', 'rb') as f:
    data = f.read()

# Let's search for "Vertices" or "PolygonVertexIndex"
idx_v = 0
found_vertices = []
while True:
    pos = data.find(b'Vertices', idx_v)
    if pos == -1: break
    found_vertices.append(pos)
    idx_v = pos + 8

print(f"Ocorrencias de 'Vertices': {len(found_vertices)}")

# Let's inspect the first occurrence
for p in found_vertices[:8]:
    # Look back for Model or Geometry name
    pre = data[max(0, p - 300):p]
    print("--- Proximo a Vertices ---")
    print(pre[-150:])
