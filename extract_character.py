import struct
import numpy as np
import os
import shutil
import trimesh
from PIL import Image

def read_doubles_node(data, tag_pos, name_len):
    hdr = data[tag_pos - 12 : tag_pos + 1]
    end_off, num_props, prop_len, n_len = struct.unpack('<IIIB', hdr)
    props_start = tag_pos + 1 + name_len
    props_data = data[props_start : props_start + prop_len]
    return np.frombuffer(props_data, dtype=[('type', 'S1'), ('val', '<f8')])['val']

def read_ints_node(data, tag_pos, name_len):
    hdr = data[tag_pos - 12 : tag_pos + 1]
    end_off, num_props, prop_len, n_len = struct.unpack('<IIIB', hdr)
    props_start = tag_pos + 1 + name_len
    props_data = data[props_start : props_start + prop_len]
    return np.frombuffer(props_data, dtype=[('type', 'S1'), ('val', '<i4')])['val']

def extract_and_build_glb():
    fbx_path = 'Models/character.fbx'
    with open(fbx_path, 'rb') as f:
        data = f.read()

    submesh_names = [
        "Shoes",
        "Tops",
        "Bottoms",
        "Hair",
        "Body",
        "Eyelashes",
        "Eyes"
    ]

    texture_map = {
        "Shoes": "Remy_Shoes_Diffuse.png",
        "Tops": "Remy_Top_Diffuse.png",
        "Bottoms": "Remy_Bottom_Diffuse.png",
        "Hair": "Remy_Hair_Diffuse.png",
        "Body": "Remy_Body_Diffuse.png",
        "Eyelashes": "Remy_Body_Diffuse.png",
        "Eyes": "Remy_Body_Diffuse.png"
    }

    tex_src_map = {
        "Remy_Shoes_Diffuse.png": "Models/character_textures/tex_0_1024x1024_RGB.png",
        "Remy_Top_Diffuse.png": "Models/character_textures/tex_4_1024x1024_RGB.png",
        "Remy_Bottom_Diffuse.png": "Models/character_textures/tex_8_1024x1024_RGB.png",
        "Remy_Hair_Diffuse.png": "Models/character_textures/tex_12_1024x1024_RGB.png",
        "Remy_Body_Diffuse.png": "Models/character_textures/tex_17_2048x2048_RGB.png"
    }

    out_tex_dir = 'textures/guide'
    os.makedirs(out_tex_dir, exist_ok=True)
    for dst_name, src_path in tex_src_map.items():
        dst_path = os.path.join(out_tex_dir, dst_name)
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)

    v_pos = 0
    all_meshes = []

    for name in submesh_names:
        pos_v = data.find(b'\x08Vertices', v_pos)
        if pos_v == -1: break
        v_pos = pos_v + 9

        verts = read_doubles_node(data, pos_v, 8).reshape(-1, 3).astype(np.float32)

        pos_p = data.find(b'\x12PolygonVertexIndex', pos_v)
        poly_indices = read_ints_node(data, pos_p, 18)

        pos_n = data.find(b'\x07Normals', pos_p)
        normals = read_doubles_node(data, pos_n, 7).reshape(-1, 3).astype(np.float32)

        pos_uv = data.find(b'\x02UV', pos_n)
        uvs = read_doubles_node(data, pos_uv, 2).reshape(-1, 2).astype(np.float32)

        pos_uvi = data.find(b'\x07UVIndex', pos_uv)
        uv_indices = read_ints_node(data, pos_uvi, 7)

        print(f"\nExtraindo '{name}':")
        print(f"  Vértices brutos: {len(verts)}, Faces/Polígonos: {len(poly_indices)}, Normais: {len(normals)}, UVs: {len(uvs)}")

        final_positions = []
        final_normals = []
        final_uvs = []
        final_indices = []
        vertex_cache = {}

        current_poly = []
        current_uv_poly = []
        current_pv_poly = []
        pv_counter = 0

        for p_idx, u_idx in zip(poly_indices, uv_indices):
            is_end = p_idx < 0
            actual_v = ~p_idx if is_end else p_idx

            current_poly.append(actual_v)
            current_uv_poly.append(u_idx)
            current_pv_poly.append(pv_counter)
            pv_counter += 1

            if is_end:
                if len(current_poly) == 3:
                    tri_tuples = [(0, 1, 2)]
                elif len(current_poly) == 4:
                    tri_tuples = [(0, 1, 2), (0, 2, 3)]
                else:
                    tri_tuples = [(0, t, t + 1) for t in range(1, len(current_poly) - 1)]

                for t0, t1, t2 in tri_tuples:
                    for t_idx in (t0, t1, t2):
                        v_i = current_poly[t_idx]
                        u_i = current_uv_poly[t_idx]
                        pv_i = current_pv_poly[t_idx]

                        pos = verts[v_i]
                        norm = normals[pv_i] if len(normals) == len(poly_indices) else normals[v_i]
                        # Invert V coordinate for OpenGL convention
                        uv = np.array([uvs[u_i][0], 1.0 - uvs[u_i][1]], dtype=np.float32)

                        key = (v_i, u_i, pv_i if len(normals) == len(poly_indices) else v_i)
                        if key in vertex_cache:
                            final_indices.append(vertex_cache[key])
                        else:
                            new_idx = len(final_positions)
                            vertex_cache[key] = new_idx
                            final_positions.append(pos)
                            final_normals.append(norm)
                            final_uvs.append(uv)
                            final_indices.append(new_idx)

                current_poly = []
                current_uv_poly = []
                current_pv_poly = []

        pos_arr = np.array(final_positions, dtype=np.float32)
        norm_arr = np.array(final_normals, dtype=np.float32)
        uv_arr = np.array(final_uvs, dtype=np.float32)
        idx_arr = np.array(final_indices, dtype=np.uint32)

        print(f"  Vértices GPU: {len(pos_arr):,}, Triângulos: {len(idx_arr)//3:,}")

        tex_filename = texture_map.get(name, "Remy_Body_Diffuse.png")
        tex_path = os.path.join(out_tex_dir, tex_filename)
        img = Image.open(tex_path)
        visual = trimesh.visual.TextureVisuals(uv=uv_arr, image=img)
        mesh = trimesh.Trimesh(
            vertices=pos_arr,
            faces=idx_arr.reshape(-1, 3),
            vertex_normals=norm_arr,
            visual=visual,
            process=False
        )
        mesh.metadata['name'] = name
        all_meshes.append((name, mesh))

    # Export combined scene as GLB into Models/guide_remy.glb
    scene = trimesh.Scene()
    for name, m in all_meshes:
        scene.add_geometry(m, node_name=name)

    out_glb = 'Models/guide_remy.glb'
    scene.export(out_glb)
    print(f"\n[SUCESSO] Guia Virtual exportado com 7 submalhas e texturas para: {out_glb}")
    print(f"Tamanho do GLB: {os.path.getsize(out_glb)/(1024*1024):.2f} MB")

if __name__ == '__main__':
    extract_and_build_glb()
