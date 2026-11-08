"""
===============================================================================
Módulo: guide/guide_renderer.py
Descrição: Renderizador 3D dedicado para o Astronomical Virtual Guide.
Possui câmara própria orbital, iluminação de estúdio e viewport independente.
===============================================================================
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import ctypes
import numpy as np
import glm
from OpenGL.GL import (
    glViewport,
    glEnable,
    glDisable,
    glClear,
    glDepthFunc,
    glDepthMask,
    glCullFace,
    glBlendFunc,
    glBindVertexArray,
    glDrawElements,
    glActiveTexture,
    glBindTexture,
    GL_DEPTH_TEST,
    GL_DEPTH_BUFFER_BIT,
    GL_LESS,
    GL_LEQUAL,
    GL_CULL_FACE,
    GL_BACK,
    GL_BLEND,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    GL_TRUE,
    GL_FALSE,
)

from shader import Shader
from texture import Texture, TextureLoader
from model_loader import GLBModel, SubMeshGPU
from .guide_animation import SkeletalTransformState
from .facial_animation import FacialParameters


class GuideRenderer:
    """
    Renderizador do personagem 3D com câmara e iluminação independentes da cena planetária.
    Pode desenhar numa janela Picture-in-Picture (PiP) ou sobre a interface gráfica.
    """

    MESH_TYPE_MAP = {
        "Body": 0,
        "Eyes": 1,
        "Eyelashes": 2,
        "Hair": 3,
        "Tops": 4,
        "Bottoms": 5,
        "Shoes": 6,
    }

    def __init__(self, model_path: str = "Models/guide_remy.glb"):
        self.model_path = Path(model_path)
        self.shader: Optional[Shader] = None
        self.model: Optional[GLBModel] = None

        # Câmara independente do Guia
        # Enquadra o busto/cabeça do apresentador cósmico
        self.camera_target = glm.vec3(0.0, 310.0, 5.0)  # Foco no peito/rosto do Remy
        self.camera_distance = 145.0                    # Distância focal perfeita
        self.camera_yaw = 0.0                           # Ângulo horizontal frontal
        self.camera_pitch = 4.0                         # Ligeiro ângulo superior profissional
        self.fov = 34.0                                 # Lente retrato de 85mm equivalente

        self._init_gl()

    def _init_gl(self) -> None:
        """Compila o shader do guia e carrega o modelo 3D."""
        vert_path = Path("shaders/guide.vert")
        frag_path = Path("shaders/guide.frag")

        if not vert_path.exists() or not frag_path.exists():
            raise FileNotFoundError("[GuideRenderer] Shaders do guia não encontrados em shaders/")

        self.shader = Shader(vert_path, frag_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"[GuideRenderer] Modelo não encontrado: {self.model_path}")

        # O GLBModel existente carrega e instancia todos os VAOs, VBOs, EBOs e Texturas!
        # Note que GLBModel normaliza para raio unitário por padrão, mas precisamos
        # das coordenadas anatómicas originais para as deformações dos ossos.
        # Vamos carregar o modelo preservando as coordenadas reais.
        self._load_unnormalized_model()

    def _load_unnormalized_model(self) -> None:
        """Carrega o modelo 3D preservando as dimensões anatómicas originais."""
        import trimesh
        from OpenGL.GL import (
            glGenVertexArrays,
            glBindVertexArray,
            glGenBuffers,
            glBindBuffer,
            glBufferData,
            glVertexAttribPointer,
            glEnableVertexAttribArray,
            GL_ARRAY_BUFFER,
            GL_ELEMENT_ARRAY_BUFFER,
            GL_STATIC_DRAW,
            GL_FLOAT,
        )

        scene = trimesh.load(self.model_path, process=False)
        self.submeshes: List[Tuple[str, SubMeshGPU]] = []

        # Texturas em cache
        tex_cache: Dict[str, Texture] = {}

        for node_name, geom in scene.geometry.items():
            if not isinstance(geom, trimesh.Trimesh):
                continue

            verts = np.asarray(geom.vertices, dtype=np.float32)
            faces = np.asarray(geom.faces, dtype=np.uint32).flatten()
            normals = np.asarray(geom.vertex_normals, dtype=np.float32)

            uvs = np.zeros((len(verts), 2), dtype=np.float32)
            if hasattr(geom.visual, "uv") and geom.visual.uv is not None:
                uvs = np.asarray(geom.visual.uv, dtype=np.float32)

            # Intercalar VBO: [Pos(3), Normal(3), UV(2)]
            vbo_data = np.hstack([verts, normals, uvs]).astype(np.float32).flatten()

            vao = glGenVertexArrays(1)
            vbo = glGenBuffers(1)
            ebo = glGenBuffers(1)

            glBindVertexArray(vao)

            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, vbo_data.nbytes, vbo_data, GL_STATIC_DRAW)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, faces.nbytes, faces, GL_STATIC_DRAW)

            stride = 8 * ctypes.sizeof(ctypes.c_float)
            # aPos
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            # aNormal
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * ctypes.sizeof(ctypes.c_float)))
            glEnableVertexAttribArray(1)
            # aTexCoords
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * ctypes.sizeof(ctypes.c_float)))
            glEnableVertexAttribArray(2)

            glBindVertexArray(0)

            # Obter textura correspondente
            sub_texture: Optional[Texture] = None
            tex_filename = f"Remy_{node_name}_Diffuse.png" if node_name in ["Shoes", "Tops", "Bottoms", "Hair"] else "Remy_Body_Diffuse.png"
            tex_path = Path("textures/guide") / tex_filename

            if tex_path.exists():
                if tex_filename not in tex_cache:
                    tex_cache[tex_filename] = TextureLoader.load(tex_path, fallback_key="guide")
                sub_texture = tex_cache[tex_filename]

            is_transparent = node_name in ["Hair", "Eyelashes"]
            submesh_gpu = SubMeshGPU(
                vao=vao,
                vbo=vbo,
                ebo=ebo,
                index_count=len(faces),
                texture=sub_texture,
                is_transparent=is_transparent
            )
            self.submeshes.append((node_name, submesh_gpu))

        print(f"[GuideRenderer] Modelo carregado com sucesso: {len(self.submeshes)} submalhas GPU prontas!")

    def render(
        self,
        viewport_x: int,
        viewport_y: int,
        viewport_w: int,
        viewport_h: int,
        skeletal_state: SkeletalTransformState,
        facial_params: FacialParameters,
    ) -> None:
        """
        Renderiza o Guia Virtual 3D na sub-região designada do ecrã.
        """
        if not self.shader or not self.submeshes:
            return

        # 1. Configurar Viewport dedicada sem afetar a câmara orbital do simulador
        glViewport(viewport_x, viewport_y, viewport_w, viewport_h)

        # Habilitar scissor test temporário para limpar apenas o buffer de profundidade desta sub-janela
        from OpenGL.GL import glEnable, glDisable, glScissor, GL_SCISSOR_TEST
        glEnable(GL_SCISSOR_TEST)
        glScissor(viewport_x, viewport_y, viewport_w, viewport_h)
        glClear(GL_DEPTH_BUFFER_BIT)
        glDisable(GL_SCISSOR_TEST)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # 2. Calcular matrizes da câmara do Guia
        rad_yaw = glm.radians(self.camera_yaw)
        rad_pitch = glm.radians(self.camera_pitch)
        cam_x = self.camera_target.x + self.camera_distance * glm.cos(rad_pitch) * glm.sin(rad_yaw)
        cam_y = self.camera_target.y + self.camera_distance * glm.sin(rad_pitch)
        cam_z = self.camera_target.z + self.camera_distance * glm.cos(rad_pitch) * glm.cos(rad_yaw)
        cam_pos = glm.vec3(cam_x, cam_y, cam_z)

        view_mat = glm.lookAt(cam_pos, self.camera_target, glm.vec3(0, 1, 0))
        aspect = max(0.1, float(viewport_w) / float(viewport_h))
        proj_mat = glm.perspective(glm.radians(self.fov), aspect, 1.0, 1000.0)

        # Matriz de Modelo (Model)
        model_mat = glm.mat4(1.0)
        norm_mat = glm.mat3(glm.transpose(glm.inverse(model_mat)))

        # 3. Ativar Shader e carregar uniformes
        self.shader.use()
        self.shader.set_mat4("uModel", model_mat)
        self.shader.set_mat4("uView", view_mat)
        self.shader.set_mat4("uProjection", proj_mat)
        self.shader.set_mat3("uNormalMatrix", norm_mat)
        self.shader.set_vec3("uViewPos", cam_pos)
        self.shader.set_int("uIsSitting", 0)

        # Uniformes esqueléticos
        self.shader.set_mat4("uHeadRotation", skeletal_state.head_rotation)
        self.shader.set_vec3("uHeadPivot", glm.vec3(0.0, 325.0, 3.0))
        self.shader.set_float("uBreathingScale", skeletal_state.breathing_scale)
        self.shader.set_mat4("uRightArmRotation", skeletal_state.right_arm_rotation)
        self.shader.set_vec3("uRightShoulderPivot", glm.vec3(38.0, 280.0, 0.0))
        self.shader.set_mat4("uLeftArmRotation", skeletal_state.left_arm_rotation)
        self.shader.set_vec3("uLeftShoulderPivot", glm.vec3(-38.0, 280.0, 0.0))

        # Uniformes faciais e lip sync
        self.shader.set_float("uMouthOpen", facial_params.mouth_open)
        self.shader.set_float("uJawDrop", facial_params.jaw_drop)
        self.shader.set_float("uMouthRound", facial_params.mouth_round)
        self.shader.set_float("uBlinkFactor", facial_params.blink_factor)

        # 4. Desenhar primeiro as submalhas opacas e depois as transparentes
        opaque_meshes = [m for m in self.submeshes if not m[1].is_transparent]
        transparent_meshes = [m for m in self.submeshes if m[1].is_transparent]

        for name, submesh in opaque_meshes + transparent_meshes:
            mtype = self.MESH_TYPE_MAP.get(name, 0)
            self.shader.set_int("uMeshType", mtype)

            if submesh.texture:
                submesh.texture.bind(0)
                self.shader.set_int("uTexture", 0)

            glBindVertexArray(submesh.vao)
            glDrawElements(GL_TRIANGLES, submesh.index_count, GL_UNSIGNED_INT, None)
            glBindVertexArray(0)

        # Restaura estado padrão
        glDisable(GL_CULL_FACE)
        glDisable(GL_DEPTH_TEST)

    def render_on_planet(
        self,
        view_mat: glm.mat4,
        proj_mat: glm.mat4,
        cam_pos: glm.vec3,
        planet_pos: glm.vec3,
        planet_radius: float,
        skeletal_state: SkeletalTransformState,
        facial_params: FacialParameters,
        axial_tilt_deg: float = 0.0,
    ) -> None:
        """
        Renderiza o Guia Virtual 3D sentado em posição de lótus no topo do planeta selecionado
        diretamente no espaço de mundo 3D do simulador, em meditação cósmica zen.
        """
        if not self.shader or not self.submeshes:
            return

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        # Desativa Face Culling para exibir perfeitamente todas as dobras anatómicas de lótus
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Proporção da altura sentada em lótus sobre o planeta
        char_height_target = max(1.6, min(9.0, planet_radius * 0.46))
        scale_val = char_height_target / 260.0

        model_mat = glm.mat4(1.0)
        # 1. Posiciona no topo da esfera do planeta
        sitting_pos = planet_pos + glm.vec3(0.0, planet_radius, 0.0)
        model_mat = glm.translate(model_mat, sitting_pos)

        # 2. Rotação para ficar voltado na direção frontal da câmara
        to_cam = cam_pos - sitting_pos
        to_cam.y = 0.0
        if glm.length(to_cam) > 0.001:
            to_cam = glm.normalize(to_cam)
            angle_rad = glm.atan(to_cam.x, to_cam.z)
            model_mat = glm.rotate(model_mat, angle_rad, glm.vec3(0.0, 1.0, 0.0))

        # 3. Escala uniforme
        model_mat = glm.scale(model_mat, glm.vec3(scale_val, scale_val, scale_val))
        norm_mat = glm.mat3(glm.transpose(glm.inverse(model_mat)))

        self.shader.use()
        self.shader.set_mat4("uModel", model_mat)
        self.shader.set_mat4("uView", view_mat)
        self.shader.set_mat4("uProjection", proj_mat)
        self.shader.set_mat3("uNormalMatrix", norm_mat)
        self.shader.set_vec3("uViewPos", cam_pos)

        # Ativa a deformação esquelética sentada em posição de lótus meditativa
        self.shader.set_int("uIsSitting", 1)

        # Uniformes esqueléticos
        self.shader.set_mat4("uHeadRotation", skeletal_state.head_rotation)
        self.shader.set_vec3("uHeadPivot", glm.vec3(0.0, 325.0, 3.0))
        self.shader.set_float("uBreathingScale", skeletal_state.breathing_scale)
        self.shader.set_mat4("uRightArmRotation", skeletal_state.right_arm_rotation)
        self.shader.set_vec3("uRightShoulderPivot", glm.vec3(38.0, 280.0, 0.0))
        self.shader.set_mat4("uLeftArmRotation", skeletal_state.left_arm_rotation)
        self.shader.set_vec3("uLeftShoulderPivot", glm.vec3(-38.0, 280.0, 0.0))

        # Uniformes faciais e lip sync
        self.shader.set_float("uMouthOpen", facial_params.mouth_open)
        self.shader.set_float("uJawDrop", facial_params.jaw_drop)
        self.shader.set_float("uMouthRound", facial_params.mouth_round)
        self.shader.set_float("uBlinkFactor", facial_params.blink_factor)

        # Desenhar submalhas
        opaque_meshes = [m for m in self.submeshes if not m[1].is_transparent]
        transparent_meshes = [m for m in self.submeshes if m[1].is_transparent]

        for name, submesh in opaque_meshes + transparent_meshes:
            mtype = self.MESH_TYPE_MAP.get(name, 0)
            self.shader.set_int("uMeshType", mtype)

            if submesh.texture:
                submesh.texture.bind(0)
                self.shader.set_int("uTexture", 0)

            glBindVertexArray(submesh.vao)
            glDrawElements(GL_TRIANGLES, submesh.index_count, GL_UNSIGNED_INT, None)
            glBindVertexArray(0)

        glDisable(GL_CULL_FACE)
        glDisable(GL_DEPTH_TEST)

    def cleanup(self) -> None:
        """Liberta buffers e recursos da GPU."""
        for name, submesh in self.submeshes:
            submesh.cleanup()
        self.submeshes.clear()
