"""
===============================================================================
Módulo: comet.py
Descrição: Cometa interestelar com órbita altamente elíptica e cauda orientada pelo vento solar.
Conceitos aplicados:
  - Órbita Kepleriana com Alta Excentricidade (e = 0.82, i = 42°).
  - Orientação Dinâmica de Vetores:
      * A cauda do cometa é orientada pela pressão da radiação solar (vetor Cometa -> Oposto ao Sol).
  - Matriz de Rotação por LookAt inverso (alinhamento do vetor frontal do cometa com o vento solar).
  - Modelo 3D Real: 3iatlas_-_blue_kachina_comet_tribute.glb.
===============================================================================
"""

from pathlib import Path
from typing import Optional, List, Tuple
import math
import glm

from model_loader import GLBModel
from orbits import KeplerianOrbit
from mesh import OrbitMesh
from shader import Shader


class Comet:
    """Representa um cometa com trajetória excêntrica e cauda iónica e de poeira."""

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.name = "Cometa 3I/ATLAS"

        # Carregamento do modelo 3D GLB do cometa
        self.model: Optional[GLBModel] = None
        model_path = models_dir / "3iatlas_-_blue_kachina_comet_tribute.glb"
        if model_path.exists():
            try:
                self.model = GLBModel(model_path)
                print(f"[Cometa 3D] Modelo GLB carregado: {model_path.name}")
            except Exception as e:
                print(f"[Cometa Warning] Falha ao carregar modelo do cometa: {e}")

        # Órbita Kepleriana altamente excêntrica e inclinada
        # Periélio: a*(1 - e) = 150 * 0.18 = 27.0 (aproxima-se de Mercúrio!)
        # Afélio: a*(1 + e) = 150 * 1.82 = 273.0 (vai além de Neptuno!)
        self.orbit = KeplerianOrbit(
            semi_major_axis=150.0,
            eccentricity=0.82,
            inclination_deg=42.0,
            orbital_period_days=1800.0,
            initial_mean_anomaly_deg=45.0,
        )

        # Linha da órbita 3D azul ciano
        orbit_pts = self.orbit.generate_orbit_points(num_points=360)
        self.orbit_mesh = OrbitMesh(orbit_pts)
        self.orbit_color = glm.vec4(0.3, 0.8, 1.0, 0.6)

        self.current_position = glm.vec3(0.0)
        self.visual_scale = 1.8

    def update(self, simulated_days: float, delta_sim_days: float) -> None:
        """Calcula a posição kepleriana do cometa."""
        self.current_position = self.orbit.get_position_at_time(simulated_days)

    def get_model_matrix(self, sun_pos: glm.vec3) -> glm.mat4:
        """
        Calcula a Matriz Model orientando a cauda do cometa na direção oposta ao Sol.
        """
        # Vetor do Sol para o cometa (direção do vento solar que empurra a cauda)
        tail_dir = glm.normalize(self.current_position - sun_pos)

        # Construção da orientação
        up_ref = glm.vec3(0.0, 1.0, 0.0)
        if abs(glm.dot(tail_dir, up_ref)) > 0.95:
            up_ref = glm.vec3(1.0, 0.0, 0.0)

        right = glm.normalize(glm.cross(up_ref, tail_dir))
        up = glm.normalize(glm.cross(tail_dir, right))

        # Matriz de Rotação por base ortonormal [right, up, tail_dir]
        rot_mat = glm.mat4(
            glm.vec4(right, 0.0),
            glm.vec4(up, 0.0),
            glm.vec4(tail_dir, 0.0),
            glm.vec4(0.0, 0.0, 0.0, 1.0),
        )

        # A cauda expande quando está mais próximo do Sol (maior desgaseificação)
        dist_to_sun = glm.length(self.current_position - sun_pos)
        tail_intensity = max(1.0, min(3.5, 300.0 / max(30.0, dist_to_sun)))

        model = glm.mat4(1.0)
        model = glm.translate(model, self.current_position)
        model = model * rot_mat
        model = glm.scale(model, glm.vec3(self.visual_scale, self.visual_scale, self.visual_scale * tail_intensity))

        return model

    def draw(
        self,
        shader: Shader,
        view: glm.mat4,
        projection: glm.mat4,
        view_pos: glm.vec3,
        sun_pos: glm.vec3,
    ) -> None:
        """Renderiza o cometa."""
        if not self.model:
            return

        shader.use()
        model_matrix = self.get_model_matrix(sun_pos)
        normal_matrix = glm.mat3(glm.transpose(glm.inverse(model_matrix)))

        shader.set_mat4("uModel", model_matrix)
        shader.set_mat4("uView", view)
        shader.set_mat4("uProjection", projection)
        shader.set_mat3("uNormalMatrix", normal_matrix)
        shader.set_vec3("uLightPos", sun_pos)
        shader.set_vec3("uLightColor", glm.vec3(1.0, 0.98, 0.92))
        shader.set_vec3("uViewPos", view_pos)
        shader.set_vec3("uAmbientColor", glm.vec3(0.25, 0.35, 0.5))  # Emissão fluorescente azulada
        shader.set_float("uShininess", 32.0)
        shader.set_float("uSpecularStrength", 0.4)

        self.model.draw()

    def draw_orbit(self, orbit_shader: Shader, view: glm.mat4, projection: glm.mat4) -> None:
        """Desenha a trajetória orbital alongada do cometa."""
        orbit_shader.use()
        orbit_shader.set_mat4("uModel", glm.mat4(1.0))
        orbit_shader.set_mat4("uView", view)
        orbit_shader.set_mat4("uProjection", projection)
        orbit_shader.set_vec4("uOrbitColor", self.orbit_color)
        self.orbit_mesh.draw()
