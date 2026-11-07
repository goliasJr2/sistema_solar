"""
===============================================================================
Módulo: galaxy.py
Descrição: Galáxia Espiral Tridimensional Completa (Via Láctea) com 4 Braços Logarítmicos.
Conceitos aplicados:
  - Astrofísica Gráfica e Modelagem Matemática de Galáxias Espirais:
      * 4 Braços Principais definidos por Espirais Logarítmicas: r = a * exp(b * theta).
      * Bojo Galáctico Central (Bulge) elipsoidal com densidade exponencial decrescente.
      * Disco Galáctico Fino (Thin Disk) com estrelas jovens azuis/brancas nos braços.
      * Populações Estelares: População II amarela/laranja no centro; População I azul nos braços.
      * Faixas de poeira cósmica interestelar escura (Dust lanes).
  - Sistemas Estelares Vizinhos e Exoplaneta de Lava (corot_7c_hot_earth.glb).
  - Posição do Sistema Solar: Localizado no Braço de Órion, a ~2200 unidades do centro.
  - Marcador Visual "ESTÁS AQUI" identificando a posição do Sol na imensidão galáctica.
===============================================================================
"""

from pathlib import Path
from typing import List, Tuple, Optional
import math
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
    GL_STATIC_DRAW,
    GL_FLOAT,
    GL_POINTS,
    GL_FALSE,
    GL_PROGRAM_POINT_SIZE,
    GL_BLEND,
    GL_SRC_ALPHA,
    GL_ONE,
    GL_ONE_MINUS_SRC_ALPHA,
)

from shader import Shader
from model_loader import GLBModel


# Posição do Sistema Solar em relação ao Centro Galáctico (Sagitário A* em (0, 0, -2200))
# Portanto o Sistema Solar fica em (0, 0, 0) e a Galáxia tem o centro em (0, 0, -2200)
GALAXY_CENTER_POS = glm.vec3(0.0, 0.0, -2200.0)
GALAXY_RADIUS = 3500.0


