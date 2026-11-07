"""
===============================================================================
Módulo: shader.py
Descrição: Gestão e compilação de shaders GLSL no Pipeline Gráfico do OpenGL 3.3.
Conceitos aplicados:
  - OpenGL Core Profile 3.3
  - Vertex Shader e Fragment Shader
  - Compilação e ligação (linkage) de programas de shader
  - Validação de erros de compilação e ligação (InfoLogs)
  - Gestão de variáveis uniform (Matrizes, Vetores, Escalares) com cache de locais
===============================================================================
"""

from pathlib import Path
from typing import Dict, Union
import numpy as np
import glm
from OpenGL.GL import (
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER,
    GL_COMPILE_STATUS,
    GL_LINK_STATUS,
    GL_TRUE,
    glCreateShader,
    glShaderSource,
    glCompileShader,
    glGetShaderiv,
    glGetShaderInfoLog,
    glCreateProgram,
    glAttachShader,
    glLinkProgram,
    glGetProgramiv,
    glGetProgramInfoLog,
    glDeleteShader,
    glUseProgram,
    glGetUniformLocation,
    glUniform1i,
    glUniform1f,
    glUniform3f,
    glUniform4f,
    glUniformMatrix3fv,
    glUniformMatrix4fv,
    GL_FALSE,
)


class Shader:
    """
    Representa um programa de shaders no pipeline programável do OpenGL 3.3 Core Profile.
    Carrega o código-fonte GLSL a partir do disco, compila e interliga os shaders.
    """

    def __init__(self, vertex_path: Union[str, Path], fragment_path: Union[str, Path]):
        self.program_id = 0
        self._uniform_cache: Dict[str, int] = {}

        v_path = Path(vertex_path)
        f_path = Path(fragment_path)

        if not v_path.exists():
            raise FileNotFoundError(f"[Shader Error] Vertex shader não encontrado: {v_path}")
        if not f_path.exists():
            raise FileNotFoundError(f"[Shader Error] Fragment shader não encontrado: {f_path}")

        vertex_code = v_path.read_text(encoding="utf-8")
        fragment_code = f_path.read_text(encoding="utf-8")

        self._compile_and_link(vertex_code, fragment_code, str(v_path), str(f_path))

    def _compile_and_link(self, v_code: str, f_code: str, v_name: str, f_name: str) -> None:
        """Compila os shaders individuais e efetua a ligação no programa final."""
        # 1. Compilação do Vertex Shader
        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, v_code)
        glCompileShader(vertex_shader)
        if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(vertex_shader).decode("utf-8")
            raise RuntimeError(f"[Shader Error] Erro ao compilar Vertex Shader ({v_name}):\n{error}")

        # 2. Compilação do Fragment Shader
        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, f_code)
        glCompileShader(fragment_shader)
        if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(fragment_shader).decode("utf-8")
            raise RuntimeError(f"[Shader Error] Erro ao compilar Fragment Shader ({f_name}):\n{error}")

        # 3. Ligação (Linkage) no Programa OpenGL
        self.program_id = glCreateProgram()
        glAttachShader(self.program_id, vertex_shader)
        glAttachShader(self.program_id, fragment_shader)
        glLinkProgram(self.program_id)

        if not glGetProgramiv(self.program_id, GL_LINK_STATUS):
            error = glGetProgramInfoLog(self.program_id).decode("utf-8")
            raise RuntimeError(f"[Shader Error] Erro ao ligar programa de shaders:\n{error}")

        # Shaders individuais podem ser descartados após a ligação no programa
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

    def use(self) -> None:
        """Ativa o programa de shader na máquina de estados do OpenGL."""
        glUseProgram(self.program_id)

    def get_uniform_location(self, name: str) -> int:
        """Recupera e armazena em cache o identificador de uma variável uniform."""
        if name not in self._uniform_cache:
            loc = glGetUniformLocation(self.program_id, name)
            self._uniform_cache[name] = loc
        return self._uniform_cache[name]

    def set_int(self, name: str, value: int) -> None:
        """Define um uniform inteiro (ex: samplers de textura)."""
        loc = self.get_uniform_location(name)
        if loc != -1:
            glUniform1i(loc, int(value))

    def set_float(self, name: str, value: float) -> None:
        """Define um uniform escalar float."""
        loc = self.get_uniform_location(name)
        if loc != -1:
            glUniform1f(loc, float(value))

    def set_vec3(self, name: str, x: Union[float, glm.vec3, tuple, list], y: float = 0.0, z: float = 0.0) -> None:
        """Define um uniform de vetor de 3 dimensões (vec3)."""
        loc = self.get_uniform_location(name)
        if loc != -1:
            if isinstance(x, (glm.vec3, tuple, list, np.ndarray)):
                glUniform3f(loc, float(x[0]), float(x[1]), float(x[2]))
            else:
                glUniform3f(loc, float(x), float(y), float(z))

    def set_vec4(self, name: str, x: Union[float, glm.vec4, tuple, list], y: float = 0.0, z: float = 0.0, w: float = 1.0) -> None:
        """Define um uniform de vetor de 4 dimensões (vec4)."""
        loc = self.get_uniform_location(name)
        if loc != -1:
            if isinstance(x, (glm.vec4, tuple, list, np.ndarray)):
                glUniform4f(loc, float(x[0]), float(x[1]), float(x[2]), float(x[3]))
            else:
                glUniform4f(loc, float(x), float(y), float(z), float(w))

    def set_mat3(self, name: str, mat: Union[glm.mat3, np.ndarray]) -> None:
        """Define um uniform de matriz 3x3 (ex: Normal Matrix)."""
        loc = self.get_uniform_location(name)
        if loc != -1:
            if isinstance(mat, glm.mat3):
                ptr = glm.value_ptr(mat)
                glUniformMatrix3fv(loc, 1, GL_FALSE, ptr)
            else:
                glUniformMatrix3fv(loc, 1, GL_FALSE, np.array(mat, dtype=np.float32))

    def set_mat4(self, name: str, mat: Union[glm.mat4, np.ndarray]) -> None:
        """Define um uniform de matriz 4x4 (Model, View, Projection)."""
        loc = self.get_uniform_location(name)
        if loc != -1:
            if isinstance(mat, glm.mat4):
                ptr = glm.value_ptr(mat)
                glUniformMatrix4fv(loc, 1, GL_FALSE, ptr)
            else:
                glUniformMatrix4fv(loc, 1, GL_FALSE, np.array(mat, dtype=np.float32))
