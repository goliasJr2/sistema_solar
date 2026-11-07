"""
===============================================================================
Módulo: mesh.py
Descrição: Geração procedural de geometrias 3D em OpenGL Core Profile 3.3.
Conceitos aplicados:
  - Geometria e Coordenadas 3D: Conversão de coordenadas polares/esféricas
    (latitude e longitude) para cartesianas (X, Y, Z).
  - Cálculo de vetores normais unitários para modelos esféricos.
  - Mapeamento UV planar sobre superfícies curvas (texturização de esferas).
  - Estruturas de Dados do OpenGL:
      * VAO (Vertex Array Object): encapsula configurações de atributos.
      * VBO (Vertex Buffer Object): transfere posições, normais e UVs para a GPU.
      * EBO (Element Buffer Object): indexação de vértices para partilha entre triângulos.
===============================================================================
"""

import math
import ctypes
from typing import List, Tuple
import numpy as np
from OpenGL.GL import (
    glGenVertexArrays,
    glBindVertexArray,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glVertexAttribPointer,
    glEnableVertexAttribArray,
    glDrawElements,
    glDrawArrays,
    glDeleteVertexArrays,
    glDeleteBuffers,
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_FLOAT,
    GL_UNSIGNED_INT,
    GL_TRIANGLES,
    GL_LINE_LOOP,
    GL_FALSE,
)


class SphereMesh:
    """
    Malha esférica UV gerada proceduralmente por código matemático.
    Suporta parametrização de resolução por stacks (latitude) e slices (longitude).
    """

    def __init__(self, radius: float = 1.0, stacks: int = 48, slices: int = 64):
        self.radius = radius
        self.stacks = stacks
        self.slices = slices
        self.index_count = 0

        self.vao = 0
        self.vbo = 0
        self.ebo = 0

        self._build_mesh()

    def _build_mesh(self) -> None:
        """
        Gera os vértices através de equações paramétricas esféricas:
          x = r * sin(phi) * cos(theta)
          y = r * cos(phi)
          z = r * sin(phi) * sin(theta)
        """
        vertices: List[float] = []
        indices: List[int] = []

        # 1. Geração dos vértices (Posição, Normal, Coordenadas UV)
        for i in range(self.stacks + 1):
            # phi varia de 0 (polo norte) até pi (polo sul)
            phi = math.pi * float(i) / float(self.stacks)
            v = 1.0 - float(i) / float(self.stacks)

            for j in range(self.slices + 1):
                # theta varia de 0 a 2*pi (rotação completa em longitude)
                theta = 2.0 * math.pi * float(j) / float(self.slices)
                u = float(j) / float(self.slices)

                # Coordenadas cartesianas unitárias da normal
                nx = math.sin(phi) * math.cos(theta)
                ny = math.cos(phi)
                nz = math.sin(phi) * math.sin(theta)

                # Posição escalada pelo raio
                x = self.radius * nx
                y = self.radius * ny
                z = self.radius * nz

                # Estrutura intercalada (interleaved):
                # [pos.x, pos.y, pos.z, norm.x, norm.y, norm.z, tex.u, tex.v]
                vertices.extend([x, y, z, nx, ny, nz, u, v])

        # 2. Geração dos índices para triangulação em grelha (quads compostos por 2 triângulos)
        for i in range(self.stacks):
            for j in range(self.slices):
                first = i * (self.slices + 1) + j
                second = first + self.slices + 1

                # Primeiro triângulo do quadrilátero (CCW - Counter Clockwise)
                indices.extend([first, second, first + 1])
                # Segundo triângulo do quadrilátero (CCW)
                indices.extend([second, second + 1, first + 1])

        self.index_count = len(indices)

        # 3. Conversão para arrays contíguos de memória em precisão simples de 32 bits
        vertices_array = np.array(vertices, dtype=np.float32)
        indices_array = np.array(indices, dtype=np.uint32)

        # 4. Configuração das Estruturas OpenGL Core Profile (VAO, VBO, EBO)
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices_array.nbytes, vertices_array, GL_STATIC_DRAW)

        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices_array.nbytes, indices_array, GL_STATIC_DRAW)

        # Stride = tamanho em bytes de cada vértice intercalado (8 floats: 3 pos + 3 norm + 2 uv = 32 bytes)
        stride = 8 * 4

        # Atributo 0: Posição do Vértice (3 floats)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Atributo 1: Vetor Normal (3 floats, offset = 3 floats * 4 bytes = 12 bytes)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        # Atributo 2: Coordenadas UV (2 floats, offset = 6 floats * 4 bytes = 24 bytes)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))
        glEnableVertexAttribArray(2)

        # Desvincula o VAO para proteger o estado
        glBindVertexArray(0)

    def draw(self) -> None:
        """Executa a chamada de desenho da esfera indexada."""
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def cleanup(self) -> None:
        """Liberta os buffers e VAO da memória de vídeo (GPU)."""
        if self.vao != 0:
            glDeleteVertexArrays(1, [self.vao])
            self.vao = 0
        if self.vbo != 0:
            glDeleteBuffers(1, [self.vbo])
            self.vbo = 0
        if self.ebo != 0:
            glDeleteBuffers(1, [self.ebo])
            self.ebo = 0


