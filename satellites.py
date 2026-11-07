"""
===============================================================================
Módulo: satellites.py
Descrição: Satélites artificiais e naves espaciais em órbita dos corpos celestes.
Conceitos aplicados:
  - Modelos 3D Reais:
      * satellite.glb: Satélite de comunicações em órbita baixa da Terra (LEO).
      * rocket_orbiting_moon.glb: Módulo orbital em volta da Lua.
  - Órbita Rápida e Rotação Orientada (antenas apontadas para a Terra).
  - Composição Hierárquica de Matrizes: Posição do Planeta -> Órbita do Satélite.
===============================================================================
"""

from pathlib import Path
from typing import Optional
import math
import glm

from model_loader import GLBModel
from shader import Shader


class EarthSatellite:
    """Satélite artificial em órbita circular ao redor da Terra."""

    def __init__(self, models_dir: Path):
        self.model: Optional[GLBModel] = None
        p = models_dir / "satellite.glb"
        if p.exists():
            try:
                self.model = GLBModel(p)
                print(f"[Satélite 3D] Modelo carregado: {p.name}")
            except Exception as e:
                print(f"[Satélite Warning] Falha ao carregar satellite.glb: {e}")

        self.orbital_radius = 4.2  # Logo acima da atmosfera terrestre (raio 2.5)
        self.orbital_speed_deg_per_sec = 45.0  # Órbita rápida
        self.current_angle_deg = 0.0
        self.scale = 0.18
        self.inclination_rad = math.radians(51.6)  # Inclinação típica da ISS

    def update(self, delta_time: float) -> None:
        """Atualiza a posição ao longo da órbita da Terra."""
        self.current_angle_deg = (self.current_angle_deg + self.orbital_speed_deg_per_sec * delta_time) % 360.0

    def draw(
        self,
        shader: Shader,
        view: glm.mat4,
        proj: glm.mat4,
        view_pos: glm.vec3,
        sun_pos: glm.vec3,
        earth_pos: glm.vec3,
    ) -> None:
        """Desenha o satélite em órbita da Terra."""
        if not self.model:
            return

        rad = math.radians(self.current_angle_deg)
        x = self.orbital_radius * math.cos(rad)
        z = self.orbital_radius * math.sin(rad)
        y = z * math.sin(self.inclination_rad)
        z = z * math.cos(self.inclination_rad)

        sat_world_pos = earth_pos + glm.vec3(x, y, z)

        model = glm.mat4(1.0)
        model = glm.translate(model, sat_world_pos)
        model = glm.rotate(model, rad, glm.vec3(0.0, 1.0, 0.0))
        model = glm.scale(model, glm.vec3(self.scale))

        normal_matrix = glm.mat3(glm.transpose(glm.inverse(model)))

        shader.use()
        shader.set_mat4("uModel", model)
        shader.set_mat4("uView", view)
        shader.set_mat4("uProjection", proj)
        shader.set_mat3("uNormalMatrix", normal_matrix)
        shader.set_vec3("uLightPos", sun_pos)
        shader.set_vec3("uLightColor", glm.vec3(1.0, 0.98, 0.92))
        shader.set_vec3("uViewPos", view_pos)
        shader.set_vec3("uAmbientColor", glm.vec3(0.08, 0.08, 0.1))
        shader.set_float("uShininess", 64.0)
        shader.set_float("uSpecularStrength", 0.8)  # Painéis solares reflexivos

        self.model.draw()


class LunarRocket:
    """Módulo orbital em volta da Lua usando rocket_orbiting_moon.glb."""

    def __init__(self, models_dir: Path):
        self.model: Optional[GLBModel] = None
        p = models_dir / "rocket_orbiting_moon.glb"
        if p.exists():
            try:
                self.model = GLBModel(p)
                print(f"[Foguetão 3D] Modelo carregado: {p.name}")
            except Exception as e:
                print(f"[Foguetão Warning] Falha ao carregar rocket_orbiting_moon.glb: {e}")

        self.orbital_radius = 1.3
        self.speed_deg = 60.0
        self.angle_deg = 0.0
        self.scale = 0.12

    def update(self, delta_time: float) -> None:
        self.angle_deg = (self.angle_deg + self.speed_deg * delta_time) % 360.0

    def draw(
        self,
        shader: Shader,
        view: glm.mat4,
        proj: glm.mat4,
        view_pos: glm.vec3,
        sun_pos: glm.vec3,
        moon_pos: glm.vec3,
    ) -> None:
        if not self.model:
            return

        rad = math.radians(self.angle_deg)
        x = self.orbital_radius * math.cos(rad)
        z = self.orbital_radius * math.sin(rad)
        pos = moon_pos + glm.vec3(x, 0.2 * math.sin(rad), z)

        model = glm.mat4(1.0)
        model = glm.translate(model, pos)
        model = glm.rotate(model, rad, glm.vec3(0.0, 1.0, 0.0))
        model = glm.scale(model, glm.vec3(self.scale))

        normal_matrix = glm.mat3(glm.transpose(glm.inverse(model)))

        shader.use()
        shader.set_mat4("uModel", model)
        shader.set_mat4("uView", view)
        shader.set_mat4("uProjection", proj)
        shader.set_mat3("uNormalMatrix", normal_matrix)
        shader.set_vec3("uLightPos", sun_pos)
        shader.set_vec3("uLightColor", glm.vec3(1.0, 0.98, 0.92))
        shader.set_vec3("uViewPos", view_pos)
        shader.set_vec3("uAmbientColor", glm.vec3(0.08, 0.08, 0.1))
        shader.set_float("uShininess", 32.0)
        shader.set_float("uSpecularStrength", 0.5)

        self.model.draw()
