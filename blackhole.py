"""
===============================================================================
Módulo: blackhole.py
Descrição: Sistema Cósmico de Buracos Negros Relativísticos (8 Singularidades)
           com Simulação Física de Atração de Matéria (Asteroides, Cometas,
           Meteoros e Satélites em Espiral de Acreção).
Conceitos aplicados:
  - Modelagem e Renderização de Objetos Relativísticos com Modelos 3D:
      * black_hole.glb (Singularidade Estelar Primária: Cygnus X-1)
      * black_hole_12.glb (Gargantua: Sistema Binário Relativístico)
      * black_hole_galaxy.glb (Sagitário A*: Buraco Negro Supermassivo Central)
      * black_hole (1).glb (V404 Cygni: Microquasar Relativístico)
      * black_hole (2).glb (GRO J1655-40: Vórtice Espaço-Temporal Escarlate)
      * black_hole (3).glb (M87* Progenitor: Horizonte das Sombras Cósmicas)
      * black_hole_12 (1).glb (Sagittarius B2: Gargantua Secundário Hiperdenso)
      * not_a_black_hole_-_1.glb (Anomalia Gravitacional Primordial Exótica)
  - Simulação de Atração Gravitacional e Espiral de Queda de Matéria:
      * Asteroides (asteroid.glb, asteroid_01.glb, wandering_asteroids_of_andromeda.glb)
      * Cometa interestelar com cauda de plasma (3iatlas_-_blue_kachina_comet_tribute.glb)
      * Meteoros e bólides em desintegração térmica (boros_meteoric_burst.glb)
      * Satélites orbitais e foguetões lunares capturados (satellite.glb, rocket_orbiting_moon.glb)
      * Dinâmica de conservação de momento angular e espargueteificação gravitacional.
  - Alerta de Perigo Progressivo (5s) e Revelação de Singularidade (+5s).
  - Teletransporte e Enquadramento Frente a Frente com a tecla [ALT].
  - Efeito de Sucção no Buraco de Minhoca e Propulsão Warp de Fuga com [SHIFT].
===============================================================================
"""

from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import math
import random
import glm

from model_loader import GLBModel
from shader import Shader


class BlackHole:
    """Representa uma singularidade gravitacional com disco de acreção rotativo."""

    def __init__(
        self,
        name: str,
        position: glm.vec3,
        scale: float,
        model_filename: str,
        models_dir: Path,
        accretion_rotation_speed: float = 35.0,
        warning_radius: float = 520.0,
        visible_radius: float = 420.0,
        pull_radius: float = 190.0,
        light_color: Optional[glm.vec3] = None,
        ambient_color: Optional[glm.vec3] = None,
        description: str = "",
    ):
        self.name = name
        self.position = glm.vec3(position)
        self.scale = scale
        self.rot_speed = accretion_rotation_speed
        self.current_rot_deg = 0.0
        self.warning_radius = warning_radius
        self.visible_radius = visible_radius
        self.pull_radius = pull_radius
        self.description = description

        self.light_color = light_color if light_color is not None else glm.vec3(1.0, 0.85, 0.5)
        self.ambient_color = ambient_color if ambient_color is not None else glm.vec3(0.85, 0.55, 0.25)
        self.is_revealed: bool = False

        self.model: Optional[GLBModel] = None
        p = models_dir / model_filename
        if p.exists():
            try:
                self.model = GLBModel(p)
                print(f"[Buraco Negro 3D] Modelo carregado para '{name}': {model_filename}")
            except Exception as e:
                print(f"[Buraco Negro Warning] Falha ao carregar {model_filename}: {e}")
        else:
            print(f"[Buraco Negro Warning] Ficheiro {model_filename} não encontrado em {models_dir}")

    def is_visible_from(self, view_pos: glm.vec3) -> bool:
        """Determina a visibilidade cósmica da singularidade."""
        if self.is_revealed:
            return glm.length(self.position - view_pos) <= 6500.0
        return glm.length(self.position - view_pos) <= self.visible_radius

    def update(self, delta_time: float) -> None:
        """Faz rodar o disco de acreção de matéria incandescente."""
        self.current_rot_deg = (self.current_rot_deg + self.rot_speed * delta_time) % 360.0

    def get_model_matrix(self) -> glm.mat4:
        """Gera a matriz Model do buraco negro com rotação do disco de acreção."""
        m = glm.mat4(1.0)
        m = glm.translate(m, self.position)
        m = glm.rotate(m, math.radians(self.current_rot_deg), glm.vec3(0.0, 1.0, 0.0))
        m = glm.scale(m, glm.vec3(self.scale))
        return m

    def draw(
        self,
        shader: Shader,
        view: glm.mat4,
        proj: glm.mat4,
        view_pos: glm.vec3,
    ) -> None:
        """Renderiza o buraco negro com iluminação emissiva e disco incandescente."""
        if not self.model:
            return

        shader.use()
        model_matrix = self.get_model_matrix()
        normal_matrix = glm.mat3(glm.transpose(glm.inverse(model_matrix)))

        shader.set_mat4("uModel", model_matrix)
        shader.set_mat4("uView", view)
        shader.set_mat4("uProjection", proj)
        shader.set_mat3("uNormalMatrix", normal_matrix)
        shader.set_vec3("uLightPos", self.position)
        shader.set_vec3("uLightColor", self.light_color)
        shader.set_vec3("uViewPos", view_pos)
        shader.set_vec3("uAmbientColor", self.ambient_color)
        shader.set_float("uShininess", 64.0)
        shader.set_float("uSpecularStrength", 0.7)

        self.model.draw()


