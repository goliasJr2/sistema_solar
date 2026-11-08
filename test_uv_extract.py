import struct
import numpy as np

with open('Models/character.fbx', 'rb') as f:
    data = f.read()

pos_p = data.find(b'\x12PolygonVertexIndex')
pos_n = data.find(b'\x07Normals', pos_p)
pos_uv = data.find(b'\x02UV', pos_n)
pos_uvi = data.find(b'\x07UVIndex', pos_uv)

print("pos_uv:", pos_uv)
hdr_uv = data[pos_uv-12:pos_uv+1]
end_off, num_props, prop_len, name_len = struct.unpack('<IIIB', hdr_uv)
name = data[pos_uv+1:pos_uv+1+name_len].decode('ascii')
print(f"Node: {name}, props: {num_props}, prop_len: {prop_len}")
props_data = data[pos_uv+1+name_len : pos_uv+1+name_len+prop_len]
print(f"props_data len: {len(props_data)} (expected {num_props * 9})")

raw_uv = np.frombuffer(props_data, dtype=[('type', 'S1'), ('val', '<f8')])['val']
uvs = raw_uv.reshape(-1, 2)
print("UV shape:", uvs.shape)
print("Sample UVs:", uvs[:3])
