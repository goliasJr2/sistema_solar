"""
===============================================================================
Módulo: camera.py
Descrição: Sistema de câmara 3D com projeção em perspetiva e matriz View.
Conceitos aplicados:
  - Espaço de Câmara / Vista (View Space):
      * Cálculo de vetores Front, Right e Up ortonormais.
      * Matriz View através de lookAt(eye, target, up).
  - Espaço de Recorte e Projeção (Clip Space):
      * Matriz Projection através de perspective(fov, aspect, near, far).
      * Viewport e atualização dinâmica da razão de aspeto (aspect ratio).
  - Interação e Controlo do Utilizador:
      * Rotação orbital com botão esquerdo do rato (Yaw e Pitch).
      * Zoom suave com a roda do rato (variação de distância focal/raio).
      * Pan com o botão direito do rato (translação no plano da câmara).
      * Navegação livre pelo teclado (WASD, Q/E).
===============================================================================
"""

import math
from typing import Tuple
import glm


class Camera:
    """
    Câmara 3D interativa para o simulador astronómico.
    Suporta visualização orbital em torno do Sol ou planetas e movimentação livre.
    """

    def __init__(
        self,
        position: glm.vec3 = glm.vec3(0.0, 75.0, 220.0),
        target: glm.vec3 = glm.vec3(0.0, 0.0, 0.0),
        up: glm.vec3 = glm.vec3(0.0, 1.0, 0.0),
        fov: float = 45.0,
        aspect_ratio: float = 16.0 / 9.0,
        near_plane: float = 0.5,
        far_plane: float = 10000.0,
    ):
        # Parâmetros de perspetiva
        self.fov = fov
        self.aspect_ratio = aspect_ratio
        self.near_plane = near_plane
        self.far_plane = far_plane

        # Estado inicial (para reposição com a tecla R)
        self.initial_pos = glm.vec3(position)
        self.initial_target = glm.vec3(target)
        self.initial_up = glm.vec3(up)

        # Vetores de posicionamento
        self.position = glm.vec3(position)
        self.target = glm.vec3(target)
        self.world_up = glm.vec3(up)

        # Parâmetros de orientação angular esférica
        diff = self.position - self.target
        self.distance = glm.length(diff)
        if self.distance < 1.0:
            self.distance = 150.0

        self.yaw = math.degrees(math.atan2(diff.z, diff.x))
        self.pitch = math.degrees(math.asin(diff.y / self.distance))

        # Configurações de sensibilidade
        self.mouse_sensitivity = 0.25
        self.zoom_sensitivity = 0.12
        self.pan_sensitivity = 0.08
        self.keyboard_speed = 60.0  # unidades por segundo

        # Vetores ortonormais calculados
        self.front = glm.vec3(0.0, 0.0, -1.0)
        self.right = glm.vec3(1.0, 0.0, 0.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)

        self._update_camera_vectors()

    def _update_camera_vectors(self) -> None:
        """
        Recalcula os vetores de orientação da câmara a partir dos ângulos de Euler (Yaw, Pitch)
        e atualiza a posição no modo orbital.
        """
        # Restringe o pitch para evitar inversão de perspetiva (Gimbal Lock)
        self.pitch = max(-88.0, min(88.0, self.pitch))

        # Conversão de coordenadas esféricas para cartesianas
        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)

        cam_x = self.distance * math.cos(rad_pitch) * math.cos(rad_yaw)
        cam_y = self.distance * math.sin(rad_pitch)
        cam_z = self.distance * math.cos(rad_pitch) * math.sin(rad_yaw)

        self.position = self.target + glm.vec3(cam_x, cam_y, cam_z)

        # Vetor frontal a apontar para o alvo
        self.front = glm.normalize(self.target - self.position)
        # Vetor lateral (Right) = Produto vetorial entre Front e World Up
        self.right = glm.normalize(glm.cross(self.front, self.world_up))
        # Vetor vertical (Up) = Produto vetorial entre Right e Front
        self.up = glm.normalize(glm.cross(self.right, self.front))

    def get_view_matrix(self) -> glm.mat4:
        """Gera a Matriz View através da função canónica glm.lookAt."""
        return glm.lookAt(self.position, self.target, self.up)

    def get_projection_matrix(self) -> glm.mat4:
        """Gera a Matriz de Projeção em Perspetiva através de glm.perspective."""
        return glm.perspective(glm.radians(self.fov), self.aspect_ratio, self.near_plane, self.far_plane)

    def update_aspect_ratio(self, width: int, height: int) -> None:
        """Atualiza a razão de aspeto aquando do redimensionamento da janela gráfica (Viewport)."""
        if height > 0:
            self.aspect_ratio = float(width) / float(height)

    def process_mouse_orbit(self, xoffset: float, yoffset: float) -> None:
        """Rotação orbital da câmara ao redor do alvo (botão esquerdo do rato)."""
        self.yaw += xoffset * self.mouse_sensitivity
        self.pitch += yoffset * self.mouse_sensitivity
        self._update_camera_vectors()

    def process_mouse_pan(self, xoffset: float, yoffset: float) -> None:
        """Deslocamento lateral e vertical do alvo e da câmara (botão direito do rato)."""
        factor = self.distance * 0.003 * self.pan_sensitivity
        self.target -= self.right * (xoffset * factor)
        self.target += self.up * (yoffset * factor)
        self._update_camera_vectors()

    def process_mouse_scroll(self, yoffset: float) -> None:
        """Zoom suave aproximando ou afastando a câmara (roda do rato)."""
        # Escala logarítmica para permitir zoom suave tanto perto como longe
        zoom_delta = self.distance * self.zoom_sensitivity * (-yoffset)
        self.distance = max(5.0, min(8000.0, self.distance + zoom_delta))
        self._update_camera_vectors()

    def process_keyboard(self, direction: str, delta_time: float) -> None:
        """
        Navegação livre pelo teclado (WASD, Q/E):
          W: Avançar
          S: Recuar
          A: Deslocar para a esquerda (Strafe Left)
          D: Deslocar para a direita (Strafe Right)
          Q: Descer
          E: Subir
        """
        velocity = self.keyboard_speed * delta_time * (self.distance / 150.0)

        if direction == "FORWARD":
            self.target += self.front * velocity
        elif direction == "BACKWARD":
            self.target -= self.front * velocity
        elif direction == "LEFT":
            self.target -= self.right * velocity
        elif direction == "RIGHT":
            self.target += self.right * velocity
        elif direction == "UP":
            self.target += self.world_up * velocity
        elif direction == "DOWN":
            self.target -= self.world_up * velocity

        self._update_camera_vectors()

    def reset(self) -> None:
        """Restaura a câmara para a posição, alvo e orientação originais (Tecla R)."""
        self.position = glm.vec3(self.initial_pos)
        self.target = glm.vec3(self.initial_target)
        diff = self.position - self.target
        self.distance = glm.length(diff)
        self.yaw = math.degrees(math.atan2(diff.z, diff.x))
        self.pitch = math.degrees(math.asin(diff.y / self.distance))
        self._update_camera_vectors()
