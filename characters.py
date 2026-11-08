"""
===============================================================================
Módulo: characters.py
Descrição: Personagens 3D "apresentadores" — cada planeta tem o seu personagem,
           que aparece ao lado do planeta quando este é focado
           (teclas 1–8, TAB ou clique com o rato).
Conceitos aplicados:
  - Configuração orientada por dados (characters.json): trocar um personagem
    não exige alterar código.
  - Dois tipos de modelo:
      * .npz (gerado por tools/fbx_to_glb.py): personagem ANIMADO — malha com
        esqueleto e pesos de pele; a pose é calculada a cada frame por
        character_rig.py (animação procedural) e aplicada na GPU pelo
        shaders/skinned.vert (Linear Blend Skinning).
      * .glb: personagem ESTÁTICO (carregado pelo GLBModel existente).
  - Carregamento preguiçoso (lazy loading) com cache: cada modelo só é
    lido e enviado para a GPU na primeira vez que o seu planeta é focado.
  - Posicionamento relativo à câmara: o personagem fica à direita do planeta
    no plano da câmara (vetor camera.right), à escala do raio visual do planeta.
  - Rotação em Y para ficar virado para a câmara, mais flutuação suave.
  - Animação de entrada (escala 0 -> 1 com easing) e aceno ao trocar de planeta.
  - Iluminação "de estúdio": luz posicionada junto à câmara para o personagem
    estar sempre visível, mesmo quando o planeta está no lado noturno.
===============================================================================
"""

import ctypes
import io
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Union

import glm
import numpy as np
from PIL import Image
from OpenGL.GL import (
    glDisable, glEnable, GL_CULL_FACE,
    glGenVertexArrays, glBindVertexArray, glGenBuffers, glBindBuffer, glBufferData,
    glVertexAttribPointer, glEnableVertexAttribArray, glDrawElements,
    glDeleteVertexArrays, glDeleteBuffers, glGetIntegerv, glUniformMatrix4fv,
    glGenTextures, glBindTexture, glTexImage2D, glGenerateMipmap, glTexParameteri,
    GL_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW, GL_FLOAT, GL_FALSE,
    GL_TRIANGLES, GL_UNSIGNED_INT, GL_MAX_VERTEX_UNIFORM_COMPONENTS,
    GL_TEXTURE_2D, GL_RGB, GL_RGBA, GL_UNSIGNED_BYTE, GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T,
    GL_REPEAT, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_LINEAR, GL_LINEAR_MIPMAP_LINEAR,
)

from character_rig import ProceduralRig
from model_loader import GLBModel
from shader import Shader
from texture import Texture

MAX_BONES = 128   # tem de coincidir com MAX_BONES em shaders/skinned.vert


def _upload_texture(img: Image.Image) -> Texture:
    """Envia uma imagem PIL para a GPU com mipmaps (mesma convenção do GLBModel)."""
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    if img.mode != "RGBA":
        img = img.convert("RGB")
    fmt = GL_RGBA if img.mode == "RGBA" else GL_RGB
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexImage2D(GL_TEXTURE_2D, 0, fmt, img.width, img.height, 0, fmt, GL_UNSIGNED_BYTE, img.tobytes())
    glGenerateMipmap(GL_TEXTURE_2D)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    return Texture(tex_id, img.width, img.height)


