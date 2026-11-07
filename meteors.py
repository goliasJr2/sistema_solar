"""
===============================================================================
Módulo: meteors.py
Descrição: Sistema de Chuva de Meteoros e explosões de bólides (Tecla M).
Conceitos aplicados:
  - Sistema de Partículas em Tempo Real com Tempo de Vida (Lifetime) e Fade.
  - Modelo 3D de Fragmentação: boros_meteoric_burst.glb.
  - Renderização com Blending Aditivo (GL_SRC_ALPHA, GL_ONE) e Linhas de Rasto.
===============================================================================
"""

from pathlib import Path
from typing import List, Optional
import random
import ctypes
import numpy as np
import glm
from OpenGL.GL import (
    glGenVertexArrays,
    glBindVertexArray,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glVertexAttribPointer,
    glEnableVertexAttribArray,
    glDrawArrays,
    glEnable,
    glDisable,
    glBlendFunc,
    GL_ARRAY_BUFFER,
    GL_DYNAMIC_DRAW,
    GL_FLOAT,
    GL_LINES,
    GL_FALSE,
    GL_BLEND,
    GL_SRC_ALPHA,
    GL_ONE,
    GL_ONE_MINUS_SRC_ALPHA,
)

from model_loader import GLBModel
from shader import Shader


class MeteorParticle:
    """Representa um meteoro individual com rasto luminoso."""

    def __init__(self, target_center: glm.vec3):
        self.reset(target_center)

    def reset(self, center: glm.vec3) -> None:
        """Reinicia o meteoro numa posição aleatória no topo da atmosfera."""
        offset = glm.vec3(
            random.uniform(-40.0, 40.0),
            random.uniform(25.0, 50.0),
            random.uniform(-40.0, 40.0),
        )
        self.pos = center + offset
        # Trajetória descendente veloz
        self.velocity = glm.vec3(
            random.uniform(-15.0, 15.0),
            random.uniform(-70.0, -110.0),
            random.uniform(-15.0, 15.0),
        )
        self.length = random.uniform(3.0, 7.0)
        self.life = 1.0
        self.decay = random.uniform(0.6, 1.4)

    def update(self, dt: float, center: glm.vec3) -> None:
        self.pos += self.velocity * dt
        self.life -= self.decay * dt
        if self.life <= 0.0:
            self.reset(center)


class MeteorShower:
    """Gere a chuva de meteoros e o efeito boros_meteoric_burst.glb."""

    def __init__(self, models_dir: Path, num_meteors: int = 50):
        self.is_active = False
        self.num_meteors = num_meteors

        self.burst_model: Optional[GLBModel] = None
        p = models_dir / "boros_meteoric_burst.glb"
        if p.exists():
            try:
                self.burst_model = GLBModel(p)
                print(f"[Meteoros 3D] Modelo de explosão carregado: {p.name}")
            except Exception as e:
                print(f"[Meteoros Warning] Falha ao carregar boros_meteoric_burst.glb: {e}")

        self.meteors = [MeteorParticle(glm.vec3(0.0, 0.0, 60.0)) for _ in range(num_meteors)]

        # VAO e VBO para renderização das linhas de rasto dos meteoros
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, num_meteors * 2 * 6 * 4, None, GL_DYNAMIC_DRAW)

        stride = 6 * 4
        # Atributo 0: Pos (3 floats)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        # Atributo 1: Cor com Alpha (3 floats)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

    def toggle(self) -> bool:
        """Alterna o estado da chuva de meteoros (Tecla M)."""
        self.is_active = not self.is_active
        print(f"[Simulador] Chuva de Meteoros (Tecla M): {'LIGADA' if self.is_active else 'DESLIGADA'}")
        return self.is_active

    def update(self, dt: float, target_pos: glm.vec3) -> None:
        if not self.is_active:
            return
        for m in self.meteors:
            m.update(dt, target_pos)

    def draw(self, orbit_shader: Shader, view: glm.mat4, proj: glm.mat4) -> None:
        """Renderiza as caudas incandescentes dos meteoros."""
        if not self.is_active:
            return

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Blending aditivo incandescente

        orbit_shader.use()
        orbit_shader.set_mat4("uModel", glm.mat4(1.0))
        orbit_shader.set_mat4("uView", view)
        orbit_shader.set_mat4("uProjection", proj)

        line_vertices = []
        for m in self.meteors:
            if m.life > 0.0:
                head = m.pos
                tail = m.pos - glm.normalize(m.velocity) * m.length

                # [x, y, z, r, g, b]
                orbit_shader.set_vec4("uOrbitColor", glm.vec4(1.0, 0.85, 0.4, m.life))
                line_vertices.extend([head.x, head.y, head.z, tail.x, tail.y, tail.z])

        if line_vertices:
            v_data = np.array(line_vertices, dtype=np.float32)
            glBindVertexArray(self.vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, v_data.nbytes, v_data, GL_DYNAMIC_DRAW)
            glDrawArrays(GL_LINES, 0, len(line_vertices) // 3)
            glBindVertexArray(0)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
