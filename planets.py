"""
===============================================================================
Módulo: planets.py
Descrição: Definição dos corpos celestes do Sistema Solar e dados físicos reais.
Conceitos aplicados:
  - Transformações Geométricas e Hierarquia de Matrizes:
      * Matriz Model = Translação(Posição Orbital) * Rotação(Inclinação Axial)
                      * Rotação(Eixo Próprio) * Escala(Raio)
  - Rotação Planetária Individual:
      * Períodos de rotação sideral próprios (Vénus retrógrado, Úrano inclinado a 97°).
      * Inclinação axial real (Obliquidade).
  - Translação Orbital Elíptica:
      * Interação com o módulo de órbitas keplerianas.
  - Iluminação Dinâmica:
      * Sol como emissor central pontual em (0, 0, 0) com Blinn-Phong nos planetas.
===============================================================================
"""

from pathlib import Path
from typing import Dict, List, Optional
import math
import glm
from OpenGL.GL import glDisable, glEnable, GL_CULL_FACE

from mesh import SphereMesh, OrbitMesh, RingMesh
from texture import TextureLoader, Texture
from shader import Shader
from orbits import KeplerianOrbit
from model_loader import GLBModel
from moons import Moon, MOONS_DATA


# =============================================================================
# BASE DE DADOS ASTRONÓMICOS REAIS DO SISTEMA SOLAR
# =============================================================================
CELESTIAL_DATA = {
    "sun": {
        "name": "Sol",
        "model_file": "sun.glb",
        "radius_km": 696340,
        "visual_radius": 14.0,           # Raio didático para visualização equilibrada
        "real_radius_scale": 109.0,
        "distance_au": 0.0,
        "semi_major_axis": 0.0,
        "eccentricity": 0.0,
        "inclination_deg": 0.0,
        "orbital_period_days": 1.0,
        "rotation_period_hours": 609.12,  # 25.38 dias no equador
        "axial_tilt_deg": 7.25,
        "mass_kg": "1.989 × 10³⁰ kg",
        "gravity": "274.0 m/s²",
        "temperature": "5500 °C (Superfície)",
        "atmosphere": "Hidrogénio (73%), Hélio (25%)",
        "moons_count": 0,
        "texture_file": "2k_sun.jpg",
        "orbit_color": glm.vec4(1.0, 1.0, 0.2, 0.3),
    },
    "mercury": {
        "name": "Mercúrio",
        "model_file": "mercurio_v1.1.glb",
        "radius_km": 2439.7,
        "visual_radius": 1.4,
        "real_radius_scale": 0.38,
        "distance_au": 0.387,
        "semi_major_axis": 28.0,
        "eccentricity": 0.2056,          # Órbita altamente excêntrica!
        "inclination_deg": 7.0,          # Maior inclinação orbital dos 8 planetas
        "orbital_period_days": 87.97,
        "initial_mean_anomaly_deg": 174.796,  # Posição real J2000.0
        "rotation_period_hours": 1407.6, # 58.6 dias
        "axial_tilt_deg": 0.034,
        "mass_kg": "3.301 × 10²³ kg",
        "gravity": "3.7 m/s²",
        "temperature": "-180 °C a 430 °C",
        "atmosphere": "Praticamente inexistente (Exosfera ténue)",
        "moons_count": 0,
        "texture_file": "2k_mercury.jpg",
        "orbit_color": glm.vec4(0.7, 0.7, 0.7, 0.45),
    },
    "venus": {
        "name": "Vénus",
        "model_file": "venus_v1.1.glb",
        "radius_km": 6051.8,
        "visual_radius": 2.2,
        "real_radius_scale": 0.95,
        "distance_au": 0.723,
        "semi_major_axis": 42.0,
        "eccentricity": 0.0067,          # A órbita mais circular do Sistema Solar
        "inclination_deg": 3.39,
        "orbital_period_days": 224.7,
        "initial_mean_anomaly_deg": 50.115,   # Posição real J2000.0
        "rotation_period_hours": -5832.5,# Rotação RETRÓGRADA! (sentido oposto)
        "axial_tilt_deg": 177.36,        # Polo norte virado "de cabeça para baixo"
        "mass_kg": "4.867 × 10²⁴ kg",
        "gravity": "8.87 m/s²",
        "temperature": "465 °C (Efeito de estufa extremo)",
        "atmosphere": "Dióxido de Carbono (96.5%), Azoto (3.5%)",
        "moons_count": 0,
        "texture_file": "2k_venus_surface.jpg",
        "orbit_color": glm.vec4(0.9, 0.7, 0.3, 0.45),
    },
    "earth": {
        "name": "Terra",
        "model_file": "planeta_tierra.glb",
        "radius_km": 6371.0,
        "visual_radius": 2.5,
        "real_radius_scale": 1.0,
        "distance_au": 1.0,
        "semi_major_axis": 60.0,
        "eccentricity": 0.0167,
        "inclination_deg": 0.00,         # Referência do plano da eclítica
        "orbital_period_days": 365.256,
        "initial_mean_anomaly_deg": 357.529,  # Posição real J2000.0
        "rotation_period_hours": 23.934, # 1 dia sideral
        "axial_tilt_deg": 23.44,         # Responsável pelas estações do ano
        "mass_kg": "5.972 × 10²⁴ kg",
        "gravity": "9.807 m/s²",
        "temperature": "-88 °C a 58 °C (Média: 15 °C)",
        "atmosphere": "Azoto (78%), Oxigénio (21%), Árgon (0.9%)",
        "moons_count": 1,
        "texture_file": "2k_earth_daymap.jpg",
        "orbit_color": glm.vec4(0.2, 0.6, 1.0, 0.5),
    },
    "mars": {
        "name": "Marte",
        "model_file": "marte_v1.1.glb",
        "radius_km": 3389.5,
        "visual_radius": 1.7,
        "real_radius_scale": 0.53,
        "distance_au": 1.524,
        "semi_major_axis": 80.0,
        "eccentricity": 0.0934,
        "inclination_deg": 1.85,
        "orbital_period_days": 686.98,
        "initial_mean_anomaly_deg": 19.373,   # Posição real J2000.0
        "rotation_period_hours": 24.623,
        "axial_tilt_deg": 25.19,
        "mass_kg": "6.417 × 10²³ kg",
        "gravity": "3.72 m/s²",
        "temperature": "-140 °C a 20 °C (Média: -63 °C)",
        "atmosphere": "Dióxido de Carbono (95%), Azoto (2.8%)",
        "moons_count": 2,
        "texture_file": "2k_mars.jpg",
        "orbit_color": glm.vec4(0.9, 0.35, 0.2, 0.5),
    },
    "jupiter": {
        "name": "Júpiter",
        "model_file": "jupiter.glb",
        "radius_km": 69911,
        "visual_radius": 6.8,
        "real_radius_scale": 11.2,
        "distance_au": 5.204,
        "semi_major_axis": 118.0,
        "eccentricity": 0.0489,
        "inclination_deg": 1.304,
        "orbital_period_days": 4332.59,  # ~11.86 anos
        "initial_mean_anomaly_deg": 20.020,   # Posição real J2000.0
        "rotation_period_hours": 9.925,  # Rotação mais rápida do Sistema Solar!
        "axial_tilt_deg": 3.13,
        "mass_kg": "1.898 × 10²⁷ kg",
        "gravity": "24.79 m/s²",
        "temperature": "-110 °C (Nuvens)",
        "atmosphere": "Hidrogénio (90%), Hélio (10%)",
        "moons_count": 95,
        "texture_file": "2k_jupiter.jpg",
        "orbit_color": glm.vec4(0.85, 0.65, 0.45, 0.5),
    },
    "saturn": {
        "name": "Saturno",
        "model_file": "saturno.glb",
        "radius_km": 58232,
        "visual_radius": 5.6,
        "real_radius_scale": 9.45,
        "distance_au": 9.582,
        "semi_major_axis": 160.0,
        "eccentricity": 0.0565,
        "inclination_deg": 2.485,
        "orbital_period_days": 10759.22, # ~29.45 anos
        "initial_mean_anomaly_deg": 317.021,  # Posição real J2000.0
        "rotation_period_hours": 10.656,
        "axial_tilt_deg": 26.73,
        "mass_kg": "5.683 × 10²⁶ kg",
        "gravity": "10.44 m/s²",
        "temperature": "-140 °C",
        "atmosphere": "Hidrogénio (96%), Hélio (3%)",
        "moons_count": 146,
        "has_rings": True,
        "ring_texture_file": "saturn_ring.png",
        "ring_inner_radius": 1.30,
        "ring_outer_radius": 2.50,
        "texture_file": "2k_saturn.jpg",
        "orbit_color": glm.vec4(0.9, 0.8, 0.5, 0.5),
    },
    "uranus": {
        "name": "Úrano",
        "model_file": None,
        "radius_km": 25362,
        "visual_radius": 3.8,
        "real_radius_scale": 4.0,
        "distance_au": 19.22,
        "semi_major_axis": 205.0,
        "eccentricity": 0.0463,
        "inclination_deg": 0.772,
        "orbital_period_days": 30685.4,  # ~84 anos
        "initial_mean_anomaly_deg": 142.238,  # Posição real J2000.0
        "rotation_period_hours": -17.24, # Rotação retrógrada e "deitado"
        "axial_tilt_deg": 97.77,         # Eixo quase paralelo ao plano orbital!
        "mass_kg": "8.681 × 10²⁵ kg",
        "gravity": "8.69 m/s²",
        "temperature": "-195 °C",
        "atmosphere": "Hidrogénio (83%), Hélio (15%), Metano (2%)",
        "moons_count": 28,
        "texture_file": "2k_uranus.jpg",
        "orbit_color": glm.vec4(0.4, 0.85, 0.85, 0.5),
    },
    "neptune": {
        "name": "Neptuno",
        "model_file": "neptuno.glb",
        "radius_km": 24622,
        "visual_radius": 3.6,
        "real_radius_scale": 3.88,
        "distance_au": 30.05,
        "semi_major_axis": 250.0,
        "eccentricity": 0.00945,
        "inclination_deg": 1.769,
        "orbital_period_days": 60189.0,  # ~164.8 anos
        "initial_mean_anomaly_deg": 256.228,  # Posição real J2000.0
        "rotation_period_hours": 16.11,
        "axial_tilt_deg": 28.32,
        "mass_kg": "1.024 × 10²⁶ kg",
        "gravity": "11.15 m/s²",
        "temperature": "-200 °C",
        "atmosphere": "Hidrogénio (80%), Hélio (19%), Metano (1.5%)",
        "moons_count": 16,
        "texture_file": "2k_neptune.jpg",
        "orbit_color": glm.vec4(0.25, 0.45, 0.95, 0.5),
    },
}


