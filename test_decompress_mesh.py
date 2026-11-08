import struct
import zlib
import numpy as np

with open('Models/character.fbx', 'rb') as f:
    data = f.read()

# Let's find Vertices and decompress
pos = data.find(b'Vertices')
# Just before Vertices is the node header: end_offset(4), num_props(4), prop_list_len(4), name_len(1), name="Vertices"(8)
# After "Vertices": type_char 'd' (1 byte), array_len (4), encoding (4), compressed_len (4), payload
after_name = pos + 8
type_char = chr(data[after_name])
array_len, encoding, comp_len = struct.unpack('<III', data[after_name+1 : after_name+13])
print(f"Vertices: type={type_char}, array_len={array_len}, encoding={encoding}, comp_len={comp_len}")

payload = data[after_name+13 : after_name+13+comp_len]
if encoding == 1:
    raw = zlib.decompress(payload)
else:
    raw = payload

verts = np.frombuffer(raw, dtype=np.float64)
print(f"Vértices descompactados: {len(verts)} floats -> {len(verts)//3} pontos 3D!")
print("Primeiros 3 pontos:", verts[:9])