class InfallBody:
    """
    Representa um corpo celeste (asteroide, cometa, meteoro, satélite ou foguetão)
    sendo inexoravelmente atraído pela gravidade extrema do buraco negro.
    """

    def __init__(
        self,
        model_key: str,
        bh_index: int,
        initial_radius: float,
        initial_angle: float,
        orbit_speed: float,
        infall_speed: float,
        scale: float,
        tilt_deg: float,
        height_offset: float,
        rot_speeds: glm.vec3,
        name: str,
    ):
        self.model_key = model_key
        self.bh_index = bh_index
        self.radius = initial_radius
        self.angle = initial_angle
        self.orbit_speed = orbit_speed
        self.infall_speed = infall_speed
        self.base_scale = scale
        self.tilt_rad = math.radians(tilt_deg)
        self.height_offset = height_offset
        self.rot_speeds = rot_speeds
        self.current_angles = glm.vec3(
            random.uniform(0.0, 360.0),
            random.uniform(0.0, 360.0),
            random.uniform(0.0, 360.0),
        )
        self.current_pos = glm.vec3(0.0)
        self.name = name
        self.event_horizon_radius = 12.0

    def update(self, delta_time: float, bh_pos: glm.vec3) -> None:
        """
        Atualiza a trajetória relativística em espiral de acreção:
        - A velocidade orbital aumenta à medida que o raio diminui (Conservação de Momento Angular).
        - A velocidade de queda radial acelera dramaticamente perto do horizonte de eventos.
        - Se atingir o horizonte, é destruído e reaparece na borda externa do disco.
        """
        r_safe = max(8.0, self.radius)
        speed_mult = (150.0 / r_safe) ** 1.25
        infall_mult = (130.0 / r_safe) ** 1.45

        self.angle += self.orbit_speed * speed_mult * delta_time
        self.radius -= self.infall_speed * infall_mult * delta_time
        self.current_angles += self.rot_speeds * (speed_mult * delta_time * 45.0)

        # Cálculo da posição tridimensional em espiral de acreção
        x = self.radius * math.cos(self.angle)
        z = self.radius * math.sin(self.angle)
        y = math.sin(self.angle * 2.2) * self.height_offset + z * math.sin(self.tilt_rad)

        self.current_pos = bh_pos + glm.vec3(x, y, z)

        # Se cruzar o horizonte de eventos (consumido pela singularidade)
        if self.radius <= self.event_horizon_radius:
            self.radius = random.uniform(190.0, 280.0)
            self.angle = random.uniform(0.0, 2.0 * math.pi)
            self.height_offset = random.uniform(-10.0, 10.0)
            self.tilt_rad = math.radians(random.uniform(-22.0, 22.0))
            self.infall_speed = random.uniform(7.0, 20.0)

    def get_model_matrix(self) -> glm.mat4:
        """
        Gera a matriz Model com rotação caótica e espargueteificação gravitacional.
        """
        m = glm.mat4(1.0)
        m = glm.translate(m, self.current_pos)
        m = glm.rotate(m, math.radians(self.current_angles.x), glm.vec3(1.0, 0.0, 0.0))
        m = glm.rotate(m, math.radians(self.current_angles.y), glm.vec3(0.0, 1.0, 0.0))
        m = glm.rotate(m, math.radians(self.current_angles.z), glm.vec3(0.0, 0.0, 1.0))

        # Espargueteificação gravitacional (alongamento tidal no sentido radial)
        stretch = min(3.0, 1.0 + max(0.0, (45.0 - self.radius) / 14.0))
        m = glm.scale(m, glm.vec3(self.base_scale, self.base_scale, self.base_scale * stretch))
        return m


