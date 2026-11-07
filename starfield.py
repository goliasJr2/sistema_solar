"""
===============================================================================
Módulo: starfield.py
Descrição: Renderização do fundo espacial com estrelas em OpenGL 3.3 Core Profile.
Conceitos aplicados:
  - Primitivas do OpenGL: GL_POINTS com glEnable(GL_PROGRAM_POINT_SIZE).
  - Geração Procedural 3D: Distribuição aleatória uniforme sobre uma esfera cósmica.
  - Astrofísica Gráfica: Classes espectrais estelares reais (Cores O, B, A, F, G, K, M).
  - Shaders para Partículas: Redimensionamento e cintilação dinâmica no Vertex Shader;
    desenho de discos suaves via gl_PointCoord no Fragment Shader.
===============================================================================
"""

import math
import random
import ctypes
from typing import List
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
    GL_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_FLOAT,
    GL_POINTS,
    GL_FALSE,
    GL_PROGRAM_POINT_SIZE,
    GL_BLEND,
    glBlendFunc,
    GL_SRC_ALPHA,
    GL_ONE,
    GL_ONE_MINUS_SRC_ALPHA,
)

from shader import Shader


class Starfield:
    """
    Gere milhares de estrelas no fundo cósmico tridimensional.
    """

    def __init__(self, num_stars: int = 4000, radius: float = 3500.0):
        self.num_stars = num_stars
        self.radius = radius

        self.vao = 0
        self.vbo = 0

        self._build_starfield()

    def _build_starfield(self) -> None:
        """
        Gera estrelas distribuídas uniformemente na casca esférica do cosmos
        com cores espectrais e magnitudes estelares variadas.
        """
        # Paleta de cores espectrais de estrelas (O=Azul, A=Branco, G=Amarelo, M=Vermelho)
        spectral_colors = [
            (0.72, 0.82, 1.00),  # Classe O/B: Azul-celeste
            (0.85, 0.90, 1.00),  # Classe A: Branco-azulado
            (1.00, 1.00, 1.00),  # Classe F: Branco
            (1.00, 0.96, 0.82),  # Classe G: Amarelo solar
            (1.00, 0.82, 0.60),  # Classe K: Laranja
            (1.00, 0.60, 0.45),  # Classe M: Vermelho rubro
        ]

        vertices: List[float] = []

        random.seed(1337)
        for _ in range(self.num_stars):
            # Distribuição uniforme sobre a superfície de uma esfera:
            # z varia uniformemente entre -1 e 1; theta varia entre 0 e 2*pi
            z_norm = random.uniform(-1.0, 1.0)
            phi = math.asin(z_norm)
            theta = random.uniform(0.0, 2.0 * math.pi)

            # Variação radial ligeira para conferir profundidade volumétrica
            r = self.radius * random.uniform(0.90, 1.10)

            x = r * math.cos(phi) * math.cos(theta)
            y = r * math.sin(phi)
            z = r * math.cos(phi) * math.sin(theta)

            # Cor espectral aleatória com pesos (mais estrelas brancas/amarelas)
            color = random.choice(spectral_colors)

            # Tamanho da estrela (magnitude visual: a maioria é pequena; algumas são brilhantes)
            size = random.triangular(1.5, 4.5, 2.0)

            # Estrutura intercalada: [pos.x, pos.y, pos.z, col.r, col.g, col.b, size]
            vertices.extend([x, y, z, color[0], color[1], color[2], size])

        vertices_array = np.array(vertices, dtype=np.float32)

        # Configuração do VAO e VBO para os pontos
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices_array.nbytes, vertices_array, GL_STATIC_DRAW)

        # Stride = 7 floats * 4 bytes = 28 bytes
        stride = 7 * 4

        # Atributo 0: Posição (3 floats)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Atributo 1: Cor (3 floats, offset = 12 bytes)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        # Atributo 2: Tamanho (1 float, offset = 24 bytes)
        glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))
        glEnableVertexAttribArray(2)

        glBindVertexArray(0)

    def draw(self, shader: Shader, view: glm.mat4, projection: glm.mat4, current_time: float) -> None:
        """Renderiza todas as estrelas com blending aditivo e tamanho de ponto ajustável."""
        # Ativa o controlo de dimensão dos pontos a partir do Vertex Shader
        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Blending aditivo para estrelas luminosas

        shader.use()
        shader.set_mat4("uView", view)
        shader.set_mat4("uProjection", projection)
        shader.set_float("uTime", current_time)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_POINTS, 0, self.num_stars)
        glBindVertexArray(0)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
