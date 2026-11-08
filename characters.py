"""
===============================================================================
Módulo: characters.py
Descrição: Personagens 3D "apresentadores" — cada planeta tem o seu personagem.
           Enquanto fala, a cabeça (e os ombros) do personagem aparece num
           RETRATO no canto superior direito do ecrã, ao lado do balão de fala.
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
  - Retrato com viewport próprio: o personagem é desenhado numa região do ecrã
    (glViewport + glScissor) com uma câmara e projeção só suas, enquadrando a
    cabeça a partir das posições dos ossos "Head" e "HeadTop_End".
  - Boca e cabeça ao ritmo da voz: a intensidade do áudio (audio.voice_envelope)
    abre o maxilar (osso "Jaw", quando existe) e acentua os acenos da cabeça.
  - Animação de entrada/saída: o retrato desliza a partir da direita.
  - Iluminação "de estúdio" própria do retrato.
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
    glDisable, glEnable, GL_CULL_FACE, glViewport, glScissor, glClear, glClearColor,
    GL_SCISSOR_TEST, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
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

    def head_frame(self):
        """(centro, tamanho) da cabeça na pose de ligação, no espaço do modelo."""
        idx = self.rig.idx
        head = self.rig.G[idx["Head"]][:3, 3] if "Head" in idx else np.array([0.0, 0.8, 0.0])
        top = self.rig.G[idx["HeadTop_End"]][:3, 3] if "HeadTop_End" in idx else head + [0.0, 0.25, 0.0]
        size = float(max(np.linalg.norm(top - head), 0.08))
        return head + (top - head) * 0.35, size

    def draw(self, shader: Shader, t: float, wave: float, point: float = 0.0,
             point_dir=None, talk: float = 0.0, mouth: float = 0.0) -> None:
        palette = self.rig.palette(t, wave, point, point_dir, talk, mouth)
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
    """Gere e desenha o retrato do personagem que está a falar.
    Quem fala, os gestos e a boca são decididos pelo presentation.py."""

    SLIDE_SECONDS = 0.35     # Duração da entrada/saída do retrato
    GESTURE_RATE = 5.0       # Velocidade das transições entre gestos (1/s)
    MARGIN = 18              # Distância do retrato às margens do ecrã (px)
    TOP = 62                 # Abaixo da barra superior (px)
    BG_COLOR = (0.05, 0.08, 0.16)
    SCENE_CLEAR = (0.01, 0.01, 0.02)   # cor de fundo da cena (main.py)
    # Direção "para o planeta" no espaço do personagem: o retrato está no canto
    # superior direito, por isso o planeta fica à esquerda (direita do personagem) e
    # abaixo. Ângulo moderado (~24°) para a cara continuar virada para quem vê.
    POINT_DIR = (-0.45, -0.3, 1.0)

    def __init__(self, base_dir: Path, shaders_dir: Optional[Path] = None,
                 config_file: str = "characters.json"):
        self.base_dir = Path(base_dir)
        self.config: Dict[str, dict] = {}
        self.defaults = {}
        self._models: Dict[str, Optional[Union[GLBModel, SkinnedCharacterModel]]] = {}
        self._shown_id: Optional[str] = None   # personagem no retrato (fica durante a saída)
        self._slide = 0.0                      # 0 = escondido, 1 = visível
        self._gestures = [0.0, 0.0, 0.0]       # aceno, apontar, falar (suavizados)
        self._mouth = 0.0
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
    def update(self, delta_time: float, speaker_id: Optional[str],
               gestures=(0.0, 0.0, 0.0), mouth: float = 0.0) -> None:
        """`speaker_id`: planeta cujo apresentador está a falar (None = ninguém).
        O retrato entra/sai a deslizar e os gestos mudam suavemente."""
        if speaker_id is not None and self.info_for(speaker_id) is None:
            speaker_id = None
        if speaker_id is not None and speaker_id != self._shown_id:
            if self._slide > 0.05 and self._shown_id is not None:
                speaker_id = None          # primeiro sai o personagem anterior
            else:
                self._shown_id = speaker_id
                self._gestures = [0.0, 0.0, 0.0]
        target = 1.0 if speaker_id is not None else 0.0
        step = delta_time / self.SLIDE_SECONDS
        self._slide = min(target, self._slide + step) if target > self._slide else max(target, self._slide - step)
        k = min(1.0, delta_time * self.GESTURE_RATE)
        for i, g in enumerate(gestures):
            self._gestures[i] += (float(g) - self._gestures[i]) * k
        self._mouth += (float(mouth) - self._mouth) * min(1.0, delta_time * 18.0)

    def portrait_rect(self, screen_w: int, screen_h: int):
        """Retângulo do retrato no ecrã (x, y, largura, altura; origem no canto superior
        esquerdo), ou None se estiver escondido."""
        if self._slide <= 0.0 or self._shown_id is None:
            return None
        size = int(max(160, min(300, screen_h * 0.38)))
        ease = 1.0 - (1.0 - self._slide) ** 3
        x = int(screen_w - (self.MARGIN + size) * ease)
        return x, self.TOP, size, size

    def portrait_name(self) -> Optional[str]:
        entry = self.info_for(self._shown_id)
        return entry.get("character") if entry else None

    def hit_test_screen(self, x: float, y: float, screen_w: int, screen_h: int) -> bool:
        """O clique (coordenadas de ecrã) foi dentro do retrato?"""
        r = self.portrait_rect(screen_w, screen_h)
        return r is not None and r[0] <= x <= r[0] + r[2] and r[1] <= y <= r[1] + r[3]

    def draw_portrait(self, shader: Shader, screen_w: int, screen_h: int, current_time: float) -> None:
        """Desenha a cabeça do personagem no retrato (viewport próprio no canto superior
        direito). `shader` é o celestial (para modelos .glb estáticos)."""
        rect = self.portrait_rect(screen_w, screen_h)
        entry = self.info_for(self._shown_id)
        if rect is None or entry is None:
            return
        model = self._get_model(entry["model"])
        if model is None:
            return
        animated = isinstance(model, SkinnedCharacterModel)

        # Enquadramento da cabeça (no espaço do modelo, de frente para +Z)
        if animated:
            center, size = model.head_frame()
            center = glm.vec3(*center)
        else:
            ext = model.normalized_extents
            size = float(ext[1]) * 0.12
            center = glm.vec3(0.0, float(ext[1]) * 0.5 - size * 0.9, 0.0)
        target = center + glm.vec3(0.0, -size * 0.35, 0.0)
        eye = target + glm.vec3(0.0, size * 0.25, size * 5.2)

        x, y, w, h = rect
        gl_y = screen_h - y - h   # o OpenGL conta y a partir de baixo
        glEnable(GL_SCISSOR_TEST)
        glScissor(x, gl_y, w, h)
        glViewport(x, gl_y, w, h)
        glClearColor(*self.BG_COLOR, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        m = glm.rotate(glm.mat4(1.0), math.radians(-12.0), glm.vec3(0.0, 1.0, 0.0))   # vista a 3/4
        view = glm.lookAt(eye, target, glm.vec3(0.0, 1.0, 0.0))
        proj = glm.perspective(glm.radians(30.0), w / max(h, 1), size * 0.5, size * 40.0)
        light = eye + glm.vec3(-size * 6.0, size * 7.0, size * 3.0)

        prog = self.skinned_shader if animated else shader
        prog.use()
        prog.set_mat4("uModel", m)
        prog.set_mat4("uView", view)
        prog.set_mat4("uProjection", proj)
        prog.set_mat3("uNormalMatrix", glm.mat3(glm.transpose(glm.inverse(m))))
        prog.set_vec3("uLightPos", light)
        prog.set_vec3("uLightColor", glm.vec3(1.0, 0.97, 0.92))
        prog.set_vec3("uViewPos", eye)
        prog.set_vec3("uAmbientColor", glm.vec3(0.42, 0.42, 0.48))
        prog.set_float("uShininess", 24.0)
        prog.set_float("uSpecularStrength", 0.25)
        prog.set_int("uTexture", 0)

        glDisable(GL_CULL_FACE)   # cabelo e roupa têm faces visíveis dos dois lados
        if animated:
            wave, point, talk = self._gestures
            model.draw(prog, current_time, wave, point, self.POINT_DIR, talk, self._mouth)
        else:
            model.draw()
        glEnable(GL_CULL_FACE)

        # Repõe o estado da cena principal
        glDisable(GL_SCISSOR_TEST)
        glViewport(0, 0, screen_w, screen_h)
        glClearColor(*self.SCENE_CLEAR, 1.0)

    def cleanup(self) -> None:
        for m in self._models.values():
            if m is not None:
                m.cleanup()
        self._models.clear()
