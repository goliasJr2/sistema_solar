import os
import re
import struct

def inspect_file(filepath):
    print("=" * 70)
    print(f"FICHEIRO: {os.path.basename(filepath)}")
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"Tamanho: {size_mb:.2f} MB")
    
    with open(filepath, 'rb') as f:
        data = f.read()

    header = data[:27]
    if header.startswith(b'Kaydara FBX Binary'):
        version = struct.unpack('<I', header[23:27])[0]
        print(f"Tipo: Binario FBX (Versao {version})")
    else:
        print("Tipo: Nao e FBX binario padrao")
        version = 0

    # 1. Procurar Meshes e Geometrias
    # No FBX: 'Geometry::' ou 'Model::' com subtype 'Mesh'
    geom_matches = re.findall(b'Geometry::([^\x00\x01,\";]+)', data)
    geometries = sorted(list(set(g.decode('utf-8', errors='ignore') for g in geom_matches)))
    print(f"Geometrias encontradas ({len(geometries)}): {geometries[:10]}")

    # 2. Procurar Model nodes (Bones, Meshes, Nulls, Locators)
    model_matches = re.findall(b'Model::([^\x00\x01,\";]+)', data)
    models = sorted(list(set(m.decode('utf-8', errors='ignore') for m in model_matches)))
    print(f"Total de Model Nodes: {len(models)}")
    
    # Separar bones dos outros nodes
    bone_keywords = ['hip', 'spine', 'head', 'neck', 'arm', 'leg', 'foot', 'hand', 'finger', 'shoulder', 'toe', 'clavicle', 'jaw', 'eye']
    bones = [m for m in models if any(k in m.lower() for k in bone_keywords) or 'mixamo' in m.lower() or 'bip' in m.lower() or 'root' in m.lower()]
    print(f"Ossos / Bones detectados ({len(bones)}): {bones[:15]}")

    # 3. Procurar Deformers (Skins, Clusters, BlendShapes / Morph Targets)
    deformer_matches = re.findall(b'Deformer::([^\x00\x01,\";]+)', data)
    deformers = sorted(list(set(d.decode('utf-8', errors='ignore') for d in deformer_matches)))
    blendshapes = [d for d in deformers if 'blendshape' in d.lower() or 'morph' in d.lower() or 'shape' in d.lower()]
    clusters = [d for d in deformers if 'cluster' in d.lower() or 'subdeformer' in d.lower()]
    skins = [d for d in deformers if 'skin' in d.lower()]
    print(f"Deformers Totais: {len(deformers)} (Skins: {len(skins)}, Clusters/SkinWeights: {len(clusters)}, BlendShapes/Morphs: {len(blendshapes)})")
    if blendshapes:
        print(f"  Exemplos de BlendShapes: {blendshapes[:10]}")

    # 4. Procurar AnimStacks e AnimLayers
    anim_stacks = re.findall(b'AnimationStack::([^\x00\x01,\";]+)', data)
    anim_stacks = sorted(list(set(a.decode('utf-8', errors='ignore') for a in anim_stacks)))
    takes = re.findall(b'Take::([^\x00\x01,\";]+)', data)
    takes = sorted(list(set(t.decode('utf-8', errors='ignore') for t in takes)))
    all_anims = anim_stacks + takes
    print(f"Animacoes embutidas ({len(all_anims)}): {all_anims}")

    # 5. Procurar Materiais e Texturas
    mat_matches = re.findall(b'Material::([^\x00\x01,\";]+)', data)
    materials = sorted(list(set(m.decode('utf-8', errors='ignore') for m in mat_matches)))
    tex_matches = re.findall(b'Texture::([^\x00\x01,\";]+)', data)
    textures = sorted(list(set(t.decode('utf-8', errors='ignore') for t in tex_matches)))
    print(f"Materiais ({len(materials)}): {materials}")
    print(f"Texturas ({len(textures)}): {textures}")

    # 6. Procurar caminhos de ficheiros de textura ou texturas embutidas
    tex_files = re.findall(rb'[A-Za-z0-9_\-\\\/ ]+\.(?:png|jpg|jpeg|tga|bmp|dds)', data, re.IGNORECASE)
    tex_files_clean = sorted(list(set(tf.decode('utf-8', errors='ignore').replace('\\', '/') for tf in tex_files)))
    print(f"Referencias a ficheiros de imagem ({len(tex_files_clean)}): {tex_files_clean[:5]}")

models_dir = 'Models'
target_files = [
    'character.fbx',
    'character (1).fbx',
    'character (2).fbx',
    'character (3).fbx',
    'goblin_d_shareyko.fbx',
    'Mutant.fbx',
    'Warrok W Kurniawan.fbx'
]

for name in target_files:
    p = os.path.join(models_dir, name)
    if os.path.exists(p):
        inspect_file(p)