class SkinnedCharacterModel:
    """Personagem animado (.npz): malhas com ossos/pesos + esqueleto procedural."""

    height = 2.0   # o conversor normaliza a altura para 2.0

    def __init__(self, path: Path):
        data = np.load(path, allow_pickle=False)
        self.rig = ProceduralRig(data["bone_names"], data["bone_parents"], data["bone_bind"])
        if self.rig.count > MAX_BONES:
            raise ValueError(f"{self.rig.count} ossos (máximo {MAX_BONES})")
        self._parts: List[tuple] = []   # (vao, vbo, ebo, n_indices, texture)
        for k in range(int(data["submesh_count"])):
            pos = data[f"sm{k}_positions"]
            inter = np.concatenate([
                pos, data[f"sm{k}_normals"], data[f"sm{k}_uvs"],
                data[f"sm{k}_joints"].astype(np.float32), data[f"sm{k}_weights"],
            ], axis=1).astype(np.float32)
            faces = data[f"sm{k}_faces"].astype(np.uint32).reshape(-1)
            img = Image.open(io.BytesIO(data[f"sm{k}_image"].tobytes()))
            img.load()

            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)
            vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, inter.nbytes, inter, GL_STATIC_DRAW)
            ebo = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, faces.nbytes, faces, GL_STATIC_DRAW)
            stride = 16 * 4   # pos 3 + normal 3 + uv 2 + joints 4 + weights 4
            for loc, size, offset in ((0, 3, 0), (1, 3, 3), (2, 2, 6), (3, 4, 8), (4, 4, 12)):
                glVertexAttribPointer(loc, size, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset * 4))
                glEnableVertexAttribArray(loc)
            glBindVertexArray(0)
            self._parts.append((vao, vbo, ebo, len(faces), _upload_texture(img)))

    def draw(self, shader: Shader, t: float, wave: float) -> None:
        palette = self.rig.palette(t, wave)
        loc = shader.get_uniform_location("uBones")
        if loc != -1:
            glUniformMatrix4fv(loc, len(palette), GL_FALSE, np.ascontiguousarray(palette.transpose(0, 2, 1)))
        for vao, _, _, n, tex in self._parts:
            tex.bind(0)
            glBindVertexArray(vao)
            glDrawElements(GL_TRIANGLES, n, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def cleanup(self) -> None:
        for vao, vbo, ebo, _, tex in self._parts:
            glDeleteVertexArrays(1, [vao])
            glDeleteBuffers(1, [vbo])
            glDeleteBuffers(1, [ebo])
            tex.cleanup()
        self._parts.clear()


class PlanetCharacters:
    """Gere e desenha o personagem apresentador do planeta selecionado."""

    APPEAR_SECONDS = 0.6                 # Duração da animação de entrada
    WAVE_IN, WAVE_HOLD, WAVE_OUT = 0.35, 2.4, 0.6   # Aceno: subir, acenar, baixar (s)

    def __init__(self, base_dir: Path, shaders_dir: Optional[Path] = None,
                 config_file: str = "characters.json"):
        self.base_dir = Path(base_dir)
        self.config: Dict[str, dict] = {}
        self.defaults = {"height_factor": 1.4, "side_offset": 2.1}
        self._models: Dict[str, Optional[Union[GLBModel, SkinnedCharacterModel]]] = {}
        self._active_id: Optional[str] = None
        self._since = 0.0      # segundos desde que o planeta atual foi selecionado
        self.skinned_shader: Optional[Shader] = None
        self._load_config(self.base_dir / config_file)

        shaders_dir = Path(shaders_dir) if shaders_dir else self.base_dir / "shaders"
        try:
            max_comp = int(glGetIntegerv(GL_MAX_VERTEX_UNIFORM_COMPONENTS))
            if max_comp < MAX_BONES * 16 + 64:
                raise RuntimeError(f"GPU só aceita {max_comp} componentes uniformes no vertex shader")
            self.skinned_shader = Shader(shaders_dir / "skinned.vert", shaders_dir / "celestial.frag")
        except Exception as e:
            print(f"[Personagens Warning] Animação desligada ({e}); personagens .npz não serão mostrados.")

    # ------------------------------------------------------------------ config
    def _load_config(self, path: Path) -> None:
        if not path.exists():
            print(f"[Personagens] {path.name} não encontrado — planetas sem apresentador.")
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Personagens Warning] Erro ao ler {path.name}: {e}")
            return
        self.defaults.update(raw.get("defaults", {}))
        self.config = {k: v for k, v in raw.get("planets", {}).items() if isinstance(v, dict)}
        n = sum(1 for v in self.config.values() if v.get("model"))
        print(f"[Personagens] {n} apresentadores configurados em {path.name}.")

    def info_for(self, body_id: Optional[str]) -> Optional[dict]:
        """Dados do personagem de um planeta (para o painel da UI), ou None."""
        entry = self.config.get(body_id or "")
        if not entry or not entry.get("model"):
            return None
        return entry

    def _get_model(self, rel_path: str):
        if rel_path not in self._models:
            path = self.base_dir / rel_path
            try:
                if path.suffix.lower() == ".npz":
                    if self.skinned_shader is None:
                        raise RuntimeError("shader de skinning indisponível")
                    self._models[rel_path] = SkinnedCharacterModel(path)
                else:
                    self._models[rel_path] = GLBModel(path)
                print(f"[Personagens] Modelo carregado: {path.name}")
            except Exception as e:
                self._models[rel_path] = None
                print(f"[Personagens Warning] Falha ao carregar {rel_path}: {e}")
        return self._models[rel_path]

    # ------------------------------------------------------------------ ciclo
    def update(self, delta_time: float, selected_id: Optional[str]) -> None:
        """Reinicia as animações de entrada e de aceno quando muda o planeta selecionado."""
        if selected_id != self._active_id:
            self._active_id = selected_id
            self._since = 0.0
        else:
            self._since += delta_time

    def _wave_weight(self) -> float:
        """0 → 1 (sobe o braço) → acena → 0 (baixa), com transições suaves."""
        t = self._since - self.APPEAR_SECONDS * 0.5
        a, b, c = self.WAVE_IN, self.WAVE_IN + self.WAVE_HOLD, self.WAVE_IN + self.WAVE_HOLD + self.WAVE_OUT

        def smooth(x: float) -> float:
            x = max(0.0, min(1.0, x))
            return x * x * (3 - 2 * x)

        if t <= 0 or t >= c:
            return 0.0
        if t < a:
            return smooth(t / a)
        if t < b:
            return 1.0
        return 1.0 - smooth((t - b) / (c - b))

    def draw(
        self,
        shader: Shader,
        view: glm.mat4,
        proj: glm.mat4,
        camera,
        body,
        current_time: float,
    ) -> None:
        """Desenha o personagem do planeta `body` (objeto CelestialBody selecionado).
        `shader` é o celestial (para modelos .glb estáticos)."""
        if body is None:
            return
        entry = self.info_for(self._active_id)
        if entry is None:
            return
        model = self._get_model(entry["model"])
        if model is None:
            return
        animated = isinstance(model, SkinnedCharacterModel)

        radius = float(body.visual_radius)
        height = radius * float(entry.get("height_factor", self.defaults["height_factor"]))
        side = radius * float(entry.get("side_offset", self.defaults["side_offset"]))

        # Animação de entrada com easing (ease-out-back: cresce e assenta)
        t = min(1.0, self._since / self.APPEAR_SECONDS)
        c = 1.70158
        appear = 1.0 + (c + 1.0) * (t - 1.0) ** 3 + c * (t - 1.0) ** 2 if t > 0.0 else 0.0
        if appear <= 0.001:
            return

        # Posição: à direita do planeta no plano da câmara, a flutuar ligeiramente
        bob = math.sin(current_time * 1.6) * radius * 0.06
        pos = glm.vec3(body.current_position) + camera.right * side + camera.up * bob

        # Rotação em Y para ficar de frente para a câmara. Os personagens animados já
        # mexem o corpo sozinhos; os estáticos ganham um balanço suave.
        to_cam = camera.position - pos
        yaw = math.atan2(to_cam.x, to_cam.z)
        if not animated:
            yaw += math.sin(current_time * 0.9) * math.radians(12.0)

        model_height = model.height if animated else float(model.normalized_extents[1])
        scale = (height / max(model_height, 1e-6)) * appear

        m = glm.mat4(1.0)
        m = glm.translate(m, pos)
        m = glm.rotate(m, yaw, glm.vec3(0.0, 1.0, 0.0))
        m = glm.scale(m, glm.vec3(scale))
        normal_matrix = glm.mat3(glm.transpose(glm.inverse(m)))

        # Luz "de estúdio": acima e atrás da câmara, para o personagem nunca ficar às escuras
        light_pos = camera.position + camera.up * (radius * 4.0) + camera.right * (radius * 2.0)

        prog = self.skinned_shader if animated else shader
        prog.use()
        prog.set_mat4("uModel", m)
        prog.set_mat4("uView", view)
        prog.set_mat4("uProjection", proj)
        prog.set_mat3("uNormalMatrix", normal_matrix)
        prog.set_vec3("uLightPos", light_pos)
        prog.set_vec3("uLightColor", glm.vec3(1.0, 0.97, 0.92))
        prog.set_vec3("uViewPos", camera.position)
        prog.set_vec3("uAmbientColor", glm.vec3(0.38, 0.38, 0.42))
        prog.set_float("uShininess", 24.0)
        prog.set_float("uSpecularStrength", 0.25)
        prog.set_int("uTexture", 0)

        # Algumas malhas (cabelo, roupa) têm faces viradas para os dois lados
        glDisable(GL_CULL_FACE)
        if animated:
            model.draw(prog, current_time, self._wave_weight())
        else:
            model.draw()
        glEnable(GL_CULL_FACE)

    def cleanup(self) -> None:
        for m in self._models.values():
            if m is not None:
                m.cleanup()
        self._models.clear()
