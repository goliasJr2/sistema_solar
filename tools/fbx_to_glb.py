"""
===============================================================================
Ferramenta: tools/fbx_to_glb.py
Descrição: Converte personagens .fbx (binário, versões 6.1 e 7.x) para .glb,
           o formato que o simulador lê através do trimesh.

Porquê existe:
  - O trimesh (usado pelo model_loader.py) não lê ficheiros .fbx.
  - Os personagens da Mixamo em Models/ vêm em .fbx; 4 deles estão no formato
    antigo FBX 6.1 (2006), que nem o Assimp suporta. Este leitor próprio lê
    diretamente a estrutura binária do FBX (árvore de nós) nas duas versões.

O que é extraído:
  - Malha (vértices + polígonos, triangulados em leque);
  - Coordenadas UV (mapeamentos ByPolygonVertex / ByVertex, Direct / IndexToDirect);
  - Material por polígono e a textura difusa de cada material
    (as imagens PNG/JPG vêm embutidas dentro do .fbx, nos nós "Video");
  - Transformação local da malha (Lcl Translation / Rotation / Scaling).
  Esqueleto, pesos e animações são ignorados: o personagem fica na pose
  em que foi exportado (normalmente a pose em T).

Normalização aplicada ao GLB gerado:
  - Eixo vertical = +Y; personagem de frente para +Z;
  - Altura total = 2.0 (de y = -1 aos pés até y = +1 no topo da cabeça),
    centrado em X/Z. O characters.py depois escala-o face ao planeta.

Uso (a partir da pasta do projeto, com o .venv):
  .venv\\Scripts\\python.exe tools\\fbx_to_glb.py                (converte a lista em CHARACTERS)
  .venv\\Scripts\\python.exe tools\\fbx_to_glb.py in.fbx out.glb  (converte um ficheiro)
  Acrescente --preview para gerar também uma imagem .png de verificação.
===============================================================================
"""

from __future__ import annotations

import io
import math
import struct
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import trimesh
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "Models"
OUT_DIR = MODELS_DIR / "characters"

# Ficheiro de origem -> nome do .glb gerado em Models/characters/
CHARACTERS: Dict[str, str] = {
    "Mutant.fbx": "mutant.glb",
    "Warrok W Kurniawan.fbx": "warrok.glb",
    "goblin_d_shareyko.fbx": "goblin.glb",
    "character (1).fbx": "vanguard.glb",
    "character (2).fbx": "ely.glb",
    "character (3).fbx": "maw.glb",
    "character.fbx": "remy.glb",
}

# Lado máximo das texturas no GLB (as originais têm até 4096 px; 1024 chega e
# mantém os ficheiros pequenos no repositório).
MAX_TEXTURE_SIZE = 1024


# =============================================================================
# 1. Leitor da árvore binária do FBX
# =============================================================================
@dataclass
class FBXNode:
    name: str
    props: list = field(default_factory=list)
    children: List["FBXNode"] = field(default_factory=list)

    def find(self, name: str) -> Optional["FBXNode"]:
        for c in self.children:
            if c.name == name:
                return c
        return None

    def find_all(self, name: str) -> List["FBXNode"]:
        return [c for c in self.children if c.name == name]

    def value(self, name: str, default=None):
        node = self.find(name)
        if node is None or not node.props:
            return default
        return node.props[0]

    def array(self, name: str) -> Optional[np.ndarray]:
        """Lista numérica de um filho. FBX 7 guarda-a como array compacto (uma só
        propriedade); FBX 6.1 guarda cada número como uma propriedade separada."""
        node = self.find(name)
        if node is None or not node.props:
            return None
        if len(node.props) == 1 and isinstance(node.props[0], np.ndarray):
            return node.props[0]
        return np.asarray(node.props)


_ARRAY_TYPES = {"f": "<f4", "d": "<f8", "l": "<i8", "i": "<i4", "b": "u1"}
_SCALAR_TYPES = {"Y": "<h", "C": "?", "I": "<i", "F": "<f", "D": "<d", "L": "<q"}


