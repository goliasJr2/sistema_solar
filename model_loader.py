"""
===============================================================================
Módulo: model_loader.py
Descrição: Carregador e renderizador de modelos 3D (.glb, .gltf, .obj) em OpenGL 3.3 Core Profile.
Conceitos aplicados:
  - Carregamento de malhas poligonais 3D arbitrárias e complexas com trimesh.
  - Normalização geométrica: cálculo de centroide e raio de escala unitário
    para manter a escala astronómica correta e uniforme no simulador.
  - Extração de topologia: Vértices (Posição), Normais de Vértice e UVs.
  - Extração e carregamento de texturas embutidas PBR/Diffuse no OpenGL com Mipmaps.
  - Suporte a modelos com múltiplas submalhas (ex: Terra + Camada de Nuvens;
    Saturno + Múltiplos Anéis).
===============================================================================
"""

from pathlib import Path
from typing import List, Optional, Tuple, Dict
import ctypes
import math
import numpy as np
import trimesh
from PIL import Image
from OpenGL.GL import (
    glGenVertexArrays,
    glBindVertexArray,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glVertexAttribPointer,
    glEnableVertexAttribArray,
    glDrawElements,
    glDeleteVertexArrays,
    glDeleteBuffers,
    glGenTextures,
    glBindTexture,
    glTexImage2D,
    glGenerateMipmap,
    glTexParameteri,
    glActiveTexture,
    glDeleteTextures,
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_FLOAT,
    GL_UNSIGNED_INT,
    GL_TRIANGLES,
    GL_FALSE,
    GL_TEXTURE_2D,
    GL_TEXTURE0,
    GL_RGB,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_REPEAT,
    GL_CLAMP_TO_EDGE,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_LINEAR,
    GL_LINEAR_MIPMAP_LINEAR,
)

from texture import Texture
from shader import Shader


class SubMeshGPU:
    """Encapsula uma submalha com VAO, VBO, EBO e a respetiva textura no OpenGL."""

    def __init__(
        self,
        vao: int,
        vbo: int,
        ebo: int,
        index_count: int,
        texture: Optional[Texture] = None,
        is_transparent: bool = False,
    ):
        self.vao = vao
        self.vbo = vbo
        self.ebo = ebo
        self.index_count = index_count
        self.texture = texture
        self.is_transparent = is_transparent

    def draw(self, default_texture: Optional[Texture] = None) -> None:
        """Vincula a textura apropriada e desenha a geometria."""
        tex_to_bind = self.texture or default_texture
        if tex_to_bind:
            tex_to_bind.bind(0)

        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def cleanup(self) -> None:
        """Desaloca os recursos da GPU."""
        if self.vao != 0:
            glDeleteVertexArrays(1, [self.vao])
            self.vao = 0
        if self.vbo != 0:
            glDeleteBuffers(1, [self.vbo])
            self.vbo = 0
        if self.ebo != 0:
            glDeleteBuffers(1, [self.ebo])
            self.ebo = 0
        if self.texture:
            self.texture.cleanup()
            self.texture = None