class OrbitMesh:
    """
    Malha 3D para renderizar trajetórias orbitais elípticas fechadas usando GL_LINE_LOOP.
    """

    def __init__(self, points: List[Tuple[float, float, float]]):
        self.point_count = len(points)
        vertices = np.array(points, dtype=np.float32).flatten()

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # Atributo 0: Posição cartesiana do ponto orbital (3 floats)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindVertexArray(0)

    def draw(self) -> None:
        """Desenha a linha contínua da órbita."""
        glBindVertexArray(self.vao)
        glDrawArrays(GL_LINE_LOOP, 0, self.point_count)
        glBindVertexArray(0)

    def cleanup(self) -> None:
        """Liberta os recursos da GPU."""
        if self.vao != 0:
            glDeleteVertexArrays(1, [self.vao])
            self.vao = 0
        if self.vbo != 0:
            glDeleteBuffers(1, [self.vbo])
            self.vbo = 0


class RingMesh:
    """
    Malha anelar 3D para anéis planetários (como Saturno) com mapeamento UV radial.
    Renderizada com triângulos indexados nos dois lados (two-sided).
    """

    def __init__(self, inner_radius: float = 1.25, outer_radius: float = 2.45, segments: int = 128):
        self.inner_radius = float(inner_radius)
        self.outer_radius = float(outer_radius)
        self.segments = segments
        self.index_count = 0

        self.vao = 0
        self.vbo = 0
        self.ebo = 0

        self._build_mesh()

    def _build_mesh(self) -> None:
        """Constrói os vértices de anel circular plano e mapeamento de coordenadas UV."""
        vertices = []
        indices = []

        for j in range(self.segments + 1):
            theta = 2.0 * math.pi * float(j) / float(self.segments)
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)

            u_coord = float(j) / float(self.segments)

            # Vértice interno: [X, Y, Z, U, V] -> V=0.0
            vertices.extend([self.inner_radius * cos_t, 0.0, self.inner_radius * sin_t, 0.0, u_coord])
            # Vértice externo: [X, Y, Z, U, V] -> V=1.0
            vertices.extend([self.outer_radius * cos_t, 0.0, self.outer_radius * sin_t, 1.0, u_coord])

        for j in range(self.segments):
            p1 = j * 2
            p2 = p1 + 1
            p3 = (j + 1) * 2
            p4 = p3 + 1

            # Frente
            indices.extend([p1, p2, p3])
            indices.extend([p2, p4, p3])
            # Trás (two-sided)
            indices.extend([p3, p2, p1])
            indices.extend([p3, p4, p2])

        self.index_count = len(indices)

        v_arr = np.array(vertices, dtype=np.float32)
        i_arr = np.array(indices, dtype=np.uint32)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, v_arr.nbytes, v_arr, GL_STATIC_DRAW)

        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, i_arr.nbytes, i_arr, GL_STATIC_DRAW)

        stride = 5 * 4  # 20 bytes (3 pos + 2 uv)

        # Atributo 0: Pos
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Atributo 1: UV
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

    def draw(self) -> None:
        """Executa a chamada de desenho da geometria dos anéis."""
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def cleanup(self) -> None:
        """Liberta os buffers da GPU."""
        if self.vao != 0:
            glDeleteVertexArrays(1, [self.vao])
            self.vao = 0
        if self.vbo != 0:
            glDeleteBuffers(1, [self.vbo])
            self.vbo = 0
        if self.ebo != 0:
            glDeleteBuffers(1, [self.ebo])
            self.ebo = 0
