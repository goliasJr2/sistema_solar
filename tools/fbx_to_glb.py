"""
===============================================================================
Ferramenta: tools/fbx_to_glb.py
Descrição: Converte personagens .fbx (binário, versões 6.1 e 7.x) para:
             .npz — personagem ANIMADO (malha + esqueleto + pesos de pele),
                    lido por characters.py e animado por character_rig.py;
             .glb — modelo ESTÁTICO, lido pelo model_loader.py (trimesh).

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
  - Transformação local da malha (Lcl Translation / Rotation / Scaling);
  - (.npz) Esqueleto: ossos "LimbNode", hierarquia, matriz global de cada osso
    na pose de ligação (Cluster.TransformLink / BindPose), e os 4 maiores pesos
    de pele por vértice (Cluster.Indexes / Weights).
  As animações gravadas no FBX são ignoradas — o movimento é procedural.

Normalização aplicada ao GLB gerado:
  - Eixo vertical = +Y; personagem de frente para +Z;
  - Altura total = 2.0 (de y = -1 aos pés até y = +1 no topo da cabeça),
    centrado em X/Z. O characters.py depois escala-o face ao planeta.

Uso (a partir da pasta do projeto, com o .venv):
  .venv\\Scripts\\python.exe tools\\fbx_to_glb.py                (converte a lista em CHARACTERS)
  .venv\\Scripts\\python.exe tools\\fbx_to_glb.py in.fbx out.npz  (um personagem animado)
  .venv\\Scripts\\python.exe tools\\fbx_to_glb.py in.fbx out.glb  (um modelo estático)
  Acrescente --preview para gerar também uma imagem .png de verificação
  (no .npz: pose de ligação, repouso e aceno lado a lado).
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

# Ficheiro de origem -> personagem animado gerado em Models/characters/
CHARACTERS: Dict[str, str] = {
    "Mutant.fbx": "mutant.npz",
    "Warrok W Kurniawan.fbx": "warrok.npz",
    "goblin_d_shareyko.fbx": "goblin.npz",
    "character (1).fbx": "vanguard.npz",
    "character (2).fbx": "ely.npz",
    "character (3).fbx": "maw.npz",
    "character.fbx": "remy.npz",
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
    cp_index: Optional[np.ndarray] = None    # (n_corners,) índice do "control point" FBX de cada canto
    local_vertices: Optional[np.ndarray] = None  # vértices antes da transformação do modelo
    geom_id: object = None
    joints: Optional[np.ndarray] = None      # (n_corners, 4) índices de ossos
    weights: Optional[np.ndarray] = None     # (n_corners, 4) pesos (soma = 1)


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

    cp = corner_vert[corners_arr]
    return RawMesh(
        name=name,
        vertices=verts[cp],
        uvs=None if uv_corner is None else uv_corner[corners_arr],
        material_ids=np.asarray(tri_mat, dtype=np.int64),
        material_names=material_names or ["default"],
        cp_index=cp,
        local_vertices=verts[cp].copy(),
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
        mesh.geom_id = obj_id(geom)
        if not mat_names:
            textures[mesh.material_names[0]] = diffuse_for_material(None, model_name)

        props = _props_table(model)
        mesh.vertices = _apply_transform(mesh.vertices, props, "Geometric")
        mesh.vertices = _apply_transform(mesh.vertices, props, "Lcl ")
        meshes.append(mesh)

    if not meshes:
        raise ValueError("Nenhuma malha encontrada no FBX.")
    ctx = {"objects": objects, "by_id": by_id, "children_of": children_of, "parents_of": parents_of}
    return meshes, textures, ctx


# =============================================================================
# 3. Esqueleto e pesos de pele (skinning)
# =============================================================================
@dataclass
class Skeleton:
    names: List[str]
    parents: np.ndarray      # (B,) índice do osso pai; -1 = raiz
    bind_global: np.ndarray  # (B, 4, 4) matriz global de cada osso na pose de ligação


def _fbx_matrix(arr) -> np.ndarray:
    """Matriz FBX (16 doubles, translação nos elementos 12–14) -> 4x4 para vetores-coluna."""
    return np.asarray(arr, dtype=np.float64).reshape(4, 4).T


def _transform_points(m: np.ndarray, pts: np.ndarray) -> np.ndarray:
    return pts @ m[:3, :3].T + m[:3, 3]


def extract_skin(meshes: List[RawMesh], ctx: dict) -> Optional[Skeleton]:
    """Lê ossos (Model LimbNode), clusters (Deformer Cluster) e a pose de ligação.
    Preenche mesh.joints / mesh.weights (4 ossos por vértice) e passa os vértices
    das malhas com pele para o espaço global da pose de ligação."""
    objects, by_id = ctx["objects"], ctx["by_id"]
    children_of, parents_of = ctx["children_of"], ctx["parents_of"]

    def node_type(n: FBXNode) -> str:
        return str(n.props[-1]) if n.props else ""

    def is_bone(n: Optional[FBXNode]) -> bool:
        return n is not None and n.name == "Model" and node_type(n) in ("LimbNode", "Limb", "Root")

    # Pose de ligação (BindPose): matriz global de cada nó
    pose_mats: Dict[object, np.ndarray] = {}
    for n in objects.children:
        if n.name != "Pose":
            continue
        for pn in n.find_all("PoseNode"):
            mat = pn.array("Matrix")
            if mat is not None and len(mat) == 16:
                pose_mats[pn.value("Node")] = _fbx_matrix(mat)

    bone_ids = [n.props[0] for n in objects.children if is_bone(n)]
    if not bone_ids:
        return None
    bone_index = {bid: i for i, bid in enumerate(bone_ids)}
    bind: Dict[int, np.ndarray] = {}

    any_skin = False
    for mesh in meshes:
        n_cp = int(mesh.cp_index.max()) + 1
        per_cp: List[List[Tuple[float, int]]] = [[] for _ in range(n_cp)]
        skins = [c for c, _ in children_of.get(mesh.geom_id, []) if by_id.get(c) is not None
                 and by_id[c].name == "Deformer" and node_type(by_id[c]) == "Skin"]
        for skin in skins:
            for cl_id, _ in children_of.get(skin, []):
                cl = by_id.get(cl_id)
                if cl is None or node_type(cl) != "Cluster":
                    continue
                bones = [c for c, _ in children_of.get(cl_id, []) if c in bone_index]
                idx, w = cl.array("Indexes"), cl.array("Weights")
                link = cl.array("TransformLink")
                if not bones:
                    continue
                b = bone_index[bones[0]]
                if link is not None and len(link) == 16:
                    bind[b] = _fbx_matrix(link)
                if idx is None or w is None:
                    continue
                for vi, wi in zip(np.asarray(idx, dtype=np.int64), np.asarray(w, dtype=np.float64)):
                    if 0 <= vi < n_cp and wi > 1e-5:
                        per_cp[vi].append((float(wi), b))
        if not any(per_cp):
            continue
        any_skin = True
        # 4 maiores pesos por vértice, normalizados para somar 1
        joints_cp = np.zeros((n_cp, 4), dtype=np.int64)
        weights_cp = np.zeros((n_cp, 4), dtype=np.float64)
        for vi, lst in enumerate(per_cp):
            lst.sort(reverse=True)
            for k, (wi, b) in enumerate(lst[:4]):
                joints_cp[vi, k], weights_cp[vi, k] = b, wi
        mesh.joints = joints_cp[mesh.cp_index]
        mesh.weights = weights_cp[mesh.cp_index]
        # Nota: os vértices ficam como em extract_meshes (transformação Lcl da malha). Nos
        # FBX da Mixamo o "Transform" de cada cluster é o inverso do osso
        # (Transform · TransformLink = I), não a matriz global da malha, por isso não se usa.

    if not any_skin:
        return None

    # Pais (hierarquia de ossos) e ordenação: pais antes dos filhos
    parent_of: Dict[int, int] = {}
    for bid, i in bone_index.items():
        ps = [p for p in parents_of.get(bid, []) if p in bone_index]
        parent_of[i] = bone_index[ps[0]] if ps else -1
    order: List[int] = []
    seen = set()

    def visit(i: int) -> None:
        if i in seen:
            return
        if parent_of[i] >= 0:
            visit(parent_of[i])
        seen.add(i)
        order.append(i)

    for i in range(len(bone_ids)):
        visit(i)

    # Matriz global de ligação: TransformLink do cluster > BindPose > pai x local
    globals_: Dict[int, np.ndarray] = {}
    for i in order:
        if i in bind:
            globals_[i] = bind[i]
        elif bone_ids[i] in pose_mats:
            globals_[i] = pose_mats[bone_ids[i]]
        else:
            props = _props_table(by_id[bone_ids[i]])
            local = np.eye(4)
            local[:3, :3] = _euler_xyz_matrix(*[float(x) for x in (props.get("Lcl Rotation") or [0, 0, 0])[:3]])
            local[:3, 3] = [float(x) for x in (props.get("Lcl Translation") or [0, 0, 0])[:3]]
            parent_g = globals_.get(parent_of[i], np.eye(4)) if parent_of[i] >= 0 else np.eye(4)
            globals_[i] = parent_g @ local

    # Reindexa pela ordem topológica e acrescenta um osso "estático" (identidade)
    # para os vértices sem pesos (ex.: olhos de alguns modelos).
    remap = {old: new for new, old in enumerate(order)}
    names = [_clean_name(by_id[bone_ids[i]].props[1] if len(by_id[bone_ids[i]].props) >= 3
                         else by_id[bone_ids[i]].props[0]) for i in order] + ["__static__"]
    parents = np.array([remap[parent_of[i]] if parent_of[i] >= 0 else -1 for i in order] + [-1])
    bind_global = np.stack([globals_[i] for i in order] + [np.eye(4)])
    static = len(order)
    lut = np.array([remap[i] for i in range(len(bone_ids))])
    for mesh in meshes:
        if mesh.joints is None:
            mesh.joints = np.full((len(mesh.vertices), 4), static, dtype=np.int64)
            mesh.weights = np.zeros((len(mesh.vertices), 4))
            mesh.weights[:, 0] = 1.0
            continue
        mesh.joints = lut[mesh.joints]
        total = mesh.weights.sum(1)
        empty = total < 1e-6
        mesh.joints[empty, 0] = static
        mesh.weights[empty, 0] = 1.0
        mesh.weights /= mesh.weights.sum(1, keepdims=True)
    return Skeleton(names=names, parents=parents, bind_global=bind_global)


# =============================================================================
# 4. Normalização e exportação
# =============================================================================
def _normalize(meshes: List[RawMesh]) -> np.ndarray:
    """Põe o personagem de pé (+Y), centrado, com altura 2.0 e pés em y = -1.
    Devolve a matriz 4x4 aplicada (para transformar também o esqueleto)."""
    all_v = np.concatenate([m.vertices for m in meshes])
    extents = all_v.max(0) - all_v.min(0)
    rot = np.eye(4)
    if extents[2] > extents[1] * 1.2:      # exportado com Z para cima
        rot[:3, :3] = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], dtype=float)
    all_v = _transform_points(rot, all_v)
    lo, hi = all_v.min(0), all_v.max(0)
    s = 2.0 / max(hi[1] - lo[1], 1e-6)
    offset = np.array([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2])
    fit = np.eye(4)
    fit[:3, :3] *= s
    fit[:3, 3] = -offset * s - np.array([0.0, 1.0, 0.0])
    n_mat = fit @ rot
    for m in meshes:
        m.vertices = _transform_points(n_mat, m.vertices)
    return n_mat


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


def build_submeshes(meshes: List[RawMesh], textures: Dict[str, Optional[bytes]]) -> List[dict]:
    """Uma submalha por material, com vértices partilhados (posição+UV), normais suaves,
    ossos/pesos e a imagem da textura. É o conteúdo do ficheiro .npz animado."""
    out: List[dict] = []
    cache: Dict[int, Image.Image] = {}
    for mesh in meshes:
        for local_idx, mat_name in enumerate(mesh.material_names):
            sel = np.nonzero(mesh.material_ids == local_idx)[0]
            if len(sel) == 0:
                continue
            corner_idx = (sel[:, None] * 3 + np.arange(3)).reshape(-1)
            pos = mesh.vertices[corner_idx]
            uv = mesh.uvs[corner_idx] if mesh.uvs is not None else np.zeros((len(pos), 2))
            key = np.concatenate([np.round(pos, 6), np.round(uv, 6)], axis=1)
            _, first, inverse = np.unique(key, axis=0, return_index=True, return_inverse=True)
            inverse = np.asarray(inverse).reshape(-1)
            positions, uvs = pos[first], uv[first]
            faces = inverse.reshape(-1, 3)

            # Normais suaves: acumula as normais das faces por posição (ignora costuras de UV)
            _, group = np.unique(np.round(positions, 5), axis=0, return_inverse=True)
            group = np.asarray(group).reshape(-1)
            tri = positions[faces]
            fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            acc = np.zeros((group.max() + 1, 3))
            for k in range(3):
                np.add.at(acc, group[faces[:, k]], fn)
            normals = acc[group]
            normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-12

            tex = textures.get(mat_name)
            if id(tex) not in cache:
                cache[id(tex)] = _load_image(tex)
            sub = {
                "name": mat_name,
                "positions": positions.astype(np.float32),
                "normals": normals.astype(np.float32),
                "uvs": uvs.astype(np.float32),
                "faces": faces.astype(np.uint32),
                "image": cache[id(tex)],
            }
            if mesh.joints is not None:
                sub["joints"] = mesh.joints[corner_idx][first].astype(np.uint16)
                sub["weights"] = mesh.weights[corner_idx][first].astype(np.float32)
            out.append(sub)
    return out


def _image_bytes(img: Image.Image) -> np.ndarray:
    buf = io.BytesIO()
    if img.mode == "RGBA":
        img.save(buf, format="PNG", optimize=True)
    else:
        img.save(buf, format="JPEG", quality=90)
    return np.frombuffer(buf.getvalue(), dtype=np.uint8)


def export_npz(path: Path, subs: List[dict], skel: Skeleton) -> None:
    """Formato do personagem animado (lido por characters.py)."""
    data = {
        "format_version": np.array(1),
        "bone_names": np.array(skel.names),
        "bone_parents": skel.parents.astype(np.int32),
        "bone_bind": skel.bind_global.astype(np.float32),
        "submesh_count": np.array(len(subs)),
    }
    for k, s in enumerate(subs):
        for field_name in ("positions", "normals", "uvs", "faces", "joints", "weights"):
            data[f"sm{k}_{field_name}"] = s[field_name]
        data[f"sm{k}_name"] = np.array(s["name"])
        data[f"sm{k}_image"] = _image_bytes(s["image"])
    np.savez_compressed(path, **data)


def render_preview(parts: List[Tuple[np.ndarray, np.ndarray, np.ndarray, Image.Image]],
                   size: int = 512) -> Image.Image:
    """Desenho de verificação simples (vista frontal, sem GPU): cada triângulo é pintado
    com a cor da textura no centro das suas UVs, do mais distante para o mais próximo.
    `parts` = lista de (posições, faces, uvs, imagem)."""
    img = Image.new("RGB", (size, size), (25, 28, 40))
    draw = ImageDraw.Draw(img)
    tris_all = []
    for v, f, uv, tex_img in parts:
        tri = v[f]
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
    return img


def _preview_scene(scene: trimesh.Scene) -> Image.Image:
    parts = []
    for geom in scene.geometry.values():
        mat = getattr(geom.visual, "material", None)
        tex = getattr(mat, "baseColorTexture", None) or getattr(mat, "image", None)
        parts.append((np.asarray(geom.vertices), np.asarray(geom.faces), getattr(geom.visual, "uv", None), tex))
    return render_preview(parts)


def _preview_animated(subs: List[dict], skel: Skeleton) -> Image.Image:
    """Três poses lado a lado: ligação (pose em T), repouso e aceno."""
    sys.path.insert(0, str(BASE_DIR))
    from character_rig import ProceduralRig, skin_vertices

    rig = ProceduralRig(skel.names, skel.parents, skel.bind_global)
    poses = [np.repeat(np.eye(4, dtype=np.float32)[None], rig.count, 0),
             rig.palette(t=1.0, wave=0.0), rig.palette(t=1.0, wave=1.0)]
    sheet = Image.new("RGB", (512 * len(poses), 512))
    for i, pal in enumerate(poses):
        parts = [(skin_vertices(pal, s["positions"], s["joints"], s["weights"]), s["faces"], s["uvs"], s["image"])
                 for s in subs]
        sheet.paste(render_preview(parts), (512 * i, 0))
    return sheet


def convert(src: Path, dst: Path, preview: bool = False) -> None:
    """Converte `src` (.fbx) para `dst`: .npz = personagem animado; .glb = modelo estático."""
    version, root = read_fbx(src)
    meshes, textures, ctx = extract_meshes(root)
    animated = dst.suffix.lower() == ".npz"
    skel = extract_skin(meshes, ctx) if animated else None
    if animated and skel is None:
        raise ValueError("o FBX não tem esqueleto com pesos de pele; use saída .glb (estática).")
    n_mat = _normalize(meshes)
    dst.parent.mkdir(parents=True, exist_ok=True)
    found = sum(1 for v in textures.values() if v)
    if animated:
        skel.bind_global = np.einsum("ij,bjk->bik", n_mat, skel.bind_global)
        subs = build_submeshes(meshes, textures)
        export_npz(dst, subs, skel)
        n_tris = sum(len(s["faces"]) for s in subs)
        extra = f"{len(skel.names) - 1} ossos"
    else:
        scene = build_scene(meshes, textures)
        scene.export(dst)
        subs = None
        n_tris = sum(len(g.faces) for g in scene.geometry.values())
        extra = "estático"
    print(f"  {src.name} (FBX {version}) -> {dst.name}: {n_tris} triângulos, {extra}, "
          f"texturas {found}/{len(textures)}, {dst.stat().st_size / 1e6:.1f} MB")
    if preview:
        out_png = dst.with_name(dst.stem + ".preview.png")
        (_preview_animated(subs, skel) if animated else _preview_scene(trimesh.load(dst))).save(out_png)


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
