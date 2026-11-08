with open('Models/character.fbx', 'rb') as f:
    data = f.read()

pos = data.find(b'Vertices')
print("Bytes antes de Vertices (16):", data[pos-16:pos])
print("Bytes apos Vertices (32):", data[pos+8:pos+40])
