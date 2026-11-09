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


CHARACTER_PROFILES: Dict[str, dict] = {
    "remy": {
        "id": "remy",
        "name": "Tracy / Humano",
        "badge": "👩‍🚀 TRACY",
        "role": "Guia Astronómica Terrestre",
        "model_path": "Models/guide_remy.glb",
        "default_texture": "Remy_Body_Diffuse.png",
        "camera_target": glm.vec3(0.0, 350.0, 4.0),
        "camera_distance": 155.0,
        "camera_pitch": 1.5,
        "camera_yaw": 0.0,
        "head_pivot": glm.vec3(0.0, 325.0, 3.0),
        "right_shoulder_pivot": glm.vec3(38.0, 280.0, 0.0),
        "left_shoulder_pivot": glm.vec3(-38.0, 280.0, 0.0),
        "sitting_scale": 1.0 / 260.0,
    },
    "goblin": {
        "id": "goblin",
        "name": "Goblin Cósmico",
        "badge": "👺 GOBLIN D'SHAREYKO",
        "role": "Explorador e Guardião das Sombras",
        "model_path": "Models/guide_goblin.glb",
        "default_texture": "goblin_diffuse.png",
        "camera_target": glm.vec3(0.0, 182.0, 10.0),
        "camera_distance": 135.0,
        "camera_pitch": 1.5,
        "camera_yaw": 0.0,
        "head_pivot": glm.vec3(0.0, 160.0, 5.0),
        "right_shoulder_pivot": glm.vec3(30.0, 140.0, 0.0),
        "left_shoulder_pivot": glm.vec3(-30.0, 140.0, 0.0),
        "sitting_scale": 1.0 / 150.0,
    },
    "mutant": {
        "id": "mutant",
        "name": "Mutante Titã",
        "badge": "🧬 MUTANTE TITÃ",
        "role": "Comandante de Mundos Hostis",
        "model_path": "Models/guide_mutant.glb",
        "default_texture": "mutant_diffuse.png",
        "camera_target": glm.vec3(0.0, 165.0, 12.0),
        "camera_distance": 120.0,
        "camera_pitch": 1.5,
        "camera_yaw": 0.0,
        "head_pivot": glm.vec3(0.0, 142.0, 5.0),
        "right_shoulder_pivot": glm.vec3(32.0, 125.0, 0.0),
        "left_shoulder_pivot": glm.vec3(-32.0, 125.0, 0.0),
        "sitting_scale": 1.0 / 140.0,
    },
    "warrok": {
        "id": "warrok",
        "name": "Warrok Guardião",
        "badge": "🐾 WARROK BASKERVILLE",
        "role": "Guardião Cósmico Feroz",
        "model_path": "Models/guide_warrok.glb",
        "default_texture": "warrok_diffuse.png",
        "camera_target": glm.vec3(0.0, 212.0, 18.0),
        "camera_distance": 160.0,
        "camera_pitch": 1.5,
        "camera_yaw": 0.0,
        "head_pivot": glm.vec3(0.0, 185.0, 10.0),
        "right_shoulder_pivot": glm.vec3(45.0, 160.0, 0.0),
        "left_shoulder_pivot": glm.vec3(-45.0, 160.0, 0.0),
        "sitting_scale": 1.0 / 180.0,
    },
}