class BlackHoleInfallSystem:
    """
    Gere a simulação de matéria cósmica capturada (asteroides, cometas, meteoros e satélites)
    sendo atraída para o vórtice dos buracos negros.
    """

    def __init__(self, models_dir: Path, black_holes: List[BlackHole]):
        self.models: Dict[str, GLBModel] = {}
        self.bodies: List[InfallBody] = []

        model_files = {
            "asteroid_main": "asteroid.glb",
            "asteroid_rock": "asteroid_01.glb",
            "andromeda_cluster": "wandering_asteroids_of_andromeda.glb",
            "asteroid_field": "asteroid_field_100_x_medium-poly.glb",
            "comet": "3iatlas_-_blue_kachina_comet_tribute.glb",
            "meteor": "boros_meteoric_burst.glb",
            "satellite": "satellite.glb",
            "rocket": "rocket_orbiting_moon.glb",
        }

        for key, fname in model_files.items():
            fpath = models_dir / fname
            if fpath.exists():
                try:
                    self.models[key] = GLBModel(fpath)
                    print(f"[Matéria em Queda] Modelo carregado para atração: {fname}")
                except Exception as e:
                    print(f"[Matéria em Queda Warning] Erro ao carregar {fname}: {e}")

        # População rica de matéria em queda gravitacional distribuída pelas singularidades
        available_keys = list(self.models.keys())
        if not available_keys:
            return

        descriptions = {
            "asteroid_main": ("Asteroide Condrítico", 2.0),
            "asteroid_rock": ("Asteroide Metálico", 1.8),
            "andromeda_cluster": ("Fragmentos de Asteroide", 2.2),
            "asteroid_field": ("Enxame de Detritos Espaciais", 2.5),
            "comet": ("Cometa Interestelar em Queda", 3.2),
            "meteor": ("Meteoro em Plasma Incandescente", 3.0),
            "satellite": ("Satélite Orbital Descontrolado", 1.8),
            "rocket": ("Foguetão Apollo Atraído", 2.4),
        }

        # Cria múltiplos corpos em órbita de atração para cada buraco negro
        for bh_idx, bh in enumerate(black_holes):
            # Singularidade primária (Cygnus X-1) e Gargantua recebem maior densidade de matéria
            count = 10 if bh_idx in (0, 1) else 4
            for _ in range(count):
                chosen_key = random.choice(available_keys)
                desc, base_sz = descriptions.get(chosen_key, ("Detrito Cósmico", 2.0))
                sz = base_sz * random.uniform(0.75, 1.35)

                body = InfallBody(
                    model_key=chosen_key,
                    bh_index=bh_idx,
                    initial_radius=random.uniform(40.0, 240.0),
                    initial_angle=random.uniform(0.0, 2.0 * math.pi),
                    orbit_speed=random.uniform(0.35, 0.85),
                    infall_speed=random.uniform(6.0, 18.0),
                    scale=sz,
                    tilt_deg=random.uniform(-20.0, 20.0),
                    height_offset=random.uniform(-10.0, 10.0),
                    rot_speeds=glm.vec3(
                        random.uniform(0.5, 3.0),
                        random.uniform(0.5, 3.0),
                        random.uniform(0.5, 3.0),
                    ),
                    name=desc,
                )
                self.bodies.append(body)

        print(f"[Matéria em Queda] {len(self.bodies)} corpos celestes em atração gravitacional gerados!")

    def update(self, delta_time: float, black_holes: List[BlackHole]) -> None:
        """Atualiza a posição de todos os asteroides, cometas, meteoros e satélites em atração."""
        for body in self.bodies:
            if 0 <= body.bh_index < len(black_holes):
                bh = black_holes[body.bh_index]
                body.update(delta_time, bh.position)

    def draw(
        self,
        shader: Shader,
        view: glm.mat4,
        proj: glm.mat4,
        view_pos: glm.vec3,
        black_holes: List[BlackHole],
    ) -> None:
        """Renderiza os corpos atraídos que orbitam buracos negros visíveis."""
        shader.use()
        for body in self.bodies:
            if 0 <= body.bh_index < len(black_holes):
                bh = black_holes[body.bh_index]
                if not bh.is_visible_from(view_pos):
                    continue

                mod = self.models.get(body.model_key)
                if not mod:
                    continue

                model_matrix = body.get_model_matrix()
                normal_matrix = glm.mat3(glm.transpose(glm.inverse(model_matrix)))

                shader.set_mat4("uModel", model_matrix)
                shader.set_mat4("uView", view)
                shader.set_mat4("uProjection", proj)
                shader.set_mat3("uNormalMatrix", normal_matrix)
                shader.set_vec3("uLightPos", bh.position)
                shader.set_vec3("uLightColor", bh.light_color)
                shader.set_vec3("uViewPos", view_pos)
                # Iluminação emissiva quente do disco de acreção
                shader.set_vec3("uAmbientColor", glm.vec3(0.9, 0.6, 0.3))
                shader.set_float("uShininess", 32.0)
                shader.set_float("uSpecularStrength", 0.5)

                mod.draw()