def _read_property(data: bytes, pos: int):
    t = chr(data[pos])
    pos += 1
    if t in _SCALAR_TYPES:
        fmt = _SCALAR_TYPES[t]
        size = struct.calcsize(fmt)
        return struct.unpack_from(fmt, data, pos)[0], pos + size
    if t in _ARRAY_TYPES:
        length, encoding, comp_len = struct.unpack_from("<III", data, pos)
        pos += 12
        raw = data[pos:pos + comp_len]
        pos += comp_len
        if encoding == 1:
            raw = zlib.decompress(raw)
        return np.frombuffer(raw, dtype=_ARRAY_TYPES[t], count=length), pos
    if t in ("S", "R"):
        (length,) = struct.unpack_from("<I", data, pos)
        pos += 4
        raw = data[pos:pos + length]
        pos += length
        if t == "S":
            return raw.decode("utf-8", errors="replace"), pos
        return bytes(raw), pos
    raise ValueError(f"Tipo de propriedade FBX desconhecido: {t!r} na posição {pos - 1}")


def _read_node(data: bytes, pos: int, wide: bool) -> Tuple[Optional[FBXNode], int]:
    if wide:
        end, num_props, _ = struct.unpack_from("<QQQ", data, pos)
        pos += 24
    else:
        end, num_props, _ = struct.unpack_from("<III", data, pos)
        pos += 12
    name_len = data[pos]
    pos += 1
    if end == 0:  # registo nulo: fim da lista de filhos
        return None, pos
    name = data[pos:pos + name_len].decode("ascii", errors="replace")
    pos += name_len
    node = FBXNode(name)
    for _ in range(num_props):
        val, pos = _read_property(data, pos)
        node.props.append(val)
    while pos < end:
        child, pos = _read_node(data, pos, wide)
        if child is None:
            break
        node.children.append(child)
    return node, end


def read_fbx(path: Path) -> Tuple[int, FBXNode]:
    data = path.read_bytes()
    if not data.startswith(b"Kaydara FBX Binary"):
        raise ValueError(f"{path.name}: só FBX binário é suportado (este parece ser ASCII).")
    (version,) = struct.unpack_from("<I", data, 23)
    wide = version >= 7500
    root = FBXNode("root")
    pos = 27
    while pos < len(data):
        node, pos = _read_node(data, pos, wide)
        if node is None:
            break
        root.children.append(node)
    return version, root


# =============================================================================
# 2. Interpretação: malhas, materiais e texturas
# =============================================================================
def _clean_name(s) -> str:
    """'Nome\\x00\\x01Model' (FBX 7) ou 'Model::Nome' (FBX 6) -> 'Nome'."""
    s = str(s)
    if "\x00\x01" in s:
        return s.split("\x00\x01")[0]
    if "::" in s:
        return s.split("::", 1)[1]
    return s


def _props_table(node: FBXNode) -> Dict[str, list]:
    """Lê Properties70 (FBX 7) ou Properties60 (FBX 6) para {nome: valores}."""
    table: Dict[str, list] = {}
    for key in ("Properties70", "Properties60"):
        block = node.find(key)
        if block is None:
            continue
        for p in block.children:
            if p.props:
                skip = 4 if key == "Properties70" else 3
                table[str(p.props[0])] = p.props[skip:]
    return table