def _compute_vertex_normals(verts: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """
    Calcula normais de vértice vetorizadas em NumPy puro em alta velocidade.
    Evita o ciclo quadrático do trimesh quando scipy não está presente.
    """
    tris = verts[faces]
    face_normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    normals = np.zeros_like(verts, dtype=np.float32)
    np.add.at(normals, faces[:, 0], face_normals)
    np.add.at(normals, faces[:, 1], face_normals)
    np.add.at(normals, faces[:, 2], face_normals)
    lens = np.linalg.norm(normals, axis=1, keepdims=True)
    lens[lens == 0.0] = 1.0
    return (normals / lens).astype(np.float32)


class GLBModel:
    """
    Carrega e gere modelos 3D em formato .glb ou .obj usando a biblioteca trimesh.
    Normaliza a escala do modelo para raio 1.0 de modo a respeitar a hierarquia do simulador.
    """

    def __init__(self, model_path: Path):
        self.model_path = Path(model_path)
        self.submeshes: List[SubMeshGPU] = []
        self.name = self.model_path.stem
        self.base_radius = 1.0

        if not self.model_path.exists():
            raise FileNotFoundError(f"[GLBModel] Ficheiro não encontrado: {self.model_path}")

        self._load_and_upload()

    def _load_and_upload(self) -> None:
        """Lê o modelo com trimesh, normaliza as coordenadas e cria os buffers na GPU."""
        try:
            scene_or_mesh = trimesh.load(self.model_path, process=False)
        except Exception as e:
            raise RuntimeError(f"[GLBModel] Erro ao analisar modelo com trimesh: {e}")

        # Se for uma Cena (trimesh.Scene), extrai as malhas com a hierarquia de nós resolvida
        geometries: List[Tuple[str, trimesh.Trimesh]] = []
        if isinstance(scene_or_mesh, trimesh.Scene):
            bounds = scene_or_mesh.bounds
            dumped = scene_or_mesh.dump(concatenate=False)
            for idx, geom in enumerate(dumped):
                if isinstance(geom, trimesh.Trimesh) and len(geom.vertices) > 0 and len(geom.faces) > 0:
                    geom_name = getattr(geom, "metadata", {}).get("name", f"mesh_{idx}")
                    geometries.append((geom_name, geom))
        elif isinstance(scene_or_mesh, trimesh.Trimesh):
            bounds = scene_or_mesh.bounds
            geometries.append(("mesh", scene_or_mesh))
        else:
            bounds = np.array([[-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]])

        if not geometries:
            raise ValueError(f"[GLBModel] Nenhuma geometria tridimensional válida encontrada em {self.model_path}")

        # 1. Determina a escala base e o centroide global do modelo
        extents = bounds[1] - bounds[0]
        center = (bounds[0] + bounds[1]) * 0.5

        # Para planetas com anéis (ex: Saturno e Neptuno), a dimensão mínima em Y é o diâmetro da esfera central
        min_extent = float(np.min(extents))
        max_extent = float(np.max(extents))
        raw_radius = min_extent * 0.5 if min_extent > 1e-4 else max_extent * 0.5
        if raw_radius <= 1e-5:
            raw_radius = 1.0
        self.base_radius = raw_radius
        # Dimensões (x, y, z) do modelo já normalizado — usado p.ex. para escalar personagens pela altura
        self.normalized_extents = extents / raw_radius

        # 2. Processa cada geometria e envia para o OpenGL
        for name, geom in geometries:
            # Subtrai o centroide global e divide pelo raio base para normalizar a escala para ~1.0
            verts = (geom.vertices - center) / self.base_radius

            # Faces (Índices)
            faces = geom.faces.astype(np.uint32)

            # Normais de vértice vetorizadas ultrarrápidas em NumPy
            normals = None
            if len(faces) > 0:
                try:
                    normals = _compute_vertex_normals(verts, faces)
                except Exception:
                    normals = None

            if normals is None or len(normals) != len(verts):
                # Fallback de projeção radial em NumPy puro
                try:
                    norm_v = verts / (np.linalg.norm(verts, axis=1, keepdims=True) + 1e-8)
                    normals = norm_v.astype(np.float32)
                except Exception:
                    normals = np.zeros_like(verts, dtype=np.float32)
                    normals[:, 1] = 1.0

            # Coordenadas UV
            uvs = None
            if hasattr(geom.visual, "uv") and geom.visual.uv is not None and len(geom.visual.uv) == len(verts):
                uvs = geom.visual.uv
            else:
                # Projeção esférica procedural caso o modelo não contenha mapa UV nativo
                uvs = []
                for v in verts:
                    norm_v = v / (np.linalg.norm(v) + 1e-8)
                    u = 0.5 + math.atan2(norm_v[2], norm_v[0]) / (2.0 * math.pi)
                    v_coord = 0.5 - math.asin(max(-1.0, min(1.0, norm_v[1]))) / math.pi
                    uvs.append([u, v_coord])
                uvs = np.array(uvs, dtype=np.float32)

            # Extração da textura embutida
            sub_tex = None
            is_transparent = False
            mat = getattr(geom.visual, "material", None)
            tex_img = getattr(mat, "baseColorTexture", None) or getattr(mat, "image", None)

            if tex_img is not None and isinstance(tex_img, Image.Image):
                sub_tex = self._upload_pil_texture(tex_img)
                is_transparent = (tex_img.mode == "RGBA" or "cloud" in str(name).lower() or "ring" in str(name).lower())

            # Intercalação de atributos: [pos(3), normal(3), uv(2)] -> 8 floats
            n_verts = len(verts)
            interleaved = np.empty((n_verts, 8), dtype=np.float32)
            interleaved[:, 0:3] = verts
            interleaved[:, 3:6] = normals
            interleaved[:, 6:8] = uvs
            interleaved_flat = interleaved.flatten()

            # Criação de VAO, VBO, EBO no OpenGL 3.3 Core Profile
            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)

            vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, interleaved_flat.nbytes, interleaved_flat, GL_STATIC_DRAW)

            ebo = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, faces.nbytes, faces.flatten(), GL_STATIC_DRAW)

            stride = 8 * 4  # 32 bytes

            # Atributo 0: aPos
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)

            # Atributo 1: aNormal (offset 12 bytes)
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
            glEnableVertexAttribArray(1)

            # Atributo 2: aTexCoords (offset 24 bytes)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))
            glEnableVertexAttribArray(2)

            glBindVertexArray(0)

            submesh_gpu = SubMeshGPU(
                vao=vao,
                vbo=vbo,
                ebo=ebo,
                index_count=len(faces.flatten()),
                texture=sub_tex,
                is_transparent=is_transparent,
            )
            self.submeshes.append(submesh_gpu)

    def _upload_pil_texture(self, img: Image.Image) -> Texture:
        """Carrega uma imagem PIL para o OpenGL gerando uma textura com mipmaps."""
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

        mode = img.mode
        if mode == "RGBA":
            gl_fmt = GL_RGBA
        elif mode == "LA":
            img = img.convert("RGBA")
            gl_fmt = GL_RGBA
        else:
            img = img.convert("RGB")
            gl_fmt = GL_RGB

        width, height = img.size
        data = img.tobytes()

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, gl_fmt, width, height, 0, gl_fmt, GL_UNSIGNED_BYTE, data)
        glGenerateMipmap(GL_TEXTURE_2D)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        return Texture(tex_id, width, height)

    def draw(self, default_texture: Optional[Texture] = None) -> None:
        """Desenha todas as submalhas do modelo 3D."""
        for sub in self.submeshes:
            sub.draw(default_texture)

    def cleanup(self) -> None:
        """Liberta todos os buffers e texturas da memória de vídeo."""
        for sub in self.submeshes:
            sub.cleanup()
        self.submeshes.clear()
