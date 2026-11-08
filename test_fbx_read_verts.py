import struct
import numpy as np

with open('Models/character.fbx', 'rb') as f:
    data = f.read()

pos_v = data.find(b'Vertices')
# Read node header
# 13 bytes before "Vertices":
hdr = data[pos_v-13:pos_v]
end_off, num_props, prop_len, name_len = struct.unpack('<IIIB', hdr)
print(f"Node Vertices: num_props={num_props}, prop_len={prop_len}, end_off={end_off}")

# Each prop is 9 bytes: 'D' + 8 bytes double
props_data = data[pos_v + 8 : pos_v + 8 + prop_len]
# Verify
print("Primeiros 27 bytes:", props_data[:27])
# Extract all doubles:
# It's an array of (b'D', double)
# Slicing: props_data is 9 * num_props
# Let's verify type char:
type_chars = props_data[0::9]
print("Todos sao 'D'?", all(c == ord('D') for c in type_chars[:100]))

# Extract doubles fast with numpy
raw_doubles = np.frombuffer(props_data, dtype=[('type', 'S1'), ('val', '<f8')])['val']
print(f"Total de doubles: {len(raw_doubles)} -> {len(raw_doubles)//3} vertices")
verts = raw_doubles.reshape(-1, 3)
print("Min bounds:", verts.min(axis=0))
print("Max bounds:", verts.max(axis=0))
print("Extents:", verts.max(axis=0) - verts.min(axis=0))