def _euler_xyz_matrix(rx: float, ry: float, rz: float) -> np.ndarray:
    """Rotação Euler XYZ do FBX (graus): R = Rz * Ry * Rx."""
    rx, ry, rz = (math.radians(v) for v in (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    rot_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    rot_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rot_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rot_z @ rot_y @ rot_x


def _apply_transform(verts: np.ndarray, props: Dict[str, list], prefix: str) -> np.ndarray:
    def vec(name, default):
        v = props.get(prefix + name)
        return np.array([float(x) for x in v[:3]]) if v and len(v) >= 3 else np.array(default, dtype=float)

    s = vec("Scaling", [1, 1, 1])
    r = vec("Rotation", [0, 0, 0])
    t = vec("Translation", [0, 0, 0])
    return (verts * s) @ _euler_xyz_matrix(*r).T + t


def _layer_values(layer: FBXNode, data_key: str, index_key: str, width: int,
                  poly_vert_idx: np.ndarray) -> Optional[np.ndarray]:
    """Expande um LayerElement para um valor por vértice-de-polígono."""
    data = layer.array(data_key)
    if data is None:
        return None
    data = np.asarray(data, dtype=np.float64).reshape(-1, width)
    mapping = str(layer.value("MappingInformationType", "ByPolygonVertex"))
    reference = str(layer.value("ReferenceInformationType", "Direct"))
    index = layer.array(index_key)
    if reference in ("IndexToDirect", "Index") and index is not None:
        data = data[np.asarray(index, dtype=np.int64)]
    if mapping == "ByPolygonVertex":
        return data
    if mapping in ("ByVertex", "ByVertice", "ByControlPoint"):
        return data[poly_vert_idx]
    return None


@dataclass
class RawMesh:
    name: str
    vertices: np.ndarray            # (n_corners, 3) — um vértice por canto de triângulo
    uvs: Optional[np.ndarray]       # (n_corners, 2)
    material_ids: np.ndarray        # (n_tris,)
    material_names: List[str]       # índice local -> nome do material


def _extract_geometry(geom: FBXNode, name: str, material_names: List[str]) -> Optional[RawMesh]:
    verts = geom.array("Vertices")
    pvi = geom.array("PolygonVertexIndex")
    if verts is None or pvi is None or len(pvi) == 0:
        return None
    verts = np.asarray(verts, dtype=np.float64).reshape(-1, 3)
    pvi = np.asarray(pvi, dtype=np.int64)

    # Índices negativos marcam o último vértice de cada polígono: idx = ~valor
    is_end = pvi < 0
    corner_vert = np.where(is_end, ~pvi, pvi)

    uv_corner = None
    uv_layer = geom.find("LayerElementUV")
    if uv_layer is not None:
        uv_corner = _layer_values(uv_layer, "UV", "UVIndex", 2, corner_vert)
        if uv_corner is not None and len(uv_corner) != len(corner_vert):
            uv_corner = None

    # Material de cada polígono
    poly_starts = np.concatenate([[0], np.nonzero(is_end)[0][:-1] + 1])
    poly_ends = np.nonzero(is_end)[0]
    n_polys = len(poly_ends)
    poly_mat = np.zeros(n_polys, dtype=np.int64)
    mat_layer = geom.find("LayerElementMaterial")
    if mat_layer is not None:
        mats = mat_layer.array("Materials")
        mapping = str(mat_layer.value("MappingInformationType", "AllSame"))
        if mats is not None and len(mats) > 0:
            mats = np.asarray(mats, dtype=np.int64)
            if mapping == "ByPolygon" and len(mats) == n_polys:
                poly_mat = mats
            else:
                poly_mat[:] = mats[0]

    # Triangulação em leque de cada polígono: (v0, vi, vi+1)
    corners: List[int] = []
    tri_mat: List[int] = []
    for p in range(n_polys):
        s, e = poly_starts[p], poly_ends[p]
        for i in range(s + 1, e):
            corners.extend((s, i, i + 1))
            tri_mat.append(poly_mat[p])
    corners_arr = np.asarray(corners, dtype=np.int64)

    return RawMesh(
        name=name,
        vertices=verts[corner_vert[corners_arr]],
        uvs=None if uv_corner is None else uv_corner[corners_arr],
        material_ids=np.asarray(tri_mat, dtype=np.int64),
        material_names=material_names or ["default"],
    )


def extract_meshes(root: FBXNode) -> Tuple[List[RawMesh], Dict[str, Optional[bytes]]]:
    """Devolve as malhas (já com a transformação local) e {material: bytes da textura difusa}."""
    objects = root.find("Objects")
    if objects is None:
        raise ValueError("FBX sem secção Objects.")

    # Identificador de cada objeto: id numérico (FBX 7) ou nome completo (FBX 6)
    def obj_id(n: FBXNode):
        return n.props[0] if n.props else None

    by_id: Dict[object, FBXNode] = {obj_id(n): n for n in objects.children if n.props}

    # Ligações filho -> pai (e o nome da propriedade em ligações "OP")
    children_of: Dict[object, List[Tuple[object, Optional[str]]]] = {}
    parents_of: Dict[object, List[object]] = {}
    conns = root.find("Connections")
    if conns is not None:
        for c in conns.children:
            if len(c.props) < 3:
                continue
            child, parent = c.props[1], c.props[2]
            prop = str(c.props[3]) if len(c.props) > 3 else None
            children_of.setdefault(parent, []).append((child, prop))
            parents_of.setdefault(child, []).append(parent)

    # Imagens embutidas (nós Video com Content), indexadas pelo nome do ficheiro
    images: Dict[str, bytes] = {}
    for n in objects.children:
        if n.name != "Video":
            continue
        content = n.value("Content")
        if isinstance(content, (bytes, bytearray)) and len(content) > 16:
            for key in ("RelativeFilename", "Filename", "FileName"):
                fname = n.value(key)
                if fname:
                    images[Path(str(fname).replace("\\", "/")).name.lower()] = bytes(content)

    def texture_bytes(tex: FBXNode) -> Optional[bytes]:
        for key in ("RelativeFilename", "FileName", "Filename"):
            fname = tex.value(key)
            if fname:
                b = images.get(Path(str(fname).replace("\\", "/")).name.lower())
                if b:
                    return b
        return None

    def is_diffuse(fname: str) -> bool:
        f = fname.lower()
        return not any(k in f for k in ("normal", "specular", "gloss", "glow", "opacity", "emissive", "rough", "metal"))

    def diffuse_for_material(mat_id, mat_name: str) -> Optional[bytes]:
        tex_nodes = [(by_id.get(cid), prop) for cid, prop in children_of.get(mat_id, [])]
        tex_nodes = [(t, p) for t, p in tex_nodes if t is not None and t.name == "Texture"]
        # 1) ligação explícita à cor difusa
        for t, prop in tex_nodes:
            if prop and "diffuse" in prop.lower():
                b = texture_bytes(t)
                if b:
                    return b
        # 2) qualquer textura do material que não seja normal/specular/...
        for t, _ in tex_nodes:
            fname = str(t.value("RelativeFilename") or t.value("FileName") or "")
            if is_diffuse(fname):
                b = texture_bytes(t)
                if b:
                    return b
        # 3) FBX 6.1: texturas ligadas ao modelo ou sem ligação — escolhe pelo nome
        token = mat_name.lower().replace("_mat", "").replace("material", "").strip("_: ")
        candidates = [k for k in images if is_diffuse(k)]
        for k in candidates:
            if token and token.split(":")[-1][:5] in k:
                return images[k]
        diffuse_named = [k for k in candidates if "diffuse" in k]
        if diffuse_named:
            return images[diffuse_named[0]]
        return images[candidates[0]] if candidates else None

    meshes: List[RawMesh] = []
    textures: Dict[str, Optional[bytes]] = {}

    for model in objects.children:
        if model.name != "Model" or len(model.props) < 2 or str(model.props[-1]) != "Mesh":
            continue
        mid = obj_id(model)
        model_name = _clean_name(model.props[1] if len(model.props) >= 3 else model.props[0])

        # Materiais deste modelo, pela ordem das ligações (= índices do LayerElementMaterial)
        mat_ids = [cid for cid, _ in children_of.get(mid, []) if by_id.get(cid) is not None and by_id[cid].name == "Material"]
        mat_names = [f"{model_name}:{_clean_name(by_id[m].props[1] if len(by_id[m].props) >= 3 else by_id[m].props[0])}" for m in mat_ids]
        for m, mname in zip(mat_ids, mat_names):
            textures[mname] = diffuse_for_material(m, mname.split(":", 1)[1])

        # Geometria: nó Geometry ligado ao modelo (FBX 7) ou dentro do próprio Model (FBX 6)
        geom = model
        for cid, _ in children_of.get(mid, []):
            node = by_id.get(cid)
            if node is not None and node.name == "Geometry":
                geom = node
                break

        mesh = _extract_geometry(geom, model_name, mat_names)
        if mesh is None:
            continue
        if not mat_names:
            textures[mesh.material_names[0]] = diffuse_for_material(None, model_name)

        props = _props_table(model)
        mesh.vertices = _apply_transform(mesh.vertices, props, "Geometric")
        mesh.vertices = _apply_transform(mesh.vertices, props, "Lcl ")
        meshes.append(mesh)

    if not meshes:
        raise ValueError("Nenhuma malha encontrada no FBX.")
    return meshes, textures


# =============================================================================
# 3. Normalização e exportação para GLB
# =============================================================================
def _normalize(meshes: List[RawMesh]) -> None:
    """Põe o personagem de pé (+Y), centrado, com altura 2.0 e pés em y = -1."""
    all_v = np.concatenate([m.vertices for m in meshes])
    extents = all_v.max(0) - all_v.min(0)
    rot = np.eye(3)
    if extents[2] > extents[1] * 1.2:      # exportado com Z para cima
        rot = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], dtype=float)
    for m in meshes:
        m.vertices = m.vertices @ rot.T
    all_v = np.concatenate([m.vertices for m in meshes])
    lo, hi = all_v.min(0), all_v.max(0)
    height = max(hi[1] - lo[1], 1e-6)
    offset = np.array([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2])
    for m in meshes:
        m.vertices = (m.vertices - offset) * (2.0 / height) - np.array([0.0, 1.0, 0.0])