class SpiralGalaxy:
    """
    Representa a galáxia espiral completa com centenas de milhares de estrelas,
    braços espirais logarítmicos, bojo luminoso e sistemas vizinhos.
    """

    def __init__(self, models_dir: Path, num_stars: int = 250000):
        self.num_stars = num_stars
        self.center = GALAXY_CENTER_POS
        self.radius = GALAXY_RADIUS

        self.vao = 0
        self.vbo = 0

        # Exoplaneta de lava vizinho (corot_7c_hot_earth.glb)
        self.exoplanet_model: Optional[GLBModel] = None
        p_corot = models_dir / "corot_7c_hot_earth.glb"
        if p_corot.exists():
            try:
                self.exoplanet_model = GLBModel(p_corot)
                print(f"[Galáxia 3D] Exoplaneta CoRoT-7b carregado: {p_corot.name}")
            except Exception as e:
                print(f"[Galáxia Warning] Falha ao carregar corot_7c_hot_earth.glb: {e}")

        # Posição do sistema estelar vizinho (Alfa Centauri e CoRoT-7b)
        self.neighbor_system_pos = self.center + glm.vec3(320.0, 45.0, 2100.0)

        self._generate_spiral_galaxy()

    def _generate_spiral_galaxy(self) -> None:
        """Gera as estrelas da galáxia seguindo distribuição física realista."""
        np.random.seed(1337)
        num_stars = self.num_stars

        # 1. 25% das estrelas compõem o Bojo Central (Bulge)
        num_bulge = int(num_stars * 0.25)
        # 2. 75% das estrelas distribuídas nos 4 braços espirais e disco
        num_arms = num_stars - num_bulge

        # Arrays para guardar atributos: [pos(3), col(3), size(1)] -> 7 floats
        data = np.empty((num_stars, 7), dtype=np.float32)

        # ---------------------------------------------------------------------
        # GERAÇÃO DO BOJO CENTRAL (BULBO GALÁCTICO)
        # ---------------------------------------------------------------------
        # Distribuição esferoidal achatada com densidade decrescente exponencial
        r_bulge = np.random.exponential(scale=200.0, size=num_bulge) + 15.0
        r_bulge = np.clip(r_bulge, 0.0, 550.0)
        phi_bulge = np.random.uniform(0.0, 2.0 * np.pi, size=num_bulge)
        theta_bulge = np.random.uniform(-np.pi * 0.5, np.pi * 0.5, size=num_bulge)

        bx = r_bulge * np.cos(theta_bulge) * np.cos(phi_bulge)
        by = r_bulge * np.sin(theta_bulge) * 0.45  # Achatado verticalmente
        bz = r_bulge * np.cos(theta_bulge) * np.sin(phi_bulge)

        data[:num_bulge, 0] = bx + self.center.x
        data[:num_bulge, 1] = by + self.center.y
        data[:num_bulge, 2] = bz + self.center.z

        # Cores quentes do bojo: Amarelo-dourado, Âmbar, Laranja e Branco antigo
        b_r = np.random.uniform(0.95, 1.0, size=num_bulge)
        b_g = np.random.uniform(0.75, 0.95, size=num_bulge)
        b_b = np.random.uniform(0.40, 0.70, size=num_bulge)
        b_size = np.random.uniform(1.2, 3.5, size=num_bulge)

        data[:num_bulge, 3] = b_r
        data[:num_bulge, 4] = b_g
        data[:num_bulge, 5] = b_b
        data[:num_bulge, 6] = b_size

        # ---------------------------------------------------------------------
        # GERAÇÃO DOS 4 BRAÇOS ESPIRAIS LOGARÍTMICOS
        # ---------------------------------------------------------------------
        # Braços: Perseus, Scutum-Centaurus, Sagitário e Norma
        num_arms_count = 4
        arm_indices = np.random.randint(0, num_arms_count, size=num_arms)
        base_angles = arm_indices * (2.0 * np.pi / num_arms_count)

        # Distância radial ao centro galáctico
        r_arms = np.random.uniform(150.0, self.radius, size=num_arms)
        # Parâmetro da espiral logarítmica: theta = log(r / a) / b
        b_param = 0.42
        a_param = 120.0
        theta_spiral = (1.0 / b_param) * np.log(r_arms / a_param) + base_angles

        # Dispersão transversal em torno do eixo central do braço
        dispersion_rad = np.random.normal(0.0, 0.28, size=num_arms)
        theta_final = theta_spiral + dispersion_rad

        # Dispersão radial adicional
        r_final = r_arms + np.random.normal(0.0, 60.0, size=num_arms)

        # Espessura vertical do disco fino (thin disk): ~60 unidades perto, afinando nas bordas
        z_disp = np.random.normal(0.0, 35.0, size=num_arms) * (1.0 - (r_arms / self.radius) * 0.4)

        ax = r_final * np.cos(theta_final)
        az = r_final * np.sin(theta_final)
        ay = z_disp

        data[num_bulge:, 0] = ax + self.center.x
        data[num_bulge:, 1] = ay + self.center.y
        data[num_bulge:, 2] = az + self.center.z

        # Cores dos braços: Estrelas azuis quentes, brancas e regiões H-II rosa/ciano
        # Fração de estrelas azuis vs brancas
        is_blue = np.random.rand(num_arms) > 0.45
        arm_r = np.where(is_blue, np.random.uniform(0.65, 0.85, size=num_arms), np.random.uniform(0.85, 1.0, size=num_arms))
        arm_g = np.where(is_blue, np.random.uniform(0.80, 0.95, size=num_arms), np.random.uniform(0.85, 0.98, size=num_arms))
        arm_b = np.where(is_blue, np.random.uniform(0.95, 1.00, size=num_arms), np.random.uniform(0.80, 0.95, size=num_arms))
        arm_size = np.random.uniform(1.0, 2.8, size=num_arms)

        data[num_bulge:, 3] = arm_r
        data[num_bulge:, 4] = arm_g
        data[num_bulge:, 5] = arm_b
        data[num_bulge:, 6] = arm_size

        # ---------------------------------------------------------------------
        # CRIAÇÃO DOS BUFFERS OPENGL CORE 3.3
        # ---------------------------------------------------------------------
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)

        stride = 7 * 4
        # Atributo 0: Pos (3 floats)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        # Atributo 1: Cor (3 floats, offset 12)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)
        # Atributo 2: Tamanho (1 float, offset 24)
        glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))
        glEnableVertexAttribArray(2)

        glBindVertexArray(0)
        print(f"[Galáxia] {num_stars:,} estrelas geradas nos 4 braços espirais com sucesso!")

    def draw(
        self,
        starfield_shader: Shader,
        celestial_shader: Shader,
        view: glm.mat4,
        proj: glm.mat4,
        view_pos: glm.vec3,
        current_time: float,
    ) -> None:
        """Renderiza a galáxia espiral e os sistemas vizinhos."""
        # 1. Renderização das estrelas da galáxia com blending aditivo
        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        starfield_shader.use()
        starfield_shader.set_mat4("uView", view)
        starfield_shader.set_mat4("uProjection", proj)
        starfield_shader.set_float("uTime", current_time * 0.4)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_POINTS, 0, self.num_stars)
        glBindVertexArray(0)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # 2. Renderização do Exoplaneta CoRoT-7b (Lava) no sistema vizinho
        if self.exoplanet_model:
            celestial_shader.use()
            m = glm.mat4(1.0)
            m = glm.translate(m, self.neighbor_system_pos)
            m = glm.rotate(m, float(current_time * 15.0), glm.vec3(0.0, 1.0, 0.0))
            m = glm.scale(m, glm.vec3(12.0))
            norm_m = glm.mat3(glm.transpose(glm.inverse(m)))

            celestial_shader.set_mat4("uModel", m)
            celestial_shader.set_mat4("uView", view)
            celestial_shader.set_mat4("uProjection", proj)
            celestial_shader.set_mat3("uNormalMatrix", norm_m)
            celestial_shader.set_vec3("uLightPos", self.neighbor_system_pos + glm.vec3(25.0, 10.0, 0.0))
            celestial_shader.set_vec3("uLightColor", glm.vec3(1.0, 0.6, 0.2))  # Estrela anã laranja
            celestial_shader.set_vec3("uViewPos", view_pos)
            celestial_shader.set_vec3("uAmbientColor", glm.vec3(0.4, 0.15, 0.05))  # Crosta de lava incandescente
            celestial_shader.set_float("uShininess", 16.0)
            celestial_shader.set_float("uSpecularStrength", 0.3)

            self.exoplanet_model.draw()