class GuideRenderer:
    """
    Renderizador do personagem 3D com câmara e iluminação independentes da cena planetária.
    Pode desenhar numa janela Picture-in-Picture (PiP) ou sobre a interface gráfica.
    Suporta variações em tempo real: Remy (Humano), Goblin, Mutant e Warrok.
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

    def __init__(self, model_path: str = "Models/guide_remy.glb", initial_character: str = "remy"):
        self.shader: Optional[Shader] = None
        self.model: Optional[GLBModel] = None

        self.current_character_id: str = initial_character
        self.submeshes: List[Tuple[str, SubMeshGPU]] = []
        self._character_cache: Dict[str, List[Tuple[str, SubMeshGPU]]] = {}
        self._tex_cache: Dict[str, Texture] = {}

        # Determina o personagem com base no model_path se fornecido explicitamente
        for cid, prof in CHARACTER_PROFILES.items():
            if Path(prof["model_path"]).name == Path(model_path).name:
                self.current_character_id = cid
                break

        profile = CHARACTER_PROFILES.get(self.current_character_id, CHARACTER_PROFILES["remy"])
        self.camera_target = glm.vec3(profile["camera_target"])
        self.camera_distance = float(profile["camera_distance"])
        self.camera_yaw = float(profile["camera_yaw"])
        self.camera_pitch = float(profile["camera_pitch"])
        self.fov = 28.0
        self.head_pivot = glm.vec3(profile["head_pivot"])
        self.right_shoulder_pivot = glm.vec3(profile["right_shoulder_pivot"])
        self.left_shoulder_pivot = glm.vec3(profile["left_shoulder_pivot"])
        self.sitting_scale = float(profile["sitting_scale"])

        self._init_gl()
        self.set_character(self.current_character_id)

    def _init_gl(self) -> None:
        """Compila o shader do guia."""
        vert_path = Path("shaders/guide.vert")
        frag_path = Path("shaders/guide.frag")

        if not vert_path.exists() or not frag_path.exists():
            raise FileNotFoundError("[GuideRenderer] Shaders do guia não encontrados em shaders/")

        self.shader = Shader(vert_path, frag_path)

    def set_character(self, character_id: str) -> None:
        """Altera dinamicamente o modelo 3D, câmara e enquadramento do apresentador cósmico."""
        if character_id not in CHARACTER_PROFILES:
            character_id = "remy"

        self.current_character_id = character_id
        profile = CHARACTER_PROFILES[character_id]

        self.camera_target = glm.vec3(profile["camera_target"])
        self.camera_distance = float(profile["camera_distance"])
        self.camera_yaw = float(profile["camera_yaw"])
        self.camera_pitch = float(profile["camera_pitch"])
        self.head_pivot = glm.vec3(profile["head_pivot"])
        self.right_shoulder_pivot = glm.vec3(profile["right_shoulder_pivot"])
        self.left_shoulder_pivot = glm.vec3(profile["left_shoulder_pivot"])
        self.sitting_scale = float(profile["sitting_scale"])

        if character_id not in self._character_cache:
            self._character_cache[character_id] = self._load_character_model(character_id)

        self.submeshes = self._character_cache[character_id]
        print(f"[GuideRenderer] Modelo ativado: {profile['name']} ({profile['badge']})")

    def _load_character_model(self, character_id: str) -> List[Tuple[str, SubMeshGPU]]:
        """Carrega a malha e texturas correspondentes do modelo GLB do personagem."""
        profile = CHARACTER_PROFILES[character_id]
        model_path = Path(profile["model_path"])

        if not model_path.exists():
            print(f"[GuideRenderer] Aviso: Modelo {model_path} não encontrado, fallback para remy.")
            profile = CHARACTER_PROFILES["remy"]
            model_path = Path(profile["model_path"])

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

        scene = trimesh.load(model_path, process=False)
        submeshes: List[Tuple[str, SubMeshGPU]] = []
        default_tex_name = profile.get("default_texture", "Remy_Body_Diffuse.png")

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
            if character_id == "remy":
                tex_filename = f"Remy_{node_name}_Diffuse.png" if node_name in ["Shoes", "Tops", "Bottoms", "Hair"] else "Remy_Body_Diffuse.png"
            else:
                tex_filename = default_tex_name

            tex_path = Path("textures/guide") / tex_filename

            if tex_path.exists():
                tex_key = str(tex_path)
                if tex_key not in self._tex_cache:
                    self._tex_cache[tex_key] = TextureLoader.load(tex_path, fallback_key="guide")
                sub_texture = self._tex_cache[tex_key]

            is_transparent = node_name in ["Hair", "Eyelashes"]
            submesh_gpu = SubMeshGPU(
                vao=vao,
                vbo=vbo,
                ebo=ebo,
                index_count=len(faces),
                texture=sub_texture,
                is_transparent=is_transparent
            )
            submeshes.append((node_name, submesh_gpu))

        print(f"[GuideRenderer] Modelo '{character_id}' carregado com sucesso: {len(submeshes)} submalhas GPU prontas!")
        return submeshes

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
        self.shader.set_vec3("uHeadPivot", self.head_pivot)
        self.shader.set_float("uBreathingScale", skeletal_state.breathing_scale)
        self.shader.set_mat4("uRightArmRotation", skeletal_state.right_arm_rotation)
        self.shader.set_vec3("uRightShoulderPivot", self.right_shoulder_pivot)
        self.shader.set_mat4("uLeftArmRotation", skeletal_state.left_arm_rotation)
        self.shader.set_vec3("uLeftShoulderPivot", self.left_shoulder_pivot)

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
        scale_val = char_height_target * self.sitting_scale

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
        self.shader.set_vec3("uHeadPivot", self.head_pivot)
        self.shader.set_float("uBreathingScale", skeletal_state.breathing_scale)
        self.shader.set_mat4("uRightArmRotation", skeletal_state.right_arm_rotation)
        self.shader.set_vec3("uRightShoulderPivot", self.right_shoulder_pivot)
        self.shader.set_mat4("uLeftArmRotation", skeletal_state.left_arm_rotation)
        self.shader.set_vec3("uLeftShoulderPivot", self.left_shoulder_pivot)

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
        """Liberta buffers e recursos da GPU de todos os personagens carregados."""
        for cid, mesh_list in self._character_cache.items():
            for name, submesh in mesh_list:
                submesh.cleanup()
        self._character_cache.clear()
        self.submeshes.clear()
        self._tex_cache.clear()
