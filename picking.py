"""
===============================================================================
Módulo: picking.py
Descrição: Seleção interativa de corpos celestes 3D através de Ray Casting (Ray Picking).
Conceitos de Computação Gráfica aplicados:
  - Transformação de Coordenadas Inversas:
      1. Coordenadas de Ecrã (Screen Pixels) -> Coordenadas Normalizadas (NDC [-1, 1]).
      2. NDC -> Espaço de Recorte (Clip Space) e Espaço de Câmara (Eye Space) via inverse(Projection).
      3. Espaço de Câmara -> Espaço de Mundo (World Space) via inverse(View).
  - Algoritmo Geométrico de Interseção Raio-Esfera (Ray-Sphere Intersection):
      * Resolução analítica da equação quadrática |P(t) - C|^2 = R^2.
      * Determinação do corpo celeste mais próximo ao longo da linha de visão do observador.
===============================================================================
"""

from typing import Dict, Optional, Tuple
import math
import glm


class RayPicker:
    """Implementa o cálculo de raio a partir do clique do rato e testes de interseção."""

    @staticmethod
    def get_ray_direction(
        mouse_x: float,
        mouse_y: float,
        screen_width: int,
        screen_height: int,
        view_matrix: glm.mat4,
        proj_matrix: glm.mat4,
    ) -> Tuple[glm.vec3, glm.vec3]:
        """
        Converte a coordenada (x, y) do rato num raio tridimensional (origem e direção)
        no Espaço de Mundo (World Space).
        """
        # 1. Coordenadas de Janela para NDC [-1, 1]
        x_ndc = (2.0 * mouse_x) / float(screen_width) - 1.0
        y_ndc = 1.0 - (2.0 * mouse_y) / float(screen_height)

        # 2. Ponto no plano próximo (Near) e distante (Far) no Clip Space
        ray_clip_near = glm.vec4(x_ndc, y_ndc, -1.0, 1.0)
        ray_clip_far = glm.vec4(x_ndc, y_ndc, 1.0, 1.0)

        inv_proj = glm.inverse(proj_matrix)
        inv_view = glm.inverse(view_matrix)

        # 3. Clip Space -> Eye Space
        ray_eye_near = inv_proj * ray_clip_near
        ray_eye_near /= ray_eye_near.w

        ray_eye_far = inv_proj * ray_clip_far
        ray_eye_far /= ray_eye_far.w

        # 4. Eye Space -> World Space
        ray_world_near = glm.vec3(inv_view * ray_eye_near)
        ray_world_far = glm.vec3(inv_view * ray_eye_far)

        # Origem e vetor direção normalizado
        ray_origin = ray_world_near
        ray_direction = glm.normalize(ray_world_far - ray_world_near)

        return ray_origin, ray_direction

    @staticmethod
    def intersect_sphere(
        ray_origin: glm.vec3,
        ray_dir: glm.vec3,
        sphere_center: glm.vec3,
        sphere_radius: float,
    ) -> Optional[float]:
        """
        Testa a interseção entre o raio P(t) = O + t*D e uma esfera de centro C e raio R.
        Retorna a distância t > 0 do ponto de contacto mais próximo, ou None se não intersetar.
        """
        # Vetor do centro da esfera para a origem do raio
        oc = ray_origin - sphere_center

        a = glm.dot(ray_dir, ray_dir)  # Deve ser 1.0 se ray_dir estiver normalizado
        b = 2.0 * glm.dot(oc, ray_dir)
        c = glm.dot(oc, oc) - (sphere_radius * sphere_radius)

        discriminant = (b * b) - (4.0 * a * c)

        if discriminant < 0.0:
            return None

        # Raiz mais próxima (menor t positivo)
        sqrt_disc = math.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2.0 * a)
        t2 = (-b + sqrt_disc) / (2.0 * a)

        if t1 > 0.0:
            return t1
        if t2 > 0.0:
            return t2
        return None