class CelestialBody:
    """
    Representa um corpo celeste individual no simulador astronómico.
    Gere a malha esférica, textura, órbita elíptica, rotação axial e matriz Model.
    """

    def __init__(
        self,
        body_id: str,
        data: dict,
        textures_dir: Path,
        models_dir: Optional[Path],
        shared_sphere_mesh: SphereMesh,
    ):
        self.id = body_id
        self.data = data
        self.name = data["name"]
        self.is_sun = (body_id == "sun")

        # Geometria partilhada da esfera unitária (fallback de segurança)
        self.mesh = shared_sphere_mesh

        # Carregamento do modelo 3D GLB da pasta Models/ (se disponível)
        self.glb_model: Optional[GLBModel] = None
        model_filename = data.get("model_file")
        if models_dir and model_filename:
            model_path = models_dir / model_filename
            if model_path.exists():
                try:
                    self.glb_model = GLBModel(model_path)
                    print(f"[Model 3D] Modelo GLB carregado para '{self.name}': {model_filename}")
                except Exception as e:
                    print(f"[Model Warning] Falha ao carregar modelo 3D '{model_filename}' para {self.name}: {e}. A usar malha esférica UV.")

        # Carregamento da textura real (com fallback procedural em caso de ausência)
        tex_path = textures_dir / data["texture_file"]
        self.texture = TextureLoader.load(tex_path, fallback_key=body_id)

        # Sistema de Luas com Hierarquia de Matrizes (Obrigatório 4)
        self.moons: List[Moon] = []
        raw_moons = MOONS_DATA.get(body_id, [])
        for m_data in raw_moons:
            moon_obj = Moon(
                moon_data=m_data,
                textures_dir=textures_dir,
                models_dir=models_dir,
                shared_sphere_mesh=shared_sphere_mesh,
            )
            self.moons.append(moon_obj)

        # Configuração da Órbita Kepleriana (exceto para o Sol que repousa no foco)
        if not self.is_sun:
            self.orbit = KeplerianOrbit(
                semi_major_axis=data["semi_major_axis"],
                eccentricity=data["eccentricity"],
                inclination_deg=data["inclination_deg"],
                orbital_period_days=data["orbital_period_days"],
                initial_mean_anomaly_deg=data.get("initial_mean_anomaly_deg", 0.0),
            )
            # Malha 3D da linha da órbita
            points = self.orbit.generate_orbit_points(num_points=240)
            self.orbit_mesh = OrbitMesh(points)
        else:
            self.orbit = None
            self.orbit_mesh = None

        # Parâmetros físicos de rotação
        self.visual_radius = float(data["visual_radius"])
        self.axial_tilt_rad = math.radians(float(data["axial_tilt_deg"]))
        self.rotation_period_hours = float(data["rotation_period_hours"])

        # Configuração de anéis planetários com sombra analítica (ex: Saturno)
        self.has_rings = data.get("has_rings", False)
        self.ring_mesh = None
        self.ring_texture = None
        if self.has_rings:
            inner_r = data.get("ring_inner_radius", 1.30)
            outer_r = data.get("ring_outer_radius", 2.50)
            self.ring_mesh = RingMesh(inner_radius=inner_r, outer_radius=outer_r, segments=144)
            ring_tex_file = data.get("ring_texture_file", "saturn_ring.png")
            ring_path = textures_dir / ring_tex_file
            if ring_path.exists():
                self.ring_texture = TextureLoader.load(ring_path)
            else:
                self.ring_texture = self.texture

        # Estado dinâmico
        self.current_position = glm.vec3(0.0, 0.0, 0.0)
        self.rotation_angle_deg = 0.0

    def update(self, simulated_days: float, delta_sim_days: float) -> None:
        """
        Atualiza a posição kepleriana e a rotação em torno do próprio eixo.
        """
        # 1. Atualização da translação orbital kepleriana
        if not self.is_sun and self.orbit:
            self.current_position = self.orbit.get_position_at_time(simulated_days)
        else:
            self.current_position = glm.vec3(0.0, 0.0, 0.0)

        # 2. Atualização da rotação axial
        delta_hours = delta_sim_days * 24.0
        degrees_per_hour = 360.0 / self.rotation_period_hours
        self.rotation_angle_deg = (self.rotation_angle_deg + degrees_per_hour * delta_hours) % 360.0

        # 3. Atualização das luas subordinadas (Hierarquia)
        for moon in self.moons:
            moon.update(simulated_days, delta_sim_days, self.current_position)

    def get_model_matrix(self) -> glm.mat4:
        """
        Constrói a Matriz de Modelo (Model Matrix) do corpo celeste aplicando
        a hierarquia clássica de transformações geométricas:
          Model = Translate(Posição Orbital)
                * Rotate(Inclinação Axial)
                * Rotate(Rotação Própria em torno do eixo Y)
                * Scale(Raio Visual)
        """
        model = glm.mat4(1.0)

        # 1. Translação para a posição no espaço de mundo (posição focal kepleriana)
        model = glm.translate(model, self.current_position)

        # 2. Inclinação axial (obliquidade em relação ao plano orbital)
        model = glm.rotate(model, self.axial_tilt_rad, glm.vec3(0.0, 0.0, 1.0))

        # 3. Rotação do planeta sobre o seu próprio eixo polar
        model = glm.rotate(model, math.radians(self.rotation_angle_deg), glm.vec3(0.0, 1.0, 0.0))

        # 4. Escala proporcional ao tamanho do corpo
        model = glm.scale(model, glm.vec3(self.visual_radius))

        return model

    def draw(
        self,
        shader: Shader,
        view: glm.mat4,
        projection: glm.mat4,
        view_pos: glm.vec3,
        sun_pos: glm.vec3,
    ) -> None:
        """Renderiza a esfera do planeta com as matrizes e texturas vinculadas."""
        shader.use()

        model = self.get_model_matrix()
        # Matriz Normal: inversa transposta dos 3x3 superiores da Model Matrix
        normal_matrix = glm.mat3(glm.transpose(glm.inverse(model)))

        shader.set_mat4("uModel", model)
        shader.set_mat4("uView", view)
        shader.set_mat4("uProjection", projection)
        shader.set_mat3("uNormalMatrix", normal_matrix)

        if not self.is_sun:
            shader.set_vec3("uLightPos", sun_pos)
            shader.set_vec3("uLightColor", glm.vec3(1.0, 0.98, 0.92))
            shader.set_vec3("uViewPos", view_pos)
            # Iluminação cósmica ambiente visível para todos os planetas (evita planetas 100% pretos no lado noturno)
            shader.set_vec3("uAmbientColor", glm.vec3(0.20, 0.20, 0.24))
            shader.set_float("uShininess", 32.0)
            shader.set_float("uSpecularStrength", 0.35 if self.id == "earth" else 0.08)

        # Garante que o sampler uTexture aponte sempre para a unidade GL_TEXTURE0
        shader.set_int("uTexture", 0)

        # Se possuir modelo 3D GLB carregado, desenha o modelo polígono
        if self.glb_model:
            self.glb_model.draw(default_texture=self.texture)
        else:
            # Caso contrário, desenha a esfera UV paramétrica com a textura vinculada
            self.texture.bind(0)
            self.mesh.draw()

        # Renderização das luas subordinadas na hierarquia (modelo do planeta * modelo da lua)
        for moon in self.moons:
            moon.draw(
                shader=shader,
                view=view,
                proj=projection,
                view_pos=view_pos,
                sun_pos=sun_pos,
                parent_model=model,
                parent_pos=self.current_position,
            )

    def draw_orbit(self, orbit_shader: Shader, view: glm.mat4, projection: glm.mat4) -> None:
        """Desenha a linha da órbita elíptica se o corpo possuir órbita definida."""
        if self.orbit_mesh is not None:
            orbit_shader.use()
            orbit_shader.set_mat4("uModel", glm.mat4(1.0))
            orbit_shader.set_mat4("uView", view)
            orbit_shader.set_mat4("uProjection", projection)
            orbit_shader.set_vec4("uOrbitColor", self.data["orbit_color"])
            self.orbit_mesh.draw()

        # Desenho das órbitas das luas
        for moon in self.moons:
            moon.draw_orbit(orbit_shader, view, projection, self.current_position)

    def draw_rings(
        self,
        ring_shader: Shader,
        view: glm.mat4,
        projection: glm.mat4,
        sun_pos: glm.vec3,
    ) -> None:
        """Renderiza os anéis com projeção de sombra analítica raio-esfera."""
        if not self.has_rings or self.ring_mesh is None or self.ring_texture is None:
            return

        ring_shader.use()

        # Matriz de modelo dos anéis alinhada com o equador do planeta
        ring_model = glm.mat4(1.0)
        ring_model = glm.translate(ring_model, self.current_position)
        ring_model = glm.rotate(ring_model, self.axial_tilt_rad, glm.vec3(0.0, 0.0, 1.0))
        ring_model = glm.scale(ring_model, glm.vec3(self.visual_radius))

        ring_shader.set_mat4("uModel", ring_model)
        ring_shader.set_mat4("uView", view)
        ring_shader.set_mat4("uProjection", projection)
        ring_shader.set_vec3("uSunPos", sun_pos)
        ring_shader.set_vec3("uPlanetCenter", self.current_position)
        ring_shader.set_float("uPlanetRadius", self.visual_radius)
        ring_shader.set_vec3("uLightColor", glm.vec3(1.0, 0.98, 0.92))
        ring_shader.set_vec3("uAmbientColor", glm.vec3(0.25, 0.25, 0.28))
        ring_shader.set_int("uTexture", 0)

        self.ring_texture.bind(0)

        # Desativa Face Culling temporariamente para anéis visíveis em ambos os lados
        glDisable(GL_CULL_FACE)
        self.ring_mesh.draw()
        glEnable(GL_CULL_FACE)


