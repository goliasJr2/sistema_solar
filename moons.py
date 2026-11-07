"""
===============================================================================
Módulo: moons.py
Descrição: Sistema de Luas com Hierarquia de Matrizes (Scene Graph).
Conceitos aplicados:
  - Hierarquia de Transformações Geométricas:
      * Matriz da Lua = Translação(Posição do Planeta) * Rotação(Inclinação Orbital da Lua)
                       * Translação(Raio Orbital da Lua) * Rotação(Rotação Própria) * Escala(Raio)
  - Órbitas Locais: cada lua possui o seu próprio raio orbital relativo, período sideral e inclinação.
  - Carregamento de Modelos 3D: utiliza lua.glb para a Lua terrestre e esferas paramétricas
    com texturas especializadas para os restantes satélites naturais do Sistema Solar.
===============================================================================
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import math
import glm

from mesh import SphereMesh, OrbitMesh
from texture import TextureLoader, Texture
from shader import Shader
from model_loader import GLBModel


# Base de dados astronómicos das Luas do Sistema Solar
MOONS_DATA = {
    # 1. Terra
    "earth": [
        {
            "id": "moon",
            "name": "Lua",
            "orbital_radius": 6.8,       # Distância visual equilibrada ao redor da Terra
            "orbital_period_days": 27.32,
            "visual_radius": 0.65,
            "inclination_deg": 5.14,
            "rotation_period_hours": 655.7,  # Rotação síncrona
            "model_file": "lua.glb",
            "color": glm.vec4(0.8, 0.8, 0.85, 0.4),
        }
    ],
    # 2. Marte
    "mars": [
        {
            "id": "phobos",
            "name": "Fobos",
            "orbital_radius": 3.4,
            "orbital_period_days": 0.318,
            "visual_radius": 0.28,
            "inclination_deg": 1.09,
            "rotation_period_hours": 7.65,
            "model_file": None,
            "color": glm.vec4(0.65, 0.55, 0.5, 0.4),
        },
        {
            "id": "deimos",
            "name": "Deimos",
            "orbital_radius": 5.2,
            "orbital_period_days": 1.262,
            "visual_radius": 0.22,
            "inclination_deg": 0.93,
            "rotation_period_hours": 30.3,
            "model_file": None,
            "color": glm.vec4(0.6, 0.5, 0.45, 0.4),
        },
    ],
    # 3. Júpiter (Luas Galileanas)
    "jupiter": [
        {
            "id": "io",
            "name": "Io",
            "orbital_radius": 11.0,
            "orbital_period_days": 1.769,
            "visual_radius": 0.62,
            "inclination_deg": 0.05,
            "rotation_period_hours": 42.4,
            "model_file": None,
            "color": glm.vec4(0.95, 0.85, 0.2, 0.45),  # Sulfuroso e vulcânico
        },
        {
            "id": "europa",
            "name": "Europa",
            "orbital_radius": 14.5,
            "orbital_period_days": 3.551,
            "visual_radius": 0.54,
            "inclination_deg": 0.47,
            "rotation_period_hours": 85.2,
            "model_file": None,
            "color": glm.vec4(0.85, 0.9, 0.95, 0.45),  # Oceano congelado e brilhante
        },
        {
            "id": "ganymede",
            "name": "Ganimedes",
            "orbital_radius": 18.5,
            "orbital_period_days": 7.154,
            "visual_radius": 0.88,  # A maior lua do Sistema Solar
            "inclination_deg": 0.20,
            "rotation_period_hours": 171.7,
            "model_file": None,
            "color": glm.vec4(0.65, 0.60, 0.55, 0.45),
        },
        {
            "id": "callisto",
            "name": "Calisto",
            "orbital_radius": 23.5,
            "orbital_period_days": 16.689,
            "visual_radius": 0.82,
            "inclination_deg": 0.28,
            "rotation_period_hours": 400.5,
            "model_file": None,
            "color": glm.vec4(0.5, 0.5, 0.55, 0.45),
        },
    ],
    # 4. Saturno
    "saturn": [
        {
            "id": "titan",
            "name": "Titã",
            "orbital_radius": 16.0,
            "orbital_period_days": 15.945,
            "visual_radius": 0.86,
            "inclination_deg": 0.35,
            "rotation_period_hours": 382.7,
            "model_file": None,
            "color": glm.vec4(0.9, 0.65, 0.25, 0.45),  # Atmosfera espessa de metano alaranjada
        }
    ],
    # 5. Neptuno
    "neptune": [
        {
            "id": "triton",
            "name": "Tritão",
            "orbital_radius": 10.0,
            "orbital_period_days": -5.877,  # Rotação e órbita RETRÓGRADAS!
            "visual_radius": 0.60,
            "inclination_deg": 156.8,       # Alta inclinação retrógrada
            "rotation_period_hours": -141.0,
            "model_file": None,
            "color": glm.vec4(0.8, 0.75, 0.85, 0.45),  # Gelo de azoto e cantaloupe
        }
    ],
}


class Moon:
    """Representa um satélite natural que orbita um planeta em hierarquia de matrizes."""

    def __init__(
        self,
        moon_data: dict,
        textures_dir: Path,
        models_dir: Optional[Path],
        shared_sphere_mesh: SphereMesh,
    ):
        self.data = moon_data
        self.id = moon_data["id"]
        self.name = moon_data["name"]
        self.orbital_radius = float(moon_data["orbital_radius"])
        self.orbital_period_days = float(moon_data["orbital_period_days"])
        self.visual_radius = float(moon_data["visual_radius"])
        self.inclination_rad = math.radians(float(moon_data["inclination_deg"]))
        self.rotation_period_hours = float(moon_data["rotation_period_hours"])

        self.mesh = shared_sphere_mesh

        # Carregamento do modelo 3D GLB específico (ex: lua.glb)
        self.glb_model: Optional[GLBModel] = None
        model_name = moon_data.get("model_file")
        if models_dir and model_name:
            p = models_dir / model_name
            if p.exists():
                try:
                    self.glb_model = GLBModel(p)
                    print(f"[Moon 3D] Modelo GLB carregado para '{self.name}': {model_name}")
                except Exception as e:
                    print(f"[Moon Warning] Falha ao carregar modelo '{model_name}': {e}")

        # Textura procedural / de fallback
        tex_path = textures_dir / f"2k_{self.id}.jpg"
        self.texture = TextureLoader.load(tex_path, fallback_key=self.id)

        # Malha da órbita circular em redor do planeta
        orbit_pts: List[Tuple[float, float, float]] = []
        for i in range(120):
            theta = (2.0 * math.pi * float(i)) / 120.0
            x = self.orbital_radius * math.cos(theta)
            z = self.orbital_radius * math.sin(theta)
            # Aplicação da inclinação orbital
            y = z * math.sin(self.inclination_rad)
            z = z * math.cos(self.inclination_rad)
            orbit_pts.append((x, y, z))
        self.orbit_mesh = OrbitMesh(orbit_pts)

        # Estado dinâmico
        self.orbit_angle_rad = 0.0
        self.rotation_angle_deg = 0.0
        self.world_position = glm.vec3(0.0)

    def update(self, simulated_days: float, delta_sim_days: float, parent_pos: glm.vec3) -> None:
        """Calcula a posição orbital da lua relativamente ao planeta e a posição absoluta no mundo."""
        # 1. Ângulo orbital da lua
        orbit_speed = (2.0 * math.pi) / self.orbital_period_days
        self.orbit_angle_rad = (self.orbit_angle_rad + orbit_speed * delta_sim_days) % (2.0 * math.pi)

        # 2. Ângulo de rotação axial da lua
        delta_hours = delta_sim_days * 24.0
        rot_speed = 360.0 / self.rotation_period_hours
        self.rotation_angle_deg = (self.rotation_angle_deg + rot_speed * delta_hours) % 360.0

        # 3. Posição relativa em relação ao centro do planeta
        rel_x = self.orbital_radius * math.cos(self.orbit_angle_rad)
        rel_z = self.orbital_radius * math.sin(self.orbit_angle_rad)
        rel_y = rel_z * math.sin(self.inclination_rad)
        rel_z = rel_z * math.cos(self.inclination_rad)

        self.world_position = parent_pos + glm.vec3(rel_x, rel_y, rel_z)

    def get_model_matrix(self, parent_model_matrix: glm.mat4, parent_pos: glm.vec3) -> glm.mat4:
        """
        Hierarquia de Matrizes:
          M_lua = Translate(Posição do Planeta)
                * Rotate(Inclinação da Órbita da Lua)
                * Translate(Raio Orbital da Lua)
                * Rotate(Rotação Própria da Lua)
                * Scale(Raio da Lua)
        """
        model = glm.mat4(1.0)
        # 1. Desloca para a posição do planeta no mundo
        model = glm.translate(model, parent_pos)
        # 2. Inclinação orbital da lua
        model = glm.rotate(model, self.inclination_rad, glm.vec3(1.0, 0.0, 0.0))
        # 3. Translação ao longo do raio orbital
        model = glm.rotate(model, self.orbit_angle_rad, glm.vec3(0.0, 1.0, 0.0))
        model = glm.translate(model, glm.vec3(self.orbital_radius, 0.0, 0.0))
        # 4. Rotação axial própria da lua
        model = glm.rotate(model, math.radians(self.rotation_angle_deg), glm.vec3(0.0, 1.0, 0.0))
        # 5. Escala proporcional
        model = glm.scale(model, glm.vec3(self.visual_radius))
        return model

    def draw(
        self,
        shader: Shader,
        view: glm.mat4,
        proj: glm.mat4,
        view_pos: glm.vec3,
        sun_pos: glm.vec3,
        parent_model: glm.mat4,
        parent_pos: glm.vec3,
    ) -> None:
        """Renderiza a lua com o shader Blinn-Phong aplicando a hierarquia de transformações."""
        shader.use()
        model = self.get_model_matrix(parent_model, parent_pos)
        normal_mat = glm.mat3(glm.transpose(glm.inverse(model)))

        shader.set_mat4("uModel", model)
        shader.set_mat4("uView", view)
        shader.set_mat4("uProjection", proj)
        shader.set_mat3("uNormalMatrix", normal_mat)
        shader.set_vec3("uLightPos", sun_pos)
        shader.set_vec3("uLightColor", glm.vec3(1.0, 0.98, 0.92))
        shader.set_vec3("uViewPos", view_pos)
        shader.set_vec3("uAmbientColor", glm.vec3(0.04, 0.04, 0.05))
        shader.set_float("uShininess", 16.0)
        shader.set_float("uSpecularStrength", 0.05)

        if self.glb_model:
            self.glb_model.draw(default_texture=self.texture)
        else:
            self.texture.bind(0)
            shader.set_int("uTexture", 0)
            self.mesh.draw()

    def draw_orbit(self, orbit_shader: Shader, view: glm.mat4, proj: glm.mat4, parent_pos: glm.vec3) -> None:
        """Desenha a linha circular da órbita em redor do planeta."""
        orbit_shader.use()
        model = glm.mat4(1.0)
        model = glm.translate(model, parent_pos)
        orbit_shader.set_mat4("uModel", model)
        orbit_shader.set_mat4("uView", view)
        orbit_shader.set_mat4("uProjection", proj)
        orbit_shader.set_vec4("uOrbitColor", self.data["color"])
        self.orbit_mesh.draw()