def _load_image(data: Optional[bytes]) -> Image.Image:
    if not data:
        return Image.new("RGB", (4, 4), (200, 200, 200))
    img = Image.open(io.BytesIO(data))
    img.load()
    img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
    if max(img.size) > MAX_TEXTURE_SIZE:
        img.thumbnail((MAX_TEXTURE_SIZE, MAX_TEXTURE_SIZE), Image.LANCZOS)
    # Se o canal alfa for todo opaco, descarta-o (evita marcar a malha como transparente)
    if img.mode == "RGBA" and img.getchannel("A").getextrema()[0] >= 250:
        img = img.convert("RGB")
    return img


def build_scene(meshes: List[RawMesh], textures: Dict[str, Optional[bytes]]) -> trimesh.Scene:
    scene = trimesh.Scene()
    cache: Dict[int, Image.Image] = {}
    for mesh in meshes:
        for local_idx, mat_name in enumerate(mesh.material_names):
            sel = np.nonzero(mesh.material_ids == local_idx)[0]
            if len(sel) == 0:
                continue
            corner_idx = (sel[:, None] * 3 + np.arange(3)).reshape(-1)
            verts = mesh.vertices[corner_idx]
            faces = np.arange(len(verts), dtype=np.int64).reshape(-1, 3)
            tex = textures.get(mat_name)
            key = id(tex)
            if key not in cache:
                cache[key] = _load_image(tex)
            if mesh.uvs is not None:
                visual = trimesh.visual.TextureVisuals(uv=mesh.uvs[corner_idx], image=cache[key])
            else:
                visual = trimesh.visual.ColorVisuals()
            tm = trimesh.Trimesh(vertices=verts, faces=faces, visual=visual, process=False)
            tm.merge_vertices(merge_tex=False, merge_norm=True)
            scene.add_geometry(tm, geom_name=mat_name.replace(":", "_"))
    return scene


