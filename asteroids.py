"""
===============================================================================
Módulo: asteroids.py
Descrição: Cintura de Asteroides do Sistema Solar e Campos de Asteroides Errantes.
Conceitos aplicados:
  - Distribuição Orbital Kepleriana Estocástica:
      * Semi-eixos maiores entre 92.0 e 108.0 unidades (entre Marte e Júpiter).
      * Excentricidades e inclinações orbitais dispersas segundo distribuições gaussianas.
  - Carregamento de Modelos 3D Reais:
      * asteroid.glb, asteroid_01.glb e wandering_asteroids_of_andromeda.glb.
  - Rotações caóticas em 3 eixos independentes para cada asteroide.
===============================================================================
"""

from pathlib import Path
from typing import List, Optional, Tuple
import random
import math
import glm

from model_loader import GLBModel
from shader import Shader


class AsteroidInstance:
    """Representa um único asteroide com parâmetros orbitais e rotacionais próprios."""

    def __init__(
        self,
        semi_major_axis: float,
        eccentricity: float,
        inclination_deg: float,
        period_days: float,
        initial_angle_deg: float,
        scale: float,
        rotation_speeds: glm.vec3,
        model_index: int,
    ):
        self.a = semi_major_axis
        self.e = eccentricity
        self.inc_rad = math.radians(inclination_deg)
        self.period = period_days
        self.mean_anomaly = math.radians(initial_angle_deg)
        self.scale = scale
        self.rot_speeds = rotation_speeds
        self.model_index = model_index

        self.current_angles = glm.vec3(
            random.uniform(0.0, 360.0),
            random.uniform(0.0, 360.0),
            random.uniform(0.0, 360.0),
        )
        self.current_position = glm.vec3(0.0)

    def update(self, simulated_days: float, delta_sim_days: float) -> None:
        """Atualiza a posição kepleriana e a rotação caótica do asteroide."""
        # 1. Movimento orbital
        mean_motion = (2.0 * math.pi) / self.period
        M = (self.mean_anomaly + mean_motion * simulated_days) % (2.0 * math.pi)

        # Aproximação elíptica rápida
        # x' = a * (cos(M) - e)
        # z' = a * sqrt(1 - e^2) * sin(M)
        b = self.a * math.sqrt(max(0.0, 1.0 - self.e * self.e))
        x_prime = self.a * (math.cos(M) - self.e)
        z_prime = b * math.sin(M)

        # Inclinação
        x = x_prime
        y = z_prime * math.sin(self.inc_rad)
        z = z_prime * math.cos(self.inc_rad)

        self.current_position = glm.vec3(x, y, z)

        # 2. Rotação do corpo rochoso
        self.current_angles += self.rot_speeds * (delta_sim_days * 24.0)

    def get_model_matrix(self) -> glm.mat4:
        """Gera a matriz de transformação do asteroide."""
        m = glm.mat4(1.0)
        m = glm.translate(m, self.current_position)
        m = glm.rotate(m, math.radians(self.current_angles.x), glm.vec3(1.0, 0.0, 0.0))
        m = glm.rotate(m, math.radians(self.current_angles.y), glm.vec3(0.0, 1.0, 0.0))
        m = glm.rotate(m, math.radians(self.current_angles.z), glm.vec3(0.0, 0.0, 1.0))
        m = glm.scale(m, glm.vec3(self.scale))
        return m


class AsteroidBelt:
    """Gere a cintura de asteroides principal e campos de asteroides com modelos 3D."""

    def __init__(self, models_dir: Path, count: int = 180):
        self.models_dir = models_dir
        self.models: List[GLBModel] = []

        # Carrega os modelos de asteroides disponíveis na pasta Models/
        model_filenames = ["asteroid.glb", "asteroid_01.glb", "wandering_asteroids_of_andromeda.glb"]
        for fn in model_filenames:
            p = models_dir / fn
            if p.exists():
                try:
                    m = GLBModel(p)
                    self.models.append(m)
                    print(f"[Asteroides 3D] Modelo carregado: {fn}")
                except Exception as e:
                    print(f"[Asteroides Warning] Falha ao carregar {fn}: {e}")

        # Se nenhum modelo foi carregado, criamos a lista vazia
        self.asteroids: List[AsteroidInstance] = []
        if self.models:
            self._generate_belt(count)

    def _generate_belt(self, count: int) -> None:
        """Gera asteroides distribuídos entre a órbita de Marte (80) e Júpiter (118)."""
        random.seed(42)
        num_models = len(self.models)

        for _ in range(count):
            # Raio orbital entre 92 e 108 unidades
            a = random.uniform(92.0, 107.0)
            e = random.uniform(0.02, 0.16)
            inc = random.uniform(-6.0, 6.0)
            # 3ª Lei de Kepler aproximada: T proporcional a a^1.5
            period = 1100.0 * ((a / 98.0) ** 1.5)
            init_angle = random.uniform(0.0, 360.0)
            scale = random.uniform(0.25, 0.75)
            rot_speeds = glm.vec3(
                random.uniform(-40.0, 40.0),
                random.uniform(-40.0, 40.0),
                random.uniform(-40.0, 40.0),
            )
            mod_idx = random.randint(0, num_models - 1)

            ast = AsteroidInstance(
                semi_major_axis=a,
                eccentricity=e,
                inclination_deg=inc,
                period_days=period,
                initial_angle_deg=init_angle,
                scale=scale,
                rotation_speeds=rot_speeds,
                model_index=mod_idx,
            )
            self.asteroids.append(ast)

    def update(self, simulated_days: float, delta_sim_days: float) -> None:
        """Atualiza a simulação física de todos os asteroides da cintura."""
        for ast in self.asteroids:
            ast.update(simulated_days, delta_sim_days)

    def draw(
        self,
        shader: Shader,
        view: glm.mat4,
        projection: glm.mat4,
        view_pos: glm.vec3,
        sun_pos: glm.vec3,
    ) -> None:
        """Renderiza todos os asteroides da cintura com iluminação solar Blinn-Phong."""
        if not self.models or not self.asteroids:
            return

        shader.use()
        shader.set_mat4("uView", view)
        shader.set_mat4("uProjection", projection)
        shader.set_vec3("uLightPos", sun_pos)
        shader.set_vec3("uLightColor", glm.vec3(1.0, 0.98, 0.92))
        shader.set_vec3("uViewPos", view_pos)
        shader.set_vec3("uAmbientColor", glm.vec3(0.04, 0.04, 0.05))
        shader.set_float("uShininess", 8.0)
        shader.set_float("uSpecularStrength", 0.02)

        for ast in self.asteroids:
            model_matrix = ast.get_model_matrix()
            normal_matrix = glm.mat3(glm.transpose(glm.inverse(model_matrix)))

            shader.set_mat4("uModel", model_matrix)
            shader.set_mat3("uNormalMatrix", normal_matrix)

            model_obj = self.models[ast.model_index]
            model_obj.draw()
