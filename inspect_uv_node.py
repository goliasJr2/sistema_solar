import struct

with open('Models/character.fbx', 'rb') as f:
    data = f.read()

pos_p = data.find(b'PolygonVertexIndex')
pos_uv = data.find(b'LayerElementUV', pos_p)
print("LayerElementUV pos:", pos_uv)
print("Bytes apos LayerElementUV (300):", repr(data[pos_uv:pos_uv+300]))