class BlackHoleSystem:
    """Gere todas as 8 singularidades cósmicas espalhadas em diferentes direções cósmicas."""

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.black_holes: List[BlackHole] = []
        self.current_index: int = 0
        self.all_revealed: bool = False

        # ---------------------------------------------------------------------
        # 1. Singularidade Estelar Primária: Cygnus X-1 (Setor Frontal: -Z)
        # Rota de saída padrão ao deixar o Sol e avançar em linha reta
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="Cygnus X-1 (⚡ O Pioneiro)",
            position=glm.vec3(0.0, 25.0, -650.0),
            scale=24.0,
            model_filename="black_hole.glb",
            models_dir=models_dir,
            accretion_rotation_speed=45.0,
            warning_radius=550.0,
            visible_radius=420.0,
            pull_radius=200.0,
            light_color=glm.vec3(1.0, 0.85, 0.5),
            ambient_color=glm.vec3(0.95, 0.6, 0.2),
            description="Buraco negro estelar na constelação do Cisne a 7.000 anos-luz, famoso pela aposta de Hawking e Thorne.",
        ))

        # ---------------------------------------------------------------------
        # 2. Gargantua (Sistema Binário Relativístico: Setor Leste: +X)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="Gargantua (Sistema Binário Relativístico)",
            position=glm.vec3(800.0, 80.0, -200.0),
            scale=28.0,
            model_filename="black_hole_12.glb",
            models_dir=models_dir,
            accretion_rotation_speed=30.0,
            warning_radius=550.0,
            visible_radius=450.0,
            pull_radius=210.0,
            light_color=glm.vec3(1.0, 0.7, 0.3),
            ambient_color=glm.vec3(0.85, 0.45, 0.15),
            description="Buraco negro massivo com disco de acreção incandescente e lente gravitacional.",
        ))

        # ---------------------------------------------------------------------
        # 3. Sagitário A* (Buraco Negro Supermassivo: Setor Núcleo Profundo: -X, -Z)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="Sagitário A* (🌀 O Gigante da Nossa Casa)",
            position=glm.vec3(-950.0, -120.0, -950.0),
            scale=45.0,
            model_filename="black_hole_galaxy.glb",
            models_dir=models_dir,
            accretion_rotation_speed=25.0,
            warning_radius=700.0,
            visible_radius=550.0,
            pull_radius=250.0,
            light_color=glm.vec3(0.8, 0.7, 1.0),
            ambient_color=glm.vec3(0.7, 0.5, 0.95),
            description="No centro da Via Láctea a 26.000 anos-luz, 4,3 milhões de massas solares e imagem do EHT em 2022.",
        ))

        # ---------------------------------------------------------------------
        # 4. Gaia BH1 (O Vizinho Silencioso: Setor Sudeste: +X, +Z)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="Gaia BH1 (🔭 O Vizinho Silencioso)",
            position=glm.vec3(700.0, -90.0, 650.0),
            scale=22.0,
            model_filename="black_hole (1).glb",
            models_dir=models_dir,
            accretion_rotation_speed=55.0,
            warning_radius=500.0,
            visible_radius=400.0,
            pull_radius=180.0,
            light_color=glm.vec3(0.5, 0.8, 1.0),
            ambient_color=glm.vec3(0.3, 0.6, 0.9),
            description="O buraco negro mais próximo da Terra a 1.600 anos-luz, silencioso e descoberto pelo satélite Gaia em 2022.",
        ))

        # ---------------------------------------------------------------------
        # 5. GW150914 (O Que Fez o Espaço Tremer: Setor Sudoeste: -X, +Z)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="GW150914 (🌊 O Que Fez o Espaço Tremer)",
            position=glm.vec3(-750.0, 110.0, 600.0),
            scale=22.0,
            model_filename="black_hole (2).glb",
            models_dir=models_dir,
            accretion_rotation_speed=50.0,
            warning_radius=500.0,
            visible_radius=400.0,
            pull_radius=180.0,
            light_color=glm.vec3(1.0, 0.35, 0.3),
            ambient_color=glm.vec3(0.9, 0.25, 0.25),
            description="Fusão de dois buracos negros a 1,3 mil milhões de anos-luz, detetada por ondas gravitacionais pelo LIGO em 2015.",
        ))

        # ---------------------------------------------------------------------
        # 6. M87* (O Primeiro Retrato: Setor Zénite / Superior: +Y)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="M87* (🔥 O Primeiro Retrato)",
            position=glm.vec3(150.0, 750.0, -300.0),
            scale=26.0,
            model_filename="black_hole (3).glb",
            models_dir=models_dir,
            accretion_rotation_speed=35.0,
            warning_radius=520.0,
            visible_radius=420.0,
            pull_radius=190.0,
            light_color=glm.vec3(1.0, 0.6, 0.2),
            ambient_color=glm.vec3(0.85, 0.5, 0.1),
            description="No centro da galáxia Messier 87 a 55 milhões de anos-luz, 6,5 mil milhões de massas solares e primeiro fotografado.",
        ))

        # ---------------------------------------------------------------------
        # 7. Sagittarius B2 (Gargantua Secundário Hiperdenso: Setor Nadir / Inferior: -Y)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="Sagittarius B2 (Gargantua Secundário Hiperdenso)",
            position=glm.vec3(-250.0, -750.0, 350.0),
            scale=28.0,
            model_filename="black_hole_12 (1).glb",
            models_dir=models_dir,
            accretion_rotation_speed=32.0,
            warning_radius=540.0,
            visible_radius=420.0,
            pull_radius=200.0,
            light_color=glm.vec3(0.85, 0.4, 0.95),
            ambient_color=glm.vec3(0.7, 0.3, 0.85),
            description="Singularidade gémea hiperdensa com oscilações violeta no tecido do espaço-tempo.",
        ))

        # ---------------------------------------------------------------------
        # 8. Anomalia Gravitacional Primordial (Setor Sul / Traseiro: +Z)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="Anomalia Primordial (Buraco Negro Exótico)",
            position=glm.vec3(0.0, -50.0, 850.0),
            scale=25.0,
            model_filename="not_a_black_hole_-_1.glb",
            models_dir=models_dir,
            accretion_rotation_speed=40.0,
            warning_radius=500.0,
            visible_radius=400.0,
            pull_radius=190.0,
            light_color=glm.vec3(0.4, 1.0, 0.8),
            ambient_color=glm.vec3(0.2, 0.85, 0.65),
            description="Anomalia misteriosa com distorção gravitacional quântica única.",
        ))

        # Inicializa o subsistema de corpos celestes em atração gravitacional
        self.infall_system = BlackHoleInfallSystem(models_dir, self.black_holes)

    def reveal_all(self) -> None:
        """Revela todas as singularidades no espaço exterior."""
        self.all_revealed = True
        for bh in self.black_holes:
            bh.is_revealed = True
        print("[Buraco Negro] Todas as 8 singularidades cósmicas reveladas no espaço profundo!")

    def align_primary_ahead(self, camera_pos: glm.vec3, camera_front: glm.vec3, distance: float = 260.0) -> None:
        """
        Posiciona a singularidade primária diretamente à frente da trajetória da câmara.
        Garante que, após 10 segundos de avanço com a seta para cima, o utilizador
        vê o buraco negro imediatamente à sua frente.
        """
        if self.black_holes:
            primary = self.black_holes[0]
            primary.position = camera_pos + glm.normalize(camera_front) * distance
            primary.is_revealed = True
            print(f"[Buraco Negro] {primary.name} posicionado diretamente à frente em {primary.position}!")

    def get_primary(self) -> BlackHole:
        """Retorna o buraco negro primário (Cygnus X-1)."""
        return self.black_holes[0]

    def get_nearest(self, pos: glm.vec3) -> BlackHole:
        """Retorna o buraco negro mais próximo da coordenada fornecida."""
        return min(self.black_holes, key=lambda bh: glm.length(bh.position - pos))

    def update(self, delta_time: float) -> None:
        """Atualiza a rotação dos discos de acreção e os corpos em atração de queda."""
        for bh in self.black_holes:
            bh.update(delta_time)
        self.infall_system.update(delta_time, self.black_holes)

    def check_proximity(self, camera_pos: glm.vec3) -> Optional[Dict[str, Any]]:
        """
        Calcula a proximidade da câmara aos buracos negros.
        Retorna informações para o alerta na interface caso esteja na área de atuação.
        """
        closest_info = None
        min_dist = float("inf")

        for bh in self.black_holes:
            dist = glm.length(bh.position - camera_pos)
            if dist < bh.warning_radius and dist < min_dist:
                min_dist = dist
                closest_info = {
                    "name": bh.name,
                    "distance": dist,
                    "warning_radius": bh.warning_radius,
                    "visible_radius": bh.visible_radius,
                    "pull_radius": bh.pull_radius,
                    "position": bh.position,
                    "is_critical": dist < bh.pull_radius,
                }

        return closest_info

    def draw(self, shader: Shader, view: glm.mat4, proj: glm.mat4, view_pos: glm.vec3) -> None:
        """Renderiza todas as singularidades e a matéria em queda de acreção que se encontrem visíveis."""
        for bh in self.black_holes:
            if bh.is_visible_from(view_pos):
                bh.draw(shader, view, proj, view_pos)
        self.infall_system.draw(shader, view, proj, view_pos, self.black_holes)

    def cycle_next(self) -> BlackHole:
        """Alterna para o próximo buraco negro (Teclas G e ALT)."""
        self.current_index = (self.current_index + 1) % len(self.black_holes)
        selected = self.black_holes[self.current_index]
        print(f"[Buraco Negro] Foco alternado ({self.current_index + 1}/{len(self.black_holes)}): {selected.name}")
        return selected

    def get_current(self) -> BlackHole:
        """Retorna o buraco negro atualmente selecionado."""
        return self.black_holes[self.current_index]
