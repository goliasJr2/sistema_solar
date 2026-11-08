with open('Models/character.fbx', 'rb') as f:
    data = f.read()

pos = data.find(b'mixamorig:Hips')
print(repr(data[pos:pos+100]))