class SolarSystem:
    """Gere todos os corpos celestes, iluminação e o ciclo de simulação física."""

    def __init__(self, textures_dir: Path, models_dir: Optional[Path] = None):
        self.textures_dir = textures_dir
        self.models_dir = models_dir
        # Malha esférica UV partilhada em memória para máxima eficiência
        self.sphere_mesh = SphereMesh(radius=1.0, stacks=48, slices=64)

        self.bodies: Dict[str, CelestialBody] = {}
        for body_id, data in CELESTIAL_DATA.items():
            self.bodies[body_id] = CelestialBody(
                body_id=body_id,
                data=data,
                textures_dir=textures_dir,
                models_dir=models_dir,
                shared_sphere_mesh=self.sphere_mesh,
            )

        # Tempo simulado acumulado (em dias terrestres)
        self.simulated_days: float = 0.0

        # Inicializa todos os corpos nas posições keplerianas do tempo inicial T=0
        for body in self.bodies.values():
            body.update(0.0, 0.0)

    def update(self, delta_time_seconds: float, time_scale_days_per_sec: float) -> None:
        """
        Avança o tempo astronómico simulado e atualiza todos os planetas.
        """
        delta_sim_days = delta_time_seconds * time_scale_days_per_sec
        self.simulated_days += delta_sim_days

        for body in self.bodies.values():
            body.update(self.simulated_days, delta_sim_days)

    def reset_time(self) -> None:
        """Repõe o tempo da simulação a zero (Tecla R)."""
        self.simulated_days = 0.0
        for body in self.bodies.values():
            body.update(0.0, 0.0)

    def draw(
        self,
        celestial_shader: Shader,
        sun_shader: Shader,
        orbit_shader: Shader,
        view: glm.mat4,
        projection: glm.mat4,
        view_pos: glm.vec3,
        show_orbits: bool = True,
        current_time: float = 0.0,
        ring_shader: Optional[Shader] = None,
    ) -> None:
        """Renderiza o Sistema Solar completo: órbitas, Sol emissivo, planetas e anéis com sombra."""
        # 1. Renderização das linhas de órbita elíptica (se ativas)
        if show_orbits:
            for body in self.bodies.values():
                body.draw_orbit(orbit_shader, view, projection)

        # 2. Renderização do Sol com o shader emissivo próprio e plasma procedural
        sun = self.bodies["sun"]
        sun_shader.use()
        sun_model = sun.get_model_matrix()
        sun_shader.set_mat4("uModel", sun_model)
        sun_shader.set_mat4("uView", view)
        sun_shader.set_mat4("uProjection", projection)
        sun_shader.set_vec3("uSunColor", glm.vec3(1.0, 0.95, 0.85))
        sun_shader.set_vec3("uViewPos", view_pos)
        sun_shader.set_float("uTime", float(current_time))
        sun_shader.set_int("uTexture", 0)
        if sun.glb_model:
            sun.glb_model.draw(default_texture=sun.texture)
        else:
            sun.texture.bind(0)
            sun.mesh.draw()

        # 3. Renderização dos 8 planetas com iluminação solar dinâmica Blinn-Phong
        sun_pos = sun.current_position
        for body_id, body in self.bodies.items():
            if body_id == "sun":
                continue
            body.draw(celestial_shader, view, projection, view_pos, sun_pos)

        # 4. Renderização dos anéis planetários com projeção analítica de sombra (ex: Saturno)
        if ring_shader is not None:
            for body in self.bodies.values():
                if getattr(body, "has_rings", False):
                    body.draw_rings(ring_shader, view, projection, sun_pos)
