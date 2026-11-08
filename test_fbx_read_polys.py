import struct
import numpy as np

with open('Models/character.fbx', 'rb') as f:
    data = f.read()

pos_v = data.find(b'Vertices')
# Just after Vertices is PolygonVertexIndex
pos_p = data.find(b'PolygonVertexIndex', pos_v)
hdr = data[pos_p-13:pos_p]
end_off, num_props, prop_len, name_len = struct.unpack('<IIIB', hdr)
print(f"PolygonVertexIndex: num_props={num_props}, prop_len={prop_len}")
props_data = data[pos_p + 18 : pos_p + 18 + prop_len]
# Each is 'I' + 4 bytes int32 (5 bytes each)
poly_indices = np.frombuffer(props_data, dtype=[('type', 'S1'), ('val', '<i4')])['val']
print("Primeiros 12 indices:", poly_indices[:12])

# Convert FBX polygon indices (triangles and quads) to pure triangle indices
triangles = []
current_poly = []
for idx in poly_indices:
    if idx < 0:
        current_poly.append(~idx)
        if len(current_poly) == 3:
            triangles.extend(current_poly)
        elif len(current_poly) == 4:
            # Quad -> 2 tris
            p0, p1, p2, p3 = current_poly
            triangles.extend([p0, p1, p2, p0, p2, p3])
        current_poly = []
    else:
        current_poly.append(idx)

triangles = np.array(triangles, dtype=np.uint32)
print(f"Total de triangulos montados: {len(triangles)//3} ({len(triangles)} indices)")

# Let's inspect UVs
pos_uv = data.find(b'UVIndex', pos_p)
if pos_uv != -1:
    hdr_uv = data[pos_uv-13:pos_uv]
    end_off, num_uv_props, prop_len, name_len = struct.unpack('<IIIB', hdr_uv)
    print(f"UVIndex: num_props={num_uv_props}")
else:
    print("No UVIndex, direct UV mapping?")