def render_preview(scene: trimesh.Scene, out_png: Path, size: int = 512) -> None:
    """Desenho de verificação simples (vista frontal, sem GPU): cada triângulo é pintado
    com a cor da textura no centro das suas UVs, do mais distante para o mais próximo."""
    img = Image.new("RGB", (size, size), (25, 28, 40))
    draw = ImageDraw.Draw(img)
    tris_all = []
    for geom in scene.geometry.values():
        v = np.asarray(geom.vertices)
        f = np.asarray(geom.faces)
        tri = v[f]
        tex = getattr(geom.visual, "material", None)
        tex_img = getattr(tex, "baseColorTexture", None) or getattr(tex, "image", None)
        uv = getattr(geom.visual, "uv", None)
        if tex_img is not None and uv is not None:
            arr = np.asarray(tex_img.convert("RGB"))
            c = np.asarray(uv)[f].mean(1) % 1.0
            px = arr[((1 - c[:, 1]) * (arr.shape[0] - 1)).astype(int), (c[:, 0] * (arr.shape[1] - 1)).astype(int)]
        else:
            px = np.full((len(f), 3), 180)
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        shade = 0.45 + 0.55 * np.abs(n[:, 2])
        for t, col, sh in zip(tri, px, shade):
            tris_all.append((t[:, 2].mean(), t, tuple(int(x * sh) for x in col)))
    tris_all.sort(key=lambda x: x[0])
    for _, t, col in tris_all:
        pts = [((p[0] * 0.45 + 0.5) * size, (0.5 - p[1] * 0.45) * size) for p in t]
        draw.polygon(pts, fill=col)
    img.save(out_png)


def convert(src: Path, dst: Path, preview: bool = False) -> None:
    version, root = read_fbx(src)
    meshes, textures = extract_meshes(root)
    _normalize(meshes)
    scene = build_scene(meshes, textures)
    dst.parent.mkdir(parents=True, exist_ok=True)
    scene.export(dst)
    n_tris = sum(len(g.faces) for g in scene.geometry.values())
    found = sum(1 for v in textures.values() if v)
    print(f"  {src.name} (FBX {version}) -> {dst.name}: {len(scene.geometry)} submalhas, "
          f"{n_tris} triângulos, texturas {found}/{len(textures)}, {dst.stat().st_size / 1e6:.1f} MB")
    if preview:
        render_preview(trimesh.load(dst), dst.with_suffix(".preview.png"))


def main(argv: List[str]) -> int:
    preview = "--preview" in argv
    args = [a for a in argv if a != "--preview"]
    if len(args) == 2:
        convert(Path(args[0]), Path(args[1]), preview)
        return 0
    if args:
        print(__doc__)
        return 1
    print(f"A converter {len(CHARACTERS)} personagens para {OUT_DIR}:")
    failures = 0
    for src_name, dst_name in CHARACTERS.items():
        try:
            convert(MODELS_DIR / src_name, OUT_DIR / dst_name, preview)
        except Exception as e:  # continua com os restantes
            failures += 1
            print(f"  [ERRO] {src_name}: {e}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
