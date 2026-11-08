import struct
import os

def read_property_fast(f):
    type_char = f.read(1)
    if not type_char:
        return None
    tc = chr(type_char[0])
    if tc == 'Y':
        return struct.unpack('<h', f.read(2))[0]
    elif tc == 'C':
        return struct.unpack('<?', f.read(1))[0]
    elif tc == 'I':
        return struct.unpack('<i', f.read(4))[0]
    elif tc == 'F':
        return struct.unpack('<f', f.read(4))[0]
    elif tc == 'D':
        return struct.unpack('<d', f.read(8))[0]
    elif tc == 'L':
        return struct.unpack('<q', f.read(8))[0]
    elif tc == 'S':
        slen = struct.unpack('<I', f.read(4))[0]
        sbytes = f.read(slen)
        return sbytes.decode('utf-8', errors='ignore')
    elif tc == 'R':
        rlen = struct.unpack('<I', f.read(4))[0]
        f.seek(rlen, 1)
        return f"<raw {rlen}>"
    elif tc in ('f', 'd', 'i', 'l', 'b', 'c'):
        array_len, encoding, compressed_len = struct.unpack('<III', f.read(12))
        f.seek(compressed_len, 1)
        return f"Array<{tc}>[{array_len}]"
    else:
        return f"Unknown<{tc}>"

def inspect_fast(filepath):
    print("=" * 70, flush=True)
    print(f"FICHEIRO: {os.path.basename(filepath)} ({os.path.getsize(filepath)/(1024*1024):.2f} MB)", flush=True)
    with open(filepath, 'rb') as f:
        magic = f.read(23)
        if not magic.startswith(b'Kaydara FBX Binary'):
            print("Not binary FBX", flush=True)
            return
        version = struct.unpack('<I', f.read(4))[0]
        is_64 = version >= 7500
        print(f"Versao: {version} (64bit={is_64})", flush=True)

        objects = {}
        models = []
        geoms = []
        deformers = []
        materials = []
        textures = []
        takes = []

        def parse_scope(end_scope):
            while f.tell() < end_scope:
                pos = f.tell()
                if is_64:
                    hdr = f.read(25)
                    if len(hdr) < 25: break
                    end_off, num_p, p_len, n_len = struct.unpack('<QQIB', hdr)
                else:
                    hdr = f.read(13)
                    if len(hdr) < 13: break
                    end_off, num_p, p_len, n_len = struct.unpack('<IIIB', hdr)
                
                if end_off == 0:
                    break
                
                name = f.read(n_len).decode('ascii', errors='ignore')
                props = []
                for _ in range(num_p):
                    props.append(read_property_fast(f))

                if name == 'Model':
                    models.append(props)
                elif name == 'Geometry':
                    geoms.append(props)
                elif name == 'Deformer':
                    deformers.append(props)
                elif name == 'Material':
                    materials.append(props)
                elif name == 'Texture':
                    textures.append(props)
                elif name in ('Take', 'AnimationStack', 'AnimationLayer'):
                    takes.append((name, props))

                # Recursively parse children if any
                if f.tell() < end_off:
                    parse_scope(end_off)
                f.seek(end_off)

        file_len = os.path.getsize(filepath)
        parse_scope(file_len - 160)

        print(f"  Geometrias ({len(geoms)}): {[g[:2] for g in geoms[:8]]}", flush=True)
        print(f"  Modelos/Nodes ({len(models)}): Total = {len(models)}", flush=True)
        # Separar bones
        bones = [m for m in models if len(m) > 1 and any(k in str(m[1]).lower() for k in ['hip', 'spine', 'head', 'neck', 'arm', 'leg', 'hand', 'foot', 'shoulder', 'jaw', 'eye', 'clavicle', 'mixamorig'])]
        print(f"  Bones detectados ({len(bones)}): {[b[1] if len(b)>1 else b for b in bones[:10]]}", flush=True)
        print(f"  Deformers/Skins ({len(deformers)}): {[d[:2] for d in deformers[:8]]}", flush=True)
        print(f"  Materiais ({len(materials)}): {[m[:2] for m in materials[:5]]}", flush=True)
        print(f"  Texturas ({len(textures)}): {[t[:2] for t in textures[:5]]}", flush=True)
        print(f"  Animacoes/Takes ({len(takes)}): {takes}", flush=True)

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
    p = os.path.join('Models', name)
    if os.path.exists(p):
        try:
            inspect_fast(p)
        except Exception as e:
            print(f"Erro em {name}: {e}", flush=True)
