import struct
import os
import re

with open('Models/character.fbx', 'rb') as f:
    data = f.read()

# Procura caminhos de imagem como fbm/Remy_...
pattern = re.compile(rb'fbm[\\/](Remy_[a-zA-Z0-9_\-]+\.png)', re.IGNORECASE)
found = set(m.group(1).decode('ascii') for m in pattern.finditer(data))
print("Ficheiros de textura Remy encontrados:")
for name in sorted(found):
    print("  ", name)

# Também procura nomes dos nós Video
v_pattern = re.compile(rb'Video::(Video\s+[^\x00\x01,\";]+|Clip\s+[^\x00\x01,\";]+|[^\x00\x01,\";]+Clip|[^\x00\x01,\";]+Video|[a-zA-Z0-9_\-]+)', re.IGNORECASE)
